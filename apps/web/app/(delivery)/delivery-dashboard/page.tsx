"use client";

import { useAuth } from "@/lib/auth";
import { LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { Order } from "@/types";
import { apiService } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRouter } from "next/navigation";
import { MapPin, Calendar, Clock, Truck, Loader2, AlertCircle } from "lucide-react";
import { format } from "date-fns";
import { Separator } from "@/components/ui/separator";

// Helper to group orders by date
type GroupedOrders = Record<string, Order[]>;

function groupOrdersByDate(orders: Order[]): GroupedOrders {
    const groups: GroupedOrders = {};
    orders.forEach(order => {
        const date = order.delivery_date; // ISO YYYY-MM-DD
        if (!groups[date]) groups[date] = [];
        groups[date].push(order);
    });
    // Sort keys?
    return groups;
}

export default function DeliveryDashboardPage() {
    const { user, logout } = useAuth();
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [filterToday, setFilterToday] = useState(false);
    const router = useRouter();

    useEffect(() => {
        loadOrders();
    }, []);

    const loadOrders = async () => {
        try {
            setLoading(true);
            const data = await apiService.delivery.queue();
            setOrders(data);
        } catch (err: any) {
            console.error("Failed to load delivery queue", err);
            setError("Failed to load delivery schedule. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const todayDate = new Date().toISOString().split("T")[0];

    const displayedOrders = filterToday
        ? orders.filter(o => o.delivery_date === todayDate)
        : orders;

    const grouped = groupOrdersByDate(displayedOrders);
    const dates = Object.keys(grouped).sort();

    if (loading && !orders.length) {
        return (
            <div className="flex flex-col h-[50vh] items-center justify-center gap-4 text-muted-foreground">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p>Loading delivery schedule...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col h-[50vh] items-center justify-center gap-4">
                <div className="rounded-full bg-red-100 p-4">
                    <AlertCircle className="h-8 w-8 text-red-600" />
                </div>
                <h3 className="text-xl font-semibold">Unable to load deliveries</h3>
                <p className="text-muted-foreground">{error}</p>
                <Button onClick={loadOrders} variant="outline" className="gap-2">
                    <Loader2 className={loading ? "animate-spin" : "hidden"} size={16} />
                    Try Again
                </Button>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-6 space-y-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Delivery Dashboard</h1>
                    <p className="text-muted-foreground">Manage logistics and daily runs.</p>
                </div>
                <div className="flex items-center gap-2">
                    <Button variant="outline" onClick={logout} size="sm" className="gap-2 text-red-600 hover:text-red-700 hover:bg-red-50">
                        <LogOut size={14} /> Logout
                    </Button>
                    <Separator orientation="vertical" className="h-6 mx-2" />
                    <Button
                        variant={filterToday ? "default" : "outline"}
                        onClick={() => setFilterToday(!filterToday)}
                    >
                        <Calendar className="mr-2 h-4 w-4" />
                        Today Only
                    </Button>
                    <Button variant="outline" onClick={loadOrders} size="icon" disabled={loading}>
                        <Clock className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                    </Button>
                </div>
            </div>

            {dates.length === 0 && (
                <div className="p-12 text-center border rounded-lg bg-muted/20">
                    <Truck className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
                    <h3 className="text-lg font-medium">No deliveries found</h3>
                    <p className="text-muted-foreground">There are no orders ready for delivery {filterToday ? "today" : ""}.</p>
                </div>
            )}

            {dates.map(date => (
                <div key={date} className="space-y-4">
                    <div className="flex items-center gap-2">
                        <div className="font-semibold text-lg">{format(new Date(date), "EEEE, MMMM do")}</div>
                        <Separator className="flex-1" />
                        <Badge variant="secondary">{grouped[date].length} Orders</Badge>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {grouped[date].map(order => (
                            <DeliveryJobCard key={order.id} order={order} router={router} />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

function DeliveryJobCard({ order, router }: { order: Order, router: any }) {
    const itemCount = order.items?.reduce((acc, i) => acc + i.quantity_ordered, 0) || 0;

    return (
        <Card className="hover:border-primary/50 transition-colors cursor-pointer" onClick={() => router.push(`/delivery-dashboard/${order.id}`)}>
            <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle className="text-base">{order.client_name || order.client?.name}</CardTitle>
                        <CardDescription>{order.id.slice(0, 8)}</CardDescription>
                    </div>
                    <Badge>{order.status}</Badge>
                </div>
            </CardHeader>
            <CardContent className="pb-3">
                <div className="space-y-2 text-sm">
                    <div className="flex items-start gap-2 text-muted-foreground">
                        <MapPin className="h-4 w-4 mt-0.5 shrink-0" />
                        <span>{order.client?.address || "No address provided"}</span>
                    </div>
                </div>
            </CardContent>
            <CardFooter className="pt-0 text-xs text-muted-foreground flex justify-between items-center">
                <span>{itemCount} Items</span>
                <span className="text-primary font-medium">View Manifest →</span>
            </CardFooter>
        </Card>
    );
}
