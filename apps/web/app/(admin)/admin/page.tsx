"use client";

import { useEffect, useMemo, useState } from "react";
import { Order, Product } from "@/types";
import { Loader2, TrendingUp, Truck, CheckCircle2, AlertCircle, Clock, Package, ClipboardList } from "lucide-react";
import { apiService } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { PageHeader } from "@/components/ui/page-header";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

export default function AdminDashboard() {
    const { toast } = useToast();
    const [stats, setStats] = useState({
        pending: 0,
        approved: 0,
        deliveryPending: 0,
        completed: 0,
        revenue: 0
    });
    const [orders, setOrders] = useState<Order[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [rangeStart, setRangeStart] = useState("");
    const [rangeEnd, setRangeEnd] = useState("");

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [ordersResponse, productsResponse] = await Promise.all([
                apiService.orders.list({ size: 100 }),
                apiService.products.list(),
            ]);

            const detailedOrders = await Promise.all(
                ordersResponse.map(async (order) => {
                    try {
                        const detail = await apiService.orders.get(order.id);
                        return {
                            ...order,
                            ...detail,
                            items: detail.items || order.items,
                        };
                    } catch {
                        return order;
                    }
                })
            );

            const newStats = {
                pending: detailedOrders.filter(o => o.status === "Pending Approval").length,
                approved: detailedOrders.filter(o => o.status === "Approved").length,
                deliveryPending: detailedOrders.filter(o => o.status === "Ready for Delivery").length,
                completed: detailedOrders.filter(o => o.status === "Completed").length,
                revenue: detailedOrders.reduce((acc, o) => acc + o.total_price_rands, 0)
            };

            setStats(newStats);
            setOrders(detailedOrders);
            setProducts(productsResponse);
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load dashboard data", description: error.message });
        } finally {
            setLoading(false);
        }
    };

    const totalStockUnits = useMemo(() => {
        return products.reduce((sum, product) => {
            return sum + product.skus.reduce((skuSum, sku) => skuSum + (sku.stock_quantity || 0), 0);
        }, 0);
    }, [products]);

    const totalAssignedUnits = useMemo(() => {
        return orders
            .filter(order => order.delivery_team_id)
            .reduce((sum, order) => {
                const orderQty = (order.items || []).reduce((itemSum, item) => itemSum + item.quantity_ordered, 0);
                return sum + orderQty;
            }, 0);
    }, [orders]);

    const totalRemainingUnits = Math.max(totalStockUnits - totalAssignedUnits, 0);

    const totalDeliveriesAssigned = useMemo(() => {
        return orders.filter(order => order.delivery_team_id).length;
    }, [orders]);

    const outstandingOrders = useMemo(() => {
        return orders.filter(order => !["Completed", "Cancelled"].includes(order.status)).length;
    }, [orders]);

    const totalProductsOrdered = useMemo(() => {
        const withinRange = orders.filter(order => {
            if (!rangeStart && !rangeEnd) return true;
            const orderDate = new Date(order.created_at).toISOString().split("T")[0];
            if (rangeStart && orderDate < rangeStart) return false;
            if (rangeEnd && orderDate > rangeEnd) return false;
            return true;
        });
        return withinRange.reduce((sum, order) => {
            const orderQty = (order.items || []).reduce((itemSum, item) => itemSum + item.quantity_ordered, 0);
            return sum + orderQty;
        }, 0);
    }, [orders, rangeStart, rangeEnd]);

    const averageDeliveryDays = useMemo(() => {
        const deliveredOrders = orders.filter(order => order.delivered_at);
        if (deliveredOrders.length === 0) return null;
        const totalDays = deliveredOrders.reduce((sum, order) => {
            if (!order.delivered_at) return sum;
            const created = new Date(order.created_at).getTime();
            const delivered = new Date(order.delivered_at).getTime();
            const days = Math.max((delivered - created) / (1000 * 60 * 60 * 24), 0);
            return sum + days;
        }, 0);
        return totalDays / deliveredOrders.length;
    }, [orders]);

    const productStats = useMemo(() => {
        const statsMap = new Map<string, { name: string; onHand: number; ordered: number; delivered: number }>();
        const skuToProduct = new Map<string, string>();

        products.forEach(product => {
            const onHand = product.skus.reduce((sum, sku) => sum + (sku.stock_quantity || 0), 0);
            statsMap.set(product.id, { name: product.name, onHand, ordered: 0, delivered: 0 });
            product.skus.forEach(sku => {
                skuToProduct.set(sku.id, product.id);
            });
        });

        orders.forEach(order => {
            (order.items || []).forEach(item => {
                const productId = skuToProduct.get(item.sku_id);
                if (!productId) return;
                const existing = statsMap.get(productId);
                if (!existing) return;
                existing.ordered += item.quantity_ordered;
                existing.delivered += item.quantity_delivered;
            });
        });

        return Array.from(statsMap.values()).sort((a, b) => a.name.localeCompare(b.name));
    }, [orders, products]);

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <PageHeader
                title="Dashboard"
                description="Welcome back. Here's what's happening today."
            />

            {/* Financial */}
            <div className="space-y-4">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Financial</h2>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <div className="stat-card">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="stat-card-label">Total Revenue</p>
                                <p className="stat-card-value">R {stats.revenue.toLocaleString()}</p>
                            </div>
                            <div className="stat-card-icon bg-green-100">
                                <TrendingUp className="h-5 w-5 text-green-600" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Orders */}
            <div className="space-y-4">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Orders</h2>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <div className="stat-card">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="stat-card-label">Pending Approvals</p>
                                <p className="stat-card-value">{stats.pending}</p>
                            </div>
                            <div className="stat-card-icon bg-amber-100">
                                <AlertCircle className="h-5 w-5 text-amber-600" />
                            </div>
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="stat-card-label">Ready for Delivery</p>
                                <p className="stat-card-value">{stats.deliveryPending}</p>
                            </div>
                            <div className="stat-card-icon bg-blue-100">
                                <Truck className="h-5 w-5 text-blue-600" />
                            </div>
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="stat-card-label">Completed</p>
                                <p className="stat-card-value">{stats.completed}</p>
                            </div>
                            <div className="stat-card-icon bg-green-100">
                                <CheckCircle2 className="h-5 w-5 text-green-600" />
                            </div>
                        </div>
                    </div>

                    <div className="stat-card">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="stat-card-label">Outstanding Orders</p>
                                <p className="stat-card-value">{outstandingOrders}</p>
                            </div>
                            <div className="stat-card-icon bg-amber-100">
                                <AlertCircle className="h-5 w-5 text-amber-600" />
                            </div>
                        </div>
                    </div>

                    <div className="stat-card md:col-span-2">
                        <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
                            <div>
                                <p className="stat-card-label">Total Products Ordered</p>
                                <p className="stat-card-value">{totalProductsOrdered.toLocaleString()}</p>
                                <p className="text-xs text-muted-foreground mt-2">Filter by date range</p>
                            </div>
                            <div className="flex flex-col gap-2 w-full sm:w-auto sm:min-w-[160px]">
                                <Input type="date" value={rangeStart} onChange={e => setRangeStart(e.target.value)} />
                                <Input type="date" value={rangeEnd} onChange={e => setRangeEnd(e.target.value)} />
                            </div>
                        </div>
                    </div>

                    <div className="stat-card md:col-span-2 lg:col-span-4">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="stat-card-label">Avg Time: Order to Delivered</p>
                                <p className="stat-card-value">
                                    {averageDeliveryDays === null ? "—" : `${averageDeliveryDays.toFixed(1)} days`}
                                </p>
                                <p className="text-xs text-muted-foreground mt-2">Based on delivered orders only</p>
                            </div>
                            <div className="stat-card-icon bg-slate-100">
                                <Clock className="h-5 w-5 text-slate-600" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Products */}
            <div className="space-y-4">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Products</h2>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <div className="stat-card">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="stat-card-label">Products On Hand</p>
                                <p className="stat-card-value">{totalStockUnits.toLocaleString()}</p>
                            </div>
                            <div className="stat-card-icon bg-emerald-100">
                                <Package className="h-5 w-5 text-emerald-600" />
                            </div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="stat-card-label">Assigned to Deliveries</p>
                                <p className="stat-card-value">{totalAssignedUnits.toLocaleString()}</p>
                            </div>
                            <div className="stat-card-icon bg-blue-100">
                                <Truck className="h-5 w-5 text-blue-600" />
                            </div>
                        </div>
                    </div>
                    <div className="stat-card">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="stat-card-label">Products Remaining</p>
                                <p className="stat-card-value">{totalRemainingUnits.toLocaleString()}</p>
                            </div>
                            <div className="stat-card-icon bg-slate-100">
                                <ClipboardList className="h-5 w-5 text-slate-600" />
                            </div>
                        </div>
                    </div>
                </div>

                <Card className="border shadow-sm">
                    <div className="p-4 border-b">
                        <h2 className="text-lg font-heading font-semibold">Product Inventory Summary</h2>
                        <p className="text-sm text-muted-foreground">On hand, ordered, and delivered totals by product.</p>
                    </div>
                    <div className="overflow-x-auto">
                    <Table>
                        <TableHeader className="bg-muted/30">
                            <TableRow>
                                <TableHead>Product</TableHead>
                                <TableHead className="text-right">On Hand</TableHead>
                                <TableHead className="text-right">Ordered</TableHead>
                                <TableHead className="text-right">Delivered</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {productStats.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                                        No product data available yet.
                                    </TableCell>
                                </TableRow>
                            ) : (
                                productStats.map(product => (
                                    <TableRow key={product.name}>
                                        <TableCell className="font-medium">{product.name}</TableCell>
                                        <TableCell className="text-right">{product.onHand.toLocaleString()}</TableCell>
                                        <TableCell className="text-right">{product.ordered.toLocaleString()}</TableCell>
                                        <TableCell className="text-right">{product.delivered.toLocaleString()}</TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                    </div>
                </Card>
            </div>
        </div>
    );
}
