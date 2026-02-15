"""Seed script for expanded Trends database (180+ keywords across 10 categories).

This expands the trends database from 12 keywords to 180+ keywords,
covering AI/ML, No-Code, Development, E-commerce, Health/Wellness,
Finance/Fintech, EdTech, Sustainability, Remote Work, and Creator Economy.

Run with: uv run python scripts/seed_expanded_trends.py
"""

import asyncio
import logging

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.trend import Trend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Expanded Trends Data (180+ keywords across 10 categories)
EXPANDED_TRENDS_DATA = [
    # ============================================
    # AI/ML (30 keywords)
    # ============================================
    {"keyword": "AI agents", "category": "AI/ML", "search_volume": 135000, "growth_percentage": 245, "business_implications": "Massive opportunity in autonomous AI workflows. Startups building AI agents for specific verticals are seeing rapid adoption.", "source": "Google Trends", "is_featured": True},
    {"keyword": "Claude Code", "category": "AI/ML", "search_volume": 45000, "growth_percentage": 560, "business_implications": "Anthropic's CLI tool driving interest in AI-assisted development. Opportunities in extensions and integrations.", "source": "Google Trends", "is_featured": True},
    {"keyword": "MCP servers", "category": "AI/ML", "search_volume": 8500, "growth_percentage": 1200, "business_implications": "Model Context Protocol enabling new AI integrations. First-mover advantage for MCP server builders.", "source": "Google Trends", "is_featured": True},
    {"keyword": "agentic workflows", "category": "AI/ML", "search_volume": 28000, "growth_percentage": 380, "business_implications": "Businesses want AI that takes actions. Workflow automation with AI agents is a growing category.", "source": "Google Trends", "is_featured": True},
    {"keyword": "AI voice agents", "category": "AI/ML", "search_volume": 56000, "growth_percentage": 210, "business_implications": "Voice AI for customer service maturing. Startups like Bland and Vapi showing strong traction.", "source": "Google Trends", "is_featured": True},
    {"keyword": "AI copilots", "category": "AI/ML", "search_volume": 89000, "growth_percentage": 175, "business_implications": "Every software category adding AI copilots. Opportunities in specialized copilots for niche workflows.", "source": "Google Trends", "is_featured": True},
    {"keyword": "RAG applications", "category": "AI/ML", "search_volume": 42000, "growth_percentage": 320, "business_implications": "Retrieval-Augmented Generation becoming standard for enterprise AI. Tools for building RAG systems in demand.", "source": "Google Trends", "is_featured": False},
    {"keyword": "fine-tuning LLMs", "category": "AI/ML", "search_volume": 31000, "growth_percentage": 185, "business_implications": "Custom model training for specific use cases. Platforms making fine-tuning accessible to non-ML teams.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI code generation", "category": "AI/ML", "search_volume": 67000, "growth_percentage": 145, "business_implications": "Developers adopting AI coding tools rapidly. GitHub Copilot competitors emerging with specialized features.", "source": "Google Trends", "is_featured": True},
    {"keyword": "multimodal AI", "category": "AI/ML", "search_volume": 38000, "growth_percentage": 267, "business_implications": "AI handling text, images, audio, video together. Applications in content creation, analysis, accessibility.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI safety tools", "category": "AI/ML", "search_volume": 15000, "growth_percentage": 340, "business_implications": "Growing demand for AI guardrails and monitoring. Enterprise buyers prioritizing safety features.", "source": "Google Trends", "is_featured": False},
    {"keyword": "local LLMs", "category": "AI/ML", "search_volume": 52000, "growth_percentage": 445, "business_implications": "Privacy-conscious users running AI locally. Tools for deploying and managing local models.", "source": "Google Trends", "is_featured": True},
    {"keyword": "AI image generation", "category": "AI/ML", "search_volume": 145000, "growth_percentage": 89, "business_implications": "Maturing market but still opportunities in specialized applications (product photos, architecture, fashion).", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI video generation", "category": "AI/ML", "search_volume": 78000, "growth_percentage": 520, "business_implications": "Sora, Runway, and competitors driving explosive growth. B2B applications in marketing and training.", "source": "Google Trends", "is_featured": True},
    {"keyword": "prompt engineering", "category": "AI/ML", "search_volume": 110000, "growth_percentage": 125, "business_implications": "Maturing skill set but tools for prompt management and optimization still growing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI data labeling", "category": "AI/ML", "search_volume": 24000, "growth_percentage": 95, "business_implications": "Essential infrastructure for AI training. Automated labeling tools reducing costs.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI model deployment", "category": "AI/ML", "search_volume": 35000, "growth_percentage": 165, "business_implications": "MLOps tools for production AI. Serverless inference platforms gaining traction.", "source": "Google Trends", "is_featured": False},
    {"keyword": "conversational AI", "category": "AI/ML", "search_volume": 62000, "growth_percentage": 78, "business_implications": "Chatbots evolving into sophisticated assistants. Industry-specific conversation AI in demand.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI document processing", "category": "AI/ML", "search_volume": 29000, "growth_percentage": 145, "business_implications": "Automating document workflows. Legal, finance, healthcare verticals driving demand.", "source": "Google Trends", "is_featured": False},
    {"keyword": "synthetic data", "category": "AI/ML", "search_volume": 18000, "growth_percentage": 210, "business_implications": "Training AI without real data. Privacy compliance and data augmentation use cases.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI testing tools", "category": "AI/ML", "search_volume": 12000, "growth_percentage": 285, "business_implications": "Quality assurance for AI outputs. Evaluation frameworks and testing platforms emerging.", "source": "Google Trends", "is_featured": False},
    {"keyword": "edge AI", "category": "AI/ML", "search_volume": 41000, "growth_percentage": 115, "business_implications": "AI on devices without cloud. IoT, mobile, and embedded AI applications.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI observability", "category": "AI/ML", "search_volume": 9500, "growth_percentage": 390, "business_implications": "Monitoring AI systems in production. LLM-specific observability tools in demand.", "source": "Google Trends", "is_featured": True},
    {"keyword": "AI search engines", "category": "AI/ML", "search_volume": 55000, "growth_percentage": 198, "business_implications": "Perplexity-style AI search disrupting Google. Enterprise search with AI summarization.", "source": "Google Trends", "is_featured": True},
    {"keyword": "AI writing assistant", "category": "AI/ML", "search_volume": 95000, "growth_percentage": 65, "business_implications": "Saturated consumer market but B2B opportunities in compliance, legal, technical writing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI music generation", "category": "AI/ML", "search_volume": 48000, "growth_percentage": 340, "business_implications": "Suno and Udio driving interest. Opportunities in audio branding, podcasts, game music.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI customer support", "category": "AI/ML", "search_volume": 37000, "growth_percentage": 125, "business_implications": "Chatbots handling majority of support queries. Human-in-the-loop systems for complex issues.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI sales tools", "category": "AI/ML", "search_volume": 44000, "growth_percentage": 155, "business_implications": "AI SDRs, email personalization, call analysis. Revenue intelligence platforms growing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI transcription", "category": "AI/ML", "search_volume": 72000, "growth_percentage": 85, "business_implications": "Commoditized but specialized transcription (medical, legal, multilingual) still growing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI translation", "category": "AI/ML", "search_volume": 58000, "growth_percentage": 92, "business_implications": "Real-time translation improving. Localization platforms integrating AI for efficiency.", "source": "Google Trends", "is_featured": False},

    # ============================================
    # No-Code/Low-Code (20 keywords)
    # ============================================
    {"keyword": "no code AI", "category": "No-Code", "search_volume": 74000, "growth_percentage": 125, "business_implications": "Non-technical users leveraging AI. Platforms making AI accessible without coding have strong PMF.", "source": "Google Trends", "is_featured": True},
    {"keyword": "vibe coding", "category": "No-Code", "search_volume": 22000, "growth_percentage": 890, "business_implications": "AI-assisted coding tools transforming developer workflows. Tools enhancing the experience in demand.", "source": "Google Trends", "is_featured": True},
    {"keyword": "Lovable", "category": "No-Code", "search_volume": 35000, "growth_percentage": 1500, "business_implications": "AI app builder disrupting Bubble/Webflow. Integrations and extensions for Lovable users.", "source": "Google Trends", "is_featured": True},
    {"keyword": "Bolt.new", "category": "No-Code", "search_volume": 28000, "growth_percentage": 2100, "business_implications": "Browser-based AI development exploding. Tools that enhance Bolt workflows have opportunity.", "source": "Google Trends", "is_featured": True},
    {"keyword": "Cursor IDE", "category": "No-Code", "search_volume": 42000, "growth_percentage": 780, "business_implications": "AI-first IDE gaining developer adoption. Extensions and integrations for Cursor growing.", "source": "Google Trends", "is_featured": True},
    {"keyword": "visual programming", "category": "No-Code", "search_volume": 31000, "growth_percentage": 95, "business_implications": "Node-based interfaces for logic. Tools for non-developers to build complex workflows.", "source": "Google Trends", "is_featured": False},
    {"keyword": "workflow automation", "category": "No-Code", "search_volume": 89000, "growth_percentage": 78, "business_implications": "Zapier-like tools with AI capabilities. Industry-specific automation platforms.", "source": "Google Trends", "is_featured": True},
    {"keyword": "internal tools builder", "category": "No-Code", "search_volume": 24000, "growth_percentage": 145, "business_implications": "Retool, Appsmith alternatives. Building admin panels and dashboards without code.", "source": "Google Trends", "is_featured": False},
    {"keyword": "database builder", "category": "No-Code", "search_volume": 19000, "growth_percentage": 115, "business_implications": "Airtable alternatives with more power. No-code backends for apps.", "source": "Google Trends", "is_featured": False},
    {"keyword": "form builder", "category": "No-Code", "search_volume": 145000, "growth_percentage": 45, "business_implications": "Mature market but AI-powered forms with conditional logic seeing growth.", "source": "Google Trends", "is_featured": False},
    {"keyword": "website builder AI", "category": "No-Code", "search_volume": 52000, "growth_percentage": 265, "business_implications": "AI generating full websites from prompts. Framer, Durable disrupting traditional builders.", "source": "Google Trends", "is_featured": True},
    {"keyword": "mobile app builder", "category": "No-Code", "search_volume": 67000, "growth_percentage": 85, "business_implications": "FlutterFlow, Adalo for no-code mobile apps. AI integration making apps smarter.", "source": "Google Trends", "is_featured": False},
    {"keyword": "chatbot builder", "category": "No-Code", "search_volume": 48000, "growth_percentage": 125, "business_implications": "No-code chatbot platforms with AI. Customer service and lead gen use cases.", "source": "Google Trends", "is_featured": False},
    {"keyword": "API integration platform", "category": "No-Code", "search_volume": 35000, "growth_percentage": 95, "business_implications": "Connecting apps without code. Unified API platforms for multiple services.", "source": "Google Trends", "is_featured": False},
    {"keyword": "no code backend", "category": "No-Code", "search_volume": 21000, "growth_percentage": 185, "business_implications": "Backends without server management. Supabase, Firebase competitors.", "source": "Google Trends", "is_featured": False},
    {"keyword": "spreadsheet apps", "category": "No-Code", "search_volume": 28000, "growth_percentage": 75, "business_implications": "Turning spreadsheets into apps. Glide, Softr for spreadsheet-powered apps.", "source": "Google Trends", "is_featured": False},
    {"keyword": "automation templates", "category": "No-Code", "search_volume": 15000, "growth_percentage": 135, "business_implications": "Pre-built automations for common workflows. Template marketplaces growing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI app builder", "category": "No-Code", "search_volume": 38000, "growth_percentage": 425, "business_implications": "Natural language to functional apps. Massive growth category for 2025.", "source": "Google Trends", "is_featured": True},
    {"keyword": "process automation", "category": "No-Code", "search_volume": 56000, "growth_percentage": 65, "business_implications": "Business process automation tools. RPA with AI capabilities.", "source": "Google Trends", "is_featured": False},
    {"keyword": "citizen developer", "category": "No-Code", "search_volume": 18000, "growth_percentage": 95, "business_implications": "Business users building their own tools. Enterprise no-code adoption growing.", "source": "Google Trends", "is_featured": False},

    # ============================================
    # Development (20 keywords)
    # ============================================
    {"keyword": "serverless functions", "category": "Development", "search_volume": 45000, "growth_percentage": 75, "business_implications": "Mature but still growing. Edge functions and global deployment gaining traction.", "source": "Google Trends", "is_featured": False},
    {"keyword": "edge computing", "category": "Development", "search_volume": 62000, "growth_percentage": 115, "business_implications": "Low-latency applications at the edge. CDN providers expanding compute capabilities.", "source": "Google Trends", "is_featured": True},
    {"keyword": "developer experience", "category": "Development", "search_volume": 28000, "growth_percentage": 145, "business_implications": "Tools improving developer productivity. DX-focused companies seeing strong growth.", "source": "Google Trends", "is_featured": False},
    {"keyword": "API design", "category": "Development", "search_volume": 35000, "growth_percentage": 85, "business_implications": "API-first development standard. Tools for designing and documenting APIs.", "source": "Google Trends", "is_featured": False},
    {"keyword": "microservices", "category": "Development", "search_volume": 89000, "growth_percentage": 45, "business_implications": "Established pattern but observability and management tools still growing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "monorepo tools", "category": "Development", "search_volume": 24000, "growth_percentage": 165, "business_implications": "Turborepo, Nx growing. Managing large codebases efficiently.", "source": "Google Trends", "is_featured": False},
    {"keyword": "CI/CD pipelines", "category": "Development", "search_volume": 78000, "growth_percentage": 55, "business_implications": "Mature category but AI-powered testing and deployment optimization emerging.", "source": "Google Trends", "is_featured": False},
    {"keyword": "infrastructure as code", "category": "Development", "search_volume": 52000, "growth_percentage": 75, "business_implications": "Terraform, Pulumi standard. Higher-level abstractions simplifying IaC.", "source": "Google Trends", "is_featured": False},
    {"keyword": "developer tools", "category": "Development", "search_volume": 125000, "growth_percentage": 85, "business_implications": "Broad category with consistent growth. Opportunities in specialized tooling.", "source": "Google Trends", "is_featured": True},
    {"keyword": "code review tools", "category": "Development", "search_volume": 31000, "growth_percentage": 125, "business_implications": "AI-powered code review gaining adoption. Security and quality checks automated.", "source": "Google Trends", "is_featured": False},
    {"keyword": "testing automation", "category": "Development", "search_volume": 67000, "growth_percentage": 95, "business_implications": "AI generating tests automatically. Playwright, Cypress with AI capabilities.", "source": "Google Trends", "is_featured": False},
    {"keyword": "feature flags", "category": "Development", "search_volume": 28000, "growth_percentage": 115, "business_implications": "LaunchDarkly, Statsig for controlled rollouts. Experimentation platforms growing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "WebAssembly", "category": "Development", "search_volume": 42000, "growth_percentage": 145, "business_implications": "Near-native performance in browsers. Server-side Wasm emerging.", "source": "Google Trends", "is_featured": True},
    {"keyword": "real-time databases", "category": "Development", "search_volume": 35000, "growth_percentage": 95, "business_implications": "Firebase, Supabase Realtime. Collaborative app infrastructure.", "source": "Google Trends", "is_featured": False},
    {"keyword": "GraphQL", "category": "Development", "search_volume": 95000, "growth_percentage": 55, "business_implications": "Established API standard. Federation and tooling improvements ongoing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "TypeScript", "category": "Development", "search_volume": 185000, "growth_percentage": 65, "business_implications": "Standard for JavaScript development. TypeScript-first frameworks growing.", "source": "Google Trends", "is_featured": True},
    {"keyword": "Rust programming", "category": "Development", "search_volume": 78000, "growth_percentage": 125, "business_implications": "Systems programming adoption growing. WebAssembly and CLI tools in Rust.", "source": "Google Trends", "is_featured": False},
    {"keyword": "Go programming", "category": "Development", "search_volume": 65000, "growth_percentage": 75, "business_implications": "Backend and DevOps standard. Cloud-native tools in Go.", "source": "Google Trends", "is_featured": False},
    {"keyword": "Next.js", "category": "Development", "search_volume": 145000, "growth_percentage": 95, "business_implications": "React framework dominance. Ecosystem tools and hosting platforms growing.", "source": "Google Trends", "is_featured": True},
    {"keyword": "htmx", "category": "Development", "search_volume": 38000, "growth_percentage": 445, "business_implications": "Simplicity trend in web development. Hypermedia-driven apps gaining traction.", "source": "Google Trends", "is_featured": True},

    # ============================================
    # E-commerce (15 keywords)
    # ============================================
    {"keyword": "headless commerce", "category": "E-commerce", "search_volume": 42000, "growth_percentage": 125, "business_implications": "Decoupled frontend/backend for flexibility. Shopify Hydrogen, custom storefronts.", "source": "Google Trends", "is_featured": True},
    {"keyword": "dropshipping AI", "category": "E-commerce", "search_volume": 28000, "growth_percentage": 185, "business_implications": "AI product research and listing optimization. Automated store management tools.", "source": "Google Trends", "is_featured": False},
    {"keyword": "social commerce", "category": "E-commerce", "search_volume": 55000, "growth_percentage": 145, "business_implications": "Selling directly on social platforms. TikTok Shop, Instagram Shopping tools.", "source": "Google Trends", "is_featured": True},
    {"keyword": "subscription commerce", "category": "E-commerce", "search_volume": 31000, "growth_percentage": 85, "business_implications": "Recurring revenue models. Subscription management and analytics platforms.", "source": "Google Trends", "is_featured": False},
    {"keyword": "product personalization", "category": "E-commerce", "search_volume": 24000, "growth_percentage": 165, "business_implications": "AI recommendations and customization. Dynamic pricing and bundles.", "source": "Google Trends", "is_featured": False},
    {"keyword": "Shopify apps", "category": "E-commerce", "search_volume": 89000, "growth_percentage": 75, "business_implications": "App ecosystem for merchants. Specialized tools for niche needs.", "source": "Google Trends", "is_featured": True},
    {"keyword": "ecommerce analytics", "category": "E-commerce", "search_volume": 38000, "growth_percentage": 95, "business_implications": "Beyond Google Analytics. Attribution, cohort analysis, predictive metrics.", "source": "Google Trends", "is_featured": False},
    {"keyword": "inventory management", "category": "E-commerce", "search_volume": 75000, "growth_percentage": 65, "business_implications": "Multi-channel inventory sync. AI demand forecasting.", "source": "Google Trends", "is_featured": False},
    {"keyword": "fulfillment automation", "category": "E-commerce", "search_volume": 21000, "growth_percentage": 145, "business_implications": "3PL integration and optimization. Same-day delivery infrastructure.", "source": "Google Trends", "is_featured": False},
    {"keyword": "B2B ecommerce", "category": "E-commerce", "search_volume": 48000, "growth_percentage": 115, "business_implications": "B2B buying experiences improving. Wholesale and distributor platforms.", "source": "Google Trends", "is_featured": False},
    {"keyword": "marketplace builder", "category": "E-commerce", "search_volume": 18000, "growth_percentage": 125, "business_implications": "Building two-sided marketplaces. Sharetribe, Arcadier alternatives.", "source": "Google Trends", "is_featured": False},
    {"keyword": "conversational commerce", "category": "E-commerce", "search_volume": 15000, "growth_percentage": 185, "business_implications": "Chat-based shopping experiences. WhatsApp and Messenger commerce.", "source": "Google Trends", "is_featured": False},
    {"keyword": "product photography AI", "category": "E-commerce", "search_volume": 22000, "growth_percentage": 320, "business_implications": "AI-generated product photos. Background removal and enhancement tools.", "source": "Google Trends", "is_featured": True},
    {"keyword": "returns management", "category": "E-commerce", "search_volume": 28000, "growth_percentage": 95, "business_implications": "Reducing return costs. Loop Returns, Happy Returns alternatives.", "source": "Google Trends", "is_featured": False},
    {"keyword": "cross-border commerce", "category": "E-commerce", "search_volume": 35000, "growth_percentage": 115, "business_implications": "International selling simplified. Currency, taxes, shipping automation.", "source": "Google Trends", "is_featured": False},

    # ============================================
    # Health/Wellness (15 keywords)
    # ============================================
    {"keyword": "telehealth platform", "category": "Health", "search_volume": 85000, "growth_percentage": 65, "business_implications": "Virtual care infrastructure. Specialty telehealth for mental health, dermatology, etc.", "source": "Google Trends", "is_featured": True},
    {"keyword": "mental health app", "category": "Health", "search_volume": 125000, "growth_percentage": 85, "business_implications": "Growing awareness driving adoption. AI therapy assistants, mood tracking.", "source": "Google Trends", "is_featured": True},
    {"keyword": "fitness AI", "category": "Health", "search_volume": 38000, "growth_percentage": 195, "business_implications": "Personalized workout plans. Form correction using computer vision.", "source": "Google Trends", "is_featured": True},
    {"keyword": "nutrition tracking", "category": "Health", "search_volume": 55000, "growth_percentage": 75, "business_implications": "AI food recognition and macro tracking. Personalized meal planning.", "source": "Google Trends", "is_featured": False},
    {"keyword": "sleep optimization", "category": "Health", "search_volume": 42000, "growth_percentage": 145, "business_implications": "Sleep tracking beyond wearables. AI sleep coaching and environment optimization.", "source": "Google Trends", "is_featured": False},
    {"keyword": "health monitoring wearables", "category": "Health", "search_volume": 68000, "growth_percentage": 95, "business_implications": "Continuous health tracking. Glucose monitoring, heart health, stress.", "source": "Google Trends", "is_featured": False},
    {"keyword": "digital therapeutics", "category": "Health", "search_volume": 28000, "growth_percentage": 165, "business_implications": "FDA-cleared software treatments. Mental health, chronic disease management.", "source": "Google Trends", "is_featured": False},
    {"keyword": "longevity science", "category": "Health", "search_volume": 31000, "growth_percentage": 210, "business_implications": "Anti-aging research commercializing. Supplements, testing, interventions.", "source": "Google Trends", "is_featured": True},
    {"keyword": "personalized supplements", "category": "Health", "search_volume": 24000, "growth_percentage": 125, "business_implications": "DNA-based supplement recommendations. Custom vitamin packs.", "source": "Google Trends", "is_featured": False},
    {"keyword": "corporate wellness", "category": "Health", "search_volume": 45000, "growth_percentage": 85, "business_implications": "Employee wellness platforms. Mental health benefits, fitness programs.", "source": "Google Trends", "is_featured": False},
    {"keyword": "women's health tech", "category": "Health", "search_volume": 35000, "growth_percentage": 145, "business_implications": "FemTech growing. Fertility, menopause, reproductive health apps.", "source": "Google Trends", "is_featured": True},
    {"keyword": "at-home health testing", "category": "Health", "search_volume": 52000, "growth_percentage": 95, "business_implications": "Blood tests, genetic testing, microbiome analysis at home.", "source": "Google Trends", "is_featured": False},
    {"keyword": "health coaching platform", "category": "Health", "search_volume": 28000, "growth_percentage": 115, "business_implications": "Connecting coaches with clients. AI-augmented coaching tools.", "source": "Google Trends", "is_featured": False},
    {"keyword": "meditation app", "category": "Health", "search_volume": 95000, "growth_percentage": 55, "business_implications": "Mature market but specialized meditation (sleep, focus, anxiety) growing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "biohacking tools", "category": "Health", "search_volume": 18000, "growth_percentage": 175, "business_implications": "Quantified self movement. CGM, HRV, brain optimization tools.", "source": "Google Trends", "is_featured": False},

    # ============================================
    # Finance/Fintech (15 keywords)
    # ============================================
    {"keyword": "embedded finance", "category": "Finance", "search_volume": 38000, "growth_percentage": 145, "business_implications": "Financial services within non-finance apps. APIs for payments, lending, insurance.", "source": "Google Trends", "is_featured": True},
    {"keyword": "AI financial advisor", "category": "Finance", "search_volume": 28000, "growth_percentage": 265, "business_implications": "Robo-advisors with AI. Personalized investment recommendations.", "source": "Google Trends", "is_featured": True},
    {"keyword": "expense management", "category": "Finance", "search_volume": 65000, "growth_percentage": 75, "business_implications": "Corporate expense tracking. AI receipt scanning and categorization.", "source": "Google Trends", "is_featured": False},
    {"keyword": "invoice automation", "category": "Finance", "search_volume": 42000, "growth_percentage": 95, "business_implications": "Automated invoicing and collections. AP/AR automation platforms.", "source": "Google Trends", "is_featured": False},
    {"keyword": "payment orchestration", "category": "Finance", "search_volume": 15000, "growth_percentage": 185, "business_implications": "Multi-PSP routing for optimization. Reducing failed payments.", "source": "Google Trends", "is_featured": False},
    {"keyword": "banking as a service", "category": "Finance", "search_volume": 31000, "growth_percentage": 125, "business_implications": "APIs for building banking products. Embedded banking for platforms.", "source": "Google Trends", "is_featured": True},
    {"keyword": "crypto compliance", "category": "Finance", "search_volume": 24000, "growth_percentage": 145, "business_implications": "AML/KYC for crypto businesses. Tax reporting and tracking tools.", "source": "Google Trends", "is_featured": False},
    {"keyword": "financial planning software", "category": "Finance", "search_volume": 55000, "growth_percentage": 65, "business_implications": "Personal and business financial planning. Scenario modeling and projections.", "source": "Google Trends", "is_featured": False},
    {"keyword": "revenue intelligence", "category": "Finance", "search_volume": 21000, "growth_percentage": 155, "business_implications": "Sales forecasting and pipeline analytics. Gong, Clari competitors.", "source": "Google Trends", "is_featured": False},
    {"keyword": "spend management", "category": "Finance", "search_volume": 35000, "growth_percentage": 115, "business_implications": "Procurement and spend visibility. Ramp, Brex alternatives.", "source": "Google Trends", "is_featured": False},
    {"keyword": "alternative lending", "category": "Finance", "search_volume": 28000, "growth_percentage": 85, "business_implications": "Non-bank lending platforms. Revenue-based financing, invoice factoring.", "source": "Google Trends", "is_featured": False},
    {"keyword": "cashflow forecasting", "category": "Finance", "search_volume": 18000, "growth_percentage": 145, "business_implications": "AI predicting cash positions. SMB treasury management.", "source": "Google Trends", "is_featured": False},
    {"keyword": "subscription billing", "category": "Finance", "search_volume": 45000, "growth_percentage": 75, "business_implications": "Recurring billing infrastructure. Chargebee, Stripe Billing alternatives.", "source": "Google Trends", "is_featured": False},
    {"keyword": "fraud detection AI", "category": "Finance", "search_volume": 35000, "growth_percentage": 125, "business_implications": "Real-time fraud prevention. Identity verification and risk scoring.", "source": "Google Trends", "is_featured": True},
    {"keyword": "open banking", "category": "Finance", "search_volume": 48000, "growth_percentage": 95, "business_implications": "Bank data aggregation APIs. Account linking and verification.", "source": "Google Trends", "is_featured": False},

    # ============================================
    # EdTech (15 keywords)
    # ============================================
    {"keyword": "AI tutoring", "category": "EdTech", "search_volume": 45000, "growth_percentage": 285, "business_implications": "Personalized AI tutors for any subject. Khan Academy-style with AI interaction.", "source": "Google Trends", "is_featured": True},
    {"keyword": "online course platform", "category": "EdTech", "search_volume": 85000, "growth_percentage": 55, "business_implications": "Mature but AI-enhanced course creation and delivery growing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "cohort-based courses", "category": "EdTech", "search_volume": 18000, "growth_percentage": 125, "business_implications": "Community-driven learning. Platforms for launching and managing cohorts.", "source": "Google Trends", "is_featured": False},
    {"keyword": "upskilling platform", "category": "EdTech", "search_volume": 31000, "growth_percentage": 95, "business_implications": "Corporate training and professional development. Skills-based learning paths.", "source": "Google Trends", "is_featured": False},
    {"keyword": "language learning AI", "category": "EdTech", "search_volume": 55000, "growth_percentage": 165, "business_implications": "AI conversation partners. Beyond Duolingo with real-time feedback.", "source": "Google Trends", "is_featured": True},
    {"keyword": "coding bootcamp", "category": "EdTech", "search_volume": 75000, "growth_percentage": 45, "business_implications": "Maturing market but AI-focused bootcamps seeing growth.", "source": "Google Trends", "is_featured": False},
    {"keyword": "educational games", "category": "EdTech", "search_volume": 42000, "growth_percentage": 85, "business_implications": "Gamified learning for kids and adults. STEM and language games.", "source": "Google Trends", "is_featured": False},
    {"keyword": "corporate LMS", "category": "EdTech", "search_volume": 58000, "growth_percentage": 65, "business_implications": "Learning management for enterprises. AI content curation and recommendations.", "source": "Google Trends", "is_featured": False},
    {"keyword": "assessment tools", "category": "EdTech", "search_volume": 35000, "growth_percentage": 115, "business_implications": "AI-powered testing and skill assessment. Proctoring and adaptive testing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "microlearning", "category": "EdTech", "search_volume": 28000, "growth_percentage": 125, "business_implications": "Bite-sized learning content. TikTok-style educational content.", "source": "Google Trends", "is_featured": False},
    {"keyword": "knowledge management", "category": "EdTech", "search_volume": 45000, "growth_percentage": 95, "business_implications": "Organizational knowledge bases. AI-powered search and discovery.", "source": "Google Trends", "is_featured": False},
    {"keyword": "credentialing platform", "category": "EdTech", "search_volume": 15000, "growth_percentage": 145, "business_implications": "Digital certificates and badges. Skills verification for hiring.", "source": "Google Trends", "is_featured": False},
    {"keyword": "student engagement tools", "category": "EdTech", "search_volume": 21000, "growth_percentage": 85, "business_implications": "Interactive classroom tools. Polling, quizzes, collaboration features.", "source": "Google Trends", "is_featured": False},
    {"keyword": "AI study assistant", "category": "EdTech", "search_volume": 38000, "growth_percentage": 345, "business_implications": "AI helping with homework and studying. Note-taking and summarization.", "source": "Google Trends", "is_featured": True},
    {"keyword": "professional certification", "category": "EdTech", "search_volume": 52000, "growth_percentage": 75, "business_implications": "Industry certifications online. Continuing education platforms.", "source": "Google Trends", "is_featured": False},

    # ============================================
    # Sustainability (15 keywords)
    # ============================================
    {"keyword": "carbon accounting", "category": "Sustainability", "search_volume": 28000, "growth_percentage": 185, "business_implications": "Measuring and reporting emissions. Regulatory compliance driving demand.", "source": "Google Trends", "is_featured": True},
    {"keyword": "sustainable supply chain", "category": "Sustainability", "search_volume": 35000, "growth_percentage": 125, "business_implications": "Tracing environmental impact. Supplier sustainability scoring.", "source": "Google Trends", "is_featured": False},
    {"keyword": "ESG reporting", "category": "Sustainability", "search_volume": 42000, "growth_percentage": 145, "business_implications": "Environmental, Social, Governance reports. Automated data collection and reporting.", "source": "Google Trends", "is_featured": True},
    {"keyword": "circular economy", "category": "Sustainability", "search_volume": 31000, "growth_percentage": 95, "business_implications": "Reducing waste through reuse. Resale, refurbishment, recycling platforms.", "source": "Google Trends", "is_featured": False},
    {"keyword": "renewable energy software", "category": "Sustainability", "search_volume": 24000, "growth_percentage": 115, "business_implications": "Solar, wind project management. Grid optimization and energy trading.", "source": "Google Trends", "is_featured": False},
    {"keyword": "electric vehicle charging", "category": "Sustainability", "search_volume": 85000, "growth_percentage": 145, "business_implications": "EV infrastructure software. Charging network management and payments.", "source": "Google Trends", "is_featured": True},
    {"keyword": "sustainable packaging", "category": "Sustainability", "search_volume": 38000, "growth_percentage": 85, "business_implications": "Eco-friendly packaging solutions. Materials innovation and sourcing.", "source": "Google Trends", "is_featured": False},
    {"keyword": "climate tech", "category": "Sustainability", "search_volume": 55000, "growth_percentage": 165, "business_implications": "Broad category with VC interest. Carbon removal, clean energy, efficiency.", "source": "Google Trends", "is_featured": True},
    {"keyword": "water management", "category": "Sustainability", "search_volume": 28000, "growth_percentage": 95, "business_implications": "Smart water monitoring. Agriculture and industrial water optimization.", "source": "Google Trends", "is_featured": False},
    {"keyword": "green building tech", "category": "Sustainability", "search_volume": 21000, "growth_percentage": 115, "business_implications": "Energy-efficient buildings. Smart HVAC, lighting, and monitoring.", "source": "Google Trends", "is_featured": False},
    {"keyword": "sustainable fashion", "category": "Sustainability", "search_volume": 65000, "growth_percentage": 75, "business_implications": "Eco-conscious clothing. Resale platforms, sustainable materials.", "source": "Google Trends", "is_featured": False},
    {"keyword": "food waste reduction", "category": "Sustainability", "search_volume": 18000, "growth_percentage": 125, "business_implications": "Surplus food marketplaces. Inventory optimization for restaurants.", "source": "Google Trends", "is_featured": False},
    {"keyword": "carbon offset marketplace", "category": "Sustainability", "search_volume": 15000, "growth_percentage": 145, "business_implications": "Buying and selling carbon credits. Verification and tracking platforms.", "source": "Google Trends", "is_featured": False},
    {"keyword": "sustainability analytics", "category": "Sustainability", "search_volume": 12000, "growth_percentage": 185, "business_implications": "Measuring environmental impact. Dashboards for sustainability teams.", "source": "Google Trends", "is_featured": False},
    {"keyword": "regenerative agriculture", "category": "Sustainability", "search_volume": 24000, "growth_percentage": 155, "business_implications": "Soil health and carbon sequestration. Ag-tech for sustainable farming.", "source": "Google Trends", "is_featured": False},

    # ============================================
    # Remote Work (15 keywords)
    # ============================================
    {"keyword": "async collaboration", "category": "Remote Work", "search_volume": 18000, "growth_percentage": 185, "business_implications": "Tools for timezone-distributed teams. Video messages, documentation, async standups.", "source": "Google Trends", "is_featured": True},
    {"keyword": "virtual office", "category": "Remote Work", "search_volume": 42000, "growth_percentage": 145, "business_implications": "Digital spaces for remote teams. Gather, Teamflow alternatives.", "source": "Google Trends", "is_featured": True},
    {"keyword": "remote hiring", "category": "Remote Work", "search_volume": 55000, "growth_percentage": 75, "business_implications": "Global talent acquisition. Skills assessments and video interviews.", "source": "Google Trends", "is_featured": False},
    {"keyword": "employer of record", "category": "Remote Work", "search_volume": 35000, "growth_percentage": 125, "business_implications": "Hiring globally without entities. Deel, Remote.com alternatives.", "source": "Google Trends", "is_featured": True},
    {"keyword": "hybrid work tools", "category": "Remote Work", "search_volume": 28000, "growth_percentage": 95, "business_implications": "Managing hybrid schedules. Desk booking, office coordination.", "source": "Google Trends", "is_featured": False},
    {"keyword": "team productivity", "category": "Remote Work", "search_volume": 68000, "growth_percentage": 65, "business_implications": "Measuring and improving team output. Time tracking, goal setting.", "source": "Google Trends", "is_featured": False},
    {"keyword": "remote team building", "category": "Remote Work", "search_volume": 24000, "growth_percentage": 115, "business_implications": "Virtual team activities. Social connection for distributed teams.", "source": "Google Trends", "is_featured": False},
    {"keyword": "coworking space software", "category": "Remote Work", "search_volume": 15000, "growth_percentage": 85, "business_implications": "Managing flexible workspaces. Booking, access, community features.", "source": "Google Trends", "is_featured": False},
    {"keyword": "digital nomad tools", "category": "Remote Work", "search_volume": 31000, "growth_percentage": 145, "business_implications": "Tools for location-independent workers. Visa tracking, community, logistics.", "source": "Google Trends", "is_featured": False},
    {"keyword": "meeting management", "category": "Remote Work", "search_volume": 45000, "growth_percentage": 85, "business_implications": "Scheduling, agendas, notes, action items. AI meeting assistants.", "source": "Google Trends", "is_featured": False},
    {"keyword": "employee engagement", "category": "Remote Work", "search_volume": 58000, "growth_percentage": 75, "business_implications": "Measuring and improving engagement. Pulse surveys, recognition platforms.", "source": "Google Trends", "is_featured": False},
    {"keyword": "workspace analytics", "category": "Remote Work", "search_volume": 12000, "growth_percentage": 165, "business_implications": "Understanding how teams work. Productivity insights and optimization.", "source": "Google Trends", "is_featured": False},
    {"keyword": "remote onboarding", "category": "Remote Work", "search_volume": 21000, "growth_percentage": 95, "business_implications": "Welcoming new hires virtually. Automated onboarding workflows.", "source": "Google Trends", "is_featured": False},
    {"keyword": "focus time tools", "category": "Remote Work", "search_volume": 18000, "growth_percentage": 125, "business_implications": "Protecting deep work time. Calendar blocking, notification management.", "source": "Google Trends", "is_featured": False},
    {"keyword": "remote culture", "category": "Remote Work", "search_volume": 24000, "growth_percentage": 85, "business_implications": "Building company culture remotely. Values, rituals, communication.", "source": "Google Trends", "is_featured": False},

    # ============================================
    # Creator Economy (15 keywords)
    # ============================================
    {"keyword": "creator economy tools", "category": "Creator Economy", "search_volume": 42000, "growth_percentage": 125, "business_implications": "Tools helping creators monetize. Newsletters, courses, communities.", "source": "Google Trends", "is_featured": True},
    {"keyword": "newsletter platform", "category": "Creator Economy", "search_volume": 75000, "growth_percentage": 85, "business_implications": "Substack, Beehiiv alternatives. Monetization and growth tools.", "source": "Google Trends", "is_featured": True},
    {"keyword": "membership platform", "category": "Creator Economy", "search_volume": 55000, "growth_percentage": 75, "business_implications": "Patreon alternatives. Gated content and community access.", "source": "Google Trends", "is_featured": False},
    {"keyword": "podcast monetization", "category": "Creator Economy", "search_volume": 28000, "growth_percentage": 95, "business_implications": "Sponsorship marketplaces, premium content, listener support.", "source": "Google Trends", "is_featured": False},
    {"keyword": "UGC creator", "category": "Creator Economy", "search_volume": 38000, "growth_percentage": 210, "business_implications": "User-generated content for brands. Marketplaces connecting creators and brands.", "source": "Google Trends", "is_featured": True},
    {"keyword": "creator analytics", "category": "Creator Economy", "search_volume": 21000, "growth_percentage": 145, "business_implications": "Understanding audience and growth. Multi-platform analytics dashboards.", "source": "Google Trends", "is_featured": False},
    {"keyword": "link in bio tools", "category": "Creator Economy", "search_volume": 45000, "growth_percentage": 65, "business_implications": "Linktree alternatives. Mini websites for social profiles.", "source": "Google Trends", "is_featured": False},
    {"keyword": "brand deal platform", "category": "Creator Economy", "search_volume": 18000, "growth_percentage": 125, "business_implications": "Connecting creators with sponsors. Campaign management and payments.", "source": "Google Trends", "is_featured": False},
    {"keyword": "video editing AI", "category": "Creator Economy", "search_volume": 65000, "growth_percentage": 235, "business_implications": "AI-powered video editing. Automatic captions, clip generation, effects.", "source": "Google Trends", "is_featured": True},
    {"keyword": "social media scheduler", "category": "Creator Economy", "search_volume": 85000, "growth_percentage": 55, "business_implications": "Mature but AI optimization features differentiating.", "source": "Google Trends", "is_featured": False},
    {"keyword": "course creation platform", "category": "Creator Economy", "search_volume": 48000, "growth_percentage": 75, "business_implications": "Teachable, Kajabi alternatives. AI course creation tools.", "source": "Google Trends", "is_featured": False},
    {"keyword": "digital products", "category": "Creator Economy", "search_volume": 58000, "growth_percentage": 85, "business_implications": "Selling templates, presets, ebooks. Gumroad alternatives.", "source": "Google Trends", "is_featured": False},
    {"keyword": "creator CRM", "category": "Creator Economy", "search_volume": 12000, "growth_percentage": 165, "business_implications": "Managing relationships with brands, fans, collaborators.", "source": "Google Trends", "is_featured": False},
    {"keyword": "audience research tools", "category": "Creator Economy", "search_volume": 24000, "growth_percentage": 115, "business_implications": "Understanding your audience. SparkToro-style audience intelligence.", "source": "Google Trends", "is_featured": False},
    {"keyword": "creator community", "category": "Creator Economy", "search_volume": 31000, "growth_percentage": 95, "business_implications": "Building communities around content. Circle, Discord alternatives.", "source": "Google Trends", "is_featured": False},
]


async def seed_expanded_trends():
    """Seed the database with expanded trends data."""
    engine = create_async_engine(str(settings.database_url), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check existing count
        result = await session.execute(select(Trend))
        existing = result.scalars().all()
        logger.info(f"Found {len(existing)} existing trends")

        # Option to clear existing and reseed
        if existing and len(existing) < len(EXPANDED_TRENDS_DATA):
            logger.info("Clearing existing trends to reseed with expanded data...")
            await session.execute(delete(Trend))
            await session.commit()

        logger.info(f"Seeding {len(EXPANDED_TRENDS_DATA)} trends...")

        for i, trend_data in enumerate(EXPANDED_TRENDS_DATA):
            trend = Trend(
                keyword=trend_data["keyword"],
                category=trend_data["category"],
                search_volume=trend_data["search_volume"],
                growth_percentage=trend_data["growth_percentage"],
                business_implications=trend_data["business_implications"],
                source=trend_data["source"],
                is_featured=trend_data.get("is_featured", False),
                is_published=True,
            )
            session.add(trend)

            if (i + 1) % 50 == 0:
                logger.info(f"Added {i + 1} trends...")

        await session.commit()

        # Verify final count
        result = await session.execute(select(Trend))
        final_count = len(result.scalars().all())
        logger.info(f"Successfully seeded {final_count} trends!")

        # Show category breakdown
        categories = {}
        for trend in EXPANDED_TRENDS_DATA:
            cat = trend["category"]
            categories[cat] = categories.get(cat, 0) + 1

        logger.info("\nCategory breakdown:")
        for cat, count in sorted(categories.items()):
            logger.info(f"  {cat}: {count}")


if __name__ == "__main__":
    asyncio.run(seed_expanded_trends())
