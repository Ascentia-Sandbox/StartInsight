"""LinkedIn posting service — Marketing API or Make.com webhook fallback."""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def post_to_linkedin(content: str) -> dict:
    """Post to LinkedIn company page. Falls back to Make.com webhook if no API token."""

    # Prefer Make.com webhook (zero-setup, free tier)
    if settings.linkedin_webhook_url:
        return await _post_via_webhook(content)

    # Direct LinkedIn Marketing API
    if settings.linkedin_access_token and settings.linkedin_company_id:
        return await _post_via_api(content)

    raise RuntimeError(
        "LinkedIn not configured — set LINKEDIN_WEBHOOK_URL or LINKEDIN_ACCESS_TOKEN"
    )


async def _post_via_webhook(content: str) -> dict:
    """Post via Make.com/n8n webhook — sends JSON, automation handles LinkedIn."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            settings.linkedin_webhook_url,
            json={"content": content, "source": "startinsight-gtm"},
        )
        resp.raise_for_status()

    logger.info("LinkedIn post sent via webhook")
    return {"id": "webhook", "text": content}


async def _post_via_api(content: str) -> dict:
    """Post via LinkedIn Marketing API v2."""
    author = f"urn:li:organization:{settings.linkedin_company_id}"
    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.linkedin.com/v2/ugcPosts",
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.linkedin_access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    post_id = data.get("id", "unknown")
    logger.info(f"LinkedIn post published: {post_id}")
    return {"id": post_id, "text": content}
