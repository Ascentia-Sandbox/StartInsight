"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Pencil, Trash2, Star, Eye, BookOpen, Search, X, Maximize2, Minimize2, Download } from "lucide-react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { getSupabaseClient } from "@/lib/supabase/client";
import { formatDateMYT } from "@/lib/utils";
import { config } from "@/lib/env";

interface MarketInsight {
  id: string;
  title: string;
  slug: string;
  summary: string;
  content: string;
  category: string;
  author_name: string;
  author_avatar_url: string | null;
  cover_image_url: string | null;
  reading_time_minutes: number;
  view_count: number;
  is_featured: boolean;
  is_published: boolean;
  published_at: string | null;
  created_at: string;
}

const categories = ["Trends", "Analysis", "Guides", "Announcements", "Case Studies"];

export default function AdminMarketInsightsPage() {
  const router = useRouter();
  const [articles, setArticles] = useState<MarketInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);
  const [editingArticle, setEditingArticle] = useState<MarketInsight | null>(null);
  const [deletingArticle, setDeletingArticle] = useState<MarketInsight | null>(null);
  const [isFullView, setIsFullView] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    slug: "",
    summary: "",
    content: "",
    category: "",
    author_name: "StartInsight Team",
    author_avatar_url: "",
    cover_image_url: "",
    reading_time_minutes: 5,
    is_featured: false,
    is_published: true,
  });

  const apiUrl = config.apiUrl;

  const authHeaders = (): HeadersInit => ({
    "Content-Type": "application/json",
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
  });

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push("/auth/login?redirectTo=/admin/market-insights");
        return;
      }
      setAccessToken(session.access_token);
    };
    checkAuth();
  }, [router]);

  useEffect(() => {
    if (accessToken) fetchArticles();
  }, [accessToken]);

  const fetchArticles = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/market-insights?limit=50`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) throw new Error("Failed to fetch");
      const data = await response.json();
      setArticles(data.articles || []);
    } catch (error) {
      console.error("Failed to fetch articles:", error);
      toast.error("Failed to load articles");
    } finally {
      setLoading(false);
    }
  };

  const generateSlug = (title: string) => {
    return title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");
  };

  const handleCreate = () => {
    setEditingArticle(null);
    setFormData({
      title: "",
      slug: "",
      summary: "",
      content: "",
      category: "",
      author_name: "StartInsight Team",
      author_avatar_url: "",
      cover_image_url: "",
      reading_time_minutes: 5,
      is_featured: false,
      is_published: true,
    });
    setDialogOpen(true);
  };

  const handleEdit = (article: MarketInsight) => {
    setEditingArticle(article);
    setFormData({
      title: article.title,
      slug: article.slug,
      summary: article.summary,
      content: article.content,
      category: article.category,
      author_name: article.author_name,
      author_avatar_url: article.author_avatar_url || "",
      cover_image_url: article.cover_image_url || "",
      reading_time_minutes: article.reading_time_minutes,
      is_featured: article.is_featured,
      is_published: article.is_published,
    });
    setDialogOpen(true);
  };

  const handleDelete = (article: MarketInsight) => {
    setDeletingArticle(article);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!deletingArticle || !accessToken) return;

    try {
      const response = await fetch(
        `${apiUrl}/api/market-insights/${deletingArticle.id}`,
        { method: "DELETE", headers: { Authorization: `Bearer ${accessToken}` } }
      );

      if (response.ok) {
        toast.success("Article deleted");
        fetchArticles();
      } else {
        toast.error("Failed to delete article");
      }
    } catch (error) {
      console.error("Failed to delete article:", error);
      toast.error("Failed to delete article");
    } finally {
      setDeleteDialogOpen(false);
      setDeletingArticle(null);
    }
  };

  const handleSubmit = async () => {
    if (!accessToken) return;
    try {
      const url = editingArticle
        ? `${apiUrl}/api/market-insights/${editingArticle.id}`
        : `${apiUrl}/api/market-insights`;

      const method = editingArticle ? "PATCH" : "POST";

      const response = await fetch(url, {
        method,
        headers: authHeaders(),
        body: JSON.stringify({
          ...formData,
          slug: formData.slug || generateSlug(formData.title),
          author_avatar_url: formData.author_avatar_url || null,
          cover_image_url: formData.cover_image_url || null,
        }),
      });

      if (response.ok) {
        toast.success(editingArticle ? "Article updated" : "Article created");
        setDialogOpen(false);
        fetchArticles();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to save article");
      }
    } catch (error) {
      console.error("Failed to save article:", error);
      toast.error("Failed to save article");
    }
  };

  const filteredArticles = articles.filter((article) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      article.title.toLowerCase().includes(q) ||
      article.category.toLowerCase().includes(q) ||
      article.author_name.toLowerCase().includes(q)
    );
  });

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === filteredArticles.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredArticles.map((a) => a.id)));
    }
  };

  const confirmBulkDelete = async () => {
    if (!accessToken || selectedIds.size === 0) return;

    let successCount = 0;
    for (const id of selectedIds) {
      try {
        const response = await fetch(`${apiUrl}/api/market-insights/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (response.ok) successCount++;
      } catch (error) {
        console.error(`Failed to delete article ${id}:`, error);
      }
    }

    toast.success(`Deleted ${successCount} of ${selectedIds.size} articles`);
    setSelectedIds(new Set());
    setBulkDeleteDialogOpen(false);
    fetchArticles();
  };

  const handleExport = async (format: "csv" | "json") => {
    if (!accessToken) return;

    try {
      const response = await fetch(
        `${apiUrl}/api/admin/export/market-insights?format=${format}`,
        {
          headers: { Authorization: `Bearer ${accessToken}` },
        }
      );

      if (!response.ok) {
        throw new Error("Export failed");
      }

      if (format === "json") {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `market-insights-export-${new Date().toISOString().split("T")[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        // CSV
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `market-insights-export-${new Date().toISOString().split("T")[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }

      toast.success(`Exported ${articles.length} articles as ${format.toUpperCase()}`);
    } catch (error) {
      console.error("Export failed:", error);
      toast.error("Failed to export articles");
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Market Insights Management</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => handleExport("csv")}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            <Button variant="outline" onClick={() => handleExport("json")}>
              <Download className="h-4 w-4 mr-2" />
              Export JSON
            </Button>
            <Button onClick={handleCreate}>
              <Plus className="h-4 w-4 mr-2" />
              Add Article
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-3 mb-4 p-3 bg-muted rounded-md">
              <span className="text-sm font-medium">{selectedIds.size} selected</span>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setBulkDeleteDialogOpen(true)}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Delete Selected
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedIds(new Set())}
              >
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            </div>
          )}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by title, category, or author..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : filteredArticles.length === 0 ? (
            <p className="text-muted-foreground">No articles found{searchQuery ? " matching your search" : ""}.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={
                        filteredArticles.length > 0 &&
                        selectedIds.size === filteredArticles.length
                      }
                      onCheckedChange={toggleAll}
                    />
                  </TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Author</TableHead>
                  <TableHead>Views</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredArticles.map((article) => (
                  <TableRow key={article.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedIds.has(article.id)}
                        onCheckedChange={() => toggleSelect(article.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium line-clamp-1">{article.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatDateMYT(article.published_at)} · {article.reading_time_minutes} min
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{article.category}</Badge>
                    </TableCell>
                    <TableCell>{article.author_name}</TableCell>
                    <TableCell>{article.view_count}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {article.is_featured && (
                          <Star className="h-4 w-4 text-yellow-500 dark:text-yellow-400 fill-yellow-500 dark:fill-yellow-400" />
                        )}
                        <Badge variant={article.is_published ? "default" : "secondary"}>
                          {article.is_published ? "Published" : "Draft"}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            window.open(`/market-insights/${article.slug}`, "_blank")
                          }
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleEdit(article)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(article)}>
                          <Trash2 className="h-4 w-4 text-red-500 dark:text-red-400" />
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
        <DialogContent className={isFullView ? "sm:max-w-[95vw] max-w-[95vw] w-full max-h-[95vh] overflow-y-auto" : "sm:max-w-4xl max-h-[90vh] overflow-y-auto"}>
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle>{editingArticle ? "Edit Article" : "Add New Article"}</DialogTitle>
                <DialogDescription>
                  {editingArticle
                    ? "Update the article details."
                    : "Create a new market insight article. Supports Markdown formatting."}
                </DialogDescription>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setIsFullView(!isFullView)} title={isFullView ? "Compact view" : "Full view"}>
                {isFullView ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </Button>
            </div>
          </DialogHeader>
          <Tabs defaultValue="content" className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="meta">Meta & Settings</TabsTrigger>
              <TabsTrigger value="preview">Preview</TabsTrigger>
            </TabsList>
            <TabsContent value="content" className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => {
                    const title = e.target.value;
                    setFormData({
                      ...formData,
                      title,
                      slug: formData.slug || generateSlug(title),
                    });
                  }}
                  placeholder="The Rise of AI Agents: Why 2025 Is the Year of Autonomous AI"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="summary">Summary</Label>
                <Textarea
                  id="summary"
                  value={formData.summary}
                  onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                  placeholder="A brief summary of the article..."
                  rows={2}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="content">Content (Markdown)</Label>
                <Textarea
                  id="content"
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="## Introduction\n\nWrite your article content here using Markdown..."
                  rows={20}
                  className="font-mono text-sm"
                />
              </div>
            </TabsContent>
            <TabsContent value="meta" className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="slug">URL Slug</Label>
                  <Input
                    id="slug"
                    value={formData.slug}
                    onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                    placeholder="rise-of-ai-agents-2025"
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
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="author_name">Author Name</Label>
                  <Input
                    id="author_name"
                    value={formData.author_name}
                    onChange={(e) => setFormData({ ...formData, author_name: e.target.value })}
                    placeholder="StartInsight Team"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reading_time_minutes">Reading Time (minutes)</Label>
                  <Input
                    id="reading_time_minutes"
                    type="number"
                    value={formData.reading_time_minutes}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        reading_time_minutes: parseInt(e.target.value) || 5,
                      })
                    }
                    placeholder="8"
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="author_avatar_url">Author Avatar URL</Label>
                  <Input
                    id="author_avatar_url"
                    value={formData.author_avatar_url}
                    onChange={(e) =>
                      setFormData({ ...formData, author_avatar_url: e.target.value })
                    }
                    placeholder="https://..."
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cover_image_url">Cover Image URL</Label>
                  <Input
                    id="cover_image_url"
                    value={formData.cover_image_url}
                    onChange={(e) =>
                      setFormData({ ...formData, cover_image_url: e.target.value })
                    }
                    placeholder="https://..."
                  />
                </div>
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
                  <Label htmlFor="is_featured">Featured Article</Label>
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
            </TabsContent>
            <TabsContent value="preview" className="space-y-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Badge variant="outline">{formData.category || "Category"}</Badge>
                    {formData.is_featured && <Badge>Featured</Badge>}
                  </div>
                  <h1 className="text-2xl font-bold mb-2">
                    {formData.title || "Article Title"}
                  </h1>
                  <p className="text-muted-foreground mb-4">
                    {formData.summary || "Article summary..."}
                  </p>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
                    <BookOpen className="h-4 w-4" />
                    <span>{formData.author_name}</span>
                    <span>·</span>
                    <span>{formData.reading_time_minutes} min read</span>
                  </div>
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    {formData.content.split("\n\n").slice(0, 3).map((p, i) => (
                      <p key={i} className="text-muted-foreground">
                        {p.replace(/^#+\s/, "")}
                      </p>
                    ))}
                    {formData.content.split("\n\n").length > 3 && (
                      <p className="text-muted-foreground italic">...more content...</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>
              {editingArticle ? "Update Article" : "Create Article"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Article</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &quot;{deletingArticle?.title}&quot;?
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
            <DialogTitle>Delete {selectedIds.size} Articles</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {selectedIds.size} selected articles? This action
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmBulkDelete}>
              Delete {selectedIds.size} Articles
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
