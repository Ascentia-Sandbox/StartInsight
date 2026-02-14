'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface AdminPaginationProps {
  totalItems: number;
  currentPage: number;
  perPage: number;
}

export function AdminPagination({
  totalItems,
  currentPage,
  perPage,
}: AdminPaginationProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const totalPages = Math.ceil(totalItems / perPage);
  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * perPage + 1;
  const endItem = Math.min(currentPage * perPage, totalItems);

  const updateParams = (page: number, newPerPage?: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('page', String(page));
    if (newPerPage) params.set('per_page', String(newPerPage));
    router.push(`?${params.toString()}`);
  };

  if (totalItems === 0) return null;

  return (
    <div className="flex items-center justify-between border-t pt-4 mt-4">
      <p className="text-sm text-muted-foreground">
        Showing {startItem}-{endItem} of {totalItems} items
      </p>
      <div className="flex items-center gap-4">
        <Select
          value={String(perPage)}
          onValueChange={(val) => updateParams(1, Number(val))}
        >
          <SelectTrigger className="w-[100px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="10">10 / page</SelectItem>
            <SelectItem value="25">25 / page</SelectItem>
            <SelectItem value="50">50 / page</SelectItem>
          </SelectContent>
        </Select>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => updateParams(currentPage - 1)}
            disabled={currentPage <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm font-medium">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => updateParams(currentPage + 1)}
            disabled={currentPage >= totalPages}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
