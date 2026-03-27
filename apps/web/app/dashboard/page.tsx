"use client";

import { useAuth } from "@/lib/auth";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import {
    LayoutDashboard,
    Truck,
    Factory,
    LogOut,
    ShoppingBag,
    Settings,
    RefreshCw,
    Package,
    Clock,
    CheckCircle2,
    AlertTriangle,
    Activity,
    Loader2,
} from "lucide-react";
import Link from "next/link";
import { useState, useEffect, useCallback } from "react";

interface Metrics {
    orders: {
        pending: number;
        approved: number;
        waiting_manufacturing: number;
        ready_for_delivery: number;
        completed: number;
    };
    manufacturing: {
        outstanding_demand: number;
        completed_today: number;
        remaining_today: number;
    };
    delivery: {
        deliveries_today: number;
        completed_today: number;
        delayed: number;
    };
    generated_at: string;
}

interface AuditEntry {
    id: string;
    timestamp: string;
    action: string;
    entity_type: string;
    user_name: string;
}

export default function DashboardPage() {
    const { user, isLoading, logout } = useAuth();
    const { toast } = useToast();

    const [metrics, setMetrics] = useState<Metrics | null>(null);
    const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
    const [metricsLoading, setMetricsLoading] = useState(false);
    const [refreshing, setRefreshing] = useState(false);

    // Redirect unauthenticated users
    useEffect(() => {
        if (!isLoading && !user) {
            window.location.href = "/login";
        }
    }, [user, isLoading]);

    const loadMetrics = useCallback(async () => {
        if (!user || user.role !== "admin") return;
        setMetricsLoading(true);
        try {
            const [m, a] = await Promise.all([
                apiService.ops.getMetrics(),
                apiService.ops.getAuditLog({ limit: 20 }),
            ]);
            setMetrics(m);
            setAuditLog(a);
        } catch (e: any) {
            toast({
                variant: "destructive",
                title: "Failed to load metrics",
                description: e?.message || "Could not fetch dashboard data.",
            });
        } finally {
            setMetricsLoading(false);
        }
    }, [user, toast]);

    useEffect(() => {
        loadMetrics();
    }, [loadMetrics]);

    const handleRefresh = async () => {
        setRefreshing(true);
        await loadMetrics();
        setRefreshing(false);
    };

    if (isLoading || !user) {
        return (
            <div className="flex h-screen items-center justify-center text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                Loading...
            </div>
        );
    }

    const isAdmin = user?.role === "admin";

    const formatTimestamp = (ts: string) => {
        try {
            const date = new Date(ts);
            return date.toLocaleString("en-ZA", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return ts;
        }
    };

    return (
        <div className="min-h-screen bg-surface">
            {/* Top Bar */}
            <div className="bg-background/80 backdrop-blur-md border-b px-8 py-5 flex justify-between items-center sticky top-0 z-20">
                <div className="flex items-center gap-3">
                    <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center shadow-lg shadow-primary/20">
                        <LayoutDashboard className="h-5 w-5 text-white" />
                    </div>
                    <h1 className="text-2xl font-heading font-semibold tracking-tight">Command Center</h1>
                </div>
                <div className="flex items-center gap-6">
                    <div className="text-sm text-right hidden md:block">
                        <div className="font-medium text-foreground">{user?.full_name}</div>
                        <div className="text-xs text-muted-foreground capitalize">{user?.role}</div>
                    </div>
                    <Button variant="ghost" className="text-muted-foreground hover:text-foreground" onClick={logout}>
                        <LogOut className="h-5 w-5 mr-2" /> Logout
                    </Button>
                </div>
            </div>

            <div className="container mx-auto p-8 space-y-8">
                {/* Navigation Cards */}
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                    <Link href="/admin">
                        <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full border-l-4 border-l-primary">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Settings className="h-5 w-5" /> Admin
                                </CardTitle>
                                <CardDescription>Approvals & Overview</CardDescription>
                            </CardHeader>
                        </Card>
                    </Link>

                    <Link href="/sales-dashboard">
                        <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full border-l-4 border-l-blue-500">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <ShoppingBag className="h-5 w-5" /> Sales
                                </CardTitle>
                                <CardDescription>Order Pipeline</CardDescription>
                            </CardHeader>
                        </Card>
                    </Link>

                    <Link href="/manufacturing-dashboard">
                        <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full border-l-4 border-l-orange-500">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Factory className="h-5 w-5" /> Manufacturing
                                </CardTitle>
                                <CardDescription>Production Queue</CardDescription>
                            </CardHeader>
                        </Card>
                    </Link>

                    <Link href="/delivery-dashboard">
                        <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full border-l-4 border-l-green-500">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Truck className="h-5 w-5" /> Delivery (Legacy)
                                </CardTitle>
                                <CardDescription>Old Dispatch View</CardDescription>
                            </CardHeader>
                        </Card>
                    </Link>
                </div>

                {/* Operational Metrics - Admin Only */}
                {isAdmin && (
                    <>
                        {/* Section Header with Refresh */}
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-semibold flex items-center gap-2">
                                <Activity className="h-5 w-5" /> Operational Metrics
                            </h2>
                            <div className="flex items-center gap-3">
                                {metrics?.generated_at && (
                                    <span className="text-xs text-muted-foreground">
                                        Updated {formatTimestamp(metrics.generated_at)}
                                    </span>
                                )}
                                <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={handleRefresh}
                                    disabled={refreshing || metricsLoading}
                                >
                                    <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
                                    Refresh
                                </Button>
                            </div>
                        </div>

                        {metricsLoading && !metrics ? (
                            <div className="flex items-center justify-center py-16 text-muted-foreground">
                                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                                Loading metrics...
                            </div>
                        ) : metrics ? (
                            <div className="space-y-6">
                                {/* Orders Section */}
                                <div>
                                    <h3 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
                                        <Package className="h-4 w-4" /> Orders
                                    </h3>
                                    <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-5">
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="text-2xl font-bold">{metrics.orders.pending}</div>
                                                <p className="text-xs text-muted-foreground mt-1">Pending</p>
                                            </CardContent>
                                        </Card>
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="text-2xl font-bold">{metrics.orders.approved}</div>
                                                <p className="text-xs text-muted-foreground mt-1">Approved</p>
                                            </CardContent>
                                        </Card>
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="text-2xl font-bold">{metrics.orders.waiting_manufacturing}</div>
                                                <p className="text-xs text-muted-foreground mt-1">Waiting Manufacturing</p>
                                            </CardContent>
                                        </Card>
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="text-2xl font-bold">{metrics.orders.ready_for_delivery}</div>
                                                <p className="text-xs text-muted-foreground mt-1">Ready for Delivery</p>
                                            </CardContent>
                                        </Card>
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="text-2xl font-bold text-green-600">{metrics.orders.completed}</div>
                                                <p className="text-xs text-muted-foreground mt-1">Completed</p>
                                            </CardContent>
                                        </Card>
                                    </div>
                                </div>

                                {/* Manufacturing Section */}
                                <div>
                                    <h3 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
                                        <Factory className="h-4 w-4" /> Manufacturing
                                    </h3>
                                    <div className="grid gap-4 md:grid-cols-3">
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="text-2xl font-bold">{metrics.manufacturing.outstanding_demand}</div>
                                                <p className="text-xs text-muted-foreground mt-1">Outstanding Demand</p>
                                            </CardContent>
                                        </Card>
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="flex items-center gap-2">
                                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                                    <div className="text-2xl font-bold text-green-600">{metrics.manufacturing.completed_today}</div>
                                                </div>
                                                <p className="text-xs text-muted-foreground mt-1">Completed Today</p>
                                            </CardContent>
                                        </Card>
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="flex items-center gap-2">
                                                    <Clock className="h-5 w-5 text-orange-500" />
                                                    <div className="text-2xl font-bold text-orange-600">{metrics.manufacturing.remaining_today}</div>
                                                </div>
                                                <p className="text-xs text-muted-foreground mt-1">Remaining Today</p>
                                            </CardContent>
                                        </Card>
                                    </div>
                                </div>

                                {/* Delivery Section */}
                                <div>
                                    <h3 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
                                        <Truck className="h-4 w-4" /> Delivery
                                    </h3>
                                    <div className="grid gap-4 md:grid-cols-3">
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="text-2xl font-bold">{metrics.delivery.deliveries_today}</div>
                                                <p className="text-xs text-muted-foreground mt-1">Deliveries Today</p>
                                            </CardContent>
                                        </Card>
                                        <Card>
                                            <CardContent className="pt-6">
                                                <div className="flex items-center gap-2">
                                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                                    <div className="text-2xl font-bold text-green-600">{metrics.delivery.completed_today}</div>
                                                </div>
                                                <p className="text-xs text-muted-foreground mt-1">Completed Today</p>
                                            </CardContent>
                                        </Card>
                                        <Card className={metrics.delivery.delayed > 0 ? "border-red-300 bg-red-50/50" : ""}>
                                            <CardContent className="pt-6">
                                                <div className="flex items-center gap-2">
                                                    {metrics.delivery.delayed > 0 && (
                                                        <AlertTriangle className="h-5 w-5 text-red-500" />
                                                    )}
                                                    <div className={`text-2xl font-bold ${metrics.delivery.delayed > 0 ? "text-red-600" : ""}`}>
                                                        {metrics.delivery.delayed}
                                                    </div>
                                                    {metrics.delivery.delayed > 0 && (
                                                        <Badge variant="destructive" className="ml-1">Warning</Badge>
                                                    )}
                                                </div>
                                                <p className="text-xs text-muted-foreground mt-1">Delayed</p>
                                            </CardContent>
                                        </Card>
                                    </div>
                                </div>
                            </div>
                        ) : null}

                        {/* Recent Activity */}
                        {auditLog.length > 0 && (
                            <div className="bg-white p-6 rounded-lg border shadow-sm">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <Activity className="h-5 w-5" /> Recent Activity
                                </h3>
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead className="w-40">Timestamp</TableHead>
                                            <TableHead>Action</TableHead>
                                            <TableHead>Entity Type</TableHead>
                                            <TableHead>User</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {auditLog.map((entry, idx) => (
                                            <TableRow key={entry.id || idx}>
                                                <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                                                    {formatTimestamp(entry.timestamp)}
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant="outline" className="font-mono text-xs">
                                                        {entry.action}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell className="text-sm">{entry.entity_type}</TableCell>
                                                <TableCell className="text-sm">{entry.user_name}</TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
