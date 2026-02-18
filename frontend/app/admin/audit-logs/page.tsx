"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Loader2,
  AlertTriangle,
  ClipboardList,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { getSupabaseClient } from "@/lib/supabase/client";
import {
  fetchAuditLogs,
  fetchAuditLogStats,
  type AuditLogEntry,
  type AuditLogStats,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDateTimeMYT } from "@/lib/utils";
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

const ACTION_COLORS: Record<string, string> = {
  "resource.create":
    "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  "resource.update":
    "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  "resource.delete":
    "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  "config.change":
    "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
  "user.login":
    "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  "user.logout":
    "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  "data.export":
    "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  "admin.impersonate":
    "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
};

function ActionBadge({ action }: { action: string }) {
  return (
    <Badge
      variant="outline"
      className={ACTION_COLORS[action] || "bg-gray-100 text-gray-700"}
    >
      {action}
    </Badge>
  );
}

function ExpandableDetails({
  details,
}: {
  details: Record<string, unknown> | null;
}) {
  const [expanded, setExpanded] = useState(false);

  if (!details || Object.keys(details).length === 0) {
    return <span className="text-muted-foreground text-xs">--</span>;
  }

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
      >
        {expanded ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        {Object.keys(details).length} fields
      </button>
      {expanded && (
        <pre className="mt-1 p-2 bg-muted rounded text-xs overflow-x-auto max-w-[300px]">
          {JSON.stringify(details, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function AdminAuditLogsPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [actionFilter, setActionFilter] = useState<string>("all");
  const [resourceFilter, setResourceFilter] = useState<string>("all");
  const [daysFilter, setDaysFilter] = useState<number>(7);

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        router.push("/auth/login?redirectTo=/admin/audit-logs");
        return;
      }
      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };
    checkAuth();
  }, [router]);

  const { data: logs, isLoading: isLoadingLogs } = useQuery({
    queryKey: [
      "audit-logs",
      accessToken,
      actionFilter,
      resourceFilter,
      daysFilter,
    ],
    queryFn: () =>
      fetchAuditLogs(accessToken!, {
        action: actionFilter === "all" ? undefined : actionFilter,
        resource_type: resourceFilter === "all" ? undefined : resourceFilter,
        days: daysFilter,
        limit: 100,
      }),
    enabled: !!accessToken,
  });

  const { data: stats } = useQuery({
    queryKey: ["audit-log-stats", accessToken, daysFilter],
    queryFn: () => fetchAuditLogStats(accessToken!, daysFilter),
    enabled: !!accessToken,
  });

  if (isCheckingAuth) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    );
  }

  const actionOptions = stats?.by_action
    ? Object.keys(stats.by_action)
    : [];
  const resourceOptions = stats?.by_resource
    ? Object.keys(stats.by_resource)
    : [];

  return (
    <div className="p-6 lg:p-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Audit Logs</h1>
        <p className="text-muted-foreground mt-2">
          Security audit trail for administrative actions
        </p>
      </div>

      {/* Stats cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                Total Events
              </CardTitle>
              <ClipboardList className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_events}</div>
              <p className="text-xs text-muted-foreground">
                last {stats.period_days} days
              </p>
            </CardContent>
          </Card>
          {Object.entries(stats.by_action)
            .sort(([, a], [, b]) => (b as number) - (a as number))
            .slice(0, 3)
            .map(([action, count]) => (
              <Card key={action}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {action}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{count as number}</div>
                  <p className="text-xs text-muted-foreground">events</p>
                </CardContent>
              </Card>
            ))}
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row gap-4">
            <Select value={actionFilter} onValueChange={setActionFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Action type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                {actionOptions.map((a) => (
                  <SelectItem key={a} value={a}>
                    {a}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={resourceFilter} onValueChange={setResourceFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Resource type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Resources</SelectItem>
                {resourceOptions.map((r) => (
                  <SelectItem key={r} value={r}>
                    {r}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={String(daysFilter)}
              onValueChange={(v) => setDaysFilter(Number(v))}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="90">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingLogs ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin h-8 w-8 text-primary" />
            </div>
          ) : !logs || logs.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No audit log entries found.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                      {formatDateTimeMYT(log.created_at)}
                    </TableCell>
                    <TableCell className="text-sm">
                      {log.user_id
                        ? log.user_id.slice(0, 8) + "..."
                        : "System"}
                    </TableCell>
                    <TableCell>
                      <ActionBadge action={log.action} />
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <span>{log.resource_type}</span>
                        {log.resource_id && (
                          <span className="text-muted-foreground text-xs block">
                            {log.resource_id.slice(0, 8)}...
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <ExpandableDetails details={log.details} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
