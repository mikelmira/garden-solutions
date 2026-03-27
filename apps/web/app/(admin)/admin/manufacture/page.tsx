"use client";

import { useEffect, useState, useMemo } from "react";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2, ChevronDown, ChevronRight, Check, Calendar, AlertCircle, Plus, RefreshCw, Send } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { ManufacturingDay, OutstandingSKUDemand } from "@/types";

export default function AdminManufacturePage() {
    const { toast } = useToast();
    const [loading, setLoading] = useState(true);
    const [outstandingSkus, setOutstandingSkus] = useState<OutstandingSKUDemand[]>([]);
    const [expandedSkus, setExpandedSkus] = useState<Set<string>>(new Set());

    // Today's plan state
    const [todayPlan, setTodayPlan] = useState<ManufacturingDay | null>(null);

    // Track planned quantity input per SKU (for creating/adding to plan)
    const [planInput, setPlanInput] = useState<Record<string, number>>({});
    const [submitting, setSubmitting] = useState(false);
    const [addingSkuId, setAddingSkuId] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            // Fetch outstanding demand and today's plan in parallel
            const [demandResponse, planResponse] = await Promise.all([
                apiService.manufacturing.getOutstandingDemand(),
                apiService.manufacturing.getTodayPlan(),
            ]);
            setOutstandingSkus(demandResponse.skus);
            setTodayPlan(planResponse);
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load data", description: error.message });
        } finally {
            setLoading(false);
        }
    };

    const toggleExpand = (skuId: string) => {
        const next = new Set(expandedSkus);
        if (next.has(skuId)) {
            next.delete(skuId);
        } else {
            next.add(skuId);
        }
        setExpandedSkus(next);
    };

    const handlePlanQuantityChange = (skuId: string, value: number, max: number) => {
        const clamped = Math.max(0, Math.min(value, max));
        setPlanInput(prev => ({ ...prev, [skuId]: clamped }));
    };

    const handleCreatePlan = async () => {
        const itemsToInclude = outstandingSkus
            .filter(sku => (planInput[sku.sku_id] || 0) > 0)
            .map(sku => ({
                sku_id: sku.sku_id,
                quantity_planned: planInput[sku.sku_id],
            }));

        if (itemsToInclude.length === 0) {
            toast({ variant: "destructive", title: "No items selected", description: "Enter quantities to include in today's plan." });
            return;
        }

        try {
            setSubmitting(true);
            const plan = await apiService.manufacturing.createPlan({
                items: itemsToInclude,
            });
            setTodayPlan(plan);
            setPlanInput({});
            toast({ title: "Plan Created", description: `Today's moulding plan created with ${itemsToInclude.length} SKUs.` });
            // Reload to refresh outstanding demand
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to create plan", description: error.message });
        } finally {
            setSubmitting(false);
        }
    };

    const handleAddSingleSku = async (sku: OutstandingSKUDemand) => {
        const qty = planInput[sku.sku_id] || sku.total_outstanding;
        if (qty <= 0) {
            toast({ variant: "destructive", title: "Invalid quantity", description: "Enter a quantity greater than 0." });
            return;
        }

        try {
            setAddingSkuId(sku.sku_id);
            const plan = await apiService.manufacturing.addItemsToPlan({
                items: [{ sku_id: sku.sku_id, quantity_planned: qty }],
            });
            setTodayPlan(plan);
            setPlanInput(prev => {
                const next = { ...prev };
                delete next[sku.sku_id];
                return next;
            });
            toast({ title: "Added to Plan", description: `${qty}x ${sku.product_name} added to today's moulding plan.` });
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to add", description: error.message });
        } finally {
            setAddingSkuId(null);
        }
    };

    const handleAddAllOutstanding = async () => {
        if (remainingOutstandingSkus.length === 0) return;

        const itemsToAdd = remainingOutstandingSkus.map(sku => ({
            sku_id: sku.sku_id,
            quantity_planned: planInput[sku.sku_id] || sku.total_outstanding,
        }));

        try {
            setSubmitting(true);
            const plan = await apiService.manufacturing.addItemsToPlan({
                items: itemsToAdd,
            });
            setTodayPlan(plan);
            setPlanInput({});
            toast({ title: "All Added", description: `${itemsToAdd.length} SKUs added to today's moulding plan.` });
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to add all", description: error.message });
        } finally {
            setSubmitting(false);
        }
    };

    const handleSelectAll = () => {
        const newInput: Record<string, number> = {};
        outstandingSkus.forEach(sku => {
            newInput[sku.sku_id] = sku.total_outstanding;
        });
        setPlanInput(newInput);
    };

    const handleClearSelection = () => {
        setPlanInput({});
    };

    const totalOutstanding = useMemo(() =>
        outstandingSkus.reduce((sum, sku) => sum + sku.total_outstanding, 0),
        [outstandingSkus]
    );

    const totalPlanned = useMemo(() =>
        Object.values(planInput).reduce((sum, qty) => sum + (qty || 0), 0),
        [planInput]
    );

    // Filter out SKUs that are already in today's plan
    const remainingOutstandingSkus = useMemo(() => {
        if (!todayPlan) return outstandingSkus;
        const plannedSkuIds = new Set(todayPlan.items.map(item => item.sku_id));
        return outstandingSkus.filter(sku => !plannedSkuIds.has(sku.sku_id));
    }, [outstandingSkus, todayPlan]);

    // Calculate today's plan progress
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
                    <h1 className="text-2xl font-bold tracking-tight">Manufacturing Overview</h1>
                    <p className="text-muted-foreground">Plan daily moulding and track completion.</p>
                </div>
                <Button variant="outline" onClick={loadData} disabled={loading}>
                    <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                    Refresh
                </Button>
            </div>

            {/* Today's Plan Section */}
            {todayPlan && (
                <Card className="border-green-200 bg-green-50/30">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
                                    <Calendar className="h-5 w-5 text-green-700" />
                                </div>
                                <div>
                                    <CardTitle className="text-lg">Today's Moulding Plan</CardTitle>
                                    <CardDescription>
                                        {new Date(todayPlan.plan_date).toLocaleDateString("en-ZA", {
                                            weekday: "long",
                                            year: "numeric",
                                            month: "long",
                                            day: "numeric"
                                        })}
                                    </CardDescription>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-2xl font-bold text-green-700">
                                    {todayPlan.total_completed} / {todayPlan.total_planned}
                                </div>
                                <div className="text-xs text-muted-foreground">units completed</div>
                            </div>
                        </div>
                        <Progress value={planProgress} className="h-3 mt-4" />
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {todayPlan.items.map(item => {
                                const itemProgress = item.quantity_planned > 0
                                    ? (item.quantity_completed / item.quantity_planned) * 100
                                    : 0;
                                const isComplete = item.quantity_completed >= item.quantity_planned;

                                return (
                                    <div
                                        key={item.id}
                                        className={cn(
                                            "flex items-center justify-between p-3 rounded-lg border",
                                            isComplete ? "bg-green-100/50 border-green-200" : "bg-white"
                                        )}
                                    >
                                        <div className="flex items-center gap-3 flex-1 min-w-0">
                                            {isComplete && (
                                                <Check className="h-5 w-5 text-green-600 flex-shrink-0" />
                                            )}
                                            <div className="min-w-0">
                                                <div className="font-medium truncate">{item.display_string}</div>
                                                <div className="text-xs text-muted-foreground font-mono">{item.sku_code}</div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4 flex-shrink-0">
                                            <div className="w-24">
                                                <Progress value={itemProgress} className="h-2" />
                                            </div>
                                            <div className="text-right w-20">
                                                <span className="font-bold">{item.quantity_completed}</span>
                                                <span className="text-muted-foreground"> / {item.quantity_planned}</span>
                                            </div>
                                            {!isComplete && (
                                                <Badge variant="outline" className="text-orange-600 border-orange-200">
                                                    {item.remaining} left
                                                </Badge>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Outstanding Demand Section - Show when no plan exists */}
            {!todayPlan && (
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle>Outstanding Demand</CardTitle>
                                <CardDescription>
                                    {outstandingSkus.length} SKUs with {totalOutstanding} total units needed
                                </CardDescription>
                            </div>
                            <div className="flex items-center gap-2">
                                {outstandingSkus.length > 0 && (
                                    <>
                                        <Button variant="outline" size="sm" onClick={handleSelectAll}>
                                            Select All
                                        </Button>
                                        <Button variant="outline" size="sm" onClick={handleClearSelection}>
                                            Clear
                                        </Button>
                                        <Button
                                            onClick={handleCreatePlan}
                                            disabled={submitting || totalPlanned === 0}
                                            className="gap-2"
                                        >
                                            {submitting ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <Plus className="h-4 w-4" />
                                            )}
                                            Create Today's Plan ({totalPlanned})
                                        </Button>
                                    </>
                                )}
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {outstandingSkus.length === 0 ? (
                            <div className="text-center py-12 border rounded-lg bg-muted/20 text-muted-foreground">
                                <Check className="h-12 w-12 mx-auto mb-3 opacity-50 text-green-500" />
                                <p>All clear!</p>
                                <p className="text-sm">No approved orders waiting for manufacturing.</p>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                {outstandingSkus.map(sku => {
                                    const isExpanded = expandedSkus.has(sku.sku_id);
                                    const currentInput = planInput[sku.sku_id] || 0;

                                    return (
                                        <div key={sku.sku_id} className="border rounded-lg overflow-hidden">
                                            <div
                                                className="flex items-center justify-between p-4 bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors"
                                                onClick={() => toggleExpand(sku.sku_id)}
                                            >
                                                <div className="flex items-center gap-3">
                                                    {isExpanded ? (
                                                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                                                    ) : (
                                                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                                    )}
                                                    <div>
                                                        <div className="font-medium">{sku.product_name}</div>
                                                        <div className="text-xs text-muted-foreground">
                                                            <span className="font-mono">{sku.sku_code}</span>
                                                            <span className="mx-2">•</span>
                                                            <span>{sku.size} {sku.color}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-4">
                                                    <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                                                        <span className="text-sm text-muted-foreground">Plan:</span>
                                                        <Input
                                                            type="number"
                                                            className="w-20 h-8"
                                                            value={currentInput || ""}
                                                            placeholder="0"
                                                            onChange={e => handlePlanQuantityChange(
                                                                sku.sku_id,
                                                                parseInt(e.target.value) || 0,
                                                                sku.total_outstanding
                                                            )}
                                                            max={sku.total_outstanding}
                                                            min={0}
                                                        />
                                                        <span className="text-sm text-muted-foreground">/ {sku.total_outstanding}</span>
                                                    </div>
                                                    <Badge variant="secondary" className="font-mono">
                                                        {sku.total_outstanding} needed
                                                    </Badge>
                                                </div>
                                            </div>

                                            {isExpanded && (
                                                <div className="p-4 border-t bg-background">
                                                    <div className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                                                        Contributing Orders
                                                    </div>
                                                    <div className="space-y-2">
                                                        {sku.breakdown.map((item, idx) => (
                                                            <div
                                                                key={`${item.order_id}-${idx}`}
                                                                className="flex items-center justify-between py-2 px-3 bg-muted/20 rounded text-sm"
                                                            >
                                                                <div className="flex items-center gap-2">
                                                                    <Badge variant="outline" className="text-xs">
                                                                        Order #{item.order_id.slice(0, 8)}
                                                                    </Badge>
                                                                    <span className="font-medium">
                                                                        {item.client_or_store_label}
                                                                    </span>
                                                                    <span className="text-muted-foreground text-xs">
                                                                        ({new Date(item.order_created_at).toLocaleDateString()})
                                                                    </span>
                                                                </div>
                                                                <div className="font-bold text-orange-600">
                                                                    {item.quantity_outstanding} outstanding
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Remaining Outstanding Demand - Show when plan exists */}
            {todayPlan && remainingOutstandingSkus.length > 0 && (
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <AlertCircle className="h-5 w-5 text-orange-500" />
                                <div>
                                    <CardTitle className="text-base">Remaining Outstanding Demand</CardTitle>
                                    <CardDescription>
                                        {remainingOutstandingSkus.length} SKUs not yet in today's plan
                                    </CardDescription>
                                </div>
                            </div>
                            <Button
                                onClick={handleAddAllOutstanding}
                                disabled={submitting}
                                size="sm"
                                className="gap-2"
                            >
                                {submitting ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Send className="h-4 w-4" />
                                )}
                                Add All to Plan
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {remainingOutstandingSkus.map(sku => {
                                const isExpanded = expandedSkus.has(sku.sku_id);
                                const currentInput = planInput[sku.sku_id] ?? sku.total_outstanding;
                                const isAdding = addingSkuId === sku.sku_id;

                                return (
                                    <div key={sku.sku_id} className="border rounded-lg overflow-hidden">
                                        <div className="flex items-center justify-between p-3 bg-muted/20">
                                            <div
                                                className="flex items-center gap-3 cursor-pointer flex-1"
                                                onClick={() => toggleExpand(sku.sku_id)}
                                            >
                                                {isExpanded ? (
                                                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                                                ) : (
                                                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                                                )}
                                                <div>
                                                    <div className="font-medium text-sm">{sku.product_name}</div>
                                                    <div className="text-xs text-muted-foreground">
                                                        <span className="font-mono">{sku.sku_code}</span>
                                                        <span className="mx-2">•</span>
                                                        <span>{sku.size} {sku.color}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <div className="flex items-center gap-2">
                                                    <Input
                                                        type="number"
                                                        className="w-16 h-8 text-center"
                                                        value={currentInput}
                                                        onChange={e => handlePlanQuantityChange(
                                                            sku.sku_id,
                                                            parseInt(e.target.value) || 0,
                                                            sku.total_outstanding
                                                        )}
                                                        max={sku.total_outstanding}
                                                        min={1}
                                                    />
                                                    <span className="text-xs text-muted-foreground">/ {sku.total_outstanding}</span>
                                                </div>
                                                <Button
                                                    size="sm"
                                                    onClick={() => handleAddSingleSku(sku)}
                                                    disabled={isAdding || submitting}
                                                    className="gap-1"
                                                >
                                                    {isAdding ? (
                                                        <Loader2 className="h-3 w-3 animate-spin" />
                                                    ) : (
                                                        <Send className="h-3 w-3" />
                                                    )}
                                                    Add
                                                </Button>
                                            </div>
                                        </div>

                                        {isExpanded && (
                                            <div className="p-3 border-t bg-background">
                                                <div className="space-y-1">
                                                    {sku.breakdown.map((item, idx) => (
                                                        <div
                                                            key={`${item.order_id}-${idx}`}
                                                            className="flex items-center justify-between py-1 px-2 text-xs"
                                                        >
                                                            <div className="flex items-center gap-2">
                                                                <span className="font-mono text-muted-foreground">
                                                                    #{item.order_id.slice(0, 8)}
                                                                </span>
                                                                <span>{item.client_or_store_label}</span>
                                                            </div>
                                                            <span className="text-orange-600 font-medium">
                                                                {item.quantity_outstanding}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
