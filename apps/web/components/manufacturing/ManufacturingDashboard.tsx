"use client";

import { useState } from "react";
import { Order } from "@/types";
import { ManufacturingStats } from "./ManufacturingStats";
import { ManufacturingOrderList } from "./ManufacturingOrderList";
import { Input } from "@/components/ui/input";
import { apiService } from "@/lib/api";

interface ManufacturingDashboardProps {
    initialOrders: Order[];
}

export function ManufacturingDashboard({ initialOrders }: ManufacturingDashboardProps) {
    const [orders, setOrders] = useState<Order[]>(initialOrders);
    const [search, setSearch] = useState("");

    const fetchOrders = async () => {
        try {
            // Fetch ALL orders first (API doesn't support generic filtering in `list` type yet, 
            // but we can pass params if updated. Based on api.ts list takes optional filters string?)
            // Actually api.ts list takes `{ status?: string }`
            // Manufacturing wants "Approved" orders.
            const data = await apiService.orders.list({ status: "Approved" });
            setOrders(data);
        } catch (e) {
            console.error("Failed to load approved orders", e);
        }
    };

    // Load initial orders if not provided or just rely on initialOrders prop initially?
    // The requirement says "refresh the queue view (re-fetch)".
    // So we should probably use initialOrders as initial state, but allow updates.
    // If I use `initialOrders` prop, `fetchOrders` will update local state.

    const handleRefresh = async () => {
        await fetchOrders();
    };

    const filteredOrders = orders.filter((order) => {
        const clientNameMatch = order.client_name?.toLowerCase().includes(search.toLowerCase()) ||
            order.client?.name.toLowerCase().includes(search.toLowerCase());
        const idMatch = order.id.toLowerCase().includes(search.toLowerCase());
        return clientNameMatch || idMatch;
    });

    return (
        <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <ManufacturingStats orders={orders} />
            </div>

            <div className="flex items-center space-x-2">
                <Input
                    placeholder="Search by Client or Order ID..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="max-w-sm"
                />
            </div>

            <ManufacturingOrderList orders={filteredOrders} onRefresh={handleRefresh} />
        </div>
    );
}
