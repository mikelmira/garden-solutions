import { Order } from "../../types";
import { formatDate } from "@/lib/date-utils";
import Link from "next/link";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "./StatusBadge";

interface Props {
    orders: Order[];
}

export function OrdersTable({ orders }: Props) {
    return (
        <div className="border rounded-md">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Order ID</TableHead>
                        <TableHead>Client</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                        <TableHead>Action</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {orders.map(order => (
                        <TableRow key={order.id}>
                            <TableCell className="font-mono text-xs">{order.id.slice(0, 8)}...</TableCell>
                            <TableCell>{order.client?.name || order.client_name || "N/A"}</TableCell>
                            <TableCell>{formatDate(order.created_at)}</TableCell>
                            <TableCell>
                                <StatusBadge status={order.status} />
                            </TableCell>
                            <TableCell className="text-right">R {(order.total_price_rands ?? 0).toFixed(2)}</TableCell>
                            <TableCell>
                                <Button variant="link" asChild className="p-0 h-auto">
                                    <Link href={`/orders/${order.id}`}>View</Link>
                                </Button>
                            </TableCell>
                        </TableRow>
                    ))}
                    {orders.length === 0 && (
                        <TableRow>
                            <TableCell colSpan={6} className="h-24 text-center">
                                No orders found.
                            </TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
        </div>
    );
}
