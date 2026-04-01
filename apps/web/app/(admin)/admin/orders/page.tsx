"use client";

import { useEffect, useState, useMemo } from "react";
import { Order, Client, Product, DeliveryTeam } from "@/types";
import { apiService } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Loader2, Plus, Calendar, X, Truck, Package, CheckCircle2, AlertCircle } from "lucide-react";
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
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { PageHeader } from "@/components/ui/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/switch";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

export default function AdminOrdersPage() {
    const { toast } = useToast();
    const [orders, setOrders] = useState<Order[]>([]);
    const [clients, setClients] = useState<Client[]>([]);
    const [products, setProducts] = useState<Product[]>([]);
    const [deliveryTeams, setDeliveryTeams] = useState<DeliveryTeam[]>([]);
    const [loading, setLoading] = useState(true);

    // Filters
    const [statusFilter, setStatusFilter] = useState<"All" | "Pending" | "Approved" | "Ready" | "Delivered" | "Cancelled">("All");
    const [dateFilter, setDateFilter] = useState<string>("");

    // Details/Edit State
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
    const [isLoadingDetails, setIsLoadingDetails] = useState(false);
    const [assignTeamId, setAssignTeamId] = useState("");
    const [editDeliveryDate, setEditDeliveryDate] = useState("");
    const [editPaused, setEditPaused] = useState(false);

    // Create Order State
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [createForm, setCreateForm] = useState({
        client_id: "",
        delivery_date: "",
        items: [] as { sku_id: string; quantity: number; product_name?: string; sku_code?: string }[]
    });
    const [newItem, setNewItem] = useState({ product_id: "", sku_id: "", quantity: 1 });
    const [saving, setSaving] = useState(false);

    // Delete State
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    useEffect(() => {
        if (!selectedOrder) {
            setAssignTeamId("");
            setEditDeliveryDate("");
            setEditPaused(false);
            return;
        }
        setAssignTeamId(selectedOrder.delivery_team_id || "");
        setEditDeliveryDate(selectedOrder.delivery_date || "");
        setEditPaused(!!selectedOrder.delivery_paused);
    }, [selectedOrder]);

    const loadData = async () => {
        try {
            setLoading(true);
            const [ordersData, clientsData, productsData, teamsData] = await Promise.all([
                apiService.orders.list(),
                apiService.clients.list(),
                apiService.products.list(),
                apiService.admin.deliveryTeams.list()
            ]);
            setOrders(ordersData);
            setClients(clientsData);
            setProducts(productsData);
            setDeliveryTeams(teamsData);
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load data", description: error.message });
        } finally {
            setLoading(false);
        }
    };

    // --- Computed Data ---
    const filteredOrders = useMemo(() => {
        return orders.filter(o => {
            // Status Filter
            if (statusFilter === "Pending") {
                if (o.status !== "Pending Approval") return false;
            } else if (statusFilter === "Approved") {
                if (o.status !== "Approved") return false;
            } else if (statusFilter === "Ready") {
                if (!["Ready for Delivery", "Out for Delivery"].includes(o.status)) return false;
            } else if (statusFilter === "Delivered") {
                if (!["Delivered", "Completed", "Partially Delivered"].includes(o.status)) return false;
            } else if (statusFilter === "Cancelled") {
                if (o.status !== "Cancelled") return false;
            }
            // Date Filter
            if (dateFilter) {
                if (o.delivery_date !== dateFilter) return false;
            }
            return true;
        });
    }, [orders, statusFilter, dateFilter]);

    const dailySummary = useMemo(() => {
        const targetDate = dateFilter || new Date().toISOString().split("T")[0];
        const relevantOrders = orders.filter(o => o.delivery_date === targetDate);

        return {
            count: relevantOrders.length,
            revenue: relevantOrders.reduce((sum, o) => sum + o.total_price_rands, 0)
        };
    }, [orders, dateFilter]);

    // --- Handlers (Keep Existing) ---
    const handleOrderClick = async (order: Order) => {
        // Optimistically set selected order (items might be missing)
        setSelectedOrder(order);

        try {
            setIsLoadingDetails(true);
            // Fetch full details including items
            const fullOrder = await apiService.orders.get(order.id);
            setSelectedOrder(fullOrder);
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load details", description: error.message });
        } finally {
            setIsLoadingDetails(false);
        }
    };

    const handleUpdateStatus = async (status: "Approved" | "Cancelled") => {
        if (!selectedOrder) return;
        try {
            const updated = await apiService.orders.updateStatus(selectedOrder.id, status);
            toast({ title: "Status Updated", description: `Order marked as ${status}` });
            setSelectedOrder(updated); // Update the modal with new status
            loadData(); // Refresh list background
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error updating status", description: error.message });
        }
    };

    const handleAssignTeam = async () => {
        if (!selectedOrder) return;
        try {
            await apiService.admin.deliveryTeams.updateAssignment(selectedOrder.id, {
                delivery_team_id: assignTeamId || undefined,
                delivery_date: editDeliveryDate || selectedOrder.delivery_date,
                paused: editPaused,
            });
            toast({ title: "Delivery assignment updated" });
            // Refresh details to reflect changes
            const fullOrder = await apiService.orders.get(selectedOrder.id);
            setSelectedOrder(fullOrder);
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error updating assignment", description: error.message });
        }
    };

    const addItemToOrder = () => {
        if (!newItem.product_id || !newItem.sku_id || newItem.quantity < 1) return;
        const product = products.find(p => p.id === newItem.product_id);
        const sku = product?.skus?.find(s => s.id === newItem.sku_id);
        if (!sku) return;
        setCreateForm(prev => ({
            ...prev,
            items: [...prev.items, {
                sku_id: sku.id,
                quantity: newItem.quantity,
                product_name: product?.name,
                sku_code: sku.code
            }]
        }));
        setNewItem({ product_id: "", sku_id: "", quantity: 1 });
    };

    const removeItemFromOrder = (index: number) => {
        setCreateForm(prev => ({ ...prev, items: prev.items.filter((_, i) => i !== index) }));
    };

    const handleSubmitOrder = async () => {
        if (!createForm.client_id || !createForm.delivery_date || createForm.items.length === 0) {
            toast({ variant: "destructive", title: "Validation Error", description: "Required fields missing." });
            return;
        }
        try {
            setSaving(true);
            await apiService.orders.create({
                client_id: createForm.client_id,
                delivery_date: createForm.delivery_date,
                items: createForm.items.map(i => ({ sku_id: i.sku_id, quantity_ordered: i.quantity }))
            });
            toast({ title: "Order Created" });
            setIsCreateOpen(false);
            setCreateForm({ client_id: "", delivery_date: "", items: [] });
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error creating order", description: error.message });
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteOrder = async () => {
        if (!selectedOrder) return;
        try {
            setIsDeleting(true);
            await apiService.orders.delete(selectedOrder.id);
            toast({ title: "Order Deleted", description: "The order has been permanently deleted." });
            setDeleteConfirmOpen(false);
            setSelectedOrder(null);
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error deleting order", description: error.message });
        } finally {
            setIsDeleting(false);
        }
    };

    // --- Render Helpers ---
    const getStatusBadge = (status: string, isReadyForDelivery?: boolean, isPaused?: boolean) => {
        let variant = "secondary";
        let className = "bg-slate-100 text-slate-700 hover:bg-slate-100/80";

        if (status === "Pending Approval") {
            className = "bg-amber-100 text-amber-700 hover:bg-amber-100/80 border-amber-200";
        } else if (["Delivered", "Completed"].includes(status)) {
            className = "bg-blue-100 text-blue-700 hover:bg-blue-100/80 border-blue-200";
        } else if (status === "Approved") {
            // If approved and ready for delivery, show special styling
            if (isReadyForDelivery) {
                className = "bg-emerald-100 text-emerald-700 hover:bg-emerald-100/80 border-emerald-200";
            } else {
                className = "bg-green-100 text-green-700 hover:bg-green-100/80 border-green-200";
            }
        } else if (status === "Cancelled") {
            className = "bg-red-100 text-red-700 hover:bg-red-100/80 border-red-200";
        }

        const displayStatus = (() => {
            if (isPaused) return "Paused";
            if (status === "Pending Approval") return "Pending";
            if (isReadyForDelivery && status === "Approved") return "Ready for Delivery";
            return status;
        })();

        if (isPaused) {
            className = "bg-slate-200 text-slate-600 border-slate-300";
        }

        return <Badge variant="outline" className={cn("font-normal border", className)}>{displayStatus}</Badge>;
    };

    const getClientDisplayName = (order: Order) => {
        if (order.client?.name) return order.client.name;
        const client = clients.find(c => c.id === order.client_id);
        if (client?.name) return client.name;
        if (order.client_name) return order.client_name;
        return order.client_id;
    };

    const getDeliveryStatusLabel = (order: Order) => {
        if (order.delivery_status === "delivered") return "Delivered";
        return "Outstanding";
    };

    const getDeliveryStatusBadgeClass = (label: string) => {
        switch (label) {
            case "Delivered":
                return "border-emerald-200 bg-emerald-100 text-emerald-700";
            case "Outstanding":
                return "border-amber-200 bg-amber-100 text-amber-700";
            default:
                return "border-slate-200 bg-slate-100 text-slate-700";
        }
    };
    return (
        <div className="space-y-6 pb-20">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Orders Management</h1>
                    <p className="text-muted-foreground">Manage and track your manufacturing orders.</p>
                </div>
                <Button onClick={() => setIsCreateOpen(true)} className="gap-2">
                    <Plus size={16} /> New Order
                </Button>
            </div>

            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <div className="stat-card">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="stat-card-label">Pending Approvals</p>
                            <p className="stat-card-value">{orders.filter(o => o.status === "Pending Approval").length}</p>
                        </div>
                        <div className="stat-card-icon bg-amber-100 p-2 rounded-full">
                            <AlertCircle className="h-5 w-5 text-amber-600" />
                        </div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="stat-card-label">Ready for Delivery</p>
                            <p className="stat-card-value">{orders.filter(o => o.status === "Ready for Delivery").length}</p>
                        </div>
                        <div className="stat-card-icon bg-blue-100 p-2 rounded-full">
                            <Truck className="h-5 w-5 text-blue-600" />
                        </div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="stat-card-label">Completed</p>
                            <p className="stat-card-value">{orders.filter(o => o.status === "Completed").length}</p>
                        </div>
                        <div className="stat-card-icon bg-green-100 p-2 rounded-full">
                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                        </div>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="stat-card-label">Outstanding Orders</p>
                            <p className="stat-card-value">{orders.filter(order => !["Completed", "Cancelled"].includes(order.status)).length}</p>
                        </div>
                        <div className="stat-card-icon bg-amber-100 p-2 rounded-full">
                            <AlertCircle className="h-5 w-5 text-amber-600" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Filter Strip */}
            <div className="flex flex-col gap-4 border-b pb-6">
                <div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
                    <div className="flex p-1 bg-muted/50 rounded-lg border w-fit">
                        {(["All", "Pending", "Approved", "Ready", "Delivered", "Cancelled"] as const).map(option => (
                            <button
                                key={option}
                                onClick={() => setStatusFilter(option)}
                                className={cn(
                                    "px-3 sm:px-4 py-1.5 text-sm font-medium rounded-md transition-all whitespace-nowrap",
                                    statusFilter === option
                                        ? "bg-white text-foreground shadow-sm"
                                        : "text-muted-foreground hover:text-foreground/80"
                                )}
                            >
                                {option === "All" ? "All" : option}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="flex items-center gap-2 sm:ml-auto">
                    <div className="relative flex-1 sm:flex-none">
                        <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                        <Input
                            type="date"
                            className="pl-9 w-full sm:w-[180px] bg-background"
                            value={dateFilter}
                            onChange={e => setDateFilter(e.target.value)}
                        />
                    </div>
                    {dateFilter && (
                        <Button variant="ghost" size="icon" onClick={() => setDateFilter("")}>
                            <X size={16} className="text-muted-foreground" />
                        </Button>
                    )}
                </div>
            </div>

            <Card className="border shadow-sm overflow-hidden">
                <div className="p-0">
                    {loading ? (
                        <div className="p-12 flex justify-center">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : filteredOrders.length === 0 ? (
                        <EmptyState
                            icon={Package}
                            title="No orders found"
                            description="Adjust your filters to see more results."
                        />
                    ) : (
                        <div className="overflow-x-auto">
                        <Table>
                            <TableHeader className="bg-muted/30">
                                <TableRow>
                                    <TableHead className="w-[120px]">Status</TableHead>
                                    <TableHead>Client / Store</TableHead>
                                    <TableHead className="w-[110px] hidden sm:table-cell">Products</TableHead>
                                    <TableHead className="w-[110px] hidden sm:table-cell">Delivered</TableHead>
                                    <TableHead className="hidden md:table-cell">Placed Order</TableHead>
                                    <TableHead className="hidden md:table-cell">Delivery Date</TableHead>
                                    <TableHead className="text-right">Total Value</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredOrders.map(order => (
                                    <TableRow
                                        key={order.id}
                                        className={cn(
                                            "cursor-pointer transition-colors",
                                            order.delivery_paused ? "bg-slate-50 hover:bg-slate-100" : "hover:bg-muted/30"
                                        )}
                                        onClick={() => handleOrderClick(order)}
                                    >
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                {getStatusBadge(order.status, order.is_ready_for_delivery, order.delivery_paused)}
                                                {order.is_ready_for_delivery && order.status === "Approved" && !order.delivery_paused && (
                                                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                                                )}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="font-medium">{getClientDisplayName(order)}</div>
                                            <div className="text-xs text-muted-foreground font-mono">#{order.id.slice(0, 6)}</div>
                                        </TableCell>
                                        <TableCell className="hidden sm:table-cell">
                                            {order.is_ready_for_delivery ? (
                                                <Badge variant="outline" className="border-emerald-200 bg-emerald-100 text-emerald-700">
                                                    Ready
                                                </Badge>
                                            ) : (
                                                <Badge variant="outline" className="border-slate-200 bg-slate-100 text-slate-700">
                                                    Not ready
                                                </Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="hidden sm:table-cell">
                                            {(() => {
                                                const label = getDeliveryStatusLabel(order);
                                                return (
                                                    <Badge variant="outline" className={getDeliveryStatusBadgeClass(label)}>
                                                        {label}
                                                    </Badge>
                                                );
                                            })()}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground hidden md:table-cell">
                                            {new Date(order.created_at).toLocaleDateString("en-GB", { day: 'numeric', month: 'short', year: 'numeric' })}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground hidden md:table-cell">
                                            {order.delivery_date ? new Date(order.delivery_date).toLocaleDateString("en-GB", { day: 'numeric', month: 'short', year: 'numeric' }) : "-"}
                                        </TableCell>
                                        <TableCell className="text-right font-medium">
                                            R {(order.total_price_rands ?? 0).toLocaleString()}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                        </div>
                    )}
                </div>
                {filteredOrders.length > 0 && (
                    <div className="bg-muted/20 p-3 border-t text-xs text-center text-muted-foreground">
                        Showing {filteredOrders.length} orders
                    </div>
                )}
            </Card>

            {/* Dialogs (Keep Existing functionality) */}
            <Dialog open={!!selectedOrder} onOpenChange={(open) => !open && setSelectedOrder(null)}>
                <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto mx-4 sm:mx-auto">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                                <Package size={20} />
                            </div>
                            <div>
                                <div>Order #{selectedOrder?.id.slice(0, 8)}</div>
                                <div className="text-sm font-normal text-muted-foreground">{selectedOrder?.client_name}</div>
                            </div>
                        </DialogTitle>
                    </DialogHeader>

                    {isLoadingDetails && !selectedOrder?.items?.length ? (
                        <div className="flex justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : selectedOrder && (
                        <div className="space-y-4 py-2">
                            {(() => {
                                const canAssignTeam = selectedOrder.status === "Approved" && selectedOrder.is_ready_for_delivery;
                                return (
                                    <>
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                {getStatusBadge(selectedOrder.status, selectedOrder.is_ready_for_delivery, selectedOrder.delivery_paused)}
                                                {selectedOrder.is_ready_for_delivery && selectedOrder.status === "Approved" && !selectedOrder.delivery_paused && (
                                                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                                                )}
                                            </div>
                                            {selectedOrder.delivery_date && (
                                                <div className="text-sm text-muted-foreground flex items-center gap-1.5">
                                                    <Calendar size={14} />
                                                    <span>Delivery: {selectedOrder.delivery_date}</span>
                                                </div>
                                            )}
                                        </div>

                                        <div className="border rounded-xl p-4 bg-muted/20">
                                            <h4 className="font-medium text-sm text-muted-foreground mb-3">Order Items</h4>
                                            <div className="space-y-3">
                                                {selectedOrder.items?.map(item => {
                                                    const allocated = item.quantity_allocated ?? 0;
                                                    const isFullyAllocated = allocated >= item.quantity_ordered;
                                                    const allocationPct = item.quantity_ordered > 0
                                                        ? Math.round((allocated / item.quantity_ordered) * 100)
                                                        : 0;
                                                    return (
                                                        <div key={item.id} className="flex justify-between items-center py-2 border-b border-border/50 last:border-0 last:pb-0">
                                                            <div className="flex-1">
                                                                <div className="font-medium text-sm">{item.product_name || item.sku_code || `SKU ${item.sku_id.slice(0, 8)}`}</div>
                                                                <div className="text-xs text-muted-foreground">{item.sku_code ?? item.sku_id.slice(0, 8)} • Qty {item.quantity_ordered}</div>
                                                                {selectedOrder.status === "Approved" && (
                                                                    <div className={cn(
                                                                        "text-xs mt-1",
                                                                        isFullyAllocated ? "text-emerald-600" : "text-amber-600"
                                                                    )}>
                                                                        {isFullyAllocated ? (
                                                                            <span className="flex items-center gap-1">
                                                                                <CheckCircle2 className="h-3 w-3" />
                                                                                Allocated
                                                                            </span>
                                                                        ) : (
                                                                            <span>{allocated}/{item.quantity_ordered} allocated ({allocationPct}%)</span>
                                                                        )}
                                                                    </div>
                                                                )}
                                                            </div>
                                                            <div className="text-right">
                                                                <div className="font-medium text-sm">R {(item.unit_price_rands * item.quantity_ordered).toLocaleString()}</div>
                                                                <div className="text-xs text-muted-foreground">R {item.unit_price_rands} ea</div>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                            <div className="border-t border-border mt-4 pt-3 flex justify-between items-center">
                                                <span className="font-semibold">Total</span>
                                                <span className="font-bold text-lg">R {(selectedOrder.total_price_rands ?? 0).toLocaleString()}</span>
                                            </div>
                                        </div>

                                        {selectedOrder.status === "Pending Approval" && (
                                            <div className="flex gap-3 pt-2">
                                                <Button className="flex-1 bg-green-600 hover:bg-green-700" onClick={() => handleUpdateStatus("Approved")}>
                                                    Approve Order
                                                </Button>
                                                <Button variant="outline" className="flex-1 border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground" onClick={() => handleUpdateStatus("Cancelled")}>
                                                    Reject
                                                </Button>
                                            </div>
                                        )}

                                        {selectedOrder.status === "Approved" && (
                                            <div className="space-y-3 pt-2">
                                                <Label className="text-sm font-medium">Delivery Scheduling & Assignment</Label>
                                                <div className="grid gap-3 sm:grid-cols-2">
                                                    <div className="space-y-2">
                                                        <Label className="text-xs text-muted-foreground">Delivery Date</Label>
                                                        <Input
                                                            type="date"
                                                            value={editDeliveryDate}
                                                            onChange={e => setEditDeliveryDate(e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="space-y-2">
                                                        <Label className="text-xs text-muted-foreground">Delivery Team</Label>
                                                        <Select value={assignTeamId} onValueChange={setAssignTeamId} disabled={!canAssignTeam}>
                                                            <SelectTrigger className="flex-1">
                                                                <SelectValue placeholder="Select Team" />
                                                            </SelectTrigger>
                                                            <SelectContent>
                                                                {deliveryTeams.map(t => (
                                                                    <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                                                                ))}
                                                            </SelectContent>
                                                        </Select>
                                                        {!canAssignTeam && (
                                                            <p className="text-xs text-muted-foreground">Assign teams once products are ready.</p>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-2">
                                                        <Switch checked={editPaused} onCheckedChange={setEditPaused} />
                                                        <span className="text-sm text-muted-foreground">Pause delivery</span>
                                                    </div>
                                                    <Button onClick={handleAssignTeam} disabled={!editDeliveryDate}>
                                                        <Truck size={16} className="mr-2" />
                                                        Save
                                                    </Button>
                                                </div>
                                            </div>
                                        )}
                                    </>
                                );
                            })()}
                            {/* Delete Button - Available for all orders */}
                            <div className="pt-6 border-t mt-4">
                                <Button
                                    variant="ghost"
                                    className="w-full text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                                    onClick={() => setDeleteConfirmOpen(true)}
                                >
                                    Delete Order
                                </Button>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Order?</DialogTitle>
                        <DialogDescription>
                            This action cannot be undone. This will permanently delete the order and return any allocated items to inventory.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="flex justify-end gap-3 py-4">
                        <Button variant="outline" onClick={() => setDeleteConfirmOpen(false)} disabled={isDeleting}>Cancel</Button>
                        <Button variant="destructive" onClick={handleDeleteOrder} disabled={isDeleting}>
                            {isDeleting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                            Confirm Delete
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>

            <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <DialogContent className="max-w-3xl">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                                <Plus size={20} />
                            </div>
                            Create New Order
                        </DialogTitle>
                        <DialogDescription>
                            Select a client, set delivery date, and add items to the order.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 py-4">
                        <div className="space-y-5">
                            <div className="space-y-2">
                                <Label className="text-sm font-medium">Client</Label>
                                <Select value={createForm.client_id} onValueChange={v => setCreateForm({ ...createForm, client_id: v })}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select Client" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {clients.map(c => (
                                            <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label className="text-sm font-medium">Delivery Date</Label>
                                <Input type="date" value={createForm.delivery_date} onChange={e => setCreateForm({ ...createForm, delivery_date: e.target.value })} />
                            </div>

                            <div className="space-y-3 border-t pt-4">
                                <Label className="text-sm font-medium">Add Item</Label>
                                <Select value={newItem.product_id} onValueChange={v => setNewItem({ ...newItem, product_id: v, sku_id: "" })}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select Product" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {products.map(p => (
                                            <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <Select value={newItem.sku_id} onValueChange={v => setNewItem({ ...newItem, sku_id: v })} disabled={!newItem.product_id}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select SKU" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {products.find(p => p.id === newItem.product_id)?.skus?.map(sku => (
                                            <SelectItem key={sku.id} value={sku.id}>{sku.code} - {sku.size} - R{sku.base_price_rands}</SelectItem>
                                        )) || []}
                                    </SelectContent>
                                </Select>
                                <div className="flex gap-2">
                                    <Input
                                        type="number"
                                        min="1"
                                        value={newItem.quantity}
                                        onChange={e => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 1 })}
                                        className="w-24"
                                        placeholder="Qty"
                                    />
                                    <Button type="button" variant="secondary" onClick={addItemToOrder}>
                                        <Plus size={16} className="mr-1" />
                                        Add
                                    </Button>
                                </div>
                            </div>
                        </div>

                        <div className="border rounded-xl p-4 bg-muted/20 flex flex-col">
                            <h4 className="font-semibold text-sm mb-3">Order Summary</h4>
                            <div className="flex-1 overflow-y-auto space-y-2 max-h-[280px]">
                                {createForm.items.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground text-sm border border-dashed rounded-lg">
                                        No items added yet
                                    </div>
                                ) : (
                                    createForm.items.map((item, i) => (
                                        <div key={item.sku_id || i} className="flex justify-between items-center bg-card border p-3 rounded-lg text-sm">
                                            <div>
                                                <div className="font-medium">{item.sku_code}</div>
                                                <div className="text-xs text-muted-foreground">{item.product_name}</div>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className="text-muted-foreground">×{item.quantity}</span>
                                                <button
                                                    onClick={() => removeItemFromOrder(i)}
                                                    className="h-6 w-6 flex items-center justify-center rounded-full text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                                                >
                                                    <X size={14} />
                                                </button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                            <div className="mt-4 pt-3 border-t">
                                <Button className="w-full" onClick={handleSubmitOrder} disabled={saving || createForm.items.length === 0}>
                                    {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Create Order
                                </Button>
                            </div>
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
}
