"""Report Generator Service - Generate PDF reports and scheduled digests.

Sprint 3.3: Provides report generation capabilities including:
- PDF export for investor-ready presentations
- HTML report generation
- Scheduled weekly digest emails
- Report templating and formatting
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.market_intel_agent import (
    MarketIntelligenceReport,
    generate_market_report,
    generate_weekly_digest,
)

logger = logging.getLogger(__name__)


# ============================================================================
# REPORT TEMPLATES
# ============================================================================

HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --primary: #3B82F6;
            --secondary: #10B981;
            --text: #1F2937;
            --bg: #F9FAFB;
            --border: #E5E7EB;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: white;
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid var(--primary);
        }}
        .header h1 {{
            font-size: 28px;
            color: var(--primary);
            margin-bottom: 8px;
        }}
        .header .subtitle {{
            color: #6B7280;
            font-size: 14px;
        }}
        .section {{
            margin-bottom: 32px;
        }}
        .section h2 {{
            font-size: 20px;
            color: var(--primary);
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }}
        .section h3 {{
            font-size: 16px;
            color: var(--text);
            margin-bottom: 12px;
        }}
        .executive-summary {{
            background: var(--bg);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid var(--primary);
            margin-bottom: 24px;
        }}
        .market-sizing {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .market-card {{
            background: var(--bg);
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        }}
        .market-card .label {{
            font-size: 12px;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .market-card .value {{
            font-size: 24px;
            font-weight: 700;
            color: var(--primary);
            margin: 8px 0;
        }}
        .market-card .description {{
            font-size: 12px;
            color: #6B7280;
        }}
        .benchmark-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
        }}
        .benchmark-table th,
        .benchmark-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        .benchmark-table th {{
            background: var(--bg);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #6B7280;
        }}
        .opportunity-card {{
            background: var(--bg);
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 16px;
        }}
        .opportunity-card .keyword {{
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 8px;
        }}
        .opportunity-card .score {{
            display: inline-block;
            background: var(--secondary);
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .insights-list, .recommendations-list {{
            list-style: none;
            padding: 0;
        }}
        .insights-list li, .recommendations-list li {{
            padding: 12px 0;
            padding-left: 24px;
            position: relative;
            border-bottom: 1px solid var(--border);
        }}
        .insights-list li:last-child, .recommendations-list li:last-child {{
            border-bottom: none;
        }}
        .insights-list li::before {{
            content: "\\2022";
            color: var(--primary);
            font-size: 20px;
            position: absolute;
            left: 0;
            top: 10px;
        }}
        .recommendations-list li::before {{
            content: "\\2713";
            color: var(--secondary);
            font-size: 16px;
            font-weight: bold;
            position: absolute;
            left: 0;
            top: 12px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
            text-align: center;
            color: #6B7280;
            font-size: 12px;
        }}
        @media print {{
            body {{
                padding: 20px;
            }}
            .section {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p class="subtitle">Generated on {generated_date} | Report ID: {report_id}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="executive-summary">
            {executive_summary}
        </div>
    </div>

    {market_sizing_section}

    {benchmarks_section}

    {opportunities_section}

    <div class="section">
        <h2>Key Insights</h2>
        <ul class="insights-list">
            {key_insights}
        </ul>
    </div>

    <div class="section">
        <h2>Strategic Recommendations</h2>
        <ul class="recommendations-list">
            {recommendations}
        </ul>
    </div>

    <div class="footer">
        <p>This report was generated by StartInsight Market Intelligence</p>
        <p>&copy; {year} StartInsight. All rights reserved.</p>
    </div>
</body>
</html>
"""


# ============================================================================
# REPORT GENERATOR CLASS
# ============================================================================

class ReportGenerator:
    """
    Service for generating various report formats from MarketIntelligenceReport.

    Supports:
    - HTML reports (for web display)
    - PDF reports (for download/print)
    - Markdown reports (for email digests)
    """

    def __init__(self):
        """Initialize the report generator."""
        self.logger = logger

    def generate_html_report(self, report: MarketIntelligenceReport) -> str:
        """
        Generate HTML report from MarketIntelligenceReport.

        Args:
            report: Market intelligence report data

        Returns:
            HTML string
        """
        # Format market sizing section
        market_sizing_section = ""
        if report.market_sizing:
            ms = report.market_sizing
            market_sizing_section = f"""
    <div class="section">
        <h2>Market Sizing</h2>
        <div class="market-sizing">
            <div class="market-card">
                <div class="label">TAM</div>
                <div class="value">{ms.tam.get('value', 'N/A')}</div>
                <div class="description">{ms.tam.get('description', 'Total Addressable Market')}</div>
            </div>
            <div class="market-card">
                <div class="label">SAM</div>
                <div class="value">{ms.sam.get('value', 'N/A')}</div>
                <div class="description">{ms.sam.get('description', 'Serviceable Addressable Market')}</div>
            </div>
            <div class="market-card">
                <div class="label">SOM</div>
                <div class="value">{ms.som.get('value', 'N/A')}</div>
                <div class="description">{ms.som.get('description', 'Serviceable Obtainable Market')}</div>
            </div>
        </div>
        <p><strong>Methodology:</strong> {ms.methodology}</p>
        <p><strong>Key Assumptions:</strong></p>
        <ul>
            {''.join(f'<li>{a}</li>' for a in ms.assumptions)}
        </ul>
        <p><strong>Confidence Level:</strong> {ms.confidence_level.title()}</p>
    </div>
"""

        # Format benchmarks section
        benchmarks_section = ""
        if report.industry_benchmarks:
            rows = "".join(
                f"""
            <tr>
                <td>{b.metric_name}</td>
                <td>{b.industry_average}</td>
                <td>{b.top_performer}</td>
                <td style="font-weight: 600; color: var(--primary);">{b.startup_target}</td>
            </tr>"""
                for b in report.industry_benchmarks
            )
            benchmarks_section = f"""
    <div class="section">
        <h2>Industry Benchmarks</h2>
        <table class="benchmark-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Industry Average</th>
                    <th>Top Performer</th>
                    <th>Your Target</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
"""

        # Format opportunities section
        opportunities_section = ""
        if report.trend_opportunities:
            opp_cards = "".join(
                f"""
            <div class="opportunity-card">
                <div class="keyword">{o.trend_keyword} <span class="score">Score: {o.opportunity_score}/100</span></div>
                <p>{o.business_implications}</p>
                <p><strong>Time Sensitivity:</strong> {o.time_sensitivity.title()}</p>
                <p><strong>Action Items:</strong></p>
                <ul>
                    {''.join(f'<li>{a}</li>' for a in o.action_items)}
                </ul>
            </div>"""
                for o in report.trend_opportunities
            )
            opportunities_section = f"""
    <div class="section">
        <h2>Trend Opportunities</h2>
        {opp_cards}
    </div>
"""

        # Format key insights
        key_insights = "".join(f"<li>{insight}</li>" for insight in report.key_insights)

        # Format recommendations
        recommendations = "".join(f"<li>{rec}</li>" for rec in report.recommendations)

        # Build final HTML
        html = HTML_REPORT_TEMPLATE.format(
            title=report.title,
            generated_date=datetime.fromisoformat(report.generated_at).strftime("%B %d, %Y"),
            report_id=report.report_id,
            executive_summary=report.executive_summary,
            market_sizing_section=market_sizing_section,
            benchmarks_section=benchmarks_section,
            opportunities_section=opportunities_section,
            key_insights=key_insights,
            recommendations=recommendations,
            year=datetime.now(UTC).year,
        )

        self.logger.info(f"Generated HTML report for {report.report_id}")
        return html

    def generate_markdown_report(self, report: MarketIntelligenceReport) -> str:
        """
        Generate Markdown report from MarketIntelligenceReport.

        Suitable for email digests and plain text displays.

        Args:
            report: Market intelligence report data

        Returns:
            Markdown string
        """
        lines = [
            f"# {report.title}",
            "",
            f"*Generated: {datetime.fromisoformat(report.generated_at).strftime('%B %d, %Y')} | Report ID: {report.report_id}*",
            "",
            "## Executive Summary",
            "",
            report.executive_summary,
            "",
        ]

        # Market sizing
        if report.market_sizing:
            ms = report.market_sizing
            lines.extend([
                "## Market Sizing",
                "",
                "| Market | Value | Description |",
                "|--------|-------|-------------|",
                f"| TAM | {ms.tam.get('value', 'N/A')} | {ms.tam.get('description', '')} |",
                f"| SAM | {ms.sam.get('value', 'N/A')} | {ms.sam.get('description', '')} |",
                f"| SOM | {ms.som.get('value', 'N/A')} | {ms.som.get('description', '')} |",
                "",
                f"**Methodology:** {ms.methodology}",
                "",
                "**Key Assumptions:**",
            ])
            for assumption in ms.assumptions:
                lines.append(f"- {assumption}")
            lines.extend(["", f"**Confidence Level:** {ms.confidence_level.title()}", ""])

        # Industry benchmarks
        if report.industry_benchmarks:
            lines.extend([
                "## Industry Benchmarks",
                "",
                "| Metric | Industry Avg | Top Performer | Your Target |",
                "|--------|--------------|---------------|-------------|",
            ])
            for b in report.industry_benchmarks:
                lines.append(f"| {b.metric_name} | {b.industry_average} | {b.top_performer} | **{b.startup_target}** |")
            lines.append("")

        # Trend opportunities
        if report.trend_opportunities:
            lines.extend(["## Trend Opportunities", ""])
            for o in report.trend_opportunities:
                lines.extend([
                    f"### {o.trend_keyword} (Score: {o.opportunity_score}/100)",
                    "",
                    o.business_implications,
                    "",
                    f"**Time Sensitivity:** {o.time_sensitivity.title()}",
                    "",
                    "**Action Items:**",
                ])
                for action in o.action_items:
                    lines.append(f"- {action}")
                lines.append("")

        # Key insights
        lines.extend(["## Key Insights", ""])
        for insight in report.key_insights:
            lines.append(f"- {insight}")
        lines.append("")

        # Recommendations
        lines.extend(["## Strategic Recommendations", ""])
        for rec in report.recommendations:
            lines.append(f"1. {rec}")
        lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            "*This report was generated by StartInsight Market Intelligence*",
        ])

        markdown = "\n".join(lines)
        self.logger.info(f"Generated Markdown report for {report.report_id}")
        return markdown

    async def generate_pdf_report(self, report: MarketIntelligenceReport) -> bytes:
        """
        Generate PDF report from MarketIntelligenceReport.

        Uses HTML-to-PDF conversion with weasyprint (if available)
        or returns HTML with print-friendly styling.

        Args:
            report: Market intelligence report data

        Returns:
            PDF bytes or HTML bytes with print CSS
        """
        html = self.generate_html_report(report)

        try:
            # Try to use weasyprint for PDF generation
            from weasyprint import HTML as WeasyHTML

            pdf_bytes = WeasyHTML(string=html).write_pdf()
            self.logger.info(f"Generated PDF report for {report.report_id} using weasyprint")
            return pdf_bytes

        except ImportError:
            # Fallback: return HTML with print CSS
            self.logger.warning("weasyprint not available, returning HTML with print CSS")
            return html.encode("utf-8")

        except Exception as e:
            self.logger.error(f"PDF generation failed: {type(e).__name__} - {e}")
            # Return HTML as fallback
            return html.encode("utf-8")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def generate_insight_report_html(
    insight_id: UUID,
    session: AsyncSession,
    report_type: str = "market_sizing",
) -> str:
    """
    Generate HTML report for an insight.

    Args:
        insight_id: Insight ID
        session: Database session
        report_type: Report type

    Returns:
        HTML string
    """
    report = await generate_market_report(
        insight_id=insight_id,
        session=session,
        report_type=report_type,
    )
    generator = ReportGenerator()
    return generator.generate_html_report(report)


async def generate_insight_report_pdf(
    insight_id: UUID,
    session: AsyncSession,
    report_type: str = "market_sizing",
) -> bytes:
    """
    Generate PDF report for an insight.

    Args:
        insight_id: Insight ID
        session: Database session
        report_type: Report type

    Returns:
        PDF bytes
    """
    report = await generate_market_report(
        insight_id=insight_id,
        session=session,
        report_type=report_type,
    )
    generator = ReportGenerator()
    return await generator.generate_pdf_report(report)


async def generate_weekly_digest_html(session: AsyncSession) -> str:
    """
    Generate weekly digest HTML.

    Args:
        session: Database session

    Returns:
        HTML string
    """
    report = await generate_weekly_digest(session)
    generator = ReportGenerator()
    return generator.generate_html_report(report)


async def generate_weekly_digest_markdown(session: AsyncSession) -> str:
    """
    Generate weekly digest Markdown (for email).

    Args:
        session: Database session

    Returns:
        Markdown string
    """
    report = await generate_weekly_digest(session)
    generator = ReportGenerator()
    return generator.generate_markdown_report(report)
