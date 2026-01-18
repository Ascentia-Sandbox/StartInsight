"""Test Phase 1.8: Documentation."""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_backend_readme_exists():
    """Test that backend README.md exists."""
    logger.info("Testing backend README.md existence...")

    readme_path = Path("README.md")
    assert readme_path.exists(), "backend/README.md not found"

    logger.info("✓ backend/README.md exists")


def test_backend_readme_content():
    """Test that backend README.md has required sections."""
    logger.info("Testing backend README.md content...")

    required_sections = [
        "# StartInsight Backend",
        "## Tech Stack",
        "## Prerequisites",
        "## Quick Start",
        "## Project Structure",
        "## API Endpoints",
        "## Development Workflow",
        "## Docker Services",
        "## Troubleshooting",
        "## Environment Variables Reference",
        "## Development Status",
    ]

    with open("README.md", "r") as f:
        content = f.read()

    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)

    assert not missing_sections, f"Missing sections in README: {missing_sections}"

    logger.info(f"✓ All {len(required_sections)} required sections present")


def test_env_example_documented():
    """Test that .env.example is referenced in README."""
    logger.info("Testing .env.example documentation...")

    with open("README.md", "r") as f:
        content = f.read()

    assert ".env.example" in content
    assert "DATABASE_URL" in content
    assert "REDIS_URL" in content
    assert "FIRECRAWL_API_KEY" in content

    logger.info("✓ Environment variables documented in README")


def test_api_endpoints_documented():
    """Test that API endpoints are documented."""
    logger.info("Testing API endpoints documentation...")

    with open("README.md", "r") as f:
        content = f.read()

    documented_endpoints = [
        "/health",
        "/api/signals",
        "/api/signals/{id}",
        "/api/signals/stats/summary",
    ]

    missing_endpoints = []
    for endpoint in documented_endpoints:
        if endpoint not in content:
            missing_endpoints.append(endpoint)

    assert not missing_endpoints, f"Missing endpoints: {missing_endpoints}"

    logger.info(f"✓ All {len(documented_endpoints)} endpoints documented")


def test_phase_1_status_documented():
    """Test that Phase 1 completion is documented."""
    logger.info("Testing Phase 1 status documentation...")

    with open("README.md", "r") as f:
        content = f.read()

    required_phases = [
        "1.1: Project Initialization",
        "1.2: Database Setup",
        "1.3: Firecrawl Integration",
        "1.4: Task Queue Setup",
        "1.5: FastAPI Endpoints",
        "1.6: Environment & Configuration",
        "1.7: Testing & Validation",
        "1.8: Documentation",
    ]

    missing_phases = []
    for phase in required_phases:
        if phase not in content:
            missing_phases.append(phase)

    assert not missing_phases, f"Missing phases: {missing_phases}"

    logger.info(f"✓ All {len(required_phases)} phases documented")


def test_troubleshooting_section():
    """Test that troubleshooting section has helpful content."""
    logger.info("Testing troubleshooting section...")

    with open("README.md", "r") as f:
        content = f.read()

    troubleshooting_topics = [
        "Database Connection Issues",
        "Redis Connection Issues",
        "Port Already in Use",
        "Dependency Issues",
    ]

    missing_topics = []
    for topic in troubleshooting_topics:
        if topic not in content:
            missing_topics.append(topic)

    assert not missing_topics, f"Missing troubleshooting topics: {missing_topics}"

    logger.info(f"✓ All {len(troubleshooting_topics)} troubleshooting topics present")


def test_docker_services_documented():
    """Test that Docker services are documented."""
    logger.info("Testing Docker services documentation...")

    with open("README.md", "r") as f:
        content = f.read()

    assert "PostgreSQL 16" in content
    assert "Redis 7" in content
    assert "5433" in content  # PostgreSQL port
    assert "6379" in content  # Redis port

    logger.info("✓ Docker services documented")


def run_all_tests():
    """Run all Phase 1.8 tests."""
    logger.info("=" * 60)
    logger.info("Phase 1.8 Test Suite: Documentation")
    logger.info("=" * 60 + "\n")

    try:
        test_backend_readme_exists()
        test_backend_readme_content()
        test_env_example_documented()
        test_api_endpoints_documented()
        test_phase_1_status_documented()
        test_troubleshooting_section()
        test_docker_services_documented()

        logger.info("=" * 60)
        logger.info("✓ ALL PHASE 1.8 TESTS PASSED")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ PHASE 1.8 TESTS FAILED: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
