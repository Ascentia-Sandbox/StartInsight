"""Service modules for Phase 5-7.

Phase 5.2: Build Tools (brand packages, landing pages, ads)
Phase 5.3: Export Services (PDF, CSV, JSON)
Phase 5.4: Real-time Feed (Supabase Realtime)
Phase 6.1: Payment Service (Stripe integration)
Phase 6.2: Email Service (Resend integration)
Phase 6.3: Rate Limiter (Redis-based)
Phase 6.4: Team Service (collaboration)
Phase 7.2: API Key Service (public API)
Phase 7.3: Tenant Service (multi-tenancy)
"""

from app.services.api_key_service import (
    APIKeyCreate,
    APIKeyResponse,
    check_api_key_rate_limit,
    check_scope,
    create_api_key,
    record_api_key_usage,
    revoke_api_key,
    validate_api_key,
)
from app.services.brand_generator import BrandPackage, generate_brand_package
from app.services.email_service import (
    send_analysis_ready_email,
    send_daily_digest,
    send_email,
    send_password_reset,
    send_payment_confirmation,
    send_team_invitation,
    send_welcome_email,
)
from app.services.export_service import (
    ExportFormat,
    export_analysis_csv,
    export_analysis_json,
    export_analysis_pdf,
    export_insight_csv,
    export_insight_pdf,
)
from app.services.landing_page import LandingPageTemplate, generate_landing_page
from app.services.payment_service import (
    PRICING_TIERS,
    PricingTier,
    check_tier_limit,
    create_checkout_session,
    create_customer_portal_session,
    get_tier_limits,
    handle_webhook_event,
)
from app.services.realtime_feed import (
    InsightFeedMessage,
    subscribe_to_insights,
    unsubscribe_from_insights,
)

from app.services.team_service import (
    TeamCreate,
    TeamMemberAdd,
    accept_invitation,
    create_team,
    invite_member,
    share_insight_with_team,
)
from app.services.tenant_service import (
    TenantBrandingUpdate,
    TenantCreate,
    configure_custom_domain,
    create_tenant,
    resolve_tenant_from_host,
    update_tenant_branding,
    verify_custom_domain,
)

__all__ = [
    # Phase 5.2: Build Tools
    "BrandPackage",
    "generate_brand_package",
    "LandingPageTemplate",
    "generate_landing_page",
    # Phase 5.3: Export Services
    "ExportFormat",
    "export_insight_pdf",
    "export_insight_csv",
    "export_analysis_pdf",
    "export_analysis_csv",
    "export_analysis_json",
    # Phase 5.4: Real-time Feed
    "InsightFeedMessage",
    "subscribe_to_insights",
    "unsubscribe_from_insights",
    # Phase 6.1: Payments
    "PRICING_TIERS",
    "PricingTier",
    "create_checkout_session",
    "create_customer_portal_session",
    "handle_webhook_event",
    "get_tier_limits",
    "check_tier_limit",
    # Phase 6.2: Email
    "send_email",
    "send_welcome_email",
    "send_daily_digest",
    "send_analysis_ready_email",
    "send_payment_confirmation",
    "send_team_invitation",
    "send_password_reset",
    # Phase 6.4: Teams
    "TeamCreate",
    "TeamMemberAdd",
    "create_team",
    "invite_member",
    "accept_invitation",
    "share_insight_with_team",
    # Phase 7.2: API Keys
    "APIKeyCreate",
    "APIKeyResponse",
    "create_api_key",
    "validate_api_key",
    "check_api_key_rate_limit",
    "record_api_key_usage",
    "revoke_api_key",
    "check_scope",
    # Phase 7.3: Multi-tenancy
    "TenantCreate",
    "TenantBrandingUpdate",
    "create_tenant",
    "update_tenant_branding",
    "configure_custom_domain",
    "verify_custom_domain",
    "resolve_tenant_from_host",
]
