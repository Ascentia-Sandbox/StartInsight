"use client";

import { useEffect, useState, useMemo, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus, Pencil, Trash2, Star, ExternalLink, Link2, Search, X, Maximize2, Minimize2 } from "lucide-react";
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
import { AdminPagination } from "@/components/admin/admin-pagination";

interface Tool {
  id: string;
  name: string;
  tagline: string;
  description: string;
  category: string;
  pricing: string;
  website_url: string;
  logo_url: string | null;
  is_featured: boolean;
  sort_order: number;
  created_at: string;
}

const categories = [
  "Payments",
  "No-Code",
  "Analytics",
  "Marketing",
  "AI/ML",
  "Development",
  "Productivity",
  "Design",
  "Communication",
  "Other",
];

export default function AdminToolsPage() {
  return (
    <Suspense fallback={<p className="p-8 text-muted-foreground">Loading...</p>}>
      <AdminToolsContent />
    </Suspense>
  );
}

function AdminToolsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const currentPage = Number(searchParams.get("page")) || 1;
  const perPage = Number(searchParams.get("per_page")) || 25;
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingTool, setEditingTool] = useState<Tool | null>(null);
  const [deletingTool, setDeletingTool] = useState<Tool | null>(null);
  const [isFullView, setIsFullView] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    tagline: "",
    description: "",
    category: "",
    pricing: "",
    website_url: "",
    logo_url: "",
    is_featured: false,
  });

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push("/auth/login?redirectTo=/admin/tools");
        return;
      }
      setAccessToken(session.access_token);
    };
    checkAuth();
  }, [router]);

  useEffect(() => {
    if (accessToken) fetchTools();
  }, [accessToken]);

  const fetchTools = async () => {
    try {
      const response = await fetch(
        `${config.apiUrl}/api/tools?limit=100`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      if (!response.ok) throw new Error("Failed to fetch");
      const data = await response.json();
      setTools(data.tools || []);
    } catch (error) {
      console.error("Failed to fetch tools:", error);
      toast.error("Failed to load tools");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingTool(null);
    setFormData({
      name: "",
      tagline: "",
      description: "",
      category: "",
      pricing: "",
      website_url: "",
      logo_url: "",
      is_featured: false,
    });
    setDialogOpen(true);
  };

  const handleEdit = (tool: Tool) => {
    setEditingTool(tool);
    setFormData({
      name: tool.name,
      tagline: tool.tagline,
      description: tool.description,
      category: tool.category,
      pricing: tool.pricing,
      website_url: tool.website_url,
      logo_url: tool.logo_url || "",
      is_featured: tool.is_featured,
    });
    setDialogOpen(true);
  };

  const handleDelete = (tool: Tool) => {
    setDeletingTool(tool);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!deletingTool) return;

    try {
      const response = await fetch(
        `${config.apiUrl}/api/tools/${deletingTool.id}`,
        { method: "DELETE", headers: { Authorization: `Bearer ${accessToken}` } }
      );

      if (response.ok) {
        toast.success("Tool deleted successfully");
        fetchTools();
      } else {
        toast.error("Failed to delete tool");
      }
    } catch (error) {
      console.error("Failed to delete tool:", error);
      toast.error("Failed to delete tool");
    } finally {
      setDeleteDialogOpen(false);
      setDeletingTool(null);
    }
  };

  const handleSubmit = async () => {
    try {
      const url = editingTool
        ? `${config.apiUrl}/api/tools/${editingTool.id}`
        : `${config.apiUrl}/api/tools`;

      const method = editingTool ? "PATCH" : "POST";

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({
          ...formData,
          logo_url: formData.logo_url || null,
        }),
      });

      if (response.ok) {
        toast.success(editingTool ? "Tool updated successfully" : "Tool created successfully");
        setDialogOpen(false);
        fetchTools();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to save tool");
      }
    } catch (error) {
      console.error("Failed to save tool:", error);
      toast.error("Failed to save tool");
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === filteredTools.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredTools.map((t) => t.id)));
    }
  };

  const confirmBulkDelete = async () => {
    const apiUrl = config.apiUrl;
    let deleted = 0;
    for (const id of selectedIds) {
      try {
        const response = await fetch(`${apiUrl}/api/tools/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (response.ok) deleted++;
      } catch {}
    }
    toast.success(`Deleted ${deleted} tools`);
    setSelectedIds(new Set());
    setBulkDeleteDialogOpen(false);
    fetchTools();
  };

  const filteredTools = tools.filter((tool) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      tool.name.toLowerCase().includes(q) ||
      tool.category.toLowerCase().includes(q) ||
      tool.description.toLowerCase().includes(q)
    );
  });

  const paginatedTools = useMemo(() => {
    const start = (currentPage - 1) * perPage;
    return filteredTools.slice(start, start + perPage);
  }, [filteredTools, currentPage, perPage]);

  return (
    <div className="container mx-auto py-8 px-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Tools Management</CardTitle>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Add Tool
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
              placeholder="Search tools by name, category, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : filteredTools.length === 0 ? (
            <p className="text-muted-foreground">No tools found{searchQuery ? " matching your search" : ". Create your first tool!"}.</p>
          ) : (
            <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={filteredTools.length > 0 && selectedIds.size === filteredTools.length}
                      onCheckedChange={toggleAll}
                    />
                  </TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Pricing</TableHead>
                  <TableHead>Affiliate / Website URL</TableHead>
                  <TableHead>Featured</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedTools.map((tool) => (
                  <TableRow key={tool.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedIds.has(tool.id)}
                        onCheckedChange={() => toggleSelect(tool.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{tool.name}</p>
                        <p className="text-sm text-muted-foreground">{tool.tagline}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{tool.category}</Badge>
                    </TableCell>
                    <TableCell>{tool.pricing}</TableCell>
                    <TableCell>
                      {tool.website_url ? (
                        <div className="flex items-center gap-1.5 max-w-[200px]">
                          <Link2 className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                          <span className="text-sm text-muted-foreground truncate" title={tool.website_url}>
                            {tool.website_url.replace(/^https?:\/\//, '').split('/')[0]}
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-red-500 dark:text-red-400">No link</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {tool.is_featured && (
                        <Star className="h-4 w-4 text-yellow-500 dark:text-yellow-400 fill-yellow-500 dark:fill-yellow-400" />
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => window.open(tool.website_url, "_blank")}
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEdit(tool)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(tool)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500 dark:text-red-400" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <AdminPagination
              totalItems={filteredTools.length}
              currentPage={currentPage}
              perPage={perPage}
            />
            </>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) setIsFullView(false); }}>
        <DialogContent className={isFullView ? "sm:max-w-[95vw] max-w-[95vw] w-full max-h-[95vh] overflow-y-auto" : "sm:max-w-2xl"}>
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle>{editingTool ? "Edit Tool" : "Add New Tool"}</DialogTitle>
                <DialogDescription>
                  {editingTool ? "Update the tool details below." : "Fill in the details for the new tool."}
                </DialogDescription>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setIsFullView(!isFullView)} title={isFullView ? "Compact view" : "Full view"}>
                {isFullView ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </Button>
            </div>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Stripe"
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
            <div className="space-y-2">
              <Label htmlFor="tagline">Tagline</Label>
              <Input
                id="tagline"
                value={formData.tagline}
                onChange={(e) => setFormData({ ...formData, tagline: e.target.value })}
                placeholder="Online payment processing"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="A detailed description of the tool..."
                rows={3}
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="pricing">Pricing</Label>
                <Input
                  id="pricing"
                  value={formData.pricing}
                  onChange={(e) => setFormData({ ...formData, pricing: e.target.value })}
                  placeholder="Freemium, Pro from $29/mo"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="website_url">Affiliate / Website URL</Label>
                <Input
                  id="website_url"
                  value={formData.website_url}
                  onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                  placeholder="https://stripe.com?ref=startinsight"
                />
                <p className="text-xs text-muted-foreground">
                  Use your affiliate link here. This is the URL visitors will be redirected to when they click &quot;Visit&quot;.
                </p>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="logo_url">Logo URL (optional)</Label>
              <Input
                id="logo_url"
                value={formData.logo_url}
                onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                placeholder="https://example.com/logo.png"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_featured"
                checked={formData.is_featured}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_featured: checked as boolean })
                }
              />
              <Label htmlFor="is_featured">Featured Tool</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit}>
              {editingTool ? "Update Tool" : "Create Tool"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Tool</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &quot;{deletingTool?.name}&quot;? This action cannot be undone.
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
            <DialogTitle>Delete {selectedIds.size} Tools</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {selectedIds.size} selected tools? This action cannot be undone.
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
