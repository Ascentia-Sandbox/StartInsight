"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Pencil, Trash2, Star, Eye, Search, X, Maximize2, Minimize2, ExternalLink } from "lucide-react";
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
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { toast } from "sonner";
import { getSupabaseClient } from "@/lib/supabase/client";
import { config } from "@/lib/env";

interface SuccessStory {
  id: string;
  founder_name: string;
  company_name: string;
  tagline: string;
  idea_summary: string;
  journey_narrative: string;
  metrics: Record<string, unknown>;
  timeline: Array<{ date: string; milestone: string }>;
  avatar_url: string | null;
  company_logo_url: string | null;
  source_url: string | null;
  is_featured: boolean;
  is_published: boolean;
  created_at: string;
}

export default function AdminSuccessStoriesPage() {
  const router = useRouter();
  const [stories, setStories] = useState<SuccessStory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [isFullView, setIsFullView] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);
  const [editingStory, setEditingStory] = useState<SuccessStory | null>(null);
  const [deletingStory, setDeletingStory] = useState<SuccessStory | null>(null);
  const [formData, setFormData] = useState({
    founder_name: "",
    company_name: "",
    tagline: "",
    idea_summary: "",
    journey_narrative: "",
    metrics_json: "{}",
    timeline_json: "[]",
    avatar_url: "",
    company_logo_url: "",
    source_url: "",
    is_featured: false,
    is_published: true,
  });

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push("/auth/login?redirectTo=/admin/success-stories");
        return;
      }
      setAccessToken(session.access_token);
    };
    checkAuth();
  }, [router]);

  useEffect(() => {
    if (accessToken) fetchStories();
  }, [accessToken]);

  const apiUrl = config.apiUrl;

  const authHeaders = (): HeadersInit => ({
    "Content-Type": "application/json",
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
  });

  const fetchStories = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/success-stories?limit=50`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) throw new Error("Failed to fetch");
      const data = await response.json();
      setStories(data.stories || []);
    } catch (error) {
      console.error("Failed to fetch stories:", error);
      toast.error("Failed to load success stories");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingStory(null);
    setFormData({
      founder_name: "",
      company_name: "",
      tagline: "",
      idea_summary: "",
      journey_narrative: "",
      metrics_json: JSON.stringify({ mrr: 0, users: 0, funding: "" }, null, 2),
      timeline_json: JSON.stringify([{ date: "", milestone: "" }], null, 2),
      avatar_url: "",
      company_logo_url: "",
      source_url: "",
      is_featured: false,
      is_published: true,
    });
    setDialogOpen(true);
  };

  const handleEdit = (story: SuccessStory) => {
    setEditingStory(story);
    setFormData({
      founder_name: story.founder_name,
      company_name: story.company_name,
      tagline: story.tagline,
      idea_summary: story.idea_summary,
      journey_narrative: story.journey_narrative,
      metrics_json: JSON.stringify(story.metrics, null, 2),
      timeline_json: JSON.stringify(story.timeline, null, 2),
      avatar_url: story.avatar_url || "",
      company_logo_url: story.company_logo_url || "",
      source_url: story.source_url || "",
      is_featured: story.is_featured,
      is_published: story.is_published,
    });
    setDialogOpen(true);
  };

  const handleDelete = (story: SuccessStory) => {
    setDeletingStory(story);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!deletingStory || !accessToken) return;

    try {
      const response = await fetch(
        `${apiUrl}/api/success-stories/${deletingStory.id}`,
        { method: "DELETE", headers: { Authorization: `Bearer ${accessToken}` } }
      );

      if (response.ok) {
        toast.success("Success story deleted");
        fetchStories();
      } else {
        toast.error("Failed to delete story");
      }
    } catch (error) {
      console.error("Failed to delete story:", error);
      toast.error("Failed to delete story");
    } finally {
      setDeleteDialogOpen(false);
      setDeletingStory(null);
    }
  };

  const handleSubmit = async () => {
    if (!accessToken) return;
    try {
      let metrics, timeline;
      try {
        metrics = JSON.parse(formData.metrics_json);
        timeline = JSON.parse(formData.timeline_json);
      } catch {
        toast.error("Invalid JSON format in metrics or timeline");
        return;
      }

      const url = editingStory
        ? `${apiUrl}/api/success-stories/${editingStory.id}`
        : `${apiUrl}/api/success-stories`;

      const method = editingStory ? "PATCH" : "POST";

      const response = await fetch(url, {
        method,
        headers: authHeaders(),
        body: JSON.stringify({
          founder_name: formData.founder_name,
          company_name: formData.company_name,
          tagline: formData.tagline,
          idea_summary: formData.idea_summary,
          journey_narrative: formData.journey_narrative,
          metrics,
          timeline,
          avatar_url: formData.avatar_url || null,
          company_logo_url: formData.company_logo_url || null,
          source_url: formData.source_url || null,
          is_featured: formData.is_featured,
          is_published: formData.is_published,
        }),
      });

      if (response.ok) {
        toast.success(editingStory ? "Story updated" : "Story created");
        setDialogOpen(false);
        fetchStories();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to save story");
      }
    } catch (error) {
      console.error("Failed to save story:", error);
      toast.error("Failed to save story");
    }
  };

  const formatMetrics = (metrics: Record<string, unknown>) => {
    const mrr = metrics.mrr;
    const users = metrics.users;
    if (typeof mrr === "number") {
      return `$${(mrr / 1000).toFixed(0)}K MRR`;
    }
    if (typeof users === "number") {
      return `${users} users`;
    }
    return "-";
  };

  const filteredStories = stories.filter((story) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      story.founder_name.toLowerCase().includes(q) ||
      story.company_name.toLowerCase().includes(q) ||
      story.tagline.toLowerCase().includes(q)
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
    if (selectedIds.size === filteredStories.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredStories.map((s) => s.id)));
    }
  };

  const confirmBulkDelete = async () => {
    if (!accessToken) return;
    let deleted = 0;
    for (const id of selectedIds) {
      try {
        const response = await fetch(`${apiUrl}/api/success-stories/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (response.ok) deleted++;
      } catch {}
    }
    toast.success(`Deleted ${deleted} success stories`);
    setSelectedIds(new Set());
    setBulkDeleteDialogOpen(false);
    fetchStories();
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Success Stories Management</CardTitle>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Add Story
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
              placeholder="Search by founder, company, or tagline..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : filteredStories.length === 0 ? (
            <p className="text-muted-foreground">No success stories found{searchQuery ? " matching your search" : ""}.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={filteredStories.length > 0 && selectedIds.size === filteredStories.length}
                      onCheckedChange={toggleAll}
                    />
                  </TableHead>
                  <TableHead>Founder</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Metrics</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredStories.map((story) => (
                  <TableRow key={story.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedIds.has(story.id)}
                        onCheckedChange={() => toggleSelect(story.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <p className="font-medium">{story.founder_name}</p>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{story.company_name}</p>
                        <p className="text-sm text-muted-foreground">{story.tagline}</p>
                      </div>
                    </TableCell>
                    <TableCell>{formatMetrics(story.metrics)}</TableCell>
                    <TableCell>
                      {story.source_url ? (
                        <a href={story.source_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-sm text-blue-600 hover:underline">
                          <ExternalLink className="h-3.5 w-3.5 flex-shrink-0" />
                          <span className="truncate max-w-[120px]">{story.source_url.replace(/^https?:\/\//, '').split('/')[0]}</span>
                        </a>
                      ) : (
                        <span className="text-sm text-muted-foreground">No link</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {story.is_featured && (
                          <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                        )}
                        <Badge variant={story.is_published ? "default" : "secondary"}>
                          {story.is_published ? "Published" : "Draft"}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => window.open(`/success-stories/${story.id}`, "_blank")}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(story)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(story)}>
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) setIsFullView(false); }}>
        <DialogContent className={isFullView ? "sm:max-w-[95vw] max-w-[95vw] w-full max-h-[95vh] overflow-y-auto" : "sm:max-w-3xl max-h-[90vh] overflow-y-auto"}>
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle>{editingStory ? "Edit Success Story" : "Add Success Story"}</DialogTitle>
                <DialogDescription>
                  {editingStory ? "Update the success story details." : "Create a new founder success story."}
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
                <Label htmlFor="founder_name">Founder Name</Label>
                <Input
                  id="founder_name"
                  value={formData.founder_name}
                  onChange={(e) => setFormData({ ...formData, founder_name: e.target.value })}
                  placeholder="Sarah Chen"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_name">Company Name</Label>
                <Input
                  id="company_name"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  placeholder="MetricMate"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="tagline">Tagline</Label>
              <Input
                id="tagline"
                value={formData.tagline}
                onChange={(e) => setFormData({ ...formData, tagline: e.target.value })}
                placeholder="AI-powered financial forecasting for startups"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="idea_summary">Idea Summary</Label>
              <Textarea
                id="idea_summary"
                value={formData.idea_summary}
                onChange={(e) => setFormData({ ...formData, idea_summary: e.target.value })}
                placeholder="Brief summary of the startup idea..."
                rows={2}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="journey_narrative">Journey Narrative</Label>
              <Textarea
                id="journey_narrative"
                value={formData.journey_narrative}
                onChange={(e) => setFormData({ ...formData, journey_narrative: e.target.value })}
                placeholder="The founder's journey story..."
                rows={6}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="metrics_json">Metrics (JSON)</Label>
                <Textarea
                  id="metrics_json"
                  value={formData.metrics_json}
                  onChange={(e) => setFormData({ ...formData, metrics_json: e.target.value })}
                  placeholder='{"mrr": 45000, "users": 1200}'
                  rows={4}
                  className="font-mono text-sm"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="timeline_json">Timeline (JSON)</Label>
                <Textarea
                  id="timeline_json"
                  value={formData.timeline_json}
                  onChange={(e) => setFormData({ ...formData, timeline_json: e.target.value })}
                  placeholder='[{"date": "Jan 2024", "milestone": "..."}]'
                  rows={4}
                  className="font-mono text-sm"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="avatar_url">Founder Avatar URL</Label>
                <Input
                  id="avatar_url"
                  value={formData.avatar_url}
                  onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
                  placeholder="https://..."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_logo_url">Company Logo URL</Label>
                <Input
                  id="company_logo_url"
                  value={formData.company_logo_url}
                  onChange={(e) => setFormData({ ...formData, company_logo_url: e.target.value })}
                  placeholder="https://..."
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="source_url">Source URL</Label>
              <Input
                id="source_url"
                value={formData.source_url}
                onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
                placeholder="https://techcrunch.com/..."
              />
              <p className="text-xs text-muted-foreground">
                Link to verify this story (TechCrunch, LinkedIn, Crunchbase, etc.)
              </p>
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
              {editingStory ? "Update Story" : "Create Story"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Success Story</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete the story for "{deletingStory?.company_name}"?
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
            <DialogTitle>Delete {selectedIds.size} Success Stories</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {selectedIds.size} selected success stories? This action cannot be undone.
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
