"""Marketing automation module — isolated from main app.

Dependency rule:
  app.marketing.* → CAN import from → app.models.*, app.core.*, app.services.*
  app.*           → NEVER imports from → app.marketing.*

This module can be extracted to a separate service later if needed.
"""
