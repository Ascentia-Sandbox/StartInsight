'use client';

import { useState } from 'react';
import { Copy, Check, Share2 } from 'lucide-react';
import { analytics, Events } from '@/lib/analytics';

interface ReferralData {
  referral_code: string;
  referral_link: string;
  referrals_count: number;
  reward_status: string;
  next_reward: string | null;
  next_reward_at: number;
}

const TIERS = [
  { at: 1, label: '1 Free Report', reward: '1 free category report (RM49 value)' },
  { at: 3, label: 'Founder Badge', reward: 'Founder badge + priority access' },
  { at: 5, label: 'All Reports', reward: 'All 3 category reports free (RM147 value)' },
];

export function ReferralWidget({ data }: { data: ReferralData }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(data.referral_link);
    setCopied(true);
    analytics.track(Events.REFERRAL_SHARED, { method: 'copy' });
    setTimeout(() => setCopied(false), 2000);
  };

  const shareUrl = encodeURIComponent(data.referral_link);
  const shareText = encodeURIComponent(
    'Discover AI-powered startup ideas backed by real data — check out StartInsight'
  );

  const progress = Math.min(data.referrals_count / 5, 1) * 100;

  return (
    <div className="rounded-xl border bg-card p-5">
      <div className="flex items-center gap-2 mb-3">
        <Share2 className="h-4 w-4 text-[#0D7377]" />
        <h3 className="font-semibold text-sm">Refer & Earn</h3>
      </div>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-muted-foreground mb-1">
          <span>{data.referrals_count} referrals</span>
          <span>Next: {data.next_reward_at > 0 ? data.next_reward_at : '—'}</span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-[#0D7377] rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Next reward */}
      {data.next_reward && (
        <p className="text-xs text-muted-foreground mb-3">
          {data.next_reward_at - data.referrals_count} more to unlock:{' '}
          <span className="font-medium text-foreground">{data.next_reward}</span>
        </p>
      )}

      {/* Tier badges */}
      <div className="flex gap-1 mb-4">
        {TIERS.map((tier) => (
          <div
            key={tier.at}
            className={`flex-1 text-center py-1 rounded text-[10px] font-medium ${
              data.referrals_count >= tier.at
                ? 'bg-[#0D7377]/10 text-[#0D7377]'
                : 'bg-muted text-muted-foreground'
            }`}
          >
            {tier.label}
          </div>
        ))}
      </div>

      {/* Copy link */}
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          readOnly
          value={data.referral_link}
          className="flex-1 text-xs bg-muted rounded px-3 py-2 truncate"
        />
        <button
          onClick={handleCopy}
          className="shrink-0 px-3 py-2 rounded bg-[#0D7377] text-white text-xs font-medium hover:bg-[#0D7377]/90 transition-colors"
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
      </div>

      {/* Share buttons */}
      <div className="flex gap-2">
        <a
          href={`https://twitter.com/intent/tweet?text=${shareText}&url=${shareUrl}`}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => analytics.track(Events.REFERRAL_SHARED, { method: 'twitter' })}
          className="flex-1 text-center py-1.5 rounded border text-xs hover:bg-muted transition-colors"
        >
          Twitter/X
        </a>
        <a
          href={`https://www.linkedin.com/sharing/share-offsite/?url=${shareUrl}`}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => analytics.track(Events.REFERRAL_SHARED, { method: 'linkedin' })}
          className="flex-1 text-center py-1.5 rounded border text-xs hover:bg-muted transition-colors"
        >
          LinkedIn
        </a>
        <a
          href={`https://wa.me/?text=${shareText}%20${shareUrl}`}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => analytics.track(Events.REFERRAL_SHARED, { method: 'whatsapp' })}
          className="flex-1 text-center py-1.5 rounded border text-xs hover:bg-muted transition-colors"
        >
          WhatsApp
        </a>
      </div>
    </div>
  );
}
