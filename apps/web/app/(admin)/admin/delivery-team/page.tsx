"use client";

import { useEffect, useMemo, useState } from "react";
import { DeliveryTeam, Order } from "@/types";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Truck, Loader2, Calendar, ChevronLeft, ChevronRight, PauseCircle, PlayCircle, AlertCircle, Clock } from "lucide-react";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { PageHeader } from "@/components/ui/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

export default function AdminDeliveryTeamsPage() {
    const { toast } = useToast();
    const [teams, setTeams] = useState<DeliveryTeam[]>([]);
    const [loading, setLoading] = useState(true);
    const [orders, setOrders] = useState<Order[]>([]);
    const [dateFilter, setDateFilter] = useState<string>(new Date().toISOString().split("T")[0]);
    const [calendarMonth, setCalendarMonth] = useState<Date>(() => new Date());
    const [assignmentDrafts, setAssignmentDrafts] = useState<Record<string, { delivery_team_id: string; delivery_date: string; paused: boolean }>>({});

    useEffect(() => {
        loadData();
    }, []);

    useEffect(() => {
        const nextDrafts: Record<string, { delivery_team_id: string; delivery_date: string; paused: boolean }> = {};
        orders.forEach(order => {
            if (order.delivery_team_id) {
                nextDrafts[order.id] = {
                    delivery_team_id: order.delivery_team_id ?? "",
                    delivery_date: order.delivery_date ?? "",
                    paused: !!order.delivery_paused,
                };
            }
        });
        setAssignmentDrafts(nextDrafts);
    }, [orders]);

    const loadData = async () => {
        try {
            setLoading(true);
            const [teamsData, ordersData] = await Promise.all([
                apiService.admin.deliveryTeams.list(),
                apiService.orders.list(),
            ]);
            setTeams(teamsData);
            setOrders(ordersData);
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load delivery teams", description: error.message });
        } finally {
            setLoading(false);
        }
    };


    const makeDateString = (year: number, month: number, day: number) => {
        return new Date(Date.UTC(year, month, day)).toISOString().split("T")[0];
    };

    const monthStart = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), 1);
    const daysInMonth = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 0).getDate();
    const startDay = monthStart.getDay();
    const monthLabel = calendarMonth.toLocaleString("default", { month: "long", year: "numeric" });

    const targetDate = dateFilter || new Date().toISOString().split("T")[0];
    const assignedOrders = orders.filter(order => order.delivery_team_id && order.delivery_date === targetDate);

    const handleAssignmentChange = (
        orderId: string,
        patch: Partial<{ delivery_team_id: string; delivery_date: string; paused: boolean }>
    ) => {
        setAssignmentDrafts(prev => ({
            ...prev,
            [orderId]: {
                delivery_team_id: prev[orderId]?.delivery_team_id ?? "",
                delivery_date: prev[orderId]?.delivery_date ?? "",
                paused: prev[orderId]?.paused ?? false,
                ...patch,
            },
        }));
    };

    const isAssignmentDirty = (order: Order) => {
        const draft = assignmentDrafts[order.id];
        if (!draft) return false;
        return (
            draft.delivery_team_id !== (order.delivery_team_id ?? "") ||
            draft.delivery_date !== (order.delivery_date ?? "") ||
            draft.paused !== !!order.delivery_paused
        );
    };

    const handleSaveAssignment = async (orderId: string) => {
        const draft = assignmentDrafts[orderId];
        if (!draft) return;
        try {
            await apiService.admin.deliveryTeams.updateAssignment(orderId, {
                delivery_team_id: draft.delivery_team_id,
                delivery_date: draft.delivery_date,
                paused: draft.paused,
            });
            toast({ title: "Assignment updated" });
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to update assignment", description: error.message });
        }
    };

    const getOrderClientName = (order: Order) => {
        return order.client?.name || order.client_name || "Unknown";
    };

    const totalDeliveriesAssigned = useMemo(() => {
        return orders.filter(order => order.delivery_team_id).length;
    }, [orders]);

    const outstandingOrders = useMemo(() => {
        return orders.filter(order => !["Completed", "Cancelled"].includes(order.status)).length;
    }, [orders]);

    const averageDeliveryDays = useMemo(() => {
        const deliveredOrders = orders.filter(order => order.delivered_at);
        if (deliveredOrders.length === 0) return null;
        const totalDays = deliveredOrders.reduce((sum, order) => {
            if (!order.delivered_at) return sum;
            const created = new Date(order.created_at).getTime();
            const delivered = new Date(order.delivered_at).getTime();
            const days = Math.max((delivered - created) / (1000 * 60 * 60 * 24), 0);
            return sum + days;
        }, 0);
        return totalDays / deliveredOrders.length;
    }, [orders]);

    const dailySummary = (() => {
        const relevantOrders = orders.filter(o => o.delivery_date === targetDate && o.delivery_team_id);

        return {
            count: relevantOrders.length,
            revenue: relevantOrders.reduce((sum, o) => sum + o.total_price_rands, 0)
        };
    })();

    return (
        <div className="space-y-6">
            <PageHeader
                title="Deliveries"
                description="Manage delivery schedules and assignments."
            />

            <>
                    {/* Delivery Calendar & Daily Summary */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <Card className="border shadow-sm">
                            <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                                <CardTitle className="text-base">Delivery Calendar</CardTitle>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="h-7 text-xs"
                                    onClick={() => setDateFilter(new Date().toISOString().split("T")[0])}
                                >
                                    TODAY
                                </Button>
                            </CardHeader>
                            <CardContent>
                                <div className="text-center pb-4 pt-2">
                                    <div className="flex items-center justify-between mb-4 px-2">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-7 w-7"
                                            onClick={() => setCalendarMonth(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))}
                                        >
                                            <ChevronLeft className="h-4 w-4" />
                                        </Button>
                                        <span className="text-sm font-medium">{monthLabel}</span>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-7 w-7"
                                            onClick={() => setCalendarMonth(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))}
                                        >
                                            <ChevronRight className="h-4 w-4" />
                                        </Button>
                                    </div>
                                    <div className="grid grid-cols-7 gap-1 text-center text-xs">
                                        {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map(d => (
                                            <div key={d} className="text-muted-foreground py-1">{d}</div>
                                        ))}
                                        {Array.from({ length: startDay }).map((_, i) => (
                                            <div key={`empty-${i}`} className="py-1.5" />
                                        ))}
                                        {Array.from({ length: daysInMonth }).map((_, i) => {
                                            const day = i + 1;
                                            const dateString = makeDateString(calendarMonth.getFullYear(), calendarMonth.getMonth(), day);
                                            const isToday = dateString === new Date().toISOString().split("T")[0];
                                            const isSelected = dateString === dateFilter;
                                            return (
                                                <button
                                                    key={dateString}
                                                    type="button"
                                                    onClick={() => setDateFilter(dateString)}
                                                    className={cn(
                                                        "py-1.5 rounded-md transition-colors",
                                                        isSelected
                                                            ? "bg-primary text-primary-foreground font-semibold"
                                                            : isToday
                                                                ? "bg-primary/10 text-primary font-semibold"
                                                                : "hover:bg-muted"
                                                    )}
                                                >
                                                    {day}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card className="border shadow-sm bg-slate-50/50">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-base">Daily Summary</CardTitle>
                                <CardDescription>
                                    {dateFilter ? `Stats for ${dateFilter}` : "Stats for Today (Filtered)"}
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-sm text-muted-foreground mb-1">Orders to Deliver</div>
                                        <div className="text-2xl font-bold">{dailySummary.count}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-muted-foreground mb-1">Expected Revenue</div>
                                        <div className="text-2xl font-bold">R {dailySummary.revenue.toLocaleString()}</div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        <div className="stat-card">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="stat-card-label">Deliveries Assigned</p>
                                    <p className="stat-card-value">{totalDeliveriesAssigned}</p>
                                </div>
                                <div className="stat-card-icon bg-blue-100">
                                    <Truck className="h-5 w-5 text-blue-600" />
                                </div>
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="stat-card-label">Outstanding Orders</p>
                                    <p className="stat-card-value">{outstandingOrders}</p>
                                </div>
                                <div className="stat-card-icon bg-amber-100">
                                    <AlertCircle className="h-5 w-5 text-amber-600" />
                                </div>
                            </div>
                        </div>

                        <div className="stat-card">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="stat-card-label">Avg Order to Delivered</p>
                                    <p className="stat-card-value">
                                        {averageDeliveryDays === null ? "—" : `${averageDeliveryDays.toFixed(1)} days`}
                                    </p>
                                </div>
                                <div className="stat-card-icon bg-slate-100">
                                    <Clock className="h-5 w-5 text-slate-600" />
                                </div>
                            </div>
                        </div>
                    </div>

                    <Card className="border shadow-sm">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-base">Assigned Orders</CardTitle>
                            <CardDescription>
                                {targetDate ? `Orders scheduled for ${targetDate}` : "Orders scheduled for today"}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {assignedOrders.length === 0 ? (
                                <EmptyState
                                    icon={Truck}
                                    title="No assigned orders"
                                    description="Assign a delivery team to orders and schedule them to see them here."
                                />
                            ) : (
                                <Table>
                                    <TableHeader className="bg-muted/30">
                                        <TableRow>
                                            <TableHead>Order</TableHead>
                                            <TableHead className="w-[220px]">Delivery Team</TableHead>
                                            <TableHead className="w-[160px]">Date</TableHead>
                                            <TableHead className="w-[140px]">Paused</TableHead>
                                            <TableHead className="text-right w-[120px]">Actions</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {assignedOrders.map(order => {
                                            const draft = assignmentDrafts[order.id];
                                            return (
                                                <TableRow key={order.id}>
                                                    <TableCell>
                                                        <div className="font-medium">#{order.id.slice(0, 8)}</div>
                                                        <div className="text-xs text-muted-foreground">{getOrderClientName(order)}</div>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Select
                                                            value={draft?.delivery_team_id ?? ""}
                                                            onValueChange={value => handleAssignmentChange(order.id, { delivery_team_id: value })}
                                                        >
                                                            <SelectTrigger>
                                                                <SelectValue placeholder="Select Team" />
                                                            </SelectTrigger>
                                                            <SelectContent>
                                                                {teams.map(team => (
                                                                    <SelectItem key={team.id} value={team.id}>{team.name}</SelectItem>
                                                                ))}
                                                            </SelectContent>
                                                        </Select>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Input
                                                            type="date"
                                                            value={draft?.delivery_date ?? ""}
                                                            onChange={e => handleAssignmentChange(order.id, { delivery_date: e.target.value })}
                                                        />
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="flex items-center gap-2">
                                                            <Switch
                                                                checked={draft?.paused ?? false}
                                                                onCheckedChange={checked => handleAssignmentChange(order.id, { paused: checked })}
                                                            />
                                                            <span className="text-xs text-muted-foreground">
                                                                {draft?.paused ? "Paused" : "Active"}
                                                            </span>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="text-right">
                                                        <Button
                                                            size="sm"
                                                            onClick={() => handleSaveAssignment(order.id)}
                                                            disabled={!isAssignmentDirty(order)}
                                                        >
                                                            {draft?.paused ? (
                                                                <PauseCircle className="mr-2 h-4 w-4" />
                                                            ) : (
                                                                <PlayCircle className="mr-2 h-4 w-4" />
                                                            )}
                                                            Save
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })}
                                    </TableBody>
                                </Table>
                            )}
                        </CardContent>
                    </Card>
            </>

        </div>
    );
}
