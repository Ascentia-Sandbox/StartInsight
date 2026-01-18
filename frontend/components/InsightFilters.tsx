'use client';

import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

export function InsightFilters() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const updateFilter = (key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.push(`${pathname}?${params.toString()}`);
  };

  const clearFilters = () => {
    router.push(pathname);
  };

  const hasFilters = searchParams.toString().length > 0;

  return (
    <div className="space-y-4 p-4 border rounded-lg">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Filters</h3>
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="h-4 w-4 mr-1" />
            Clear
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {/* Source Filter */}
        <div>
          <label className="text-sm font-medium mb-1 block">Source</label>
          <Select
            value={searchParams.get('source') || 'all'}
            onValueChange={(value) => updateFilter('source', value === 'all' ? null : value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="All sources" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All sources</SelectItem>
              <SelectItem value="reddit">Reddit</SelectItem>
              <SelectItem value="product_hunt">Product Hunt</SelectItem>
              <SelectItem value="google_trends">Google Trends</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Min Score Filter */}
        <div>
          <label className="text-sm font-medium mb-1 block">Minimum Relevance</label>
          <Select
            value={searchParams.get('min_score') || '0'}
            onValueChange={(value) => updateFilter('min_score', value === '0' ? null : value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Any score" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="0">Any score</SelectItem>
              <SelectItem value="0.5">0.5+ (Moderate)</SelectItem>
              <SelectItem value="0.7">0.7+ (Good)</SelectItem>
              <SelectItem value="0.9">0.9+ (Excellent)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Search */}
        <div>
          <label className="text-sm font-medium mb-1 block">Search</label>
          <Input
            placeholder="Search insights..."
            defaultValue={searchParams.get('search') || ''}
            onChange={(e) => {
              const value = e.target.value;
              // Debounce search
              setTimeout(() => updateFilter('search', value || null), 500);
            }}
          />
        </div>
      </div>
    </div>
  );
}
