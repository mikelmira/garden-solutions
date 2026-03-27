"use client";

import { useState, useEffect } from "react";
import { apiService } from "@/lib/api";
import { DeliveryTeam, Order } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Check, Truck, X, Loader2, ArrowRight, MapPin, Package, Calendar, LogOut } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

type Screen = "gate" | "list";

export default function DeliveryPage() {
    const { toast } = useToast();
    const [screen, setScreen] = useState<Screen>("gate");
    const [loading, setLoading] = useState(false);

    // Auth State
    const [teamCode, setTeamCode] = useState("");
    const [team, setTeam] = useState<DeliveryTeam | null>(null);

    // Data State
    const [orders, setOrders] = useState<Order[]>([]);
    const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split("T")[0]);

    // Action State
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
    const [outcomeType, setOutcomeType] = useState<"Delivered" | "Partially Delivered" | "Not Delivered" | null>(null);
    const [reason, setReason] = useState("");
    const [receiverName, setReceiverName] = useState("");
    const [partialQtys, setPartialQtys] = useState<Record<string, number>>({});

    useEffect(() => {
        const savedCode = localStorage.getItem("garden_delivery_code");
        if (savedCode) {
            verifyCode(savedCode, true);
        }
    }, []);

    useEffect(() => {
        if (team && screen === "list") {
            loadQueue();
        }
    }, [team, selectedDate, screen]);

    const verifyCode = async (code: string, silent = false) => {
        if (!code) return;
        setLoading(true);
        try {
            const data = await apiService.public.deliveryTeams.resolve(code);
            setTeam(data);
            setTeamCode(data.code);
            localStorage.setItem("garden_delivery_code", data.code);
            setScreen("list");
        } catch (error) {
            if (!silent) {
                toast({ variant: "destructive", title: "Invalid Code", description: "Team not found." });
            }
            localStorage.removeItem("garden_delivery_code");
        } finally {
            setLoading(false);
        }
    };

    const loadQueue = async () => {
        if (!team) return;
        setLoading(true);
        try {
            const data = await apiService.public.delivery.queue(team.code, selectedDate);
            setOrders(data);
        } catch (error) {
            console.error(error);
            toast({ variant: "destructive", title: "Network Error", description: "Failed to load queue." });
        } finally {
            setLoading(false);
        }
    };

    const handleAction = (order: Order, type: "Delivered" | "Partially Delivered" | "Not Delivered") => {
        setSelectedOrder(order);
        setOutcomeType(type);
        setReason("");
        setReceiverName("");
        // Reset partial quantities
        const initial: Record<string, number> = {};
        order.items?.forEach(i => initial[i.id] = i.quantity_ordered);
        setPartialQtys(initial);
    };

    const submitOutcome = async () => {
        if (!selectedOrder || !outcomeType) return;

        // Validation
        if ((outcomeType === "Not Delivered" || outcomeType === "Partially Delivered") && !reason.trim()) {
            toast({ variant: "destructive", title: "Required", description: "Please enter a reason." });
            return;
        }

        setLoading(true);
        try {
            const payload: any = {
                team_code: team?.code,
                outcome: outcomeType,
                receiver_name: receiverName,
                reason: reason,
            };

            if (outcomeType === "Partially Delivered") {
                payload.items = Object.entries(partialQtys).map(([id, qty]) => ({
                    order_item_id: id,
                    quantity_delivered: qty
                }));
            }

            await apiService.public.delivery.setOutcome(selectedOrder.id, payload);

            toast({ title: "Success", description: "Delivery status updated." });
            setOutcomeType(null);
            setSelectedOrder(null);
            loadQueue();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error", description: error.message || "Update failed." });
        } finally {
            setLoading(false);
        }
    };

    if (screen === "gate") {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-gradient-to-b from-background to-muted/30">
                <div className="w-full max-w-sm space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    {/* Logo */}
                    <div className="flex justify-center">
                        <div className="h-16 w-16 bg-white rounded-2xl flex items-center justify-center shadow-lg border">
                            <img src="/logo.avif" alt="Garden Solutions" className="h-10 w-10 object-contain" />
                        </div>
                    </div>
                    <div className="text-center space-y-2">
                        <h1 className="text-3xl font-heading font-semibold tracking-tight text-foreground">Delivery Portal</h1>
                        <p className="text-muted-foreground">Enter your team code to access the delivery queue</p>
                    </div>
                    <Card className="border shadow-xl shadow-black/5">
                        <CardContent className="pt-6 space-y-4">
                            <Input
                                className="text-center text-lg tracking-widest font-mono uppercase h-12"
                                value={teamCode}
                                onChange={e => setTeamCode(e.target.value)}
                                placeholder="XXX-XXX"
                                onKeyDown={e => e.key === "Enter" && verifyCode(teamCode)}
                            />
                            <Button
                                className="w-full h-12 text-base font-medium bg-blue-600 hover:bg-blue-700"
                                onClick={() => verifyCode(teamCode)}
                                disabled={loading || !teamCode}
                            >
                                {loading && <Loader2 className="mr-2 h-5 w-5 animate-spin" />}
                                Access Route
                                {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    // Get status badge class
    const getStatusClass = (status: string, isDone: boolean, isFailed: boolean) => {
        if (isDone) return "status-badge-success";
        if (isFailed) return "status-badge-error";
        return "status-badge-info";
    };

    // List Screen
    return (
        <div className="min-h-screen pb-8 bg-background">
            {/* Header */}
            <div className="bg-background/95 backdrop-blur-lg border-b sticky top-0 z-10">
                <div className="px-6 py-4 max-w-lg mx-auto">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 bg-blue-600 rounded-xl flex items-center justify-center">
                                <Truck className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <div className="font-heading font-semibold text-lg text-foreground">Delivery Run</div>
                                <div className="text-sm text-muted-foreground">{team?.name}</div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="flex items-center gap-2 bg-muted px-3 py-2 rounded-lg">
                                <Calendar size={16} className="text-muted-foreground" />
                                <Input
                                    type="date"
                                    className="w-auto h-auto p-0 border-0 bg-transparent text-sm font-medium focus-visible:ring-0"
                                    value={selectedDate}
                                    onChange={e => setSelectedDate(e.target.value)}
                                />
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-9 w-9 text-muted-foreground hover:text-foreground"
                                onClick={() => {
                                    localStorage.removeItem("garden_delivery_code");
                                    setTeam(null);
                                    setOrders([]);
                                    setTeamCode("");
                                    setScreen("gate");
                                }}
                                title="Sign Out"
                            >
                                <LogOut size={16} />
                            </Button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-4 space-y-4 max-w-lg mx-auto">
                {loading && (
                    <div className="flex justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </div>
                )}

                {orders.length === 0 && !loading && (
                    <div className="text-center py-16 px-6">
                        <div className="h-16 w-16 mx-auto bg-muted rounded-2xl flex items-center justify-center mb-4">
                            <Package className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <h3 className="font-semibold text-foreground mb-1">No deliveries</h3>
                        <p className="text-sm text-muted-foreground">No orders scheduled for this date.</p>
                    </div>
                )}

                {orders.map(order => {
                    const isDone = ["Completed", "Partially Delivered"].includes(order.status) || order.delivery_status === "delivered";
                    const isFailed = order.delivery_status === "not_delivered" || order.status === "Cancelled";

                    return (
                        <Card key={order.id} className={cn(
                            "transition-all",
                            isDone && "opacity-60 bg-muted/30",
                            isFailed && "opacity-60 border-destructive/30"
                        )}>
                            <CardHeader className="pb-3">
                                <div className="flex justify-between items-start mb-2">
                                    <span className={cn("status-badge", getStatusClass(order.status, isDone, isFailed))}>
                                        {order.status}
                                    </span>
                                    <span className="text-xs font-mono text-muted-foreground">#{order.id.slice(0, 6)}</span>
                                </div>
                                <CardTitle className="text-lg text-foreground">{order.client_name || order.client?.name}</CardTitle>
                                {(order.client?.address) && (
                                    <CardDescription className="flex items-start gap-1.5">
                                        <MapPin size={14} className="mt-0.5 flex-shrink-0" />
                                        <span>{order.client.address}</span>
                                    </CardDescription>
                                )}
                            </CardHeader>
                            <CardContent className="pb-4">
                                <div className="space-y-2">
                                    {order.items?.map(item => (
                                        <div key={item.id} className="flex items-center gap-3 text-sm bg-muted/50 p-3 rounded-lg">
                                            {item.product_image ? (
                                                <img src={item.product_image} className="w-10 h-10 rounded-lg object-cover bg-white border" alt={item.product_name || "Product"} />
                                            ) : (
                                                <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center border text-muted-foreground">
                                                    <Package size={16} />
                                                </div>
                                            )}
                                            <div className="flex-1 min-w-0">
                                                <div className="font-medium text-foreground truncate">{item.product_name || `Item #${item.sku_id.slice(0, 4)}`}</div>
                                                <div className="text-xs text-muted-foreground">{item.sku_code || "Unknown SKU"}</div>
                                            </div>
                                            <div className="font-bold text-foreground">×{item.quantity_ordered}</div>
                                        </div>
                                    ))}
                                    <div className="pt-3 flex justify-between items-center border-t mt-3">
                                        <span className="text-sm text-muted-foreground">Order Total</span>
                                        <span className="font-bold text-foreground">R{(order.total_price_rands ?? 0).toFixed(0)}</span>
                                    </div>
                                </div>
                            </CardContent>

                            {!isDone && !isFailed && (
                                <CardFooter className="grid grid-cols-3 gap-2 pt-0 pb-4">
                                    <Button size="sm" variant="outline" className="border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 hover:border-red-300" onClick={() => handleAction(order, "Not Delivered")}>
                                        <X className="h-4 w-4 mr-1" /> Fail
                                    </Button>
                                    <Button size="sm" variant="outline" className="border-amber-200 text-amber-600 hover:bg-amber-50 hover:text-amber-700 hover:border-amber-300" onClick={() => handleAction(order, "Partially Delivered")}>
                                        Partial
                                    </Button>
                                    <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white" onClick={() => handleAction(order, "Delivered")}>
                                        <Check className="h-4 w-4 mr-1" /> Done
                                    </Button>
                                </CardFooter>
                            )}
                        </Card>
                    );
                })}
            </div>

            {/* Action Dialog */}
            <Dialog open={!!selectedOrder} onOpenChange={(o) => !o && setSelectedOrder(null)}>
                <DialogContent className="max-w-md">
                    <DialogHeader>
                        <DialogTitle>{outcomeType} Outcome</DialogTitle>
                        <DialogDescription>
                            Recording status for {selectedOrder?.client_name || "Client"}
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
                        {outcomeType === "Delivered" && (
                            <div className="space-y-2">
                                <Label>Received By (Optional)</Label>
                                <Input placeholder="Name / Signature" value={receiverName} onChange={e => setReceiverName(e.target.value)} />
                            </div>
                        )}

                        {outcomeType === "Not Delivered" && (
                            <div className="space-y-2">
                                <Label>Reason for Failure <span className="text-red-500">*</span></Label>
                                <Input placeholder="e.g., Gate locked, client closed" value={reason} onChange={e => setReason(e.target.value)} />
                            </div>
                        )}

                        {outcomeType === "Partially Delivered" && (
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Reason for Partial <span className="text-red-500">*</span></Label>
                                    <Input placeholder="e.g., Damaged items, out of stock" value={reason} onChange={e => setReason(e.target.value)} />
                                </div>

                                <Separator />
                                <Label>Confirm Quantities Delivered</Label>
                                <div className="space-y-3">
                                    {selectedOrder?.items?.map(item => (
                                        <div key={item.id} className="flex justify-between items-center bg-slate-50 p-2 rounded">
                                            <div className="flex items-center gap-3">
                                                {item.product_image && (
                                                    <img src={item.product_image} className="w-8 h-8 rounded-sm object-cover border" alt={item.product_name} />
                                                )}
                                                <div className="text-sm">
                                                    <div className="font-medium text-slate-700">{item.product_name || `Item #${item.sku_id.slice(0, 4)}`}</div>
                                                    <div className="text-xs text-muted-foreground">Ord: {item.quantity_ordered}</div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Button size="icon" variant="outline" className="h-8 w-8" onClick={() => setPartialQtys(p => ({ ...p, [item.id]: Math.max(0, (p[item.id] || 0) - 1) }))}>-</Button>
                                                <span className="w-8 text-center">{partialQtys[item.id]}</span>
                                                <Button size="icon" variant="outline" className="h-8 w-8" onClick={() => setPartialQtys(p => ({ ...p, [item.id]: Math.min(item.quantity_ordered, (p[item.id] || 0) + 1) }))}>+</Button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setSelectedOrder(null)}>Cancel</Button>
                        <Button onClick={submitOutcome} disabled={loading} className={outcomeType === "Delivered" ? "bg-green-600 hover:bg-green-700" : ""}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Confirm {outcomeType}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
