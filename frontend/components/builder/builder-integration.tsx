'use client';

import { useState } from 'react';
import { Hammer, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { BuilderPlatformGrid, BUILDER_PLATFORMS, type BuilderPlatformId } from './builder-platform-card';
import { PromptTypeSelector, PROMPT_TYPES, generatePrompt, type PromptTypeId } from './prompt-type-selector';
import { PromptPreviewModal } from './prompt-preview-modal';

interface InsightData {
  id: string;
  problem_statement: string;
  proposed_solution: string;
  market_size_estimate: 'Small' | 'Medium' | 'Large';
  relevance_score: number;
  competitor_analysis?: Array<{
    name: string;
    url: string;
    description: string;
  }>;
}

interface BuilderIntegrationProps {
  insight: InsightData;
  defaultExpanded?: boolean;
}

export function BuilderIntegration({ insight, defaultExpanded = true }: BuilderIntegrationProps) {
  const [selectedPlatform, setSelectedPlatform] = useState<BuilderPlatformId | null>(null);
  const [selectedPromptType, setSelectedPromptType] = useState<PromptTypeId>('landing_page');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [generatedPrompt, setGeneratedPrompt] = useState('');

  const handleGeneratePrompt = () => {
    if (!selectedPlatform) return;

    const platform = BUILDER_PLATFORMS[selectedPlatform];
    const prompt = generatePrompt(selectedPromptType, insight, platform.promptPrefix);
    setGeneratedPrompt(prompt);
    setIsModalOpen(true);
  };

  const handleBuild = () => {
    // Track analytics (placeholder for actual implementation)
    console.log('Build started:', {
      insightId: insight.id,
      platform: selectedPlatform,
      promptType: selectedPromptType,
    });
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Hammer className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">Build This Idea</CardTitle>
            <Badge variant="secondary" className="ml-2">
              <Sparkles className="h-3 w-3 mr-1" />
              AI-Powered
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Turn this insight into reality with one click. Select a builder platform and what you want to create.
          </p>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Step 1: Select Platform */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary text-primary-foreground text-xs">
                1
              </span>
              Choose Builder Platform
            </h4>
            <BuilderPlatformGrid
              selectedPlatform={selectedPlatform}
              onSelect={setSelectedPlatform}
              size="md"
            />
          </div>

          <Separator />

          {/* Step 2: Select What to Build */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary text-primary-foreground text-xs">
                2
              </span>
              Select What to Build
            </h4>
            <PromptTypeSelector
              value={selectedPromptType}
              onChange={setSelectedPromptType}
              className="w-full sm:w-[300px]"
            />
          </div>

          <Separator />

          {/* Step 3: Generate & Build */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary text-primary-foreground text-xs">
                3
              </span>
              Generate Prompt & Build
            </h4>
            <div className="flex items-center gap-3">
              <Button
                onClick={handleGeneratePrompt}
                disabled={!selectedPlatform}
                className="gap-2"
              >
                <Sparkles className="h-4 w-4" />
                Generate {PROMPT_TYPES[selectedPromptType].name} Prompt
              </Button>
              {!selectedPlatform && (
                <span className="text-sm text-muted-foreground">
                  Select a platform first
                </span>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="pt-4 border-t">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-lg font-bold text-primary">5</div>
                <div className="text-xs text-muted-foreground">Builder Platforms</div>
              </div>
              <div>
                <div className="text-lg font-bold text-primary">4</div>
                <div className="text-xs text-muted-foreground">Output Types</div>
              </div>
              <div>
                <div className="text-lg font-bold text-primary">1-Click</div>
                <div className="text-xs text-muted-foreground">To Build</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Prompt Preview Modal */}
      {selectedPlatform && (
        <PromptPreviewModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          prompt={generatedPrompt}
          platformId={selectedPlatform}
          promptType={selectedPromptType}
          onBuild={handleBuild}
        />
      )}
    </>
  );
}

// Export all builder components for easier imports
export { BuilderPlatformCard, BuilderPlatformGrid, BUILDER_PLATFORMS } from './builder-platform-card';
export { PromptTypeSelector, PROMPT_TYPES, generatePrompt } from './prompt-type-selector';
export { PromptPreviewModal } from './prompt-preview-modal';
