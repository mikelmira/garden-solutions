"use client";

import { useEffect, useMemo, useState } from "react";
import {
    EmailAutomation,
    EmailAutomationFrequency,
    EmailAutomationPlanType,
    EmailRecipient,
    EmailRecipientCategory,
    OnceOffSendPayload,
} from "@/types";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
    Mail, Plus, Pencil, Trash2, Loader2, Send, Play, Clock, CalendarClock,
    Power, PowerOff, Inbox,
} from "lucide-react";
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

type TabKey = "schedule" | "once-off" | "recipients";

const PLAN_TYPES: { value: EmailAutomationPlanType; label: string; helper: string }[] = [
    { value: "moulding", label: "Moulding plan", helper: "Today's moulding plan with SKU breakdown." },
    { value: "painting", label: "Painting plan", helper: "Today's painting plan, per order item." },
    { value: "orders", label: "Open orders", helper: "Summary of all open (non-terminal) orders." },
    { value: "deliveries", label: "Today's deliveries", helper: "Delivery roster for today." },
];

const FREQUENCIES: { value: EmailAutomationFrequency; label: string }[] = [
    { value: "daily", label: "Every day" },
    { value: "weekdays", label: "Weekdays (Mon–Fri)" },
    { value: "weekly", label: "Once a week" },
    { value: "once", label: "Once, at a specific time" },
];

const DAYS = [
    { value: 0, label: "Monday" },
    { value: 1, label: "Tuesday" },
    { value: 2, label: "Wednesday" },
    { value: 3, label: "Thursday" },
    { value: 4, label: "Friday" },
    { value: 5, label: "Saturday" },
    { value: 6, label: "Sunday" },
];

const PLAN_BADGE: Record<EmailAutomationPlanType, string> = {
    moulding: "border-amber-200 bg-amber-50 text-amber-700",
    painting: "border-sky-200 bg-sky-50 text-sky-700",
    orders: "border-purple-200 bg-purple-50 text-purple-700",
    deliveries: "border-emerald-200 bg-emerald-50 text-emerald-700",
};

function formatNextRun(iso?: string | null): string {
    if (!iso) return "—";
    try {
        const d = new Date(iso);
        return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
    } catch {
        return iso;
    }
}

function summarizeSchedule(a: EmailAutomation): string {
    const time = a.send_time ? a.send_time.slice(0, 5) : "";  // HH:MM
    switch (a.frequency) {
        case "daily":
            return `Daily at ${time}`;
        case "weekdays":
            return `Weekdays at ${time}`;
        case "weekly": {
            const day = DAYS.find(d => d.value === a.day_of_week)?.label ?? "?";
            return `${day} at ${time}`;
        }
        case "once":
            return a.send_at
                ? `Once at ${new Date(a.send_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}`
                : "Once";
        default:
            return a.frequency;
    }
}

// ---------------------------------------------------------------- Page
export default function AutomationsPage() {
    const [tab, setTab] = useState<TabKey>("schedule");

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight">Automations</h1>
                <p className="text-muted-foreground">
                    Schedule recurring plan emails, send one-off updates, and manage who receives the daily plan emails.
                </p>
            </div>

            <div className="border-b border-border/60">
                <nav className="flex items-end gap-1 overflow-x-auto" aria-label="Automations tabs">
                    {([
                        { key: "schedule", label: "Scheduled" },
                        { key: "once-off", label: "Send Once-off" },
                        { key: "recipients", label: "Trigger Recipients" },
                    ] as { key: TabKey; label: string }[]).map(t => {
                        const active = tab === t.key;
                        return (
                            <button
                                key={t.key}
                                type="button"
                                onClick={() => setTab(t.key)}
                                aria-current={active ? "page" : undefined}
                                className={
                                    "inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px " +
                                    (active
                                        ? "border-primary text-foreground"
                                        : "border-transparent text-muted-foreground hover:text-foreground hover:border-border")
                                }
                            >
                                {t.label}
                            </button>
                        );
                    })}
                </nav>
            </div>

            {tab === "schedule" && <ScheduledTab />}
            {tab === "once-off" && <OnceOffTab />}
            {tab === "recipients" && <RecipientsTab />}

            <Card className="border-amber-200 bg-amber-50/40">
                <CardContent className="pt-6 text-sm text-amber-900">
                    <strong>Setup note:</strong> emails send via Resend. To actually deliver, set{" "}
                    <code className="bg-amber-100 px-1 rounded">RESEND_API_KEY</code> in{" "}
                    <code className="bg-amber-100 px-1 rounded">apps/api/.env</code> on the server and restart the API. The free tier covers 3,000 emails/month.
                </CardContent>
            </Card>
        </div>
    );
}

// ---------------------------------------------------------------- Tab 1
function ScheduledTab() {
    const { toast } = useToast();
    const [rows, setRows] = useState<EmailAutomation[]>([]);
    const [loading, setLoading] = useState(true);
    const [includeInactive, setIncludeInactive] = useState(false);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editing, setEditing] = useState<EmailAutomation | null>(null);
    const [form, setForm] = useState({
        name: "",
        plan_type: "moulding" as EmailAutomationPlanType,
        frequency: "daily" as EmailAutomationFrequency,
        send_time: "06:00",
        day_of_week: 0,
        send_at_date: "",
        send_at_time: "",
        recipients: "",
    });
    const [saving, setSaving] = useState(false);
    const [runningId, setRunningId] = useState<string | null>(null);

    const load = async () => {
        try {
            setLoading(true);
            const data = await apiService.admin.emailAutomations.list({ include_inactive: includeInactive });
            setRows(data);
        } catch (e: any) {
            toast({ variant: "destructive", title: "Failed to load automations", description: e.message });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, [includeInactive]);

    const open = (row?: EmailAutomation) => {
        if (row) {
            setEditing(row);
            const sendAt = row.send_at ? new Date(row.send_at) : null;
            setForm({
                name: row.name,
                plan_type: row.plan_type,
                frequency: row.frequency,
                send_time: row.send_time ? row.send_time.slice(0, 5) : "06:00",
                day_of_week: row.day_of_week ?? 0,
                send_at_date: sendAt ? sendAt.toISOString().slice(0, 10) : "",
                send_at_time: sendAt ? sendAt.toISOString().slice(11, 16) : "",
                recipients: (row.recipients || []).join(", "),
            });
        } else {
            setEditing(null);
            setForm({
                name: "",
                plan_type: "moulding",
                frequency: "daily",
                send_time: "06:00",
                day_of_week: 0,
                send_at_date: "",
                send_at_time: "",
                recipients: "",
            });
        }
        setDialogOpen(true);
    };

    const parseRecipients = (s: string): string[] =>
        s.split(/[\s,;]+/).map(t => t.trim()).filter(Boolean);

    const save = async () => {
        const recipients = parseRecipients(form.recipients);
        if (!form.name.trim()) { toast({ variant: "destructive", title: "Name is required" }); return; }
        if (recipients.length === 0) { toast({ variant: "destructive", title: "At least one recipient is required" }); return; }

        const payload: any = {
            name: form.name,
            plan_type: form.plan_type,
            frequency: form.frequency,
            recipients,
        };
        if (form.frequency === "once") {
            if (!form.send_at_date || !form.send_at_time) {
                toast({ variant: "destructive", title: "Pick a date and time for the once-off send." });
                return;
            }
            // Local datetime → naive ISO (server treats as UTC; matches existing convention).
            payload.send_at = `${form.send_at_date}T${form.send_at_time}:00`;
            payload.send_time = null;
            payload.day_of_week = null;
        } else {
            payload.send_time = `${form.send_time}:00`;
            payload.send_at = null;
            payload.day_of_week = form.frequency === "weekly" ? form.day_of_week : null;
        }

        try {
            setSaving(true);
            if (editing) {
                await apiService.admin.emailAutomations.update(editing.id, payload);
                toast({ title: "Automation updated" });
            } else {
                await apiService.admin.emailAutomations.create(payload);
                toast({ title: "Automation created" });
            }
            setDialogOpen(false);
            load();
        } catch (e: any) {
            toast({ variant: "destructive", title: "Save failed", description: e.message });
        } finally {
            setSaving(false);
        }
    };

    const toggleActive = async (row: EmailAutomation) => {
        try {
            await apiService.admin.emailAutomations.update(row.id, { is_active: !row.is_active });
            toast({ title: row.is_active ? "Paused" : "Activated" });
            load();
        } catch (e: any) {
            toast({ variant: "destructive", title: "Toggle failed", description: e.message });
        }
    };

    const remove = async (row: EmailAutomation) => {
        if (!confirm(`Delete automation "${row.name}"?`)) return;
        try {
            await apiService.admin.emailAutomations.delete(row.id);
            toast({ title: "Automation deleted" });
            load();
        } catch (e: any) {
            toast({ variant: "destructive", title: "Delete failed", description: e.message });
        }
    };

    const runNow = async (row: EmailAutomation) => {
        try {
            setRunningId(row.id);
            await apiService.admin.emailAutomations.runNow(row.id);
            toast({ title: "Sent", description: `${row.name} dispatched.` });
            load();
        } catch (e: any) {
            toast({ variant: "destructive", title: "Run failed", description: e.message });
        } finally {
            setRunningId(null);
        }
    };

    return (
        <Card>
            <CardContent className="pt-6 space-y-3">
                <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 text-sm">
                        <label className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                checked={includeInactive}
                                onChange={e => setIncludeInactive(e.target.checked)}
                            />
                            Include inactive
                        </label>
                    </div>
                    <Button onClick={() => open()} className="gap-2">
                        <Plus className="h-4 w-4" /> New automation
                    </Button>
                </div>

                {loading ? (
                    <div className="flex h-[20vh] items-center justify-center">
                        <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    </div>
                ) : rows.length === 0 ? (
                    <div className="py-10 text-center">
                        <CalendarClock className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                        <p className="text-sm text-muted-foreground">
                            No automations yet. Create one to start scheduled plan emails.
                        </p>
                    </div>
                ) : (
                    <div className="divide-y border rounded-md">
                        {rows.map(row => (
                            <div key={row.id} className="flex items-center justify-between gap-3 px-3 py-3">
                                <div className="min-w-0 flex-1">
                                    <div className="flex flex-wrap items-center gap-2">
                                        <span className="font-medium truncate">{row.name}</span>
                                        <Badge variant="outline" className={PLAN_BADGE[row.plan_type]}>
                                            {row.plan_type}
                                        </Badge>
                                        {!row.is_active && (
                                            <Badge variant="outline" className="bg-muted text-muted-foreground">paused</Badge>
                                        )}
                                    </div>
                                    <div className="text-xs text-muted-foreground mt-0.5 flex flex-wrap gap-x-3 gap-y-0.5">
                                        <span className="inline-flex items-center gap-1">
                                            <Clock className="h-3 w-3" /> {summarizeSchedule(row)}
                                        </span>
                                        <span>Next run: <strong>{formatNextRun(row.next_run_at)}</strong></span>
                                        {row.last_sent_at && (
                                            <span>Last sent: {formatNextRun(row.last_sent_at)}</span>
                                        )}
                                        <span>{row.recipients.length} recipient{row.recipients.length === 1 ? "" : "s"}</span>
                                    </div>
                                </div>
                                <div className="flex gap-1">
                                    <Button
                                        size="icon" variant="ghost"
                                        title="Send now"
                                        onClick={() => runNow(row)}
                                        disabled={runningId === row.id}
                                    >
                                        {runningId === row.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                                    </Button>
                                    <Button
                                        size="icon" variant="ghost"
                                        title={row.is_active ? "Pause" : "Activate"}
                                        onClick={() => toggleActive(row)}
                                    >
                                        {row.is_active ? <Power className="h-4 w-4" /> : <PowerOff className="h-4 w-4" />}
                                    </Button>
                                    <Button size="icon" variant="ghost" onClick={() => open(row)} title="Edit">
                                        <Pencil className="h-4 w-4" />
                                    </Button>
                                    <Button size="icon" variant="ghost" onClick={() => remove(row)} title="Delete">
                                        <Trash2 className="h-4 w-4 text-red-600" />
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>

            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="sm:max-w-xl">
                    <DialogHeader>
                        <DialogTitle>{editing ? "Edit automation" : "New automation"}</DialogTitle>
                        <DialogDescription>
                            Pick the content, when to send it, and who receives it.
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-3">
                        <div>
                            <Label htmlFor="auto-name">Name</Label>
                            <Input id="auto-name" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} placeholder="e.g. Daily moulding plan" />
                        </div>
                        <div>
                            <Label>What to send</Label>
                            <Select value={form.plan_type} onValueChange={(v: EmailAutomationPlanType) => setForm(p => ({ ...p, plan_type: v }))}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    {PLAN_TYPES.map(p => (
                                        <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <p className="text-xs text-muted-foreground mt-1">
                                {PLAN_TYPES.find(p => p.value === form.plan_type)?.helper}
                            </p>
                        </div>
                        <div>
                            <Label>How often</Label>
                            <Select value={form.frequency} onValueChange={(v: EmailAutomationFrequency) => setForm(p => ({ ...p, frequency: v }))}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    {FREQUENCIES.map(f => (
                                        <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {form.frequency === "once" ? (
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <Label htmlFor="once-date">Date</Label>
                                    <Input id="once-date" type="date" value={form.send_at_date} onChange={e => setForm(p => ({ ...p, send_at_date: e.target.value }))} />
                                </div>
                                <div>
                                    <Label htmlFor="once-time">Time</Label>
                                    <Input id="once-time" type="time" value={form.send_at_time} onChange={e => setForm(p => ({ ...p, send_at_time: e.target.value }))} />
                                </div>
                            </div>
                        ) : (
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <Label htmlFor="send-time">Time of day</Label>
                                    <Input id="send-time" type="time" value={form.send_time} onChange={e => setForm(p => ({ ...p, send_time: e.target.value }))} />
                                </div>
                                {form.frequency === "weekly" && (
                                    <div>
                                        <Label>Day of week</Label>
                                        <Select value={String(form.day_of_week)} onValueChange={v => setForm(p => ({ ...p, day_of_week: parseInt(v, 10) }))}>
                                            <SelectTrigger><SelectValue /></SelectTrigger>
                                            <SelectContent>
                                                {DAYS.map(d => (
                                                    <SelectItem key={d.value} value={String(d.value)}>{d.label}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                )}
                            </div>
                        )}

                        <div>
                            <Label htmlFor="auto-recipients">Recipients</Label>
                            <Input
                                id="auto-recipients"
                                value={form.recipients}
                                onChange={e => setForm(p => ({ ...p, recipients: e.target.value }))}
                                placeholder="alice@example.com, bob@example.com"
                            />
                            <p className="text-xs text-muted-foreground mt-1">
                                Comma- or space-separated email addresses.
                            </p>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={saving}>Cancel</Button>
                        <Button onClick={save} disabled={saving}>
                            {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            Save
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </Card>
    );
}

// ---------------------------------------------------------------- Tab 2
function OnceOffTab() {
    const { toast } = useToast();
    const [planType, setPlanType] = useState<EmailAutomationPlanType>("orders");
    const [recipients, setRecipients] = useState("");
    const [forDate, setForDate] = useState<string>(new Date().toISOString().slice(0, 10));
    const [sending, setSending] = useState(false);
    const [lastResult, setLastResult] = useState<string | null>(null);

    const submit = async () => {
        const list = recipients.split(/[\s,;]+/).map(s => s.trim()).filter(Boolean);
        if (list.length === 0) {
            toast({ variant: "destructive", title: "Add at least one recipient" });
            return;
        }
        try {
            setSending(true);
            setLastResult(null);
            const payload: OnceOffSendPayload = {
                plan_type: planType,
                recipients: list,
                for_date: forDate || undefined,
            };
            const result = await apiService.admin.emailAutomations.sendOnceOff(payload);
            if (result.sent) {
                toast({ title: "Sent", description: `${result.recipients.length} recipient${result.recipients.length === 1 ? "" : "s"}` });
                setLastResult(`Dispatched to ${result.recipients.join(", ")}.`);
            } else {
                toast({ variant: "destructive", title: "Not sent", description: result.note || "Unknown reason" });
                setLastResult(result.note || "Send returned false.");
            }
        } catch (e: any) {
            toast({ variant: "destructive", title: "Send failed", description: e.message });
        } finally {
            setSending(false);
        }
    };

    return (
        <Card>
            <CardContent className="pt-6 space-y-4">
                <div>
                    <Label>What to send</Label>
                    <Select value={planType} onValueChange={(v: EmailAutomationPlanType) => setPlanType(v)}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                            {PLAN_TYPES.map(p => (
                                <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground mt-1">
                        {PLAN_TYPES.find(p => p.value === planType)?.helper}
                    </p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <Label htmlFor="for-date">For date</Label>
                        <Input id="for-date" type="date" value={forDate} onChange={e => setForDate(e.target.value)} />
                        <p className="text-xs text-muted-foreground mt-1">
                            Default: today. Most types use today's plan/data anyway.
                        </p>
                    </div>
                </div>
                <div>
                    <Label htmlFor="oo-recipients">Recipients</Label>
                    <Input
                        id="oo-recipients"
                        value={recipients}
                        onChange={e => setRecipients(e.target.value)}
                        placeholder="alice@example.com, bob@example.com"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Comma- or space-separated.</p>
                </div>
                <div className="flex items-center justify-end gap-3">
                    {lastResult && <span className="text-xs text-muted-foreground">{lastResult}</span>}
                    <Button onClick={submit} disabled={sending} className="gap-2">
                        {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                        Send now
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}

// ---------------------------------------------------------------- Tab 3 (existing recipients list)
function RecipientsTab() {
    const { toast } = useToast();
    const [rows, setRows] = useState<EmailRecipient[]>([]);
    const [loading, setLoading] = useState(true);
    const [includeInactive, setIncludeInactive] = useState(false);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editing, setEditing] = useState<EmailRecipient | null>(null);
    const [form, setForm] = useState<{ email: string; name: string; category: EmailRecipientCategory }>({
        email: "", name: "", category: "moulding",
    });
    const [saving, setSaving] = useState(false);

    const load = async () => {
        try {
            setLoading(true);
            const data = await apiService.admin.emailRecipients.list({ include_inactive: includeInactive });
            setRows(data);
        } catch (e: any) {
            toast({ variant: "destructive", title: "Failed to load", description: e.message });
        } finally {
            setLoading(false);
        }
    };
    useEffect(() => { load(); }, [includeInactive]);

    const open = (row?: EmailRecipient) => {
        if (row) {
            setEditing(row);
            setForm({ email: row.email, name: row.name || "", category: row.category });
        } else {
            setEditing(null);
            setForm({ email: "", name: "", category: "moulding" });
        }
        setDialogOpen(true);
    };

    const save = async () => {
        if (!form.email.trim()) {
            toast({ variant: "destructive", title: "Email is required" }); return;
        }
        try {
            setSaving(true);
            if (editing) {
                await apiService.admin.emailRecipients.update(editing.id, {
                    email: form.email, name: form.name || undefined, category: form.category,
                });
                toast({ title: "Recipient updated" });
            } else {
                await apiService.admin.emailRecipients.create({
                    email: form.email, name: form.name || undefined, category: form.category,
                });
                toast({ title: "Recipient added" });
            }
            setDialogOpen(false);
            load();
        } catch (e: any) {
            toast({ variant: "destructive", title: "Save failed", description: e.message });
        } finally {
            setSaving(false);
        }
    };

    const remove = async (row: EmailRecipient) => {
        if (!confirm(`Remove ${row.email}?`)) return;
        try {
            await apiService.admin.emailRecipients.delete(row.id);
            toast({ title: "Removed" });
            load();
        } catch (e: any) {
            toast({ variant: "destructive", title: "Remove failed", description: e.message });
        }
    };

    return (
        <Card>
            <CardContent className="pt-6 space-y-3">
                <p className="text-sm text-muted-foreground">
                    These addresses are emailed automatically when an admin creates today's moulding or painting plan.
                    For scheduled or one-off sends, use the other tabs.
                </p>
                <div className="flex items-center justify-between gap-3">
                    <label className="flex items-center gap-2 text-sm">
                        <input type="checkbox" checked={includeInactive} onChange={e => setIncludeInactive(e.target.checked)} />
                        Include inactive
                    </label>
                    <Button onClick={() => open()} className="gap-2"><Plus className="h-4 w-4" /> Add recipient</Button>
                </div>
                {loading ? (
                    <div className="flex h-[20vh] items-center justify-center">
                        <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    </div>
                ) : rows.length === 0 ? (
                    <div className="py-10 text-center">
                        <Inbox className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                        <p className="text-sm text-muted-foreground">No recipients yet.</p>
                    </div>
                ) : (
                    <div className="divide-y border rounded-md">
                        {rows.map(r => (
                            <div key={r.id} className="flex items-center justify-between gap-3 px-3 py-2">
                                <div className="min-w-0">
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium truncate">{r.email}</span>
                                        <Badge variant="outline" className={
                                            r.category === "moulding" ? "border-amber-200 bg-amber-50 text-amber-700"
                                                : r.category === "painting" ? "border-sky-200 bg-sky-50 text-sky-700"
                                                    : "border-purple-200 bg-purple-50 text-purple-700"
                                        }>
                                            {r.category}
                                        </Badge>
                                        {!r.is_active && (
                                            <Badge variant="outline" className="bg-muted text-muted-foreground">inactive</Badge>
                                        )}
                                    </div>
                                    {r.name && <div className="text-xs text-muted-foreground truncate">{r.name}</div>}
                                </div>
                                <div className="flex gap-1">
                                    <Button size="icon" variant="ghost" onClick={() => open(r)}><Pencil className="h-4 w-4" /></Button>
                                    <Button size="icon" variant="ghost" onClick={() => remove(r)}><Trash2 className="h-4 w-4 text-red-600" /></Button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>

            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                        <DialogTitle>{editing ? "Edit recipient" : "Add recipient"}</DialogTitle>
                        <DialogDescription>Who should receive the auto-trigger plan email?</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-3">
                        <div>
                            <Label htmlFor="rec-email">Email</Label>
                            <Input id="rec-email" type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} />
                        </div>
                        <div>
                            <Label htmlFor="rec-name">Name (optional)</Label>
                            <Input id="rec-name" value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} />
                        </div>
                        <div>
                            <Label>Plan</Label>
                            <Select value={form.category} onValueChange={(v: EmailRecipientCategory) => setForm(p => ({ ...p, category: v }))}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="moulding">Moulding</SelectItem>
                                    <SelectItem value="painting">Painting</SelectItem>
                                    <SelectItem value="both">Both</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={saving}>Cancel</Button>
                        <Button onClick={save} disabled={saving}>
                            {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            Save
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </Card>
    );
}
