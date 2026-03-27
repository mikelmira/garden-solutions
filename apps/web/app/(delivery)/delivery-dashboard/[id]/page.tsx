"use client";

import { useEffect, useState } from "react";
import { Order } from "@/types";
import { apiService } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ArrowLeft, Box, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useToast } from "@/hooks/use-toast";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function DeliveryOrderPage({ params }: { params: { id: string } }) {
    const [order, setOrder] = useState<Order | null>(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const router = useRouter();
    const { toast } = useToast();

    // Action State
    const [actionType, setActionType] = useState<"Complete" | "Partial" | null>(null);
    const [receiverName, setReceiverName] = useState("");
    const [notes, setNotes] = useState("");
    // Track partial quantities per item ID
    const [partialQuantities, setPartialQuantities] = useState<Record<string, number>>({});
    // Track validation error message for toast
    const [validationError, setValidationError] = useState<string | null>(null);

    useEffect(() => {
        apiService.orders.get(params.id)
            .then((data) => {
                setOrder(data);
                // Initialize partial quantities to 0
                const initial: Record<string, number> = {};
                data.items?.forEach(i => {
                    if (i.id) initial[i.id] = 0;
                });
                setPartialQuantities(initial);
            })
            .catch(() => {
                toast({ variant: "destructive", title: "Error", description: "Failed to load order" });
            })
            .finally(() => setLoading(false));
    }, [params.id, toast]);

    const handleAction = async () => {
        if (!order || !actionType) return;

        // Validation
        if (!receiverName) {
            toast({ variant: "destructive", title: "Required", description: "Receiver name is required" });
            return;
        }
        if (actionType === "Partial" && !notes) {
            toast({ variant: "destructive", title: "Required", description: "Reason is required for partial delivery" });
            return;
        }

        setSubmitting(true);
        try {
            if (actionType === "Complete") {
                // API only accepts receiver_name per DeliveryComplete schema
                await apiService.delivery.completeDelivery(order.id, receiverName);
                toast({ title: "Success", description: "Delivery confirmed complete." });
                router.push("/delivery-dashboard");
            } else {
                // Partial Delivery
                const itemsToUpdate = Object.entries(partialQuantities)
                    .filter(([_, qty]) => qty > 0)
                    .map(([id, quantity]) => ({ id, quantity }));

                if (itemsToUpdate.length === 0) {
                    toast({ variant: "destructive", title: "No Items", description: "Please enter at least one quantity to deliver." });
                    setSubmitting(false);
                    return;
                }

                // API expects reason (not notes) per DeliveryPartial schema
                await apiService.delivery.partialDelivery(order.id, itemsToUpdate, receiverName, notes);
                toast({ title: "Success", description: "Partial delivery recorded." });

                // Refresh order data
                const updated = await apiService.orders.get(order.id);
                setOrder(updated);

                // Reset form state properly
                setPartialQuantities({});
                const initial: Record<string, number> = {};
                updated.items?.forEach(i => { if (i.id) initial[i.id] = 0; });
                setPartialQuantities(initial);
                setReceiverName("");
                setNotes("");
                setActionType(null);
            }
        } catch (error: any) {
            console.error(error);
            toast({
                variant: "destructive",
                title: "Action Failed",
                description: error.message || "An unexpected error occurred. Please try again."
            });
        } finally {
            setSubmitting(false);
        }
    };

    // Helper to handle partial quantity input
    const updatePartialQty = (itemId: string, val: string, max: number) => {
        const qty = parseInt(val, 10);
        if (isNaN(qty)) {
            setPartialQuantities(prev => ({ ...prev, [itemId]: 0 }));
            return;
        }
        if (qty < 0) return;
        if (qty > max) {
            toast({ variant: "destructive", title: "Limit Exceeded", description: `Cannot deliver more than remaining: ${max}` });
            return;
        }
        setPartialQuantities(prev => ({ ...prev, [itemId]: qty }));
    };

    if (loading) {
        return (
            <div className="container mx-auto p-6 max-w-4xl space-y-6">
                <div className="h-10 w-32 bg-muted animate-pulse rounded" />
                <div className="flex justify-between items-start">
                    <div className="space-y-2">
                        <div className="h-8 w-64 bg-muted animate-pulse rounded" />
                        <div className="h-6 w-32 bg-muted animate-pulse rounded" />
                    </div>
                </div>
                <div className="h-48 bg-muted animate-pulse rounded-lg" />
            </div>
        );
    }

    if (!order) {
        return (
            <div className="container mx-auto p-6 flex flex-col items-center justify-center min-h-[50vh] gap-4">
                <Box className="h-12 w-12 text-muted-foreground/50" />
                <h3 className="text-xl font-semibold">Order Not Found</h3>
                <p className="text-muted-foreground">The requested delivery manifest could not be loaded.</p>
                <Button onClick={() => router.push("/delivery-dashboard")} variant="outline">
                    Return to Dashboard
                </Button>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-6 max-w-4xl space-y-6">
            <Button variant="ghost" className="mb-4 pl-0" onClick={() => router.back()}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Dashboard
            </Button>

            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-bold">Delivery Manifest</h1>
                    <div className="text-lg text-muted-foreground">#{order.id.slice(0, 8)}</div>
                </div>
                <Badge className="text-base">{order.status}</Badge>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Delivery Details</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-2">
                    <div>
                        <Label className="text-muted-foreground">Client</Label>
                        <div className="font-medium text-lg">{order.client_name || order.client?.name}</div>
                    </div>
                    <div>
                        <Label className="text-muted-foreground">Address</Label>
                        <div className="font-medium">{order.client?.address || "No address on file"}</div>
                    </div>
                    <div>
                        <Label className="text-muted-foreground">Delivery Date</Label>
                        <div>{order.delivery_date}</div>
                    </div>
                </CardContent>
            </Card>

            {/* Checklist Section */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex justify-between items-center">
                        <span>Items to Deliver</span>
                        <Badge variant="outline">{order.items?.length || 0} items</Badge>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[50px]">Check</TableHead>
                                <TableHead>SKU</TableHead>
                                <TableHead className="text-right">Ordered</TableHead>
                                <TableHead className="text-right">Manufactured</TableHead>
                                <TableHead className="text-right">Delivered</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {order.items?.map((item, idx) => (
                                <TableRow key={idx} className="hover:bg-muted/50 transition-colors">
                                    <TableCell>
                                        <Checkbox
                                            id={`check-${idx}`}
                                            aria-label={`Select ${item.sku_id}`}
                                        />
                                    </TableCell>
                                    <TableCell className="font-medium">
                                        <label htmlFor={`check-${idx}`} className="cursor-pointer">
                                            {item.sku_id.slice(0, 8)}...
                                        </label>
                                    </TableCell>
                                    <TableCell className="text-right">{item.quantity_ordered}</TableCell>
                                    <TableCell className="text-right">{item.quantity_manufactured || 0}</TableCell>
                                    <TableCell className="text-right">{item.quantity_delivered || 0}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            <div className="flex gap-4 pt-4">
                <Dialog open={actionType !== null} onOpenChange={(open) => !open && setActionType(null)}>
                    <div className="flex w-full gap-4">
                        <Button className="flex-1" variant="secondary" onClick={() => setActionType("Partial")}>
                            Report Partial Delivery
                        </Button>
                        <Button className="flex-1" onClick={() => setActionType("Complete")}>
                            Confirm Delivery Complete
                        </Button>
                    </div>

                    <DialogContent className="max-w-2xl">
                        <DialogHeader>
                            <DialogTitle>{actionType === "Complete" ? "Complete Delivery" : "Partial Delivery"}</DialogTitle>
                            <DialogDescription>
                                {actionType === "Complete"
                                    ? "Confirm that all items have been offloaded and accepted."
                                    : "Specify quantities delivered for each item below."}
                            </DialogDescription>
                        </DialogHeader>

                        <div className="gap-6 py-4 grid">
                            {actionType === "Partial" && (
                                <div className="border rounded-md p-4 bg-muted/20">
                                    <h4 className="font-semibold mb-3">Item Quantities</h4>
                                    <ScrollArea className="h-[200px] pr-4">
                                        <div className="space-y-4">
                                            {order.items?.map((item, idx) => (
                                                <div key={idx} className="flex items-center justify-between gap-4">
                                                    <div className="flex-1">
                                                        <div className="font-medium text-sm">{item.sku_id.slice(0, 12)}...</div>
                                                        <div className="text-xs text-muted-foreground">
                                                            Ordered: {item.quantity_ordered} | Delivered: {item.quantity_delivered || 0}
                                                        </div>
                                                    </div>
                                                    <div className="w-32">
                                                        <Input
                                                            type="number"
                                                            placeholder="Qty"
                                                            className="h-8 text-right"
                                                            min={0}
                                                            max={item.quantity_ordered - (item.quantity_delivered || 0)}
                                                            value={item.id ? (partialQuantities[item.id] || "") : ""}
                                                            onChange={(e) => item.id && updatePartialQty(
                                                                item.id,
                                                                e.target.value,
                                                                item.quantity_ordered - (item.quantity_delivered || 0)
                                                            )}
                                                            disabled={!item.id}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </ScrollArea>
                                </div>
                            )}

                            <div className="grid gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="receiver">Receiver Name *</Label>
                                    <Input
                                        id="receiver"
                                        placeholder="Who accepted the delivery?"
                                        value={receiverName}
                                        onChange={(e) => setReceiverName(e.target.value)}
                                        className={!receiverName && submitting ? "border-red-500" : ""}
                                        disabled={submitting}
                                    />
                                </div>

                                {actionType === "Partial" && (
                                    <div className="space-y-2">
                                        <Label htmlFor="notes">Reason *</Label>
                                        <Input
                                            id="notes"
                                            placeholder="e.g., Truck full, Item damaged..."
                                            value={notes}
                                            onChange={(e) => setNotes(e.target.value)}
                                            className={!notes && submitting ? "border-red-500" : ""}
                                            disabled={submitting}
                                        />
                                    </div>
                                )}
                            </div>
                        </div>

                        <DialogFooter>
                            <Button variant="outline" onClick={() => setActionType(null)} disabled={submitting}>Cancel</Button>
                            <Button onClick={handleAction} disabled={submitting || !receiverName}>
                                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                {submitting ? "Submitting..." : "Confirm Update"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
        </div>
    );
}
