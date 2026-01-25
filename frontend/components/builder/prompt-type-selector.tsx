'use client';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { FileText, Palette, Mail, Megaphone } from 'lucide-react';

// Prompt types for different builder outputs
export const PROMPT_TYPES = {
  landing_page: {
    name: 'Landing Page',
    description: 'Marketing page with hero, features, and CTA',
    icon: FileText,
  },
  brand_package: {
    name: 'Brand Package',
    description: 'Logo concept, colors, taglines, and brand voice',
    icon: Palette,
  },
  email_sequence: {
    name: 'Email Sequence',
    description: 'Welcome series, onboarding, and nurture emails',
    icon: Mail,
  },
  ad_creative: {
    name: 'Ad Creative',
    description: 'Social media ads and marketing copy',
    icon: Megaphone,
  },
} as const;

export type PromptTypeId = keyof typeof PROMPT_TYPES;

interface PromptTypeSelectorProps {
  value?: PromptTypeId;
  onChange?: (value: PromptTypeId) => void;
  className?: string;
}

export function PromptTypeSelector({ value, onChange, className }: PromptTypeSelectorProps) {
  return (
    <Select value={value} onValueChange={(v) => onChange?.(v as PromptTypeId)}>
      <SelectTrigger className={className}>
        <SelectValue placeholder="Select what to build" />
      </SelectTrigger>
      <SelectContent>
        {(Object.entries(PROMPT_TYPES) as [PromptTypeId, typeof PROMPT_TYPES[PromptTypeId]][]).map(
          ([id, type]) => {
            const Icon = type.icon;
            return (
              <SelectItem key={id} value={id}>
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <span className="font-medium">{type.name}</span>
                    <span className="text-xs text-muted-foreground ml-2 hidden sm:inline">
                      - {type.description}
                    </span>
                  </div>
                </div>
              </SelectItem>
            );
          }
        )}
      </SelectContent>
    </Select>
  );
}

// Prompt generation utility
interface InsightContext {
  problem_statement: string;
  proposed_solution: string;
  market_size_estimate: string;
  relevance_score: number;
  competitor_analysis?: Array<{ name: string; url: string; description: string }>;
}

export function generatePrompt(
  promptType: PromptTypeId,
  insight: InsightContext,
  platformPrefix?: string
): string {
  const competitorList = insight.competitor_analysis
    ?.map((c) => `- ${c.name}: ${c.description}`)
    .join('\n') || 'None identified';

  const baseContext = `
## Market Opportunity
**Problem:** ${insight.problem_statement}

**Solution:** ${insight.proposed_solution}

**Market Size:** ${insight.market_size_estimate}
**Relevance Score:** ${(insight.relevance_score * 100).toFixed(0)}%

## Competitor Landscape
${competitorList}
`.trim();

  const prompts: Record<PromptTypeId, string> = {
    landing_page: `${platformPrefix || 'Create'} a high-converting landing page for a startup solving this problem:

${baseContext}

Requirements:
1. Hero section with compelling headline and subheadline
2. Problem/solution section with clear value proposition
3. Features section (3-5 key features)
4. Social proof section (testimonials placeholder)
5. Pricing section (3 tiers: Free, Pro, Enterprise)
6. FAQ section (5 common questions)
7. Final CTA section
8. Modern, clean design with good typography
9. Mobile-responsive layout
10. Dark mode support`,

    brand_package: `${platformPrefix || 'Create'} a complete brand identity package for a startup:

${baseContext}

Requirements:
1. Brand name suggestions (3 options with rationale)
2. Tagline options (3 variations)
3. Color palette (primary, secondary, accent colors with hex codes)
4. Logo concept description (visual direction, not actual logo)
5. Brand voice and tone guidelines
6. Typography recommendations (heading and body fonts)
7. Brand personality traits (5 adjectives)
8. Messaging framework (elevator pitch, value proposition, key messages)`,

    email_sequence: `${platformPrefix || 'Create'} an email marketing sequence for a startup:

${baseContext}

Requirements:
1. Welcome email (sent immediately after signup)
2. Problem awareness email (day 2)
3. Solution introduction email (day 4)
4. Case study/social proof email (day 7)
5. Feature highlight email (day 10)
6. Limited-time offer email (day 14)
7. Each email should have: Subject line, preview text, body copy, CTA
8. Include personalization tokens where appropriate
9. Conversational, helpful tone`,

    ad_creative: `${platformPrefix || 'Create'} social media ad creatives for a startup:

${baseContext}

Requirements:
1. Facebook/Instagram ad (1080x1080 image concept + copy)
2. Twitter/X ad (1200x675 image concept + copy)
3. LinkedIn ad (1200x627 image concept + copy)
4. Google Display ad headlines (3 variations, 30 chars each)
5. Google Display ad descriptions (2 variations, 90 chars each)
6. Each ad should have: Hook, benefit, CTA
7. A/B test variations for top performing platforms
8. Targeting recommendations`,
  };

  return prompts[promptType];
}
