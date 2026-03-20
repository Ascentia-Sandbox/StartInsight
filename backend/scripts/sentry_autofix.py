"""Sentry auto-fix script for known error patterns.

Reads SENTRY_ISSUE_TITLE and ERROR_PATTERN from environment variables,
matches against known fixable patterns, and applies the fix.

Called by .github/workflows/sentry-autofix.yml via repository_dispatch.

Safety: Only patterns verified manually >=2 times are auto-fixable.
All PRs created from this script require human review.
"""

import os
import re
import sys

# Known auto-fixable patterns: (regex, description, fix function)
KNOWN_PATTERNS: list[tuple[str, str, str]] = [
    (
        r"ConnectionDoesNotExistError",
        "DB session held too long during async operation",
        "connection_does_not_exist",
    ),
    (
        r"MaxClientsInSessionMode",
        "DB pool size exceeds Supabase session-mode limit",
        "max_clients_pool",
    ),
    (
        r"429.*Resource exhausted",
        "Gemini API rate limit exceeded",
        "gemini_rate_limit",
    ),
    (
        r"asyncio\.TimeoutError.*enhanced_analyzer",
        "LLM call timeout in enhanced analyzer",
        "analyzer_timeout",
    ),
]


def fix_connection_does_not_exist() -> bool:
    """Add retry wrapper guidance for DB session management.

    This pattern occurs when a DB session is held open during a long
    async operation (e.g., LLM call). The fix is to use micro-sessions.
    """
    target = "backend/app/worker.py"
    if not os.path.exists(target):
        print(f"Target file not found: {target}")
        return False

    with open(target) as f:
        content = f.read()

    # Check if fix already applied
    if "# AUTOFIX: micro-session pattern" in content:
        print("Fix already applied to worker.py")
        return False

    # Add a comment marker at the top of the file to indicate the fix was applied
    # The actual refactoring requires human review, so we add guidance
    marker = (
        "# AUTOFIX: micro-session pattern — split long-running tasks into\n"
        "# separate DB sessions (fetch → expunge, process, write) to prevent\n"
        "# ConnectionDoesNotExistError. See memory-bank for pattern details.\n"
    )

    if content.startswith('"""'):
        # Insert after docstring
        end_doc = content.index('"""', 3) + 3
        content = content[:end_doc] + "\n" + marker + content[end_doc:]
    else:
        content = marker + content

    with open(target, "w") as f:
        f.write(content)

    return True


def fix_max_clients_pool() -> bool:
    """Reduce DB pool_size in config.py to prevent MaxClientsInSessionMode."""
    target = "backend/app/core/config.py"
    if not os.path.exists(target):
        print(f"Target file not found: {target}")
        return False

    with open(target) as f:
        content = f.read()

    # Look for pool_size > 5 and reduce it
    new_content = re.sub(
        r"db_pool_size:\s*int\s*=\s*(\d+)",
        lambda m: "db_pool_size: int = 5" if int(m.group(1)) > 5 else m.group(0),
        content,
    )
    new_content = re.sub(
        r"db_max_overflow:\s*int\s*=\s*(\d+)",
        lambda m: "db_max_overflow: int = 10" if int(m.group(1)) > 10 else m.group(0),
        new_content,
    )

    if new_content == content:
        print("Pool size already at safe levels")
        return False

    with open(target, "w") as f:
        f.write(new_content)

    return True


def fix_gemini_rate_limit() -> bool:
    """Increase Gemini retry wait times to handle 429 rate limits."""
    target = "backend/app/agents/enhanced_analyzer.py"
    if not os.path.exists(target):
        print(f"Target file not found: {target}")
        return False

    with open(target) as f:
        content = f.read()

    # Increase wait_exponential min from <60 to 60
    new_content = re.sub(
        r"wait_exponential\(min=(\d+),\s*max=(\d+)\)",
        lambda m: "wait_exponential(min=60, max=120)" if int(m.group(1)) < 60 else m.group(0),
        content,
    )

    if new_content == content:
        print("Retry wait times already at safe levels")
        return False

    with open(target, "w") as f:
        f.write(new_content)

    return True


def fix_analyzer_timeout() -> bool:
    """Increase LLM call timeout in enhanced analyzer."""
    target = "backend/app/agents/enhanced_analyzer.py"
    if not os.path.exists(target):
        print(f"Target file not found: {target}")
        return False

    with open(target) as f:
        content = f.read()

    # Increase LLM agent timeout from <120 to 120 (scoped to agent.run calls)
    new_content = re.sub(
        r"(agent\.run\([^)]*?)timeout=(\d+)",
        lambda m: (
            m.group(1) + ("timeout=120" if int(m.group(2)) < 120 else f"timeout={m.group(2)}")
        ),
        content,
    )

    if new_content == content:
        print("Timeout already at safe level")
        return False

    with open(target, "w") as f:
        f.write(new_content)

    return True


FIX_FUNCTIONS = {
    "connection_does_not_exist": fix_connection_does_not_exist,
    "max_clients_pool": fix_max_clients_pool,
    "gemini_rate_limit": fix_gemini_rate_limit,
    "analyzer_timeout": fix_analyzer_timeout,
}


def main():
    title = os.environ.get("SENTRY_ISSUE_TITLE", "")
    pattern = os.environ.get("ERROR_PATTERN", "")
    issue_id = os.environ.get("SENTRY_ISSUE_ID", "unknown")
    issue_url = os.environ.get("SENTRY_ISSUE_URL", "")

    search_text = f"{title} {pattern}"
    print(f"Matching error: {search_text}")
    print(f"Sentry issue: {issue_id} ({issue_url})")

    matched = False
    for regex, description, fix_key in KNOWN_PATTERNS:
        if re.search(regex, search_text, re.IGNORECASE):
            print(f"Matched pattern: {description} ({fix_key})")
            fix_fn = FIX_FUNCTIONS.get(fix_key)
            if fix_fn and fix_fn():
                print(f"Fix applied: {fix_key}")
                matched = True
                # Write GitHub Actions output
                github_output = os.environ.get("GITHUB_OUTPUT", "")
                if github_output:
                    with open(github_output, "a") as f:
                        f.write("fixed=true\n")
                break
            else:
                print("Fix function returned False (already applied or target missing)")

    if not matched:
        print(f"No matching pattern found for: {search_text}")
        github_output = os.environ.get("GITHUB_OUTPUT", "")
        if github_output:
            with open(github_output, "a") as f:
                f.write("fixed=false\n")
        sys.exit(0)  # Don't fail — unmatched patterns handled by workflow


if __name__ == "__main__":
    main()
