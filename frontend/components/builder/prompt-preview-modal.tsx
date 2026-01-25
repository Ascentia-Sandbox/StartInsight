'use client';

import { useState } from 'react';
import { Copy, Check, ExternalLink, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { BUILDER_PLATFORMS, type BuilderPlatformId } from './builder-platform-card';
import { PROMPT_TYPES, type PromptTypeId } from './prompt-type-selector';

interface PromptPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  prompt: string;
  platformId: BuilderPlatformId;
  promptType: PromptTypeId;
  onBuild?: () => void;
  isLoading?: boolean;
}

export function PromptPreviewModal({
  isOpen,
  onClose,
  prompt,
  platformId,
  promptType,
  onBuild,
  isLoading = false,
}: PromptPreviewModalProps) {
  const [copied, setCopied] = useState(false);

  const platform = BUILDER_PLATFORMS[platformId];
  const promptTypeInfo = PROMPT_TYPES[promptType];

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleOpenInBuilder = () => {
    // For now, open the builder URL and let user paste
    // In the future, could use URL query params for some platforms
    window.open(platform.url, '_blank');
    onBuild?.();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold ${platform.color}`}
            >
              {platform.icon}
            </div>
            Build with {platform.name}
          </DialogTitle>
          <DialogDescription>
            {promptTypeInfo.description} - Copy the prompt below and paste it into {platform.name}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[400px] mt-4">
          <div className="relative">
            <pre className="bg-muted p-4 rounded-lg text-sm whitespace-pre-wrap font-mono overflow-x-auto">
              {prompt}
            </pre>
          </div>
        </ScrollArea>

        <DialogFooter className="flex flex-col sm:flex-row gap-2 mt-4">
          <Button
            variant="outline"
            onClick={handleCopy}
            className="gap-2"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="h-4 w-4" />
                Copy Prompt
              </>
            )}
          </Button>
          <Button
            onClick={handleOpenInBuilder}
            disabled={isLoading}
            className="gap-2"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ExternalLink className="h-4 w-4" />
            )}
            Open {platform.name}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
