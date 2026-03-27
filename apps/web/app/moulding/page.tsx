"use client";

import { useState, useEffect } from "react";
import { apiService } from "@/lib/api";
import { ManufacturingDay, ManufacturingDayItem } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Check, Loader2, ArrowRight, Factory, Calendar, Plus, Minus, LogOut } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

type Screen = "gate" | "list";

export default function MouldingPage() {
    const { toast } = useToast();
    const [screen, setScreen] = useState<Screen>("gate");
    const [loading, setLoading] = useState(false);

    // Auth State - simple code-based access with backend validation
    const [accessCode, setAccessCode] = useState("");
    const [factoryCode, setFactoryCode] = useState<string | null>(null);

    // Data State
    const [plan, setPlan] = useState<ManufacturingDay | null>(null);
    const [updatingItem, setUpdatingItem] = useState<string | null>(null);

    useEffect(() => {
        const savedCode = localStorage.getItem("garden_moulding_code");
        if (savedCode) {
            verifyCode(savedCode, true);
        }
    }, []);

    useEffect(() => {
        if (factoryCode && screen === "list") {
            loadTodayPlan();
        }
    }, [factoryCode, screen]);

    const verifyCode = async (code: string, silent = false) => {
        if (!code) return;
        setLoading(true);

        try {
            // Validate code with backend
            const data = await apiService.moulding.verifyCode(code);
            if (data.valid) {
                localStorage.setItem("garden_moulding_code", data.code);
                setFactoryCode(data.code);
                setScreen("list");
            }
        } catch (error: any) {
            if (!silent) {
                toast({ variant: "destructive", title: "Invalid Code", description: "Please enter a valid factory code." });
            }
            localStorage.removeItem("garden_moulding_code");
        } finally {
            setLoading(false);
        }
    };

    const loadTodayPlan = async () => {
        if (!factoryCode) return;
        setLoading(true);
        try {
            const data = await apiService.moulding.getTodayPlan(factoryCode);
            setPlan(data);
        } catch (error: any) {
            // No plan for today is expected sometimes
            if (error.response?.status === 404 || error.message?.includes("404") || error.message?.includes("No manufacturing plan")) {
                setPlan(null);
            } else {
                toast({ variant: "destructive", title: "Network Error", description: "Failed to load today's plan." });
            }
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateCompletion = async (item: ManufacturingDayItem, delta: number) => {
        if (!factoryCode) return;
        const newQty = Math.max(0, Math.min(item.quantity_planned, item.quantity_completed + delta));
        if (newQty === item.quantity_completed) return;

        setUpdatingItem(item.id);
        try {
            await apiService.moulding.updateItemCompletion(item.id, newQty, factoryCode);

            // Update local state
            setPlan(prev => {
                if (!prev) return null;
                const updatedItems = prev.items.map(i =>
                    i.id === item.id ? { ...i, quantity_completed: newQty, remaining: i.quantity_planned - newQty } : i
                );
                const total_completed = updatedItems.reduce((sum, i) => sum + i.quantity_completed, 0);
                return { ...prev, items: updatedItems, total_completed };
            });

            if (newQty === item.quantity_planned) {
                toast({ title: "Complete!", description: `${item.display_string} fully completed.` });
            }
        } catch (error: any) {
            toast({ variant: "destructive", title: "Update Failed", description: error.message || "Could not update completion." });
        } finally {
            setUpdatingItem(null);
        }
    };

    const handleCompleteItem = async (item: ManufacturingDayItem) => {
        if (!factoryCode) return;
        if (item.quantity_completed >= item.quantity_planned) return;

        setUpdatingItem(item.id);
        try {
            await apiService.moulding.updateItemCompletion(item.id, item.quantity_planned, factoryCode);

            // Update local state
            setPlan(prev => {
                if (!prev) return null;
                const updatedItems = prev.items.map(i =>
                    i.id === item.id ? { ...i, quantity_completed: i.quantity_planned, remaining: 0 } : i
                );
                const total_completed = updatedItems.reduce((sum, i) => sum + i.quantity_completed, 0);
                return { ...prev, items: updatedItems, total_completed };
            });

            toast({ title: "Complete!", description: `${item.display_string} marked as fully completed.` });
        } catch (error: any) {
            toast({ variant: "destructive", title: "Update Failed", description: error.message || "Could not update completion." });
        } finally {
            setUpdatingItem(null);
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
                        <h1 className="text-3xl font-heading font-semibold tracking-tight text-foreground">Moulding Portal</h1>
                        <p className="text-muted-foreground">Enter your factory code to access today's manufacturing plan</p>
                    </div>
                    <Card className="border shadow-xl shadow-black/5">
                        <CardContent className="pt-6 space-y-4">
                            <Input
                                className="text-center text-lg tracking-widest font-mono uppercase h-12"
                                value={accessCode}
                                onChange={e => setAccessCode(e.target.value)}
                                placeholder="FACTORY CODE"
                                onKeyDown={e => e.key === "Enter" && verifyCode(accessCode)}
                            />
                            <Button
                                className="w-full h-12 text-base font-medium bg-amber-600 hover:bg-amber-700"
                                onClick={() => verifyCode(accessCode)}
                                disabled={loading || !accessCode}
                            >
                                {loading && <Loader2 className="mr-2 h-5 w-5 animate-spin" />}
                                Access Manufacturing
                                {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    // Calculate overall progress (guard division by zero)
    const overallProgress = plan && plan.total_planned > 0
        ? (plan.total_completed / plan.total_planned) * 100
        : 0;

    // List Screen
    return (
        <div className="min-h-screen pb-8 bg-background">
            {/* Header */}
            <div className="bg-background/95 backdrop-blur-lg border-b sticky top-0 z-10">
                <div className="px-6 py-4 max-w-lg mx-auto">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 bg-white rounded-xl flex items-center justify-center border">
                                <img src="/logo.avif" alt="Garden Solutions" className="h-6 w-6 object-contain" />
                            </div>
                            <div>
                                <div className="font-heading font-semibold text-lg text-foreground">Moulding</div>
                                <div className="text-sm text-muted-foreground">Today's Plan</div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="flex items-center gap-2 bg-muted px-3 py-2 rounded-lg">
                                <Calendar size={16} className="text-muted-foreground" />
                                <span className="text-sm font-medium">{new Date().toLocaleDateString()}</span>
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-9 w-9 text-muted-foreground hover:text-foreground"
                                onClick={() => {
                                    localStorage.removeItem("garden_moulding_code");
                                    setFactoryCode(null);
                                    setPlan(null);
                                    setAccessCode("");
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

                {!plan && !loading && (
                    <div className="text-center py-16 px-6">
                        <div className="h-16 w-16 mx-auto bg-muted rounded-2xl flex items-center justify-center mb-4">
                            <Factory className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <h3 className="font-semibold text-foreground mb-1">No Plan Today</h3>
                        <p className="text-sm text-muted-foreground">No manufacturing plan has been created for today yet.</p>
                        <Button
                            variant="outline"
                            className="mt-4"
                            onClick={loadTodayPlan}
                        >
                            Refresh
                        </Button>
                    </div>
                )}

                {plan && !loading && (
                    <>
                        {/* Summary Card */}
                        <Card className="border-amber-200 bg-amber-50/50">
                            <CardHeader className="pb-3">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">Overall Progress</CardTitle>
                                    <div className="text-right">
                                        <div className="text-2xl font-bold text-amber-700">
                                            {plan.total_completed} / {plan.total_planned}
                                        </div>
                                        <div className="text-xs text-muted-foreground">units completed</div>
                                    </div>
                                </div>
                                <Progress
                                    value={overallProgress}
                                    className="h-3 mt-3"
                                />
                            </CardHeader>
                        </Card>

                        {/* SKU Items */}
                        <div className="space-y-3">
                            {plan.items.map(item => {
                                const isComplete = item.quantity_completed >= item.quantity_planned;
                                const progress = item.quantity_planned > 0
                                    ? (item.quantity_completed / item.quantity_planned) * 100
                                    : 0;
                                const isUpdating = updatingItem === item.id;

                                return (
                                    <Card
                                        key={item.id}
                                        className={cn(
                                            "transition-all",
                                            isComplete && "bg-green-50/50 border-green-200"
                                        )}
                                    >
                                        <CardContent className="pt-4 pb-4">
                                            <div className="space-y-3">
                                                {/* SKU Info */}
                                                <div className="flex items-start justify-between">
                                                    <div className="flex-1 min-w-0">
                                                        <div className="font-medium text-foreground">
                                                            {item.display_string}
                                                        </div>
                                                        <div className="text-xs text-muted-foreground font-mono">
                                                            {item.sku_code}
                                                        </div>
                                                    </div>
                                                    {isComplete && (
                                                        <Badge className="bg-green-600 text-white">
                                                            <Check className="h-3 w-3 mr-1" />
                                                            Done
                                                        </Badge>
                                                    )}
                                                </div>

                                                {/* Progress Bar */}
                                                <div className="space-y-1">
                                                    <div className="flex justify-between text-xs text-muted-foreground">
                                                        <span>Progress</span>
                                                        <span>{item.quantity_completed} / {item.quantity_planned}</span>
                                                    </div>
                                                    <Progress value={progress} className="h-2" />
                                                </div>

                                                {/* Controls */}
                                                {!isComplete && (
                                                    <div className="flex items-center justify-between pt-2">
                                                        <div className="flex items-center gap-2">
                                                            <Button
                                                                size="icon"
                                                                variant="outline"
                                                                className="h-10 w-10"
                                                                onClick={() => handleUpdateCompletion(item, -1)}
                                                                disabled={isUpdating || item.quantity_completed <= 0}
                                                            >
                                                                <Minus className="h-4 w-4" />
                                                            </Button>
                                                            <div className="w-16 text-center">
                                                                <span className="text-2xl font-bold">{item.quantity_completed}</span>
                                                            </div>
                                                            <Button
                                                                size="icon"
                                                                variant="outline"
                                                                className="h-10 w-10"
                                                                onClick={() => handleUpdateCompletion(item, 1)}
                                                                disabled={isUpdating || item.quantity_completed >= item.quantity_planned}
                                                            >
                                                                <Plus className="h-4 w-4" />
                                                            </Button>
                                                        </div>
                                                        <Button
                                                            size="sm"
                                                            className="bg-green-600 hover:bg-green-700 text-white"
                                                            onClick={() => handleCompleteItem(item)}
                                                            disabled={isUpdating}
                                                        >
                                                            {isUpdating ? (
                                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                            ) : (
                                                                <>
                                                                    <Check className="h-4 w-4 mr-1" />
                                                                    Complete All
                                                                </>
                                                            )}
                                                        </Button>
                                                    </div>
                                                )}

                                                {isComplete && (
                                                    <div className="flex items-center justify-between pt-2">
                                                        <span className="text-sm text-green-700">All {item.quantity_planned} units manufactured</span>
                                                        <Button
                                                            size="sm"
                                                            variant="outline"
                                                            onClick={() => handleUpdateCompletion(item, -1)}
                                                            disabled={isUpdating}
                                                        >
                                                            Undo Last
                                                        </Button>
                                                    </div>
                                                )}
                                            </div>
                                        </CardContent>
                                    </Card>
                                );
                            })}
                        </div>

                        {/* Refresh Button */}
                        <div className="pt-4 text-center">
                            <Button
                                variant="outline"
                                onClick={loadTodayPlan}
                                disabled={loading}
                            >
                                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Refresh Plan
                            </Button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
