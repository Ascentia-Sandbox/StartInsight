'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2, Settings, Save, RotateCcw, Globe, Mail, Sparkles,
  Activity, Bot, Radar,
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import {
  fetchSystemSettings, updateSystemSetting,
  type SystemSetting,
} from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';

const CATEGORY_META: Record<string, { label: string; icon: React.ElementType; description: string }> = {
  general: { label: 'General', icon: Globe, description: 'Site name and branding' },
  email: { label: 'Email', icon: Mail, description: 'Email delivery settings' },
  features: { label: 'Features', icon: Sparkles, description: 'Feature flags and toggles' },
  pipeline: { label: 'Pipeline', icon: Activity, description: 'Scraping and analysis configuration' },
  ai: { label: 'AI', icon: Bot, description: 'AI model and generation settings' },
  scraper: { label: 'Scraper Sources', icon: Radar, description: 'Data source configuration for each scraper' },
};

function SettingInput({
  setting,
  value,
  onChange,
}: {
  setting: SystemSetting;
  value: unknown;
  onChange: (val: unknown) => void;
}) {
  // Boolean → Switch
  if (typeof value === 'boolean') {
    return (
      <div className="flex items-center justify-between">
        <div>
          <Label className="text-sm font-medium">
            {formatKey(setting.key)}
          </Label>
          <p className="text-xs text-muted-foreground">{setting.description}</p>
        </div>
        <Switch checked={value} onCheckedChange={(checked) => onChange(checked)} />
      </div>
    );
  }

  // Number → Number input
  if (typeof value === 'number') {
    return (
      <div>
        <Label className="text-sm font-medium">
          {formatKey(setting.key)}
        </Label>
        <p className="text-xs text-muted-foreground mb-1">{setting.description}</p>
        <Input
          type="number"
          value={value}
          step={value % 1 !== 0 ? '0.1' : '1'}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
          className="max-w-xs"
        />
      </div>
    );
  }

  // Array → Comma-separated tags input
  if (Array.isArray(value)) {
    return (
      <div>
        <Label className="text-sm font-medium">
          {formatKey(setting.key)}
        </Label>
        <p className="text-xs text-muted-foreground mb-1">{setting.description}</p>
        <Input
          value={value.join(', ')}
          onChange={(e) => {
            const tags = e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean);
            onChange(tags);
          }}
          placeholder="Comma-separated values"
          className="max-w-md"
        />
      </div>
    );
  }

  // String → Text input
  return (
    <div>
      <Label className="text-sm font-medium">
        {formatKey(setting.key)}
      </Label>
      <p className="text-xs text-muted-foreground mb-1">{setting.description}</p>
      <Input
        value={String(value || '')}
        onChange={(e) => onChange(e.target.value)}
        className="max-w-md"
      />
    </div>
  );
}

function formatKey(key: string): string {
  // "pipeline.scrape_interval_hours" → "Scrape Interval Hours"
  const parts = key.split('.');
  const name = parts[parts.length - 1];
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function SettingsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [localSettings, setLocalSettings] = useState<Record<string, unknown>>({});
  const [dirtyKeys, setDirtyKeys] = useState<Set<string>>(new Set());

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push('/auth/login?redirectTo=/admin/settings');
        return;
      }
      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };
    checkAuth();
  }, [router]);

  const { data: settings, isLoading } = useQuery({
    queryKey: ['system-settings', accessToken],
    queryFn: () => fetchSystemSettings(accessToken!),
    enabled: !!accessToken,
  });

  // Initialize local state from fetched settings
  useEffect(() => {
    if (settings) {
      const flat: Record<string, unknown> = {};
      for (const category of Object.values(settings.settings)) {
        for (const s of category) {
          flat[s.key] = s.value;
        }
      }
      setLocalSettings(flat);
      setDirtyKeys(new Set());
    }
  }, [settings]);

  const saveMutation = useMutation({
    mutationFn: async ({ key, value }: { key: string; value: unknown }) => {
      return updateSystemSetting(accessToken!, key, value);
    },
    onSuccess: (_data, { key }) => {
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
      setDirtyKeys((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
      toast.success(`Setting "${formatKey(key)}" saved`);
    },
    onError: (_err, { key }) => {
      toast.error(`Failed to save "${formatKey(key)}"`);
    },
  });

  const handleChange = (key: string, value: unknown) => {
    setLocalSettings((prev) => ({ ...prev, [key]: value }));
    setDirtyKeys((prev) => new Set(prev).add(key));
  };

  const handleSaveAll = async () => {
    const promises = Array.from(dirtyKeys).map((key) =>
      saveMutation.mutateAsync({ key, value: localSettings[key] })
    );
    await Promise.allSettled(promises);
  };

  if (isCheckingAuth || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    );
  }

  const categories = Object.keys(settings?.settings || {});

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Settings className="h-6 w-6" />
            System Settings
          </h1>
          <p className="text-muted-foreground mt-1">
            Configure system-wide settings
          </p>
        </div>
        {dirtyKeys.size > 0 && (
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // Reset to server values
                if (settings) {
                  const flat: Record<string, unknown> = {};
                  for (const category of Object.values(settings.settings)) {
                    for (const s of category) {
                      flat[s.key] = s.value;
                    }
                  }
                  setLocalSettings(flat);
                  setDirtyKeys(new Set());
                }
              }}
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Reset
            </Button>
            <Button size="sm" onClick={handleSaveAll} disabled={saveMutation.isPending}>
              {saveMutation.isPending && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
              <Save className="h-3 w-3 mr-1" />
              Save {dirtyKeys.size} change{dirtyKeys.size !== 1 ? 's' : ''}
            </Button>
          </div>
        )}
      </div>

      <div className="space-y-6">
        {categories.map((category) => {
          const meta = CATEGORY_META[category] || {
            label: category,
            icon: Settings,
            description: '',
          };
          const Icon = meta.icon;
          const categorySettings = settings!.settings[category];

          return (
            <Card key={category}>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  {meta.label}
                </CardTitle>
                {meta.description && (
                  <CardDescription>{meta.description}</CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-5">
                {categorySettings.map((setting) => (
                  <SettingInput
                    key={setting.key}
                    setting={setting}
                    value={localSettings[setting.key] ?? setting.value}
                    onChange={(val) => handleChange(setting.key, val)}
                  />
                ))}
              </CardContent>
            </Card>
          );
        })}

        {categories.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <Settings className="h-10 w-10 mx-auto mb-3 opacity-50" />
              <p>No settings found. Run the database migration to seed defaults.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
