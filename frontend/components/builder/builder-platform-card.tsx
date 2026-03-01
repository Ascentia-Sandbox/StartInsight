'use client';

import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// Builder platform configurations with platform-optimized prompt templates
export const BUILDER_PLATFORMS = {
  lovable: {
    name: 'Lovable',
    description: 'AI-powered full-stack app builder',
    icon: 'L',
    color: 'bg-purple-500',
    url: 'https://lovable.dev',
    promptPrefix: 'Build a full-stack web application with React + Tailwind CSS + Supabase auth.',
    promptTemplate: (idea: string, promptType: string) =>
      `Build a full-stack web application with the following specifications:

## Tech Stack
- Frontend: React + Tailwind CSS + shadcn/ui components
- Auth: Supabase (email + Google OAuth)
- Database: Supabase PostgreSQL
- Deployment: Auto-deploy

## Visual Style
Modern, clean, premium SaaS aesthetic. Use consistent spacing, subtle shadows, and professional typography.

## Idea
${idea}

## What to Build
Create a ${promptType} with these requirements:
- Responsive layout (mobile-first)
- Dark mode support
- User authentication flow (sign up, login, forgot password)
- Dashboard with key metrics
- Clean navigation with sidebar
- Form validation with helpful error messages
- Loading states and skeleton screens

Build incrementally — start with the core layout and auth, then add features.`,
  },
  v0: {
    name: 'v0',
    description: 'Vercel AI UI generator',
    icon: 'v0',
    color: 'bg-black dark:bg-white dark:text-black',
    url: 'https://v0.dev',
    promptPrefix: 'Create a responsive React component using shadcn/ui and Tailwind CSS.',
    promptTemplate: (idea: string, promptType: string) =>
      `Create a production-ready ${promptType} React component with the following specifications:

## Component Requirements
- Built with Next.js 14 App Router patterns
- Uses shadcn/ui components (Button, Card, Input, Badge, etc.)
- Styled with Tailwind CSS utility classes
- Fully responsive (mobile, tablet, desktop)
- Accessible (ARIA labels, keyboard navigation, focus states)
- Dark mode compatible via CSS variables

## Design Specifications
- Typography: Inter or system font stack, clear hierarchy (text-4xl for hero, text-lg for body)
- Colors: Use CSS variables for theming (--primary, --muted, --accent)
- Spacing: Consistent padding (p-4/p-6/p-8) and gap (gap-4/gap-6)
- Animations: Subtle transitions on hover/focus states

## Context
${idea}

## Include
- Sample data with realistic content (not "Lorem ipsum")
- Proper TypeScript types for all props
- Mobile-first responsive breakpoints (sm:, md:, lg:)
- Hover and focus interaction states`,
  },
  replit: {
    name: 'Replit',
    description: 'Online IDE with AI assistant',
    icon: 'R',
    color: 'bg-orange-500',
    url: 'https://replit.com',
    promptPrefix: 'Create a full-stack application with a clear project structure.',
    promptTemplate: (idea: string, promptType: string) =>
      `Create a ${promptType} application with the following project structure:

## Project Setup
- Language: TypeScript (Node.js)
- Framework: Express.js backend + React frontend (or Python Flask if simpler)
- Entry point: index.ts (or main.py)
- Package manager: npm (package.json with all dependencies listed)
- Environment: .env file with clearly documented variables

## Idea
${idea}

## Implementation Steps (build sequentially)
1. Set up project structure with package.json and dependencies
2. Create the backend API with 3-5 core endpoints
3. Add a simple database (SQLite for simplicity, or PostgreSQL)
4. Build the frontend UI with forms and data display
5. Connect frontend to backend API
6. Add basic error handling and input validation
7. Test the core user flow end-to-end

## Requirements
- Clear file organization (src/routes, src/models, src/views)
- Environment variable configuration (no hardcoded secrets)
- Basic README with setup instructions
- Working deployment configuration`,
  },
  chatgpt: {
    name: 'ChatGPT',
    description: 'OpenAI conversational AI',
    icon: 'GPT',
    color: 'bg-emerald-500',
    url: 'https://chat.openai.com',
    promptPrefix: 'You are a senior full-stack developer. Help me build a production-ready application.',
    promptTemplate: (idea: string, promptType: string) =>
      `You are a senior full-stack developer specializing in modern web applications. Help me build a ${promptType}.

## Context
${idea}

## Your Task
Provide a complete, production-ready implementation plan and code. Structure your response as follows:

### 1. Architecture Overview
- Tech stack recommendation with justification
- System diagram (describe the components and data flow)
- Database schema (tables, relationships, key fields)

### 2. Implementation
- Provide code in clearly labeled files (e.g., \`// src/app/page.tsx\`)
- Use TypeScript with strict types
- Include error handling for edge cases
- Add inline comments only where logic is non-obvious

### 3. Key Decisions
- Explain any trade-offs you made and why
- Note any assumptions about the requirements

## Constraints
- Keep the solution simple — minimum viable, not over-engineered
- Use well-known libraries (React, Next.js, Tailwind, Prisma, or similar)
- All code should be copy-paste ready
- If something needs clarification, state your assumption and proceed`,
  },
  claude: {
    name: 'Claude',
    description: 'Anthropic AI assistant',
    icon: 'C',
    color: 'bg-amber-600',
    url: 'https://claude.ai',
    promptPrefix: 'Help me implement a well-architected application with clean code patterns.',
    promptTemplate: (idea: string, promptType: string) =>
      `<context>
I'm building a ${promptType} for a startup. I need a well-architected, production-quality implementation.
</context>

<instructions>
## Idea
${idea}

## Architecture Requirements
- Framework: Next.js 14+ with App Router (or FastAPI for backend-heavy)
- Language: TypeScript (strict mode) / Python with type hints
- Styling: Tailwind CSS + shadcn/ui components
- Database: PostgreSQL with an ORM (Prisma or SQLAlchemy)
- Auth: NextAuth.js or Supabase Auth

## Implementation Approach
1. Start with the data model — define types/schemas first
2. Build API routes with proper validation (Zod or Pydantic)
3. Create UI components following atomic design (atoms → molecules → organisms)
4. Wire up data fetching with proper loading/error states
5. Add auth-gated routes where needed

## Code Standards
- Prefer composition over inheritance
- Use async/await for all I/O
- Extract reusable logic into custom hooks (React) or service classes (Python)
- No any types — define explicit interfaces
- File naming: kebab-case for files, PascalCase for components

## Output Format
Provide the implementation as a series of files with their full paths. Include:
- Type definitions
- API routes/endpoints
- UI components
- Database schema/migration
</instructions>`,
  },
} as const;

export type BuilderPlatformId = keyof typeof BUILDER_PLATFORMS;

interface BuilderPlatformCardProps {
  platformId: BuilderPlatformId;
  isSelected?: boolean;
  onSelect?: (platformId: BuilderPlatformId) => void;
  size?: 'sm' | 'md' | 'lg';
}

export function BuilderPlatformCard({
  platformId,
  isSelected = false,
  onSelect,
  size = 'md',
}: BuilderPlatformCardProps) {
  const platform = BUILDER_PLATFORMS[platformId];

  const sizeConfig = {
    sm: { card: 'p-2', icon: 'w-6 h-6 text-xs', text: 'text-xs' },
    md: { card: 'p-3', icon: 'w-10 h-10 text-sm', text: 'text-sm' },
    lg: { card: 'p-4', icon: 'w-12 h-12 text-base', text: 'text-base' },
  };

  const { card: cardSize, icon: iconSize, text: textSize } = sizeConfig[size];

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-md',
        cardSize,
        isSelected
          ? 'border-2 border-primary ring-2 ring-primary/20'
          : 'border hover:border-primary/50'
      )}
      onClick={() => onSelect?.(platformId)}
    >
      <CardContent className="p-0 flex items-center gap-3">
        {/* Platform Icon */}
        <div
          className={cn(
            'flex items-center justify-center rounded-lg font-bold text-white',
            platform.color,
            iconSize
          )}
        >
          {platform.icon}
        </div>

        {/* Platform Info */}
        <div className="flex-1 min-w-0">
          <h4 className={cn('font-semibold truncate', textSize)}>{platform.name}</h4>
          {size !== 'sm' && (
            <p className="text-xs text-muted-foreground truncate">{platform.description}</p>
          )}
        </div>

        {/* Selection indicator */}
        {isSelected && (
          <div className="flex-shrink-0 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
            <svg className="w-3 h-3 text-primary-foreground" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface BuilderPlatformGridProps {
  selectedPlatform?: BuilderPlatformId | null;
  onSelect?: (platformId: BuilderPlatformId) => void;
  size?: 'sm' | 'md' | 'lg';
}

export function BuilderPlatformGrid({ selectedPlatform, onSelect, size = 'md' }: BuilderPlatformGridProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {(Object.keys(BUILDER_PLATFORMS) as BuilderPlatformId[]).map((platformId) => (
        <BuilderPlatformCard
          key={platformId}
          platformId={platformId}
          isSelected={selectedPlatform === platformId}
          onSelect={onSelect}
          size={size}
        />
      ))}
    </div>
  );
}
