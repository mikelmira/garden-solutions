"use client";

import { useEffect, useState, useCallback } from "react";
import { apiService } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
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
    Loader2,
    RefreshCw,
    TrendingUp,
    TrendingDown,
    Factory,
    Truck,
    AlertTriangle,
    BarChart3,
    Package,
    MapPin,
    Clock,
    ShieldAlert,
    DollarSign,
    Users,
    ArrowUpRight,
    ArrowDownRight,
    Zap,
    Target,
    CalendarClock,
    Boxes,
} from "lucide-react";

type Tab = "demand" | "manufacturing" | "delivery" | "alerts" | "business";

export default function IntelligenceDashboardPage() {
    const { toast } = useToast();
    const [activeTab, setActiveTab] = useState<Tab>("alerts");
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    // Data state for each phase
    const [topSkus, setTopSkus] = useState<any[]>([]);
    const [forecast, setForecast] = useState<any[]>([]);
    const [suggestions, setSuggestions] = useState<any>(null);
    const [deliveryOps, setDeliveryOps] = useState<any>(null);
    const [alerts, setAlerts] = useState<any>(null);
    const [business, setBusiness] = useState<any>(null);

    const loadAll = useCallback(async () => {
        try {
            const [topSkuData, forecastData, suggestData, delivData, alertData, bizData] = await Promise.all([
                apiService.analytics.getTopSkus({ days: 30, limit: 10 }).catch(() => []),
                apiService.analytics.getDemandForecast().catch(() => []),
                apiService.analytics.getManufacturingSuggestions().catch(() => null),
                apiService.analytics.getDeliveryOperations().catch(() => null),
                apiService.analytics.getAlerts().catch(() => null),
                apiService.analytics.getBusinessOverview().catch(() => null),
            ]);
            setTopSkus(topSkuData);
            setForecast(forecastData);
            setSuggestions(suggestData);
            setDeliveryOps(delivData);
            setAlerts(alertData);
            setBusiness(bizData);
        } catch (e: any) {
            toast({ variant: "destructive", title: "Failed to load intelligence data", description: e?.message });
        } finally {
            setLoading(false);
        }
    }, [toast]);

    useEffect(() => { loadAll(); }, [loadAll]);

    const handleRefresh = async () => {
        setRefreshing(true);
        await loadAll();
        setRefreshing(false);
    };

    const tabs: { key: Tab; label: string; icon: any; badge?: number }[] = [
        {
            key: "alerts", label: "Alerts", icon: ShieldAlert,
            badge: alerts?.summary?.total || 0,
        },
        { key: "demand", label: "Demand Forecast", icon: TrendingUp },
        { key: "manufacturing", label: "Mfg Planner", icon: Factory },
        { key: "delivery", label: "Delivery Ops", icon: Truck },
        { key: "business", label: "Business", icon: BarChart3 },
    ];

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-24 text-muted-foreground gap-3">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span className="text-sm">Loading operational intelligence...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-heading font-bold tracking-tight">Intelligence</h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        Operational intelligence & analytics
                    </p>
                </div>
                <Button size="sm" variant="outline" onClick={handleRefresh} disabled={refreshing}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
                    Refresh
                </Button>
            </div>

            {/* Alert Summary Banner */}
            {alerts && alerts.summary.high > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0" />
                    <span className="text-sm text-red-800 font-medium">
                        {alerts.summary.high} high-severity alert{alerts.summary.high !== 1 ? "s" : ""} require attention
                    </span>
                    <Button size="sm" variant="ghost" className="ml-auto text-red-700 hover:bg-red-100" onClick={() => setActiveTab("alerts")}>
                        View Alerts
                    </Button>
                </div>
            )}

            {/* Tab Navigation */}
            <div className="flex gap-1 bg-muted/50 p-1 rounded-lg">
                {tabs.map(tab => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                            activeTab === tab.key
                                ? "bg-background text-foreground shadow-sm"
                                : "text-muted-foreground hover:text-foreground"
                        }`}
                    >
                        <tab.icon className="h-4 w-4" />
                        {tab.label}
                        {tab.badge !== undefined && tab.badge > 0 && (
                            <Badge variant={tab.key === "alerts" ? "destructive" : "secondary"} className="ml-1 text-xs px-1.5 py-0">
                                {tab.badge}
                            </Badge>
                        )}
                    </button>
                ))}
            </div>

            {/* ═══ ALERTS TAB ═══ */}
            {activeTab === "alerts" && (
                <AlertsPanel alerts={alerts} />
            )}

            {/* ═══ DEMAND TAB ═══ */}
            {activeTab === "demand" && (
                <DemandPanel topSkus={topSkus} forecast={forecast} />
            )}

            {/* ═══ MANUFACTURING TAB ═══ */}
            {activeTab === "manufacturing" && (
                <ManufacturingPanel suggestions={suggestions} />
            )}

            {/* ═══ DELIVERY TAB ═══ */}
            {activeTab === "delivery" && (
                <DeliveryPanel deliveryOps={deliveryOps} />
            )}

            {/* ═══ BUSINESS TAB ═══ */}
            {activeTab === "business" && (
                <BusinessPanel business={business} />
            )}
        </div>
    );
}


// ──────────────────────────────────────────────────────
// ALERTS PANEL (Phase 4)
// ──────────────────────────────────────────────────────
function AlertsPanel({ alerts }: { alerts: any }) {
    if (!alerts || !alerts.alerts) {
        return <EmptyState message="No alert data available." />;
    }

    const severityColors: Record<string, string> = {
        high: "bg-red-100 text-red-800 border-red-200",
        medium: "bg-amber-100 text-amber-800 border-amber-200",
        low: "bg-blue-100 text-blue-800 border-blue-200",
    };

    const typeIcons: Record<string, any> = {
        stuck_order: Clock,
        negative_inventory: Package,
        manufacturing_backlog: Factory,
        delayed_delivery: Truck,
        low_stock: Boxes,
    };

    if (alerts.alerts.length === 0) {
        return (
            <Card>
                <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                    <ShieldAlert className="h-10 w-10 mb-3 text-green-500" />
                    <p className="font-medium text-foreground">All Clear</p>
                    <p className="text-sm">No active alerts. The system is operating normally.</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-4">
            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                <Card className="border-red-200 bg-red-50/50">
                    <CardContent className="pt-6 flex items-center gap-4">
                        <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
                            <AlertTriangle className="h-5 w-5 text-red-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-red-700">{alerts.summary.high}</div>
                            <p className="text-xs text-red-600">High Severity</p>
                        </div>
                    </CardContent>
                </Card>
                <Card className="border-amber-200 bg-amber-50/50">
                    <CardContent className="pt-6 flex items-center gap-4">
                        <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center">
                            <AlertTriangle className="h-5 w-5 text-amber-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-amber-700">{alerts.summary.medium}</div>
                            <p className="text-xs text-amber-600">Medium Severity</p>
                        </div>
                    </CardContent>
                </Card>
                <Card className="border-blue-200 bg-blue-50/50">
                    <CardContent className="pt-6 flex items-center gap-4">
                        <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                            <ShieldAlert className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-blue-700">{alerts.summary.low}</div>
                            <p className="text-xs text-blue-600">Low Severity</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Alert List */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-base">Active Alerts ({alerts.alerts.length})</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    {alerts.alerts.map((alert: any, idx: number) => {
                        const Icon = typeIcons[alert.type] || AlertTriangle;
                        return (
                            <div
                                key={idx}
                                className={`flex items-start gap-3 p-3 rounded-lg border ${severityColors[alert.severity] || "bg-muted"}`}
                            >
                                <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium text-sm">{alert.title}</span>
                                        <Badge variant="outline" className="text-xs capitalize">
                                            {alert.type.replace(/_/g, " ")}
                                        </Badge>
                                    </div>
                                    <p className="text-xs mt-0.5 opacity-80">{alert.description}</p>
                                </div>
                                <Badge variant={alert.severity === "high" ? "destructive" : "secondary"} className="flex-shrink-0 text-xs capitalize">
                                    {alert.severity}
                                </Badge>
                            </div>
                        );
                    })}
                </CardContent>
            </Card>
        </div>
    );
}


// ──────────────────────────────────────────────────────
// DEMAND PANEL (Phase 1)
// ──────────────────────────────────────────────────────
function DemandPanel({ topSkus, forecast }: { topSkus: any[]; forecast: any[] }) {
    return (
        <div className="space-y-6">
            {/* Top SKUs */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                        <Target className="h-4 w-4" />
                        Top Selling SKUs (Last 30 Days)
                    </CardTitle>
                    <CardDescription>Ranked by total quantity ordered</CardDescription>
                </CardHeader>
                <CardContent>
                    {topSkus.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-8">No order data found for this period.</p>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-8">#</TableHead>
                                    <TableHead>Product / SKU</TableHead>
                                    <TableHead className="text-right">Ordered</TableHead>
                                    <TableHead className="text-right">Orders</TableHead>
                                    <TableHead className="text-right">Stock</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {topSkus.map((sku: any, idx: number) => (
                                    <TableRow key={sku.sku_id}>
                                        <TableCell className="font-medium text-muted-foreground">{idx + 1}</TableCell>
                                        <TableCell>
                                            <div className="font-medium text-sm">{sku.product_name}</div>
                                            <div className="text-xs text-muted-foreground">{sku.sku_code} &middot; {sku.size} / {sku.color}</div>
                                        </TableCell>
                                        <TableCell className="text-right font-bold">{sku.total_ordered}</TableCell>
                                        <TableCell className="text-right text-muted-foreground">{sku.order_count}</TableCell>
                                        <TableCell className="text-right">
                                            <span className={sku.current_stock <= 0 ? "text-red-600 font-medium" : ""}>
                                                {sku.current_stock}
                                            </span>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>

            {/* Demand Forecast */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                        <TrendingUp className="h-4 w-4" />
                        Demand Forecast by SKU
                    </CardTitle>
                    <CardDescription>Projected demand based on recent order velocity</CardDescription>
                </CardHeader>
                <CardContent>
                    {forecast.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-8">No forecast data available.</p>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Product / SKU</TableHead>
                                    <TableHead className="text-right">Stock</TableHead>
                                    <TableHead className="text-right">Outstanding</TableHead>
                                    <TableHead className="text-right">7d Rate</TableHead>
                                    <TableHead className="text-right">30d Rate</TableHead>
                                    <TableHead className="text-right">Days of Stock</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {forecast.slice(0, 15).map((item: any) => (
                                    <TableRow key={item.sku_id}>
                                        <TableCell>
                                            <div className="font-medium text-sm">{item.product_name}</div>
                                            <div className="text-xs text-muted-foreground">{item.sku_code} &middot; {item.size} / {item.color}</div>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <span className={item.current_stock <= 0 ? "text-red-600 font-medium" : ""}>
                                                {item.current_stock}
                                            </span>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            {item.outstanding_demand > 0 ? (
                                                <span className="text-amber-600 font-medium">{item.outstanding_demand}</span>
                                            ) : (
                                                <span className="text-muted-foreground">0</span>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-right font-mono text-xs">{item.daily_rate_7d}/day</TableCell>
                                        <TableCell className="text-right font-mono text-xs">{item.daily_rate_30d}/day</TableCell>
                                        <TableCell className="text-right">
                                            {item.days_of_stock !== null ? (
                                                <Badge variant={item.days_of_stock < 3 ? "destructive" : item.days_of_stock < 7 ? "secondary" : "outline"}>
                                                    {item.days_of_stock}d
                                                </Badge>
                                            ) : (
                                                <span className="text-xs text-muted-foreground">N/A</span>
                                            )}
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


// ──────────────────────────────────────────────────────
// MANUFACTURING PANEL (Phase 2)
// ──────────────────────────────────────────────────────
function ManufacturingPanel({ suggestions }: { suggestions: any }) {
    if (!suggestions) return <EmptyState message="No manufacturing suggestions available." />;

    const items = suggestions.suggestions || [];

    return (
        <div className="space-y-6">
            {/* Summary */}
            <div className="grid gap-4 md:grid-cols-3">
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-2xl font-bold">{items.length}</div>
                        <p className="text-xs text-muted-foreground mt-1">SKUs to Manufacture</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-2xl font-bold">{suggestions.total_suggested_units}</div>
                        <p className="text-xs text-muted-foreground mt-1">Total Suggested Units</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-2">
                            {suggestions.has_plan_today ? (
                                <Badge className="bg-green-100 text-green-800">Active</Badge>
                            ) : (
                                <Badge variant="secondary">No Plan</Badge>
                            )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Today&apos;s Plan Status</p>
                    </CardContent>
                </Card>
            </div>

            {/* Suggestions Table */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                        <Zap className="h-4 w-4" />
                        Manufacturing Suggestions
                    </CardTitle>
                    <CardDescription>Ranked by priority score (demand weight + velocity - inventory)</CardDescription>
                </CardHeader>
                <CardContent>
                    {items.length === 0 ? (
                        <div className="flex flex-col items-center py-12 text-muted-foreground">
                            <Factory className="h-8 w-8 mb-2" />
                            <p className="text-sm">No manufacturing needed right now.</p>
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Priority</TableHead>
                                    <TableHead>Product / SKU</TableHead>
                                    <TableHead className="text-right">Demand</TableHead>
                                    <TableHead className="text-right">Stock</TableHead>
                                    <TableHead className="text-right">7d Velocity</TableHead>
                                    <TableHead className="text-right">Suggested Qty</TableHead>
                                    <TableHead className="text-right">Planned Today</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {items.map((item: any) => (
                                    <TableRow key={item.sku_id}>
                                        <TableCell>
                                            <Badge variant={
                                                item.priority === "high" ? "destructive" :
                                                item.priority === "medium" ? "secondary" : "outline"
                                            } className="capitalize">
                                                {item.priority}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <div className="font-medium text-sm">{item.product_name}</div>
                                            <div className="text-xs text-muted-foreground">{item.sku_code} &middot; {item.size} / {item.color}</div>
                                        </TableCell>
                                        <TableCell className="text-right font-medium text-amber-600">{item.outstanding_demand}</TableCell>
                                        <TableCell className="text-right">{item.current_stock}</TableCell>
                                        <TableCell className="text-right font-mono text-xs">{item.velocity_7d} ({item.daily_rate}/d)</TableCell>
                                        <TableCell className="text-right">
                                            <span className="font-bold text-primary">{item.suggested_quantity}</span>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            {item.already_planned_today > 0 ? (
                                                <span className="text-green-600">{item.already_completed_today}/{item.already_planned_today}</span>
                                            ) : (
                                                <span className="text-muted-foreground">-</span>
                                            )}
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


// ──────────────────────────────────────────────────────
// DELIVERY PANEL (Phase 3)
// ──────────────────────────────────────────────────────
function DeliveryPanel({ deliveryOps }: { deliveryOps: any }) {
    if (!deliveryOps) return <EmptyState message="No delivery operations data available." />;

    const summary = deliveryOps.summary || {};
    const locations = deliveryOps.locations || [];
    const delayed = deliveryOps.delayed_orders || [];

    return (
        <div className="space-y-6">
            {/* Summary */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-2xl font-bold">{summary.total_active_deliveries}</div>
                        <p className="text-xs text-muted-foreground mt-1">Active Deliveries</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-2xl font-bold">{summary.total_locations}</div>
                        <p className="text-xs text-muted-foreground mt-1">Delivery Locations</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-2xl font-bold text-blue-600">{summary.today_count}</div>
                        <p className="text-xs text-muted-foreground mt-1">Due Today</p>
                    </CardContent>
                </Card>
                <Card className={summary.delayed_count > 0 ? "border-red-200 bg-red-50/50" : ""}>
                    <CardContent className="pt-6">
                        <div className={`text-2xl font-bold ${summary.delayed_count > 0 ? "text-red-600" : ""}`}>
                            {summary.delayed_count}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">Delayed</p>
                    </CardContent>
                </Card>
            </div>

            {/* Delayed Orders */}
            {delayed.length > 0 && (
                <Card className="border-red-200">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-base text-red-700">
                            <AlertTriangle className="h-4 w-4" />
                            Delayed Deliveries ({delayed.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Client</TableHead>
                                    <TableHead>Address</TableHead>
                                    <TableHead>Due Date</TableHead>
                                    <TableHead className="text-right">Days Overdue</TableHead>
                                    <TableHead className="text-right">Value</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {delayed.map((order: any) => (
                                    <TableRow key={order.order_id}>
                                        <TableCell className="font-medium">{order.client_name}</TableCell>
                                        <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">{order.address}</TableCell>
                                        <TableCell className="text-sm">{order.delivery_date}</TableCell>
                                        <TableCell className="text-right">
                                            <Badge variant="destructive">{order.days_overdue}d</Badge>
                                        </TableCell>
                                        <TableCell className="text-right font-medium">R{order.total_price_rands?.toLocaleString()}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}

            {/* Location Groups */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                        <MapPin className="h-4 w-4" />
                        Deliveries by Location
                    </CardTitle>
                    <CardDescription>Grouped by client address for route optimization</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {locations.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-8">No active deliveries.</p>
                    ) : (
                        locations.map((loc: any, idx: number) => (
                            <div key={idx} className={`border rounded-lg p-4 ${loc.has_delayed ? "border-red-200 bg-red-50/30" : ""}`}>
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <MapPin className="h-4 w-4 text-muted-foreground" />
                                        <span className="font-medium text-sm">{loc.address}</span>
                                        {loc.has_delayed && (
                                            <Badge variant="destructive" className="text-xs">Delayed</Badge>
                                        )}
                                    </div>
                                    <div className="text-sm text-muted-foreground">
                                        {loc.order_count} order{loc.order_count !== 1 ? "s" : ""} &middot; R{loc.total_value?.toLocaleString()}
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    {loc.orders.map((order: any) => (
                                        <div key={order.order_id} className="flex items-center gap-2 text-xs text-muted-foreground pl-6">
                                            <span className="font-medium text-foreground">{order.client_name}</span>
                                            <span>&middot;</span>
                                            <span>Due: {order.delivery_date}</span>
                                            <span>&middot;</span>
                                            <span>R{order.total_price_rands?.toLocaleString()}</span>
                                            {order.is_delayed && <Badge variant="destructive" className="text-[10px] px-1 py-0">Overdue</Badge>}
                                            {order.delivery_team_name && (
                                                <>
                                                    <span>&middot;</span>
                                                    <span className="text-blue-600">{order.delivery_team_name}</span>
                                                </>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))
                    )}
                </CardContent>
            </Card>
        </div>
    );
}


// ──────────────────────────────────────────────────────
// BUSINESS PANEL (Phase 5)
// ──────────────────────────────────────────────────────
function BusinessPanel({ business }: { business: any }) {
    if (!business) return <EmptyState message="No business analytics available." />;

    const sales = business.sales || {};
    const mfg = business.manufacturing || {};
    const delivery = business.delivery || {};
    const inventory = business.inventory || {};
    const topClients = business.top_clients || [];

    return (
        <div className="space-y-6">
            {/* Revenue KPIs */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-2 mb-1">
                            <DollarSign className="h-4 w-4 text-green-500" />
                            <span className="text-xs text-muted-foreground">Revenue (30d)</span>
                        </div>
                        <div className="text-2xl font-bold">R{(sales.last_30d?.revenue || 0).toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground mt-1">{sales.last_30d?.order_count || 0} orders</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-2 mb-1">
                            <DollarSign className="h-4 w-4 text-blue-500" />
                            <span className="text-xs text-muted-foreground">Revenue (7d)</span>
                        </div>
                        <div className="text-2xl font-bold">R{(sales.last_7d?.revenue || 0).toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground mt-1">{sales.last_7d?.order_count || 0} orders</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-2 mb-1">
                            <ArrowUpRight className="h-4 w-4 text-primary" />
                            <span className="text-xs text-muted-foreground">Avg Order Value</span>
                        </div>
                        <div className="text-2xl font-bold">R{(sales.avg_order_value_30d || 0).toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground mt-1">Last 30 days</div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-2 mb-1">
                            <TrendingDown className="h-4 w-4 text-red-500" />
                            <span className="text-xs text-muted-foreground">Cancelled (30d)</span>
                        </div>
                        <div className="text-2xl font-bold">{sales.last_30d?.cancelled_count || 0}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                            {sales.last_30d?.order_count > 0
                                ? `${((sales.last_30d.cancelled_count / sales.last_30d.order_count) * 100).toFixed(1)}% rate`
                                : "N/A"}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Sales Trend (sparkline) */}
            {sales.trend && sales.trend.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-base flex items-center gap-2">
                            <BarChart3 className="h-4 w-4" /> Daily Sales (14 days)
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-end gap-1 h-24">
                            {(() => {
                                const maxRev = Math.max(...sales.trend.map((d: any) => d.revenue || 0), 1);
                                return sales.trend.map((day: any, idx: number) => {
                                    const height = Math.max(2, (day.revenue / maxRev) * 100);
                                    return (
                                        <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                                            <div
                                                className="w-full bg-primary/80 rounded-t-sm transition-all"
                                                style={{ height: `${height}%` }}
                                                title={`${day.date}: R${day.revenue?.toLocaleString()} (${day.orders} orders)`}
                                            />
                                            <span className="text-[9px] text-muted-foreground">{day.date?.slice(8)}</span>
                                        </div>
                                    );
                                });
                            })()}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Efficiency Metrics */}
            <div className="grid gap-4 md:grid-cols-3">
                {/* Manufacturing Efficiency */}
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center gap-2">
                            <Factory className="h-4 w-4" /> Manufacturing Efficiency
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold mb-2">{mfg.efficiency_30d}%</div>
                        <Progress value={mfg.efficiency_30d} className="h-2" />
                        <div className="text-xs text-muted-foreground mt-2">
                            {mfg.total_completed_30d} / {mfg.total_planned_30d} units in {mfg.plan_count_30d} plans
                        </div>
                    </CardContent>
                </Card>

                {/* Delivery Rate */}
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center gap-2">
                            <Truck className="h-4 w-4" /> Delivery Completion
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold mb-2">{delivery.completion_rate_30d}%</div>
                        <Progress value={delivery.completion_rate_30d} className="h-2" />
                        <div className="text-xs text-muted-foreground mt-2">
                            {delivery.completed_30d} completed, {delivery.partial_30d} partial of {delivery.total_deliveries_30d}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                            On-time rate: <span className="font-medium">{delivery.on_time_rate_30d}%</span>
                        </div>
                    </CardContent>
                </Card>

                {/* Inventory Turnover */}
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm flex items-center gap-2">
                            <Boxes className="h-4 w-4" /> Inventory Turnover
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-3xl font-bold mb-2">{inventory.turnover_annualized}x</div>
                        <div className="text-xs text-muted-foreground">
                            {inventory.units_delivered_30d} units delivered (30d)
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                            {inventory.total_on_hand} units on hand
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Top Clients */}
            {topClients.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-base flex items-center gap-2">
                            <Users className="h-4 w-4" /> Top Clients (30 days)
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>#</TableHead>
                                    <TableHead>Client</TableHead>
                                    <TableHead className="text-right">Orders</TableHead>
                                    <TableHead className="text-right">Revenue</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {topClients.map((client: any, idx: number) => (
                                    <TableRow key={idx}>
                                        <TableCell className="text-muted-foreground">{idx + 1}</TableCell>
                                        <TableCell className="font-medium">{client.name}</TableCell>
                                        <TableCell className="text-right">{client.order_count}</TableCell>
                                        <TableCell className="text-right font-medium">R{client.revenue?.toLocaleString()}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}


// ──────────────────────────────────────────────────────
// EMPTY STATE
// ──────────────────────────────────────────────────────
function EmptyState({ message }: { message: string }) {
    return (
        <Card>
            <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                <BarChart3 className="h-10 w-10 mb-3" />
                <p className="text-sm">{message}</p>
            </CardContent>
        </Card>
    );
}
