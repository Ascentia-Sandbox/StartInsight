"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Pencil, Trash2, Star, TrendingUp, Search, X, Maximize2, Minimize2 } from "lucide-react";
import { getSupabaseClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { config } from "@/lib/env";

interface Trend {
  id: string;
  keyword: string;
  category: string;
  search_volume: number;
  growth_percentage: number;
  business_implications: string;
  trend_data: Record<string, unknown>;
  source: string;
  is_featured: boolean;
  is_published: boolean;
  created_at: string;
}

const categories = [
  "AI/ML",
  "SaaS",
  "Development",
  "No-Code",
  "Marketing",
  "Legal",
  "Healthcare",
  "Finance",
  "E-commerce",
  "Other",
];

export default function AdminTrendsPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingTrend, setEditingTrend] = useState<Trend | null>(null);
  const [deletingTrend, setDeletingTrend] = useState<Trend | null>(null);
  const [isFullView, setIsFullView] = useState(false);
  const [formData, setFormData] = useState({
    keyword: "",
    category: "",
    search_volume: 0,
    growth_percentage: 0,
    business_implications: "",
    source: "Google Trends",
    is_featured: false,
    is_published: true,
  });

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push("/auth/login?redirectTo=/admin/trends");
        return;
      }
      setAccessToken(session.access_token);
    };
    checkAuth();
  }, [router]);

  useEffect(() => {
    if (accessToken) fetchTrends();
  }, [accessToken]);

  const fetchTrends = async () => {
    try {
      const response = await fetch(
        `${config.apiUrl}/api/trends?limit=100`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      if (!response.ok) throw new Error("Failed to fetch");
      const data = await response.json();
      setTrends(data.trends || []);
    } catch (error) {
      console.error("Failed to fetch trends:", error);
      toast.error("Failed to load trends");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingTrend(null);
    setFormData({
      keyword: "",
      category: "",
      search_volume: 0,
      growth_percentage: 0,
      business_implications: "",
      source: "Google Trends",
      is_featured: false,
      is_published: true,
    });
    setDialogOpen(true);
  };

  const handleEdit = (trend: Trend) => {
    setEditingTrend(trend);
    setFormData({
      keyword: trend.keyword,
      category: trend.category,
      search_volume: trend.search_volume,
      growth_percentage: trend.growth_percentage,
      business_implications: trend.business_implications,
      source: trend.source,
      is_featured: trend.is_featured,
      is_published: trend.is_published,
    });
    setDialogOpen(true);
  };

  const handleDelete = (trend: Trend) => {
    setDeletingTrend(trend);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!deletingTrend) return;

    try {
      const response = await fetch(
        `${config.apiUrl}/api/trends/${deletingTrend.id}`,
        { method: "DELETE", headers: { Authorization: `Bearer ${accessToken}` } }
      );

      if (response.ok) {
        toast.success("Trend deleted");
        fetchTrends();
      } else {
        toast.error("Failed to delete trend");
      }
    } catch (error) {
      console.error("Failed to delete trend:", error);
      toast.error("Failed to delete trend");
    } finally {
      setDeleteDialogOpen(false);
      setDeletingTrend(null);
    }
  };

  const handleSubmit = async () => {
    try {
      const url = editingTrend
        ? `${config.apiUrl}/api/trends/${editingTrend.id}`
        : `${config.apiUrl}/api/trends`;

      const method = editingTrend ? "PATCH" : "POST";

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success(editingTrend ? "Trend updated" : "Trend created");
        setDialogOpen(false);
        fetchTrends();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to save trend");
      }
    } catch (error) {
      console.error("Failed to save trend:", error);
      toast.error("Failed to save trend");
    }
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(0)}K`;
    return volume.toString();
  };

  const getGrowthBadge = (growth: number) => {
    if (growth >= 500) return { label: "Explosive", variant: "destructive" as const };
    if (growth >= 200) return { label: "Surging", variant: "default" as const };
    if (growth >= 100) return { label: "Growing", variant: "secondary" as const };
    return { label: "Steady", variant: "outline" as const };
  };

  const filteredTrends = trends.filter((trend) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      trend.keyword.toLowerCase().includes(q) ||
      trend.category.toLowerCase().includes(q)
    );
  });

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === filteredTrends.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredTrends.map((t) => t.id)));
    }
  };

  const confirmBulkDelete = async () => {
    const apiUrl = config.apiUrl;
    let deleted = 0;
    for (const id of selectedIds) {
      try {
        const response = await fetch(`${apiUrl}/api/trends/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (response.ok) deleted++;
      } catch {}
    }
    toast.success(`Deleted ${deleted} trends`);
    setSelectedIds(new Set());
    setBulkDeleteDialogOpen(false);
    fetchTrends();
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Trends Management</CardTitle>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Add Trend
          </Button>
        </CardHeader>
        <CardContent>
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-3 mb-4 p-3 bg-muted rounded-lg">
              <span className="text-sm font-medium">{selectedIds.size} selected</span>
              <Button size="sm" variant="destructive" onClick={() => setBulkDeleteDialogOpen(true)}>
                <Trash2 className="h-3 w-3 mr-1" />
                Delete Selected
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setSelectedIds(new Set())}>
                <X className="h-3 w-3 mr-1" />
                Clear
              </Button>
            </div>
          )}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by keyword or category..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : filteredTrends.length === 0 ? (
            <p className="text-muted-foreground">No trends found{searchQuery ? " matching your search" : ""}.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={filteredTrends.length > 0 && selectedIds.size === filteredTrends.length}
                      onCheckedChange={toggleAll}
                    />
                  </TableHead>
                  <TableHead>Keyword</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Volume</TableHead>
                  <TableHead>Growth</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTrends.map((trend) => {
                  const growthBadge = getGrowthBadge(trend.growth_percentage);
                  return (
                    <TableRow key={trend.id}>
                      <TableCell>
                        <Checkbox
                          checked={selectedIds.has(trend.id)}
                          onCheckedChange={() => toggleSelect(trend.id)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <TrendingUp className="h-4 w-4 text-green-500" />
                          <span className="font-medium">{trend.keyword}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{trend.category}</Badge>
                      </TableCell>
                      <TableCell>{formatVolume(trend.search_volume)}</TableCell>
                      <TableCell>
                        <Badge variant={growthBadge.variant}>
                          +{trend.growth_percentage}% {growthBadge.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          {trend.is_featured && (
                            <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                          )}
                          <Badge variant={trend.is_published ? "default" : "secondary"}>
                            {trend.is_published ? "Published" : "Draft"}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="icon" onClick={() => handleEdit(trend)}>
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => handleDelete(trend)}>
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) setIsFullView(false); }}>
        <DialogContent className={isFullView ? "sm:max-w-[95vw] max-w-[95vw] w-full max-h-[95vh] overflow-y-auto" : "sm:max-w-2xl"}>
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle>{editingTrend ? "Edit Trend" : "Add New Trend"}</DialogTitle>
                <DialogDescription>
                  {editingTrend ? "Update the trend details." : "Add a new trending keyword."}
                </DialogDescription>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setIsFullView(!isFullView)} title={isFullView ? "Compact view" : "Full view"}>
                {isFullView ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </Button>
            </div>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="keyword">Keyword</Label>
                <Input
                  id="keyword"
                  value={formData.keyword}
                  onChange={(e) => setFormData({ ...formData, keyword: e.target.value })}
                  placeholder="AI agents"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData({ ...formData, category: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((cat) => (
                      <SelectItem key={cat} value={cat}>
                        {cat}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="search_volume">Search Volume</Label>
                <Input
                  id="search_volume"
                  type="number"
                  value={formData.search_volume}
                  onChange={(e) =>
                    setFormData({ ...formData, search_volume: parseInt(e.target.value) || 0 })
                  }
                  placeholder="135000"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="growth_percentage">Growth Percentage</Label>
                <Input
                  id="growth_percentage"
                  type="number"
                  value={formData.growth_percentage}
                  onChange={(e) =>
                    setFormData({ ...formData, growth_percentage: parseFloat(e.target.value) || 0 })
                  }
                  placeholder="245"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="business_implications">Business Implications</Label>
              <Textarea
                id="business_implications"
                value={formData.business_implications}
                onChange={(e) =>
                  setFormData({ ...formData, business_implications: e.target.value })
                }
                placeholder="What this trend means for startups..."
                rows={4}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="source">Source</Label>
              <Input
                id="source"
                value={formData.source}
                onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                placeholder="Google Trends"
              />
            </div>
            <div className="flex gap-6">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_featured"
                  checked={formData.is_featured}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, is_featured: checked as boolean })
                  }
                />
                <Label htmlFor="is_featured">Featured</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_published"
                  checked={formData.is_published}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, is_published: checked as boolean })
                  }
                />
                <Label htmlFor="is_published">Published</Label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>
              {editingTrend ? "Update Trend" : "Create Trend"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Trend</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{deletingTrend?.keyword}"?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog open={bulkDeleteDialogOpen} onOpenChange={setBulkDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete {selectedIds.size} Trends</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {selectedIds.size} selected trends? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmBulkDelete}>
              Delete All
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
