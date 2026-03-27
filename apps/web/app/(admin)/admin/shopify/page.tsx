"use client";

import { useEffect, useState, useCallback } from "react";
import { apiService } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { useToast } from "@/hooks/use-toast";
import {
    Loader2,
    RefreshCw,
    ShoppingCart,
    Link2,
    Link2Off,
    Package,
    AlertTriangle,
    CheckCircle2,
    XCircle,
    Clock,
    Webhook,
    ArrowRight,
    Search,
    EyeOff,
    Boxes,
} from "lucide-react";

type Tab = "overview" | "unmapped" | "mapped" | "orders" | "webhooks";

export default function ShopifyAdminPage() {
    const { toast } = useToast();
    const [activeTab, setActiveTab] = useState<Tab>("overview");
    const [loading, setLoading] = useState(true);

    const [status, setStatus] = useState<any>(null);
    const [variants, setVariants] = useState<any[]>([]);
    const [orders, setOrders] = useState<any[]>([]);
    const [webhooks, setWebhooks] = useState<any[]>([]);
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    // SKU search for mapping
    const [skuSearch, setSkuSearch] = useState("");
    const [skuResults, setSkuResults] = useState<any[]>([]);
    const [mappingVariant, setMappingVariant] = useState<string | null>(null);

    const loadStatus = useCallback(async () => {
        try {
            const s = await apiService.admin.shopify.getStatus();
            setStatus(s);
        } catch {
            // Store might not exist yet
            setStatus(null);
        }
    }, []);

    const loadAll = useCallback(async () => {
        try {
            await loadStatus();
        } catch { /* handled */ } finally {
            setLoading(false);
        }
    }, [loadStatus]);

    useEffect(() => { loadAll(); }, [loadAll]);

    // Load tab-specific data on tab change
    useEffect(() => {
        if (activeTab === "unmapped") {
            apiService.admin.shopify.getVariants({ status: "unmapped" }).then(setVariants).catch(() => setVariants([]));
        } else if (activeTab === "mapped") {
            apiService.admin.shopify.getVariants({ status: "mapped" }).then(setVariants).catch(() => setVariants([]));
        } else if (activeTab === "orders") {
            apiService.admin.shopify.getOrders().then(setOrders).catch(() => setOrders([]));
        } else if (activeTab === "webhooks") {
            apiService.admin.shopify.getRecentWebhooks().then(setWebhooks).catch(() => setWebhooks([]));
        }
    }, [activeTab]);

    const handleAction = async (action: string, fn: () => Promise<any>) => {
        setActionLoading(action);
        try {
            const result = await fn();
            toast({ title: "Success", description: JSON.stringify(result).slice(0, 200) });
            await loadStatus();
            // Reload current tab data
            if (activeTab === "unmapped" || activeTab === "mapped") {
                const data = await apiService.admin.shopify.getVariants({ status: activeTab });
                setVariants(data);
            } else if (activeTab === "orders") {
                setOrders(await apiService.admin.shopify.getOrders());
            }
        } catch (e: any) {
            toast({ variant: "destructive", title: "Action Failed", description: e?.message });
        } finally {
            setActionLoading(null);
        }
    };

    const handleMapVariant = async (variantId: string, skuId: string) => {
        await handleAction("map", () => apiService.admin.shopify.mapVariant(variantId, skuId));
        setMappingVariant(null);
        setSkuSearch("");
        setSkuResults([]);
    };

    const handleIgnoreVariant = async (variantId: string) => {
        await handleAction("ignore", () => apiService.admin.shopify.ignoreVariant(variantId));
    };

    const searchSkus = async (q: string) => {
        setSkuSearch(q);
        if (q.length < 2) { setSkuResults([]); return; }
        try {
            const results = await apiService.admin.shopify.searchSkus(q);
            setSkuResults(results);
        } catch { setSkuResults([]); }
    };

    const formatTs = (ts: string | null) => {
        if (!ts) return "Never";
        try {
            return new Date(ts).toLocaleString("en-ZA", {
                month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
            });
        } catch { return ts; }
    };

    const tabs: { key: Tab; label: string; icon: any; count?: number }[] = [
        { key: "overview", label: "Overview", icon: ShoppingCart },
        { key: "unmapped", label: "Unmapped", icon: Link2Off, count: status?.variants?.unmapped || 0 },
        { key: "mapped", label: "Mapped", icon: Link2, count: status?.variants?.mapped || 0 },
        { key: "orders", label: "Orders", icon: Package, count: status?.orders?.total || 0 },
        { key: "webhooks", label: "Webhooks", icon: Webhook, count: status?.webhooks_24h || 0 },
    ];

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-24 text-muted-foreground gap-3">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span className="text-sm">Loading Shopify integration...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-heading font-bold tracking-tight">Shopify Integration</h1>
                    <p className="text-sm text-muted-foreground mt-1">
                        {status?.store ? `Connected: ${status.store.name}` : "Pot Shack Shopify Store"}
                    </p>
                </div>
                <Button size="sm" variant="outline" onClick={() => { setLoading(true); loadAll(); }}>
                    <RefreshCw className="h-4 w-4 mr-2" /> Refresh
                </Button>
            </div>

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
                        {tab.count !== undefined && tab.count > 0 && (
                            <Badge variant={tab.key === "unmapped" ? "destructive" : "secondary"} className="ml-1 text-xs px-1.5 py-0">
                                {tab.count}
                            </Badge>
                        )}
                    </button>
                ))}
            </div>

            {/* ═══ OVERVIEW TAB ═══ */}
            {activeTab === "overview" && (
                <div className="space-y-6">
                    {!status ? (
                        <Card>
                            <CardContent className="py-12 text-center text-muted-foreground">
                                <ShoppingCart className="h-10 w-10 mx-auto mb-3" />
                                <p className="font-medium text-foreground">No Shopify store configured</p>
                                <p className="text-sm mt-1">Create a store with type &quot;shopify&quot; in Stores management to get started.</p>
                            </CardContent>
                        </Card>
                    ) : (
                        <>
                            {/* Sync Status Cards */}
                            <div className="grid gap-4 md:grid-cols-4">
                                <Card>
                                    <CardContent className="pt-6">
                                        <div className="text-2xl font-bold">{status.products?.synced || 0}</div>
                                        <p className="text-xs text-muted-foreground mt-1">Products Synced</p>
                                        <p className="text-[10px] text-muted-foreground">{formatTs(status.last_product_sync)}</p>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardContent className="pt-6">
                                        <div className="flex items-baseline gap-2">
                                            <span className="text-2xl font-bold">{status.variants?.mapped || 0}</span>
                                            <span className="text-sm text-muted-foreground">/ {status.variants?.total || 0}</span>
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1">Variants Mapped</p>
                                    </CardContent>
                                </Card>
                                <Card className={status.variants?.unmapped > 0 ? "border-amber-200 bg-amber-50/50" : ""}>
                                    <CardContent className="pt-6">
                                        <div className={`text-2xl font-bold ${status.variants?.unmapped > 0 ? "text-amber-600" : ""}`}>
                                            {status.variants?.unmapped || 0}
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1">Unmapped Variants</p>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardContent className="pt-6">
                                        <div className="text-2xl font-bold">{status.orders?.total || 0}</div>
                                        <p className="text-xs text-muted-foreground mt-1">Orders Synced</p>
                                        <p className="text-[10px] text-muted-foreground">{formatTs(status.last_order_sync)}</p>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* Order Sync Breakdown */}
                            <div className="grid gap-4 md:grid-cols-4">
                                <Card>
                                    <CardContent className="pt-6 flex items-center gap-3">
                                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                                        <div>
                                            <div className="text-lg font-bold">{status.orders?.synced || 0}</div>
                                            <p className="text-xs text-muted-foreground">Synced OK</p>
                                        </div>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardContent className="pt-6 flex items-center gap-3">
                                        <AlertTriangle className="h-5 w-5 text-amber-500" />
                                        <div>
                                            <div className="text-lg font-bold">{status.orders?.partial || 0}</div>
                                            <p className="text-xs text-muted-foreground">Partial (unmapped items)</p>
                                        </div>
                                    </CardContent>
                                </Card>
                                <Card className={status.orders?.failed > 0 ? "border-red-200 bg-red-50/50" : ""}>
                                    <CardContent className="pt-6 flex items-center gap-3">
                                        <XCircle className="h-5 w-5 text-red-500" />
                                        <div>
                                            <div className="text-lg font-bold">{status.orders?.failed || 0}</div>
                                            <p className="text-xs text-muted-foreground">Failed</p>
                                        </div>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardContent className="pt-6 flex items-center gap-3">
                                        <Webhook className="h-5 w-5 text-blue-500" />
                                        <div>
                                            <div className="text-lg font-bold">{status.webhooks_24h || 0}</div>
                                            <p className="text-xs text-muted-foreground">Webhooks (24h)</p>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>

                            {/* Actions */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="text-base">Sync Actions</CardTitle>
                                    <CardDescription>Trigger manual syncs and reconciliation</CardDescription>
                                </CardHeader>
                                <CardContent className="flex flex-wrap gap-3">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        disabled={!!actionLoading}
                                        onClick={() => handleAction("reconcile-mappings", () => apiService.admin.shopify.reconcileMappings())}
                                    >
                                        {actionLoading === "reconcile-mappings" && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                        <Link2 className="h-4 w-4 mr-2" />
                                        Reconcile Mappings
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        disabled={!!actionLoading}
                                        onClick={() => handleAction("reconcile-orders", () => apiService.admin.shopify.reconcileOrders())}
                                    >
                                        {actionLoading === "reconcile-orders" && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                        <Package className="h-4 w-4 mr-2" />
                                        Reprocess Failed Orders
                                    </Button>
                                </CardContent>
                            </Card>

                            {/* Webhook Endpoint Info */}
                            <Card>
                                <CardHeader>
                                    <CardTitle className="text-base">Webhook Configuration</CardTitle>
                                    <CardDescription>Configure these URLs in your Shopify admin</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-2 text-sm font-mono bg-muted p-4 rounded-lg">
                                        <p className="text-muted-foreground text-xs mb-2">Base URL: <span className="text-foreground">https://your-domain.com</span></p>
                                        <p>POST /api/v1/webhooks/shopify/orders/create</p>
                                        <p>POST /api/v1/webhooks/shopify/orders/updated</p>
                                        <p>POST /api/v1/webhooks/shopify/orders/cancelled</p>
                                        <p>POST /api/v1/webhooks/shopify/products/create</p>
                                        <p>POST /api/v1/webhooks/shopify/products/update</p>
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-2">
                                        Set <code className="bg-muted px-1 rounded">SHOPIFY_WEBHOOK_SECRET</code> in env to enable HMAC signature verification.
                                    </p>
                                </CardContent>
                            </Card>
                        </>
                    )}
                </div>
            )}

            {/* ═══ UNMAPPED VARIANTS TAB ═══ */}
            {activeTab === "unmapped" && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-base">
                            <Link2Off className="h-4 w-4" />
                            Unmapped Variants ({variants.length})
                        </CardTitle>
                        <CardDescription>Shopify variants without an internal SKU mapping. Map or ignore each one.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {variants.length === 0 ? (
                            <div className="text-center py-12 text-muted-foreground">
                                <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-green-500" />
                                <p className="font-medium text-foreground">All variants mapped!</p>
                                <p className="text-sm">No unmapped Shopify variants found.</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {variants.map((v: any) => (
                                    <div key={v.id} className="border rounded-lg p-4 space-y-3">
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <div className="font-medium text-sm">{v.product_title}</div>
                                                <div className="text-xs text-muted-foreground">
                                                    Variant: {v.title} &middot; SKU: {v.shopify_sku || "N/A"} &middot; Price: {v.price}
                                                </div>
                                                <div className="text-[10px] text-muted-foreground mt-0.5">
                                                    Shopify IDs: product={v.shopify_product_id}, variant={v.shopify_variant_id}
                                                </div>
                                                {v.option1 && <div className="text-xs text-muted-foreground">{v.option1}{v.option2 ? ` / ${v.option2}` : ""}{v.option3 ? ` / ${v.option3}` : ""}</div>}
                                            </div>
                                            <Badge variant="secondary">Unmapped</Badge>
                                        </div>

                                        {/* Suggested matches */}
                                        {v.suggested_sku && v.suggested_sku.length > 0 && (
                                            <div className="bg-blue-50 border border-blue-200 rounded p-2">
                                                <p className="text-xs text-blue-700 font-medium mb-1">Suggested matches:</p>
                                                <div className="space-y-1">
                                                    {v.suggested_sku.map((s: any) => (
                                                        <div key={s.id} className="flex items-center justify-between text-xs">
                                                            <span>{s.product_name} - {s.code}</span>
                                                            <Button
                                                                size="sm"
                                                                variant="ghost"
                                                                className="h-6 text-xs text-blue-700"
                                                                onClick={() => handleMapVariant(v.id, s.id)}
                                                                disabled={!!actionLoading}
                                                            >
                                                                <ArrowRight className="h-3 w-3 mr-1" /> Map
                                                            </Button>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Manual mapping */}
                                        <div className="flex items-center gap-2">
                                            {mappingVariant === v.id ? (
                                                <div className="flex-1 space-y-2">
                                                    <div className="flex gap-2">
                                                        <Input
                                                            placeholder="Search SKU code..."
                                                            value={skuSearch}
                                                            onChange={(e) => searchSkus(e.target.value)}
                                                            className="h-8 text-sm"
                                                        />
                                                        <Button size="sm" variant="ghost" onClick={() => { setMappingVariant(null); setSkuSearch(""); setSkuResults([]); }}>
                                                            Cancel
                                                        </Button>
                                                    </div>
                                                    {skuResults.length > 0 && (
                                                        <div className="border rounded max-h-32 overflow-y-auto">
                                                            {skuResults.map((s: any) => (
                                                                <button
                                                                    key={s.id}
                                                                    className="w-full text-left px-3 py-1.5 text-xs hover:bg-muted flex justify-between"
                                                                    onClick={() => handleMapVariant(v.id, s.id)}
                                                                >
                                                                    <span>{s.product_name} - {s.code}</span>
                                                                    <span className="text-muted-foreground">{s.size}/{s.color}</span>
                                                                </button>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                <>
                                                    <Button size="sm" variant="outline" onClick={() => setMappingVariant(v.id)}>
                                                        <Search className="h-3 w-3 mr-1" /> Map to SKU
                                                    </Button>
                                                    <Button size="sm" variant="ghost" className="text-muted-foreground" onClick={() => handleIgnoreVariant(v.id)}>
                                                        <EyeOff className="h-3 w-3 mr-1" /> Ignore
                                                    </Button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* ═══ MAPPED VARIANTS TAB ═══ */}
            {activeTab === "mapped" && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-base">
                            <Link2 className="h-4 w-4" />
                            Mapped Variants ({variants.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {variants.length === 0 ? (
                            <p className="text-sm text-muted-foreground text-center py-8">No mapped variants yet.</p>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Shopify Product / Variant</TableHead>
                                        <TableHead>Shopify SKU</TableHead>
                                        <TableHead><ArrowRight className="h-4 w-4" /></TableHead>
                                        <TableHead>Internal SKU</TableHead>
                                        <TableHead>Internal Product</TableHead>
                                        <TableHead>Last Synced</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {variants.map((v: any) => (
                                        <TableRow key={v.id}>
                                            <TableCell>
                                                <div className="text-sm font-medium">{v.product_title}</div>
                                                <div className="text-xs text-muted-foreground">{v.title}</div>
                                            </TableCell>
                                            <TableCell className="font-mono text-xs">{v.shopify_sku || "-"}</TableCell>
                                            <TableCell><ArrowRight className="h-3 w-3 text-muted-foreground" /></TableCell>
                                            <TableCell className="font-mono text-xs font-medium">{v.sku_code || "-"}</TableCell>
                                            <TableCell className="text-sm">{v.sku_product_name || "-"}</TableCell>
                                            <TableCell className="text-xs text-muted-foreground">{formatTs(v.last_synced_at)}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* ═══ ORDERS TAB ═══ */}
            {activeTab === "orders" && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-base">
                            <Package className="h-4 w-4" />
                            Shopify Orders ({orders.length})
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {orders.length === 0 ? (
                            <p className="text-sm text-muted-foreground text-center py-8">No Shopify orders synced yet.</p>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Order #</TableHead>
                                        <TableHead>Customer</TableHead>
                                        <TableHead>Total</TableHead>
                                        <TableHead>Shopify Status</TableHead>
                                        <TableHead>Sync Status</TableHead>
                                        <TableHead>Internal Order</TableHead>
                                        <TableHead>Synced</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {orders.map((o: any) => (
                                        <TableRow key={o.id}>
                                            <TableCell className="font-medium">#{o.shopify_order_number}</TableCell>
                                            <TableCell className="text-sm">{o.customer_name}</TableCell>
                                            <TableCell className="text-sm">{o.currency} {o.total_price}</TableCell>
                                            <TableCell>
                                                <Badge variant="outline" className="text-xs capitalize">{o.shopify_status}</Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant={
                                                        o.sync_status === "synced" ? "default" :
                                                        o.sync_status === "failed" ? "destructive" :
                                                        o.sync_status === "partial" ? "secondary" : "outline"
                                                    }
                                                    className="text-xs capitalize"
                                                >
                                                    {o.sync_status}
                                                </Badge>
                                                {o.error_message && (
                                                    <p className="text-[10px] text-red-500 mt-0.5 max-w-[200px] truncate">{o.error_message}</p>
                                                )}
                                            </TableCell>
                                            <TableCell className="font-mono text-xs">
                                                {o.internal_order_id ? o.internal_order_id.slice(0, 8) + "..." : "-"}
                                            </TableCell>
                                            <TableCell className="text-xs text-muted-foreground">{formatTs(o.last_synced_at)}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* ═══ WEBHOOKS TAB ═══ */}
            {activeTab === "webhooks" && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-base">
                            <Webhook className="h-4 w-4" />
                            Recent Webhook Events
                        </CardTitle>
                        <CardDescription>Last 30 incoming Shopify webhook events</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {webhooks.length === 0 ? (
                            <p className="text-sm text-muted-foreground text-center py-8">No webhook events recorded yet.</p>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Topic</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Processing Time</TableHead>
                                        <TableHead>Error</TableHead>
                                        <TableHead>Received</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {webhooks.map((e: any) => (
                                        <TableRow key={e.id}>
                                            <TableCell className="font-mono text-xs">{e.topic}</TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant={
                                                        e.status === "processed" ? "default" :
                                                        e.status === "failed" ? "destructive" :
                                                        e.status === "duplicate" ? "secondary" : "outline"
                                                    }
                                                    className="text-xs capitalize"
                                                >
                                                    {e.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell className="text-xs">{e.processing_time_ms ? `${e.processing_time_ms}ms` : "-"}</TableCell>
                                            <TableCell className="text-xs text-red-500 max-w-[200px] truncate">{e.error_message || "-"}</TableCell>
                                            <TableCell className="text-xs text-muted-foreground">{formatTs(e.received_at)}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
