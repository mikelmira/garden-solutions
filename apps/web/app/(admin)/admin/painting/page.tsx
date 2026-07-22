"use client";

import { useEffect, useState, useMemo } from "react";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2, Calendar, Plus, RefreshCw, Brush } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { PaintingDay, PaintingDemandItem } from "@/types";

export default function AdminPaintingPage() {
    const { toast } = useToast();
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [outstandingItems, setOutstandingItems] = useState<PaintingDemandItem[]>([]);
    const [todayPlan, setTodayPlan] = useState<PaintingDay | null>(null);
    // Per-row planned quantity input (keyed by order_item_id)
    const [planInput, setPlanInput] = useState<Record<string, number>>({});
    const [addingItemId, setAddingItemId] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [demand, plan] = await Promise.all([
                apiService.painting.getOutstanding(),
                apiService.painting.getTodayPlan(),
            ]);
            setOutstandingItems(demand.items);
            setTodayPlan(plan);
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load data", description: error.message });
        } finally {
            setLoading(false);
        }
    };

    const handlePlanQtyChange = (orderItemId: string, value: number, max: number) => {
        const clamped = Math.max(0, Math.min(value, max));
        setPlanInput(prev => ({ ...prev, [orderItemId]: clamped }));
    };

    const handleSelectAll = () => {
        // Only the rows the user can actually see (items already on today's
        // plan are hidden from the list and must not be re-selected).
        const next: Record<string, number> = {};
        remainingOutstandingItems.forEach(it => { next[it.order_item_id] = it.quantity_outstanding; });
        setPlanInput(next);
    };

    const handleClear = () => setPlanInput({});

    // Effective quantity per row: what the input displays and what every
    // action uses. Untouched rows default to the full outstanding quantity;
    // a typed 0 excludes the row.
    const effectiveQty = (it: PaintingDemandItem): number =>
        planInput[it.order_item_id] ?? it.quantity_outstanding;

    const handleCreatePlan = async () => {
        const items = remainingOutstandingItems
            .map(it => ({ order_item_id: it.order_item_id, quantity_planned: effectiveQty(it) }))
            .filter(it => it.quantity_planned > 0);

        if (items.length === 0) {
            toast({ variant: "destructive", title: "No items selected", description: "Enter quantities to include in today's plan." });
            return;
        }
        try {
            setSubmitting(true);
            const plan = await apiService.painting.createPlan({ items });
            setTodayPlan(plan);
            setPlanInput({});
            toast({ title: "Plan Created", description: `Today's painting plan created with ${items.length} item${items.length === 1 ? "" : "s"}.` });
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to create plan", description: error.message });
        } finally {
            setSubmitting(false);
        }
    };

    const handleAddOne = async (it: PaintingDemandItem) => {
        const qty = effectiveQty(it);
        if (qty <= 0) {
            toast({ variant: "destructive", title: "Invalid quantity", description: "Enter a quantity greater than 0." });
            return;
        }
        try {
            setAddingItemId(it.order_item_id);
            const plan = await apiService.painting.addItemsToPlan({
                items: [{ order_item_id: it.order_item_id, quantity_planned: qty }],
            });
            setTodayPlan(plan);
            setPlanInput(prev => { const next = { ...prev }; delete next[it.order_item_id]; return next; });
            toast({ title: "Added to Plan", description: `${qty}× ${it.product_name} added.` });
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to add", description: error.message });
        } finally {
            setAddingItemId(null);
        }
    };

    const handleAddAllOutstanding = async () => {
        const remaining = remainingOutstandingItems;
        if (remaining.length === 0) return;
        const items = remaining
            .map(it => ({
                order_item_id: it.order_item_id,
                quantity_planned: effectiveQty(it),
            }))
            .filter(it => it.quantity_planned > 0);
        if (items.length === 0) {
            toast({ variant: "destructive", title: "Nothing to add", description: "All visible items have quantity 0." });
            return;
        }
        try {
            setSubmitting(true);
            const plan = await apiService.painting.addItemsToPlan({ items });
            setTodayPlan(plan);
            setPlanInput({});
            toast({ title: "All Added", description: `${items.length} items added to today's painting plan.` });
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to add all", description: error.message });
        } finally {
            setSubmitting(false);
        }
    };

    // Hide items already on today's plan from "outstanding"
    const remainingOutstandingItems = useMemo(() => {
        if (!todayPlan) return outstandingItems;
        const planned = new Set(todayPlan.items.map(i => i.order_item_id));
        return outstandingItems.filter(it => !planned.has(it.order_item_id));
    }, [outstandingItems, todayPlan]);

    // Header total must match the visible list, not the full demand set.
    const totalOutstanding = useMemo(
        () => remainingOutstandingItems.reduce((s, it) => s + it.quantity_outstanding, 0),
        [remainingOutstandingItems]
    );

    // Sum of effective quantities over visible rows — drives the action bar.
    const totalPlanned = useMemo(
        () => remainingOutstandingItems.reduce((s, it) => s + effectiveQty(it), 0),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [remainingOutstandingItems, planInput]
    );

    const planProgress = todayPlan && todayPlan.total_planned > 0
        ? (todayPlan.total_completed / todayPlan.total_planned) * 100
        : 0;

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Painting Overview</h1>
                    <p className="text-muted-foreground">Plan today's painting (per order) and track completion.</p>
                </div>
                <Button variant="outline" onClick={loadData} disabled={loading}>
                    <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                    Refresh
                </Button>
            </div>

            {/* Today's plan summary */}
            {todayPlan && (
                <Card className="border-sky-200 bg-sky-50/40">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="flex items-center gap-2">
                                    <Calendar className="h-5 w-5 text-sky-600" />
                                    Today's Painting Plan
                                </CardTitle>
                                <CardDescription>
                                    {todayPlan.items.length} item{todayPlan.items.length === 1 ? "" : "s"} · {todayPlan.total_planned} units planned
                                </CardDescription>
                            </div>
                            <div className="text-right">
                                <div className="text-2xl font-bold text-sky-700">
                                    {todayPlan.total_completed} / {todayPlan.total_planned}
                                </div>
                                <div className="text-xs text-muted-foreground">units painted</div>
                            </div>
                        </div>
                        <Progress value={planProgress} className="h-2 mt-3" />
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {todayPlan.items.map(item => {
                                const isDone = item.quantity_completed >= item.quantity_planned;
                                return (
                                    <div
                                        key={item.id}
                                        className={cn(
                                            "flex items-center justify-between rounded-md border px-3 py-2 text-sm",
                                            isDone && "bg-green-50 border-green-200"
                                        )}
                                    >
                                        <div className="min-w-0">
                                            <div className="font-medium truncate">{item.display_string}</div>
                                            <div className="text-xs text-muted-foreground truncate">
                                                {item.client_or_store_label}
                                                {item.customer_name ? ` · ${item.customer_name}` : ""}
                                            </div>
                                        </div>
                                        <Badge variant="outline" className={cn(isDone && "border-green-300 text-green-700")}>
                                            {item.quantity_completed} / {item.quantity_planned}
                                        </Badge>
                                    </div>
                                );
                            })}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Outstanding demand → plan builder */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between gap-4">
                        <div>
                            <CardTitle className="flex items-center gap-2">
                                <Brush className="h-5 w-5 text-amber-600" />
                                Outstanding paint demand
                            </CardTitle>
                            <CardDescription>
                                {remainingOutstandingItems.length} item{remainingOutstandingItems.length === 1 ? "" : "s"} ready to paint · {totalOutstanding} units total
                            </CardDescription>
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={handleSelectAll} disabled={remainingOutstandingItems.length === 0}>Select all</Button>
                            <Button variant="outline" size="sm" onClick={handleClear} disabled={totalPlanned === 0}>Clear</Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    {remainingOutstandingItems.length === 0 ? (
                        <div className="text-sm text-muted-foreground py-6 text-center">
                            Nothing waiting to be painted right now.
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {remainingOutstandingItems.map(it => {
                                const planned = effectiveQty(it);
                                return (
                                    <div key={it.order_item_id} className="flex items-center justify-between gap-3 border rounded-md px-3 py-2">
                                        <div className="min-w-0 flex-1">
                                            <div className="font-medium truncate">{it.display_string}</div>
                                            <div className="text-xs text-muted-foreground truncate">
                                                {it.client_or_store_label}
                                                {it.customer_name ? ` · ${it.customer_name}` : ""}
                                                <span className="ml-2 font-mono">{it.sku_code}</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Input
                                                type="number"
                                                min={0}
                                                max={it.quantity_outstanding}
                                                value={planned}
                                                onChange={e => handlePlanQtyChange(it.order_item_id, Number(e.target.value), it.quantity_outstanding)}
                                                className="w-20"
                                            />
                                            <span className="text-xs text-muted-foreground whitespace-nowrap">/ {it.quantity_outstanding}</span>
                                            {todayPlan ? (
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => handleAddOne(it)}
                                                    disabled={addingItemId === it.order_item_id}
                                                >
                                                    {addingItemId === it.order_item_id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
                                                    Add
                                                </Button>
                                            ) : null}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Action bar */}
                    <div className="pt-4 mt-4 border-t flex items-center justify-between gap-3">
                        <div className="text-sm text-muted-foreground">
                            {totalPlanned > 0 ? `${totalPlanned} units selected` : "Select items to add to today's plan"}
                        </div>
                        <div className="flex gap-2">
                            {!todayPlan ? (
                                <Button onClick={handleCreatePlan} disabled={submitting || totalPlanned === 0}>
                                    {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                    Create today's plan
                                </Button>
                            ) : (
                                <Button onClick={handleAddAllOutstanding} disabled={submitting || remainingOutstandingItems.length === 0}>
                                    {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                                    Add all remaining
                                </Button>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
