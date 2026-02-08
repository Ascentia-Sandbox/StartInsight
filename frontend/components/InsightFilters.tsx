'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { X, Sparkles, TrendingUp, Target, Wrench, Clock, Star, Loader2 } from 'lucide-react';

export function InsightFilters() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const [searchValue, setSearchValue] = useState(searchParams.get('search') || '');
  const [isSearching, setIsSearching] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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
  const isFeatured = searchParams.get('featured') === 'true';

  const handleSearchChange = useCallback((value: string) => {
    setSearchValue(value);
    setIsSearching(true);

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      updateFilter('search', value || null);
      setIsSearching(false);
    }, 500);
  }, [updateFilter]);

  const clearSearch = useCallback(() => {
    setSearchValue('');
    setIsSearching(false);
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    updateFilter('search', null);
  }, [updateFilter]);

  // Sync searchValue with URL params when they change externally
  useEffect(() => {
    const urlSearch = searchParams.get('search') || '';
    if (urlSearch !== searchValue && !isSearching) {
      setSearchValue(urlSearch);
    }
  }, [searchParams]);

  return (
    <div className="space-y-4 p-4 border rounded-lg" role="search" aria-label="Filter insights" data-tour="insights-filters">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold" id="filters-heading">Filters</h3>
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters} aria-label="Clear all filters" className="min-h-[44px]">
            <X className="h-4 w-4 mr-1" />
            Clear
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {/* Sort By */}
        <div>
          <label className="text-sm font-medium mb-1 block">Sort By</label>
          <Select
            value={searchParams.get('sort') || 'newest'}
            onValueChange={(value) => updateFilter('sort', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Newest First" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Newest First
                </div>
              </SelectItem>
              <SelectItem value="relevance">
                <div className="flex items-center gap-2">
                  <Star className="h-4 w-4" />
                  Best Match
                </div>
              </SelectItem>
              <SelectItem value="founder_fit">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4" />
                  Founder Fit
                </div>
              </SelectItem>
              <SelectItem value="opportunity">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Opportunity Score
                </div>
              </SelectItem>
              <SelectItem value="feasibility">
                <div className="flex items-center gap-2">
                  <Wrench className="h-4 w-4" />
                  Easy to Build
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Featured Toggle */}
        <div className="flex items-center justify-between py-2">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-yellow-500" />
            <Label htmlFor="featured-toggle" className="text-sm font-medium cursor-pointer">
              Featured Only
            </Label>
          </div>
          <Switch
            id="featured-toggle"
            checked={isFeatured}
            onCheckedChange={(checked) => updateFilter('featured', checked ? 'true' : null)}
          />
        </div>

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
              <SelectItem value="twitter">Twitter/X</SelectItem>
              <SelectItem value="hacker_news">Hacker News</SelectItem>
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
          <label className="text-sm font-medium mb-1 block" id="search-label">Search</label>
          <div className="relative">
            <Input
              placeholder="Search insights..."
              value={searchValue}
              onChange={(e) => handleSearchChange(e.target.value)}
              aria-labelledby="search-label"
              aria-describedby={isSearching ? 'search-status' : undefined}
            />

            {/* Loading indicator during debounce */}
            {isSearching && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2" aria-hidden="true">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            )}

            {/* Clear button when has value and not searching */}
            {searchValue && !isSearching && (
              <button
                onClick={clearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 min-h-[44px] min-w-[44px] flex items-center justify-center -mr-3"
                aria-label="Clear search"
              >
                <X className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors" />
              </button>
            )}

            {/* Screen reader status */}
            {isSearching && (
              <span id="search-status" className="sr-only" role="status" aria-live="polite">
                Searching...
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
