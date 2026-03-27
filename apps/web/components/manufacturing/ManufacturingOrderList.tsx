import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Order, OrderItem } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { ChevronDown, ChevronUp, Loader2, RefreshCw } from "lucide-react";
import { apiService } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

// Since we know the backend endpoint is missing, we create a mock-like experience or just disabled state.
// User requested "input to set 'qty manufactured increment' OR set absolute manufactured qty"
// "button: 'Mark Manufactured' (updates backend)"

// We will implement the row component to handle local state for inputs.

function ManufacturingOrderItemRow({ item, onRefresh }: { item: OrderItem; onRefresh: () => void }) {
    const [manufactureQty, setManufactureQty] = useState<string>("");
    const [loading, setLoading] = useState(false);
    const { toast } = useToast();
    const [errorMsg, setErrorMsg] = useState("");

    const remaining = item.quantity_ordered - (item.quantity_manufactured || 0);
    const isCompleted = remaining <= 0;

    const handleMarkManufactured = async () => {
        setErrorMsg("");
        const qty = parseInt(manufactureQty, 10);

        // Validation: must have item.id for PATCH endpoint
        if (!item.id) {
            toast({
                variant: "destructive",
                title: "Missing Item ID",
                description: "Cannot update item - missing item identifier.",
            });
            return;
        }

        // Validation: must be a positive number
        if (isNaN(qty) || qty <= 0) {
            setErrorMsg("Enter > 0");
            return;
        }

        const current = item.quantity_manufactured || 0;
        const newTotal = current + qty;

        // Validation: cannot exceed ordered quantity
        if (newTotal > item.quantity_ordered) {
            setErrorMsg(`Max: ${remaining}`);
            return;
        }

        setLoading(true);
        try {
            // Use item.id (not sku_id) for the PATCH endpoint
            await apiService.orderItems.updateManufactured(item.id, newTotal);

            toast({
                title: "Updated",
                description: `Manufactured ${qty} items. New total: ${newTotal}`,
            });
            setManufactureQty("");
            onRefresh();
        } catch (error: any) {
            console.error(error);
            toast({
                variant: "destructive",
                title: "Update Failed",
                description: error.message || "Failed to update manufactured quantity.",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <TableRow>
            <TableCell>
                <div className="flex flex-col">
                    <span className="font-medium">SKU: {item.sku_id.slice(0, 8)}...</span>
                </div>
            </TableCell>
            <TableCell>{item.quantity_ordered}</TableCell>
            <TableCell>{item.quantity_manufactured || 0}</TableCell>
            <TableCell>{remaining}</TableCell>
            <TableCell>
                {!isCompleted && (
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center space-x-2">
                            <Input
                                type="number"
                                className={`w-20 ${errorMsg ? "border-red-500" : ""}`}
                                placeholder="Qty"
                                value={manufactureQty}
                                onChange={(e) => {
                                    setManufactureQty(e.target.value);
                                    setErrorMsg("");
                                }}
                                max={remaining}
                            />
                            <Button
                                size="sm"
                                onClick={handleMarkManufactured}
                                disabled={!manufactureQty || loading}
                            >
                                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Update"}
                            </Button>
                        </div>
                        {errorMsg && <span className="text-xs text-red-500">{errorMsg}</span>}
                    </div>
                )}
                {isCompleted && <Badge variant="secondary">Completed</Badge>}
            </TableCell>
        </TableRow>
    );
}

function ManufacturingOrderCard({ order, onRefresh }: { order: Order; onRefresh: () => void }) {
    const [isExpanded, setIsExpanded] = useState(false);

    const totalOrdered = order.items?.reduce((acc, i) => acc + i.quantity_ordered, 0) || 0;
    const totalManufactured = order.items?.reduce((acc, i) => acc + (i.quantity_manufactured || 0), 0) || 0;
    const progress = totalOrdered > 0 ? Math.round((totalManufactured / totalOrdered) * 100) : 0;

    return (
        <Card className="w-full">
            <CardHeader className="p-4 cursor-pointer hover:bg-muted/50" onClick={() => setIsExpanded(!isExpanded)}>
                <div className="flex items-center justify-between">
                    <div className="flex flex-col items-start gap-1">
                        <CardTitle className="text-base">{order.client_name || order.client?.name || "Unknown Client"}</CardTitle>
                        <span className="text-xs text-muted-foreground">ID: {order.id.slice(0, 8)}...</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex flex-col items-end">
                            <span className="text-sm">Due: {new Date(order.delivery_date).toLocaleDateString()}</span>
                            <span className="text-xs text-muted-foreground">{progress}% Manufactured</span>
                        </div>
                        <Badge>{order.status}</Badge>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={(e) => { e.stopPropagation(); onRefresh(); }}
                            title="Refresh Order"
                        >
                            <Loader2 className="h-4 w-4" /> {/* Re-using loader icon as refresh somewhat generic */}
                        </Button>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </div>
                </div>
            </CardHeader>
            {isExpanded && (
                <CardContent className="p-4 pt-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Product / SKU</TableHead>
                                <TableHead>Ordered</TableHead>
                                <TableHead>Manufactured</TableHead>
                                <TableHead>Remaining</TableHead>
                                <TableHead>Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {order.items?.map((item) => (
                                <ManufacturingOrderItemRow key={item.id || item.sku_id} item={item} onRefresh={onRefresh} />
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            )}
        </Card>
    );
}

export function ManufacturingOrderList({ orders, onRefresh }: { orders: Order[], onRefresh?: () => void }) {
    if (orders.length === 0) {
        return <div className="text-center py-8 text-muted-foreground">No approved orders found.</div>;
    }

    // Handle missing onRefresh gracefully for now or enforce it
    const handleRefresh = onRefresh || (() => { });

    return (
        <div className="space-y-4">
            {orders.map((order) => (
                <ManufacturingOrderCard key={order.id} order={order} onRefresh={handleRefresh} />
            ))}
        </div>
    );
}
