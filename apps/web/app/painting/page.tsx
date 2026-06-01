"use client";

import { useState, useEffect } from "react";
import { apiService } from "@/lib/api";
import { PaintingDay, PaintingDayItem } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Check, Loader2, ArrowRight, Brush, Calendar, Plus, Minus, LogOut } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

type Screen = "gate" | "list";

export default function PaintingPage() {
    const { toast } = useToast();
    const [screen, setScreen] = useState<Screen>("gate");
    const [loading, setLoading] = useState(false);

    // Code-based access (mirrors moulding)
    const [accessCode, setAccessCode] = useState("");
    const [paintingCode, setPaintingCode] = useState<string | null>(null);

    const [plan, setPlan] = useState<PaintingDay | null>(null);
    const [updatingItem, setUpdatingItem] = useState<string | null>(null);

    useEffect(() => {
        const saved = localStorage.getItem("garden_painting_code");
        if (saved) {
            verifyCode(saved, true);
        }
    }, []);

    useEffect(() => {
        if (paintingCode && screen === "list") {
            loadTodayPlan();
        }
    }, [paintingCode, screen]);

    const verifyCode = async (code: string, silent = false) => {
        if (!code) return;
        setLoading(true);
        try {
            const data = await apiService.painting.verifyCode(code);
            if (data.valid) {
                localStorage.setItem("garden_painting_code", data.code);
                setPaintingCode(data.code);
                setScreen("list");
            }
        } catch (error: any) {
            if (!silent) {
                toast({ variant: "destructive", title: "Invalid Code", description: "Please enter a valid painting code." });
            }
            localStorage.removeItem("garden_painting_code");
        } finally {
            setLoading(false);
        }
    };

    const loadTodayPlan = async () => {
        if (!paintingCode) return;
        setLoading(true);
        try {
            const data = await apiService.painting.getTodayPlanPublic(paintingCode);
            setPlan(data);
        } catch (error: any) {
            if (error.response?.status === 404 || error.message?.includes("404")) {
                setPlan(null);
            } else {
                toast({ variant: "destructive", title: "Network Error", description: "Failed to load today's painting plan." });
            }
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateCompletion = async (item: PaintingDayItem, delta: number) => {
        if (!paintingCode) return;
        const newQty = Math.max(0, Math.min(item.quantity_planned, item.quantity_completed + delta));
        if (newQty === item.quantity_completed) return;

        setUpdatingItem(item.id);
        try {
            await apiService.painting.updateItemCompletion(item.id, newQty, paintingCode);

            setPlan(prev => {
                if (!prev) return null;
                const updatedItems = prev.items.map(i =>
                    i.id === item.id ? { ...i, quantity_completed: newQty, remaining: i.quantity_planned - newQty } : i
                );
                const total_completed = updatedItems.reduce((sum, i) => sum + i.quantity_completed, 0);
                return { ...prev, items: updatedItems, total_completed };
            });

            if (newQty === item.quantity_planned) {
                toast({ title: "Complete!", description: `${item.display_string} fully painted.` });
            }
        } catch (error: any) {
            toast({ variant: "destructive", title: "Update Failed", description: error.message || "Could not update completion." });
        } finally {
            setUpdatingItem(null);
        }
    };

    const handleCompleteItem = async (item: PaintingDayItem) => {
        if (!paintingCode) return;
        if (item.quantity_completed >= item.quantity_planned) return;

        setUpdatingItem(item.id);
        try {
            await apiService.painting.updateItemCompletion(item.id, item.quantity_planned, paintingCode);

            setPlan(prev => {
                if (!prev) return null;
                const updatedItems = prev.items.map(i =>
                    i.id === item.id ? { ...i, quantity_completed: i.quantity_planned, remaining: 0 } : i
                );
                const total_completed = updatedItems.reduce((sum, i) => sum + i.quantity_completed, 0);
                return { ...prev, items: updatedItems, total_completed };
            });

            toast({ title: "Complete!", description: `${item.display_string} fully painted.` });
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
                    <div className="flex justify-center">
                        <div className="h-16 w-16 bg-white rounded-2xl flex items-center justify-center shadow-lg border">
                            <img src="/logo.avif" alt="Garden Solutions" className="h-10 w-10 object-contain" />
                        </div>
                    </div>
                    <div className="text-center space-y-2">
                        <h1 className="text-3xl font-heading font-semibold tracking-tight text-foreground">Painting Portal</h1>
                        <p className="text-muted-foreground">Enter your painting code to access today's plan</p>
                    </div>
                    <Card className="border shadow-xl shadow-black/5">
                        <CardContent className="pt-6 space-y-4">
                            <Input
                                className="text-center text-lg tracking-widest font-mono uppercase h-12"
                                value={accessCode}
                                onChange={e => setAccessCode(e.target.value)}
                                placeholder="PAINTING CODE"
                                onKeyDown={e => e.key === "Enter" && verifyCode(accessCode)}
                            />
                            <Button
                                className="w-full h-12 text-base font-medium bg-sky-600 hover:bg-sky-700"
                                onClick={() => verifyCode(accessCode)}
                                disabled={loading || !accessCode}
                            >
                                {loading && <Loader2 className="mr-2 h-5 w-5 animate-spin" />}
                                Access Painting
                                {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    const overallProgress = plan && plan.total_planned > 0
        ? (plan.total_completed / plan.total_planned) * 100
        : 0;

    return (
        <div className="min-h-screen pb-8 bg-background">
            <div className="bg-background/95 backdrop-blur-lg border-b sticky top-0 z-10">
                <div className="px-6 py-4 max-w-lg mx-auto">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 bg-white rounded-xl flex items-center justify-center border">
                                <img src="/logo.avif" alt="Garden Solutions" className="h-6 w-6 object-contain" />
                            </div>
                            <div>
                                <div className="font-heading font-semibold text-lg text-foreground">Painting</div>
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
                                    localStorage.removeItem("garden_painting_code");
                                    setPaintingCode(null);
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
                            <Brush className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <h3 className="font-semibold text-foreground mb-1">No Plan Today</h3>
                        <p className="text-sm text-muted-foreground">No painting plan has been created for today yet.</p>
                        <Button variant="outline" className="mt-4" onClick={loadTodayPlan}>Refresh</Button>
                    </div>
                )}

                {plan && !loading && (
                    <>
                        <Card className="border-sky-200 bg-sky-50/50">
                            <CardHeader className="pb-3">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">Overall Progress</CardTitle>
                                    <div className="text-right">
                                        <div className="text-2xl font-bold text-sky-700">
                                            {plan.total_completed} / {plan.total_planned}
                                        </div>
                                        <div className="text-xs text-muted-foreground">units painted</div>
                                    </div>
                                </div>
                                <Progress value={overallProgress} className="h-3 mt-3" />
                            </CardHeader>
                        </Card>

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
                                                {/* Order context */}
                                                {(item.client_or_store_label || item.customer_name) && (
                                                    <div className="text-xs text-muted-foreground bg-muted/40 rounded px-2 py-1">
                                                        {item.client_or_store_label}
                                                        {item.customer_name ? ` · ${item.customer_name}` : ""}
                                                    </div>
                                                )}
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

                                                <div className="space-y-1">
                                                    <div className="flex justify-between text-xs text-muted-foreground">
                                                        <span>Progress</span>
                                                        <span>{item.quantity_completed} / {item.quantity_planned}</span>
                                                    </div>
                                                    <Progress value={progress} className="h-2" />
                                                </div>

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
                                                        <span className="text-sm text-green-700">All {item.quantity_planned} units painted</span>
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
