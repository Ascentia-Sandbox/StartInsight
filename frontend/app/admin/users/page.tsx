"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Loader2,
  Search,
  Crown,
  Shield,
  AlertTriangle,
  Plus,
  Pencil,
  Trash2,
  Eye,
  UserX,
  UserCheck,
  CheckSquare,
  Square,
  X,
} from "lucide-react";
import { getSupabaseClient } from "@/lib/supabase/client";
import {
  fetchAdminUsers,
  fetchAdminUserDetail,
  createAdminUser,
  updateAdminUser,
  deleteAdminUser,
  bulkAdminUserAction,
  type AdminUserListItem,
  type AdminUserDetail,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { formatDateMYT } from "@/lib/utils";

const TIERS = ["free", "starter", "pro", "enterprise"] as const;

const tierColors: Record<string, string> = {
  free: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  starter: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  pro: "bg-violet-100 text-violet-700 dark:bg-violet-900 dark:text-violet-300",
  enterprise:
    "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
};

function TierBadge({ tier }: { tier: string }) {
  return (
    <Badge variant="outline" className={tierColors[tier] || tierColors.free}>
      {tier === "enterprise" && <Crown className="h-3 w-3 mr-1" />}
      {tier === "pro" && <Shield className="h-3 w-3 mr-1" />}
      {tier.charAt(0).toUpperCase() + tier.slice(1)}
    </Badge>
  );
}

function RoleBadge({ role }: { role: string | null }) {
  if (!role) return <span className="text-muted-foreground">--</span>;
  const colors: Record<string, string> = {
    admin: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
    moderator:
      "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
    viewer:
      "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  };
  return (
    <Badge variant="outline" className={colors[role] || ""}>
      {role.charAt(0).toUpperCase() + role.slice(1)}
    </Badge>
  );
}

function StatusBadge({ suspended }: { suspended: boolean }) {
  if (suspended) {
    return (
      <Badge variant="destructive" className="text-xs">
        Suspended
      </Badge>
    );
  }
  return (
    <Badge
      variant="outline"
      className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 text-xs"
    >
      Active
    </Badge>
  );
}

export default function AdminUsersPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [search, setSearch] = useState("");
  const [tierFilter, setTierFilter] = useState<string>("all");

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUserListItem | null>(
    null
  );
  const [deletingUser, setDeletingUser] = useState<AdminUserListItem | null>(
    null
  );
  const [viewingUserId, setViewingUserId] = useState<string | null>(null);

  // Form states
  const [createForm, setCreateForm] = useState({
    email: "",
    display_name: "",
    subscription_tier: "free",
    language: "en",
  });
  const [editForm, setEditForm] = useState({
    display_name: "",
    subscription_tier: "",
    language: "",
    is_suspended: false,
  });
  const [deleteReason, setDeleteReason] = useState("");

  // Bulk selection
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        router.push("/auth/login?redirectTo=/admin/users");
        return;
      }
      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };
    checkAuth();
  }, [router]);

  const {
    data: users,
    isLoading,
    error,
  } = useQuery({
    queryKey: [
      "admin-users",
      accessToken,
      search,
      tierFilter === "all" ? undefined : tierFilter,
    ],
    queryFn: () =>
      fetchAdminUsers(accessToken!, {
        search: search || undefined,
        tier: tierFilter === "all" ? undefined : tierFilter,
        limit: 100,
      }),
    enabled: !!accessToken,
  });

  const { data: userDetail, isLoading: isLoadingDetail } = useQuery({
    queryKey: ["admin-user-detail", accessToken, viewingUserId],
    queryFn: () => fetchAdminUserDetail(accessToken!, viewingUserId!),
    enabled: !!accessToken && !!viewingUserId,
  });

  const invalidateUsers = () =>
    queryClient.invalidateQueries({ queryKey: ["admin-users"] });

  const createMutation = useMutation({
    mutationFn: () => createAdminUser(accessToken!, createForm),
    onSuccess: () => {
      toast.success("User created successfully");
      invalidateUsers();
      setCreateDialogOpen(false);
      setCreateForm({
        email: "",
        display_name: "",
        subscription_tier: "free",
        language: "en",
      });
    },
    onError: (err: any) => {
      toast.error(
        err?.response?.data?.detail || "Failed to create user"
      );
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ userId, updates }: { userId: string; updates: any }) =>
      updateAdminUser(accessToken!, userId, updates),
    onSuccess: () => {
      toast.success("User updated successfully");
      invalidateUsers();
      setEditingUser(null);
    },
    onError: () => toast.error("Failed to update user"),
  });

  const deleteMutation = useMutation({
    mutationFn: ({ userId, reason }: { userId: string; reason: string }) =>
      deleteAdminUser(accessToken!, userId, reason),
    onSuccess: () => {
      toast.success("User deleted successfully");
      invalidateUsers();
      setDeletingUser(null);
      setDeleteReason("");
    },
    onError: () => toast.error("Failed to delete user"),
  });

  const bulkMutation = useMutation({
    mutationFn: (payload: {
      user_ids: string[];
      action: string;
      tier?: string;
      reason?: string;
    }) => bulkAdminUserAction(accessToken!, payload),
    onSuccess: (data) => {
      toast.success(`Bulk action applied to ${data.affected} users`);
      invalidateUsers();
      setSelectedIds(new Set());
    },
    onError: () => toast.error("Bulk action failed"),
  });

  const handleEditOpen = (user: AdminUserListItem) => {
    setEditingUser(user);
    setEditForm({
      display_name: user.display_name || "",
      subscription_tier: user.subscription_tier,
      language: user.language,
      is_suspended: user.is_suspended,
    });
  };

  const handleEditSave = () => {
    if (!editingUser) return;
    updateMutation.mutate({
      userId: editingUser.id,
      updates: {
        display_name: editForm.display_name || undefined,
        subscription_tier: editForm.subscription_tier,
        language: editForm.language,
        is_suspended: editForm.is_suspended,
      },
    });
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
    if (!users) return;
    if (selectedIds.size === users.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(users.map((u) => u.id)));
    }
  };

  const handleBulkAction = (action: string, tier?: string) => {
    if (selectedIds.size === 0) return;
    bulkMutation.mutate({
      user_ids: Array.from(selectedIds),
      action,
      tier,
    });
  };

  if (isCheckingAuth) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
            <p className="text-muted-foreground">
              You do not have permission to view user management.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const tierCounts = (users || []).reduce(
    (acc, u) => {
      acc[u.subscription_tier] = (acc[u.subscription_tier] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="p-6 lg:p-8 max-w-7xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            User Management
          </h1>
          <p className="text-muted-foreground mt-2">
            View and manage user accounts, tiers, and permissions
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add User
        </Button>
      </div>

      {/* Tier distribution stats */}
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        {TIERS.map((tier) => (
          <Card key={tier}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium capitalize">
                {tier}
              </CardTitle>
              {tier === "enterprise" && (
                <Crown className="h-4 w-4 text-amber-500" />
              )}
              {tier === "pro" && (
                <Shield className="h-4 w-4 text-violet-500" />
              )}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {isLoading ? (
                  <Loader2 className="animate-spin h-5 w-5" />
                ) : (
                  tierCounts[tier] || 0
                )}
              </div>
              <p className="text-xs text-muted-foreground">users</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Bulk action bar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-3 mb-4 p-3 bg-muted rounded-lg">
          <span className="text-sm font-medium">
            {selectedIds.size} selected
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleBulkAction("suspend")}
          >
            <UserX className="h-3 w-3 mr-1" />
            Suspend
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleBulkAction("unsuspend")}
          >
            <UserCheck className="h-3 w-3 mr-1" />
            Unsuspend
          </Button>
          <Select
            onValueChange={(tier) => handleBulkAction("change_tier", tier)}
          >
            <SelectTrigger className="w-[160px] h-8 text-sm">
              <SelectValue placeholder="Bulk Change Tier" />
            </SelectTrigger>
            <SelectContent>
              {TIERS.map((t) => (
                <SelectItem key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            size="sm"
            variant="destructive"
            onClick={() => handleBulkAction("delete")}
          >
            <Trash2 className="h-3 w-3 mr-1" />
            Delete
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setSelectedIds(new Set())}
          >
            <X className="h-3 w-3 mr-1" />
            Clear
          </Button>
        </div>
      )}

      {/* Search and filters */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by email or name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={tierFilter} onValueChange={setTierFilter}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Filter by tier" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tiers</SelectItem>
                {TIERS.map((tier) => (
                  <SelectItem key={tier} value={tier}>
                    {tier.charAt(0).toUpperCase() + tier.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin h-8 w-8 text-primary" />
            </div>
          ) : !users || users.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No users found.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={
                        users.length > 0 && selectedIds.size === users.length
                      }
                      onCheckedChange={toggleAll}
                    />
                  </TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Tier</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedIds.has(user.id)}
                        onCheckedChange={() => toggleSelect(user.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">
                          {user.display_name || "\u2014"}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {user.email}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <TierBadge tier={user.subscription_tier} />
                    </TableCell>
                    <TableCell>
                      <RoleBadge role={user.admin_role} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge suspended={user.is_suspended} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {user.last_login_at
                        ? formatDateMYT(user.last_login_at)
                        : "\u2014"}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setViewingUserId(user.id)}
                          title="View details"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEditOpen(user)}
                          title="Edit user"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeletingUser(user)}
                          title="Delete user"
                        >
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

      {/* Create User Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
            <DialogDescription>
              Add a new user account manually.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="create-email">Email</Label>
              <Input
                id="create-email"
                type="email"
                value={createForm.email}
                onChange={(e) =>
                  setCreateForm({ ...createForm, email: e.target.value })
                }
                placeholder="user@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-name">Display Name</Label>
              <Input
                id="create-name"
                value={createForm.display_name}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    display_name: e.target.value,
                  })
                }
                placeholder="John Doe"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Subscription Tier</Label>
                <Select
                  value={createForm.subscription_tier}
                  onValueChange={(v) =>
                    setCreateForm({ ...createForm, subscription_tier: v })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TIERS.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Language</Label>
                <Select
                  value={createForm.language}
                  onValueChange={(v) =>
                    setCreateForm({ ...createForm, language: v })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="zh-CN">Chinese</SelectItem>
                    <SelectItem value="id-ID">Indonesian</SelectItem>
                    <SelectItem value="vi-VN">Vietnamese</SelectItem>
                    <SelectItem value="th-TH">Thai</SelectItem>
                    <SelectItem value="tl-PH">Filipino</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setCreateDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending || !createForm.email}
            >
              {createMutation.isPending && (
                <Loader2 className="animate-spin h-4 w-4 mr-2" />
              )}
              Create User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog
        open={!!editingUser}
        onOpenChange={(open) => !open && setEditingUser(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>
              Update details for <strong>{editingUser?.email}</strong>
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Display Name</Label>
              <Input
                value={editForm.display_name}
                onChange={(e) =>
                  setEditForm({ ...editForm, display_name: e.target.value })
                }
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Subscription Tier</Label>
                <Select
                  value={editForm.subscription_tier}
                  onValueChange={(v) =>
                    setEditForm({ ...editForm, subscription_tier: v })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TIERS.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Language</Label>
                <Select
                  value={editForm.language}
                  onValueChange={(v) =>
                    setEditForm({ ...editForm, language: v })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="zh-CN">Chinese</SelectItem>
                    <SelectItem value="id-ID">Indonesian</SelectItem>
                    <SelectItem value="vi-VN">Vietnamese</SelectItem>
                    <SelectItem value="th-TH">Thai</SelectItem>
                    <SelectItem value="tl-PH">Filipino</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div>
                <Label>Suspended</Label>
                <p className="text-xs text-muted-foreground">
                  Suspend this user&apos;s account
                </p>
              </div>
              <Switch
                checked={editForm.is_suspended}
                onCheckedChange={(v) =>
                  setEditForm({ ...editForm, is_suspended: v })
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingUser(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleEditSave}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending && (
                <Loader2 className="animate-spin h-4 w-4 mr-2" />
              )}
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog
        open={!!deletingUser}
        onOpenChange={(open) => !open && setDeletingUser(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete User</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete{" "}
              <strong>{deletingUser?.email}</strong>? This is a soft delete and
              can be reversed.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="delete-reason">Reason (optional)</Label>
            <Textarea
              id="delete-reason"
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
              placeholder="Reason for deletion..."
              rows={3}
              className="mt-2"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeletingUser(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() =>
                deletingUser &&
                deleteMutation.mutate({
                  userId: deletingUser.id,
                  reason: deleteReason,
                })
              }
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && (
                <Loader2 className="animate-spin h-4 w-4 mr-2" />
              )}
              Delete User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* User Detail Sheet */}
      <Sheet
        open={!!viewingUserId}
        onOpenChange={(open) => !open && setViewingUserId(null)}
      >
        <SheetContent className="sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>User Details</SheetTitle>
            <SheetDescription>
              Full user profile and statistics
            </SheetDescription>
          </SheetHeader>
          {isLoadingDetail ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin h-8 w-8 text-primary" />
            </div>
          ) : userDetail ? (
            <div className="mt-6 space-y-6">
              <div className="space-y-2">
                <p className="text-xl font-semibold">
                  {userDetail.display_name || "\u2014"}
                </p>
                <p className="text-sm text-muted-foreground">
                  {userDetail.email}
                </p>
              </div>
              <div className="flex gap-2">
                <TierBadge tier={userDetail.subscription_tier} />
                <RoleBadge role={userDetail.admin_role} />
                <StatusBadge suspended={userDetail.is_suspended} />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-4 text-center">
                    <p className="text-2xl font-bold">
                      {userDetail.insights_saved}
                    </p>
                    <p className="text-xs text-muted-foreground">Saved</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-center">
                    <p className="text-2xl font-bold">
                      {userDetail.research_count}
                    </p>
                    <p className="text-xs text-muted-foreground">Research</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4 text-center">
                    <p className="text-2xl font-bold">
                      {userDetail.total_sessions}
                    </p>
                    <p className="text-xs text-muted-foreground">Sessions</p>
                  </CardContent>
                </Card>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Language</span>
                  <span>{userDetail.language}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Joined</span>
                  <span>
                    {formatDateMYT(userDetail.created_at)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Last Login</span>
                  <span>
                    {userDetail.last_login_at
                      ? formatDateMYT(userDetail.last_login_at)
                      : "\u2014"}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground py-8 text-center">
              User not found.
            </p>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
