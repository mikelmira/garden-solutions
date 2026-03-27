"use client";

import { useAuth } from "@/lib/auth";
import { apiService } from "@/lib/api";
import { Order } from "@/types";
import { formatDate } from "@/lib/date-utils";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/admin/StatusBadge";
import { Loader2, Plus, LogOut, AlertCircle, ShoppingBag } from "lucide-react";

export default function SalesDashboard() {
    const { user, logout } = useAuth();
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const loadOrders = async () => {
        setLoading(true);
        setError("");
        try {
            const data = await apiService.orders.list();
            setOrders(data);
        } catch (err: any) {
            console.error(err);
            setError("Failed to load your pipeline.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadOrders();
    }, []);

    if (loading && !orders.length) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col h-[50vh] items-center justify-center gap-4">
                <AlertCircle className="h-10 w-10 text-red-500" />
                <p className="text-muted-foreground">{error}</p>
                <Button onClick={loadOrders} variant="outline">Retry</Button>
            </div>
        );
    }

    const drafts = orders.filter(o => o.status === 'Draft').length;
    const pending = orders.filter(o => o.status === 'Pending Approval').length;

    return (
        <div className="container mx-auto p-6 space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Sales Dashboard</h1>
                    <p className="text-muted-foreground">Welcome back, {user?.full_name}</p>
                </div>
                <div className="flex items-center gap-4">
                    <Button variant="outline" onClick={logout} size="sm" className="gap-2 text-red-600 hover:text-red-700 hover:bg-red-50">
                        <LogOut size={14} /> Logout
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <Card className="border-l-4 border-blue-500 bg-blue-50/20">
                    <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                        <div className="text-3xl font-bold">{drafts}</div>
                        <div className="text-xs text-blue-700 font-medium uppercase tracking-wide">Drafts</div>
                    </CardContent>
                </Card>
                <Card className="border-l-4 border-orange-500 bg-orange-50/20">
                    <CardContent className="p-4 flex flex-col items-center justify-center text-center">
                        <div className="text-3xl font-bold">{pending}</div>
                        <div className="text-xs text-orange-700 font-medium uppercase tracking-wide">Pending Approval</div>
                    </CardContent>
                </Card>
            </div>

            <div className="flex justify-end">
                <Link href="/new-order">
                    <Button className="gap-2">
                        <Plus size={16} /> New Order
                    </Button>
                </Link>
            </div>

            <div>
                <h3 className="text-xl font-bold mb-4">Recent Orders</h3>
                {orders.length === 0 ? (
                    <div className="p-12 text-center border rounded-lg bg-muted/20">
                        <ShoppingBag className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                        <h3 className="text-lg font-medium">No orders yet</h3>
                        <p className="text-muted-foreground mb-4">Start by creating a new order for your clients.</p>
                        <Link href="/new-order">
                            <Button variant="outline">Create Order</Button>
                        </Link>
                    </div>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {orders.map(order => (
                            <Card key={order.id} className="hover:border-primary/50 transition-colors">
                                <CardHeader className="pb-3">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <CardTitle className="text-base font-bold">#{order.id.slice(0, 8)}</CardTitle>
                                            <CardDescription>{order.client?.name || 'Unknown Client'}</CardDescription>
                                        </div>
                                        <StatusBadge status={order.status} />
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-muted-foreground">{formatDate(order.created_at)}</span>
                                        <span className="font-bold">R {order.total_price_rands.toFixed(2)}</span>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
