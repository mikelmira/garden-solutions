import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Order } from "@/types";
import { Package, CheckCircle, Clock } from "lucide-react";

interface ManufacturingStatsProps {
    orders: Order[];
}

export function ManufacturingStats({ orders }: ManufacturingStatsProps) {
    const totalOrders = orders.length;

    // Calculate total items stats
    let totalItemsOrdered = 0;
    let totalItemsManufactured = 0;

    orders.forEach(order => {
        order.items?.forEach(item => {
            totalItemsOrdered += item.quantity_ordered;
            totalItemsManufactured += item.quantity_manufactured || 0;
        });
    });

    const remainingItems = totalItemsOrdered - totalItemsManufactured;
    const progress = totalItemsOrdered > 0
        ? Math.round((totalItemsManufactured / totalItemsOrdered) * 100)
        : 0;

    return (
        <>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Orders</CardTitle>
                    <Package className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{totalOrders}</div>
                    <p className="text-xs text-muted-foreground">Approved for production</p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Items Remaining</CardTitle>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{remainingItems}</div>
                    <p className="text-xs text-muted-foreground">To be manufactured</p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Production Progress</CardTitle>
                    <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{progress}%</div>
                    <p className="text-xs text-muted-foreground">{totalItemsManufactured} / {totalItemsOrdered} items done</p>
                </CardContent>
            </Card>
        </>
    );
}
