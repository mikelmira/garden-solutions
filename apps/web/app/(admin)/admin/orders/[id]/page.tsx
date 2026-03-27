"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiService } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Order } from "@/types";
import { formatDateTime } from "@/lib/date-utils";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { StatusBadge } from "@/components/admin/StatusBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function OrderDetailPage({ params }: { params: { id: string } }) {
    const [order, setOrder] = useState<Order | null>(null);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    const router = useRouter();
    const { user } = useAuth(); // Get current user

    useEffect(() => {
        apiService.orders.get(params.id)
            .then(setOrder)
            .catch((err) => {
                console.error(err);
                alert("Failed to load order");
            })
            .finally(() => setLoading(false));
    }, [params.id]);

    const handleStatusChange = async (status: "Approved" | "Cancelled") => {
        if (!confirm(`Are you sure you want to ${status}?`)) return;
        setProcessing(true);
        try {
            await apiService.orders.updateStatus(params.id, status);
            router.push("/admin");
            router.refresh();
        } catch (err) {
            console.error(err);
            alert("Failed to update status");
        } finally {
            setProcessing(false);
        }
    };

    if (loading) return <div className="flex items-center justify-center h-64"><Loader2 className="animate-spin h-8 w-8 text-muted-foreground" /></div>;
    if (!order) return <div className="flex items-center justify-center h-64 text-muted-foreground">Order not found</div>;

    const isAdmin = user?.role === 'admin';
    const canApprove = isAdmin && order.status === "Pending Approval";

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Order #{order.id.slice(0, 8)}</h1>
                    <p className="text-muted-foreground">Placed on {formatDateTime(order.created_at)}</p>
                </div>
                <div className="flex space-x-2">
                    {canApprove && (
                        <>
                            <Button
                                variant="destructive"
                                onClick={() => handleStatusChange("Cancelled")}
                                disabled={processing}
                            >
                                Reject
                            </Button>
                            <Button
                                variant="default" // Shadcn default is black usually, maybe custom class?
                                className="bg-green-600 hover:bg-green-700"
                                onClick={() => handleStatusChange("Approved")}
                                disabled={processing}
                            >
                                Approve Order
                            </Button>
                        </>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Client Details</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-lg font-medium">{order.client?.name}</div>
                        <div className="text-muted-foreground">{order.client?.address}</div>
                        <Separator className="my-2" />
                        <div className="text-sm">
                            Price Tier: <span className="font-medium">{order.client?.price_tier?.name || "Standard"}</span>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Order Info</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                        <div className="flex justify-between">
                            <span className="text-muted-foreground">Status</span>
                            <StatusBadge status={order.status} />
                        </div>
                        <Separator />
                        <div className="flex justify-between items-center text-lg font-bold">
                            <span>Total</span>
                            <span className="text-green-700">R {(order.total_price_rands ?? 0).toFixed(2)}</span>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Order Items</CardTitle>
                    <CardDescription>Line items for this order.</CardDescription>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>SKU</TableHead>
                                <TableHead className="text-right">Qty</TableHead>
                                <TableHead className="text-right">Unit Price</TableHead>
                                <TableHead className="text-right">Line Total</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {(order.items || []).map((item) => (
                                <TableRow key={item.id || item.sku_id}>
                                    <TableCell className="font-medium">{item.product_name || item.sku_code || `SKU-${item.sku_id?.slice(0, 8)}`}</TableCell>
                                    <TableCell className="text-right">{item.quantity_ordered}</TableCell>
                                    <TableCell className="text-right">R {(item.unit_price_rands ?? 0).toFixed(2)}</TableCell>
                                    <TableCell className="text-right font-bold">
                                        R {((item.quantity_ordered ?? 0) * (item.unit_price_rands ?? 0)).toFixed(2)}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
