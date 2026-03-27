"use client";

import { apiService } from "@/lib/api";
import { Order } from "@/types";
import { ManufacturingDashboard } from "@/components/manufacturing/ManufacturingDashboard";
import { Loader2, AlertCircle, LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";

export default function ManufacturingPage() {
    const { user, logout } = useAuth();
    const [orders, setOrders] = useState<Order[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const load = async () => {
        setLoading(true);
        setError("");
        try {
            const data = await apiService.orders.list({ status: "Approved" });
            setOrders(data);
        } catch (e) {
            console.error("Failed to load approved orders", e);
            setError("Failed to load manufacturing queue.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, []);

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex flex-col h-[50vh] items-center justify-center gap-4">
                <AlertCircle className="h-10 w-10 text-red-500" />
                <p className="text-muted-foreground">{error}</p>
                <Button onClick={load} variant="outline">Retry</Button>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-6 space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Manufacturing Dashboard</h1>
                    <p className="text-muted-foreground">Production queue for confirmed orders.</p>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-sm text-muted-foreground">Hello, {user?.full_name}</span>
                    <Button variant="outline" onClick={logout} size="sm" className="gap-2 text-red-600 hover:text-red-700 hover:bg-red-50">
                        <LogOut size={14} /> Logout
                    </Button>
                </div>
            </div>

            <ManufacturingDashboard initialOrders={orders || []} />
        </div>
    );
}
