"use client";

import { useEffect, useState } from "react";
import { DeliveryTeam, DeliveryTeamMember, FactoryTeam, FactoryTeamMember, SalesAgent } from "@/types";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Plus, Search, Pencil, Trash2, Briefcase, Loader2, Hash, Truck, Users, X } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { PageHeader } from "@/components/ui/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { Switch } from "@/components/ui/switch";

export default function AdminSalesTeamPage() {
    const { toast } = useToast();
    const [agents, setAgents] = useState<SalesAgent[]>([]);
    const [teams, setTeams] = useState<DeliveryTeam[]>([]);
    const [factoryTeams, setFactoryTeams] = useState<FactoryTeam[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [teamDialogOpen, setTeamDialogOpen] = useState(false);
    const [viewMode, setViewMode] = useState<"all" | "sales" | "delivery" | "factory">("all");

    const [editingId, setEditingId] = useState<string | null>(null);
    const [formData, setFormData] = useState({ name: "", code: "" });
    const [saving, setSaving] = useState(false);

    const [teamEditingId, setTeamEditingId] = useState<string | null>(null);
    const [teamFormData, setTeamFormData] = useState<{ name: string; code: string; members: DeliveryTeamMember[] }>({
        name: "",
        code: "",
        members: []
    });
    const [originalMembers, setOriginalMembers] = useState<DeliveryTeamMember[]>([]);
    const [teamSaving, setTeamSaving] = useState(false);

    const [factoryDialogOpen, setFactoryDialogOpen] = useState(false);
    const [factoryEditingId, setFactoryEditingId] = useState<string | null>(null);
    const [factoryFormData, setFactoryFormData] = useState<{ name: string; code: string; members: FactoryTeamMember[] }>({
        name: "",
        code: "",
        members: []
    });
    const [factoryOriginalMembers, setFactoryOriginalMembers] = useState<FactoryTeamMember[]>([]);
    const [factorySaving, setFactorySaving] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [agentsData, teamsData, factoryTeamsData] = await Promise.all([
                apiService.admin.salesAgents.list(),
                apiService.admin.deliveryTeams.list(),
                apiService.admin.factoryTeams.list()
            ]);
            setAgents(agentsData);
            setTeams(teamsData);
            setFactoryTeams(factoryTeamsData);
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load sales agents", description: error.message });
        } finally {
            setLoading(false);
        }
    };

    const filteredAgents = agents.filter(a => a.name.toLowerCase().includes(search.toLowerCase()) || a.code.toLowerCase().includes(search.toLowerCase()));
    const filteredTeams = teams.filter(t => t.name.toLowerCase().includes(search.toLowerCase()) || t.code.toLowerCase().includes(search.toLowerCase()));
    const filteredFactoryTeams = factoryTeams.filter(t => t.name.toLowerCase().includes(search.toLowerCase()) || t.code.toLowerCase().includes(search.toLowerCase()));

    const handleOpen = (agent?: SalesAgent) => {
        if (agent) {
            setEditingId(agent.id);
            setFormData({ name: agent.name, code: agent.code });
        } else {
            setEditingId(null);
            setFormData({ name: "", code: "" });
        }
        setIsDialogOpen(true);
    };

    const handleOpenTeam = (team?: DeliveryTeam) => {
        if (team) {
            setTeamEditingId(team.id);
            setTeamFormData({ name: team.name, code: team.code, members: team.members ? [...team.members] : [] });
            setOriginalMembers(team.members ? [...team.members] : []);
        } else {
            setTeamEditingId(null);
            setTeamFormData({ name: "", code: "", members: [] });
            setOriginalMembers([]);
        }
        setTeamDialogOpen(true);
    };

    const handleOpenFactoryTeam = (team?: FactoryTeam) => {
        if (team) {
            setFactoryEditingId(team.id);
            setFactoryFormData({ name: team.name, code: team.code, members: team.members ? [...team.members] : [] });
            setFactoryOriginalMembers(team.members ? [...team.members] : []);
        } else {
            setFactoryEditingId(null);
            setFactoryFormData({ name: "", code: "", members: [] });
            setFactoryOriginalMembers([]);
        }
        setFactoryDialogOpen(true);
    };

    const handleSave = async () => {
        if (!formData.name || !formData.code) return;

        try {
            setSaving(true);
            if (editingId) {
                await apiService.admin.salesAgents.update(editingId, formData);
                toast({ title: "Agent Updated" });
            } else {
                await apiService.admin.salesAgents.create(formData);
                toast({ title: "Agent Created" });
            }
            setIsDialogOpen(false);
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error saving agent", description: error.message });
        } finally {
            setSaving(false);
        }
    };

    const handleSaveTeam = async () => {
        if (!teamFormData.name || !teamFormData.code) return;

        try {
            setTeamSaving(true);
            const { members, ...payload } = teamFormData;

            let teamId = teamEditingId;

            if (teamEditingId) {
                await apiService.admin.deliveryTeams.update(teamEditingId, payload);
                toast({ title: "Team Updated" });
            } else {
                const newTeam = await apiService.admin.deliveryTeams.create(payload);
                teamId = newTeam.id;
                toast({ title: "Team Created" });
            }

            if (!teamId) throw new Error("Failed to resolve team ID");

            const currentMembers = members;
            const removed = originalMembers.filter(orig => !currentMembers.find(curr => curr.id === orig.id));
            for (const m of removed) {
                await apiService.admin.deliveryTeams.removeMember(teamId, m.id);
            }

            const added = currentMembers.filter(m => m.id.startsWith("temp-"));
            for (const m of added) {
                if (m.name.trim()) {
                    await apiService.admin.deliveryTeams.addMember(teamId, { name: m.name, phone: m.phone });
                }
            }

            const updated = currentMembers.filter(m => !m.id.startsWith("temp-"));
            for (const m of updated) {
                const orig = originalMembers.find(o => o.id === m.id);
                if (orig) {
                    if (orig.name !== m.name || orig.phone !== m.phone || orig.is_active !== m.is_active) {
                        await apiService.admin.deliveryTeams.updateMember(teamId, m.id, {
                            name: m.name,
                            phone: m.phone,
                            is_active: m.is_active
                        });
                    }
                }
            }

            setTeamDialogOpen(false);
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error saving team", description: error.message || "Unknown error" });
        } finally {
            setTeamSaving(false);
        }
    };

    const handleSaveFactoryTeam = async () => {
        if (!factoryFormData.name || !factoryFormData.code) return;

        try {
            setFactorySaving(true);
            const { members, ...payload } = factoryFormData;

            let teamId = factoryEditingId;

            if (factoryEditingId) {
                await apiService.admin.factoryTeams.update(factoryEditingId, payload);
                toast({ title: "Factory Team Updated" });
            } else {
                const newTeam = await apiService.admin.factoryTeams.create(payload);
                teamId = newTeam.id;
                toast({ title: "Factory Team Created" });
            }

            if (!teamId) throw new Error("Failed to resolve team ID");

            const currentMembers = members;
            const removed = factoryOriginalMembers.filter(orig => !currentMembers.find(curr => curr.id === orig.id));
            for (const m of removed) {
                await apiService.admin.factoryTeams.removeMember(teamId, m.id);
            }

            const added = currentMembers.filter(m => m.id.startsWith("temp-"));
            for (const m of added) {
                if (m.name.trim() && m.code.trim()) {
                    await apiService.admin.factoryTeams.addMember(teamId, { name: m.name, code: m.code, phone: m.phone });
                }
            }

            const updated = currentMembers.filter(m => !m.id.startsWith("temp-"));
            for (const m of updated) {
                const orig = factoryOriginalMembers.find(o => o.id === m.id);
                if (orig) {
                    if (orig.name !== m.name || orig.phone !== m.phone || orig.is_active !== m.is_active || orig.code !== m.code) {
                        await apiService.admin.factoryTeams.updateMember(teamId, m.id, {
                            name: m.name,
                            code: m.code,
                            phone: m.phone,
                            is_active: m.is_active
                        });
                    }
                }
            }

            setFactoryDialogOpen(false);
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error saving factory team", description: error.message || "Unknown error" });
        } finally {
            setFactorySaving(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (confirm("Delete this agent?")) {
            try {
                await apiService.admin.salesAgents.delete(id);
                toast({ title: "Agent Deleted" });
                loadData();
            } catch (error: any) {
                toast({ variant: "destructive", title: "Error deleting agent", description: error.message });
            }
        }
    };

    const handleDeleteTeam = async (id: string) => {
        if (confirm("Delete this team?")) {
            try {
                await apiService.admin.deliveryTeams.delete(id);
                toast({ title: "Team Deleted" });
                loadData();
            } catch (error: any) {
                toast({ variant: "destructive", title: "Error deleting team", description: error.message });
            }
        }
    };

    const handleDeleteFactoryTeam = async (id: string) => {
        if (confirm("Delete this factory team?")) {
            try {
                await apiService.admin.factoryTeams.delete(id);
                toast({ title: "Factory Team Deleted" });
                loadData();
            } catch (error: any) {
                toast({ variant: "destructive", title: "Error deleting factory team", description: error.message });
            }
        }
    };

    const addEmptyMember = () => {
        const newMember: DeliveryTeamMember = {
            id: `temp-${Date.now()}`,
            delivery_team_id: teamEditingId || "",
            name: "",
            phone: "",
            is_active: true
        };
        setTeamFormData(prev => ({ ...prev, members: [...prev.members, newMember] }));
    };

    const updateMemberField = (index: number, field: keyof DeliveryTeamMember, value: any) => {
        const newMembers = [...teamFormData.members];
        newMembers[index] = { ...newMembers[index], [field]: value };
        setTeamFormData(prev => ({ ...prev, members: newMembers }));
    };

    const removeMember = (index: number) => {
        setTeamFormData(prev => ({ ...prev, members: prev.members.filter((_, i) => i !== index) }));
    };

    const addEmptyFactoryMember = () => {
        const newMember: FactoryTeamMember = {
            id: `temp-${Date.now()}`,
            factory_team_id: factoryEditingId || "",
            name: "",
            code: "",
            phone: "",
            is_active: true
        };
        setFactoryFormData(prev => ({ ...prev, members: [...prev.members, newMember] }));
    };

    const updateFactoryMemberField = (index: number, field: keyof FactoryTeamMember, value: any) => {
        const newMembers = [...factoryFormData.members];
        newMembers[index] = { ...newMembers[index], [field]: value };
        setFactoryFormData(prev => ({ ...prev, members: newMembers }));
    };

    const removeFactoryMember = (index: number) => {
        setFactoryFormData(prev => ({ ...prev, members: prev.members.filter((_, i) => i !== index) }));
    };

    return (
        <div className="space-y-6">
            <PageHeader
                title="Teams"
                description="Manage sales and delivery teams in one place."
            >
                <div className="flex gap-2">
                    {(viewMode === "sales" || viewMode === "all") && (
                        <Button onClick={() => handleOpen()} className="gap-2">
                            <Plus size={16} /> Add Agent
                        </Button>
                    )}
                    {(viewMode === "delivery" || viewMode === "all") && (
                        <Button variant="outline" onClick={() => handleOpenTeam()} className="gap-2">
                            <Plus size={16} /> Add Delivery Team
                        </Button>
                    )}
                    {(viewMode === "factory" || viewMode === "all") && (
                        <Button variant="outline" onClick={() => handleOpenFactoryTeam()} className="gap-2">
                            <Plus size={16} /> Add Factory Team
                        </Button>
                    )}
                </div>
            </PageHeader>

            {/* Filters */}
            <div className="filter-bar bg-card border rounded-xl p-4">
                <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
                    <div className="flex gap-2">
                        <Button
                            type="button"
                            size="sm"
                            variant={viewMode === "all" ? "default" : "outline"}
                            onClick={() => setViewMode("all")}
                        >
                            All
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            variant={viewMode === "sales" ? "default" : "outline"}
                            onClick={() => setViewMode("sales")}
                        >
                            Sales Team
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            variant={viewMode === "delivery" ? "default" : "outline"}
                            onClick={() => setViewMode("delivery")}
                        >
                            Delivery Teams
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            variant={viewMode === "factory" ? "default" : "outline"}
                            onClick={() => setViewMode("factory")}
                        >
                            Factory Teams
                        </Button>
                    </div>
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder={
                                viewMode === "delivery"
                                    ? "Search delivery teams..."
                                    : viewMode === "factory"
                                        ? "Search factory teams..."
                                        : "Search agents..."
                            }
                            className="pl-9 max-w-md"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                        />
                    </div>
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center py-16">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            ) : (
                <div className="space-y-8">
                    {(viewMode === "sales" || viewMode === "all") && (
                        <>
                            {filteredAgents.length === 0 ? (
                                <EmptyState
                                    icon={Briefcase}
                                    title="No sales agents found"
                                    description="No agents match your search. Try adjusting your criteria or add a new agent."
                                />
                            ) : (
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {filteredAgents.map(agent => (
                                        <Card key={agent.id} className="group hover:shadow-md transition-shadow">
                                            <CardContent className="p-5">
                                                <div className="flex justify-between items-start mb-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="h-10 w-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center text-orange-600 dark:text-orange-400">
                                                            <Briefcase size={18} />
                                                        </div>
                                                        <div>
                                                            <h3 className="font-semibold text-foreground">{agent.name}</h3>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleOpen(agent)}>
                                                            <Pencil size={14} />
                                                        </Button>
                                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => handleDelete(agent.id)}>
                                                            <Trash2 size={14} />
                                                        </Button>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                    <Hash size={14} />
                                                    <span className="font-mono">{agent.code}</span>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            )}
                        </>
                    )}

                    {(viewMode === "delivery" || viewMode === "all") && (
                        <>
                            {filteredTeams.length === 0 ? (
                                <EmptyState
                                    icon={Truck}
                                    title="No delivery teams found"
                                    description="No teams match your search. Try adjusting your criteria or add a new team."
                                />
                            ) : (
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {filteredTeams.map(team => (
                                        <Card key={team.id} className="group hover:shadow-md transition-shadow">
                                            <CardContent className="p-5">
                                                <div className="flex justify-between items-start mb-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="h-10 w-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-600 dark:text-blue-400">
                                                            <Truck size={18} />
                                                        </div>
                                                        <div>
                                                            <h3 className="font-semibold text-foreground">{team.name}</h3>
                                                            <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground">
                                                                <Users size={12} />
                                                                <span>{team.members?.length || 0} members</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleOpenTeam(team)}>
                                                            <Pencil size={14} />
                                                        </Button>
                                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => handleDeleteTeam(team.id)}>
                                                            <Trash2 size={14} />
                                                        </Button>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                    <Hash size={14} />
                                                    <span className="font-mono">{team.code}</span>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            )}
                        </>
                    )}

                    {(viewMode === "factory" || viewMode === "all") && (
                        <>
                            {filteredFactoryTeams.length === 0 ? (
                                <EmptyState
                                    icon={Users}
                                    title="No factory teams found"
                                    description="No factory teams match your search. Try adjusting your criteria or add a new team."
                                />
                            ) : (
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {filteredFactoryTeams.map(team => (
                                        <Card key={team.id} className="group hover:shadow-md transition-shadow">
                                            <CardContent className="p-5">
                                                <div className="flex justify-between items-start mb-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="h-10 w-10 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                                                            <Users size={18} />
                                                        </div>
                                                        <div>
                                                            <h3 className="font-semibold text-foreground">{team.name}</h3>
                                                            <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground">
                                                                <Users size={12} />
                                                                <span>{team.members?.length || 0} members</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleOpenFactoryTeam(team)}>
                                                            <Pencil size={14} />
                                                        </Button>
                                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => handleDeleteFactoryTeam(team.id)}>
                                                            <Trash2 size={14} />
                                                        </Button>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                    <Hash size={14} />
                                                    <span className="font-mono">{team.code}</span>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}

            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center text-orange-600 dark:text-orange-400">
                                <Briefcase size={20} />
                            </div>
                            {editingId ? "Edit Agent" : "Add Agent"}
                        </DialogTitle>
                        <DialogDescription>
                            {editingId ? "Update sales agent information below." : "Enter agent details to add them to the team."}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Name</Label>
                            <Input
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Agent name"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Code</Label>
                            <Input
                                value={formData.code}
                                onChange={e => setFormData({ ...formData, code: e.target.value })}
                                placeholder="Unique access code"
                            />
                            <p className="text-xs text-muted-foreground">This code is used for agent identification</p>
                        </div>
                    </div>
                    <DialogFooter className="gap-2 sm:gap-0">
                        <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                        <Button onClick={handleSave} disabled={saving}>
                            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {editingId ? "Save Changes" : "Add Agent"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            <Dialog open={teamDialogOpen} onOpenChange={setTeamDialogOpen}>
                <DialogContent className="max-w-xl">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                                <Truck size={20} />
                            </div>
                            {teamEditingId ? "Edit Team" : "Add Team"}
                        </DialogTitle>
                        <DialogDescription>
                            {teamEditingId ? "Update delivery team information below." : "Enter team details to create a new delivery team."}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label className="text-sm font-medium">Name</Label>
                                <Input
                                    value={teamFormData.name}
                                    onChange={e => setTeamFormData({ ...teamFormData, name: e.target.value })}
                                    placeholder="Team Name"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label className="text-sm font-medium">Code</Label>
                                <Input
                                    value={teamFormData.code}
                                    onChange={e => setTeamFormData({ ...teamFormData, code: e.target.value })}
                                    placeholder="Access Code"
                                />
                            </div>
                        </div>

                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <Label className="text-sm font-medium">Team Members</Label>
                                <Button size="sm" variant="secondary" onClick={addEmptyMember} type="button">
                                    <Plus size={14} className="mr-1" /> Add Member
                                </Button>
                            </div>

                            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                {teamFormData.members.length === 0 ? (
                                    <div className="text-center py-6 border rounded-lg border-dashed text-muted-foreground text-sm">
                                        No members added yet.
                                    </div>
                                ) : (
                                    teamFormData.members.map((m, i) => (
                                        <div key={m.id || i} className="flex gap-2 items-start p-2 rounded-lg border bg-muted/20">
                                            <div className="grid gap-2 flex-1 sm:grid-cols-2">
                                                <Input
                                                    value={m.name}
                                                    onChange={e => updateMemberField(i, "name", e.target.value)}
                                                    placeholder="Name"
                                                    className="h-8"
                                                />
                                                <Input
                                                    value={m.phone || ""}
                                                    onChange={e => updateMemberField(i, "phone", e.target.value)}
                                                    placeholder="Phone (optional)"
                                                    className="h-8"
                                                />
                                            </div>
                                            <div className="flex items-center gap-1 pt-0.5">
                                                <Switch
                                                    checked={m.is_active !== false}
                                                    onCheckedChange={c => updateMemberField(i, "is_active", c)}
                                                    className="scale-75"
                                                    title="Active Status"
                                                />
                                                <Button
                                                    size="icon"
                                                    variant="ghost"
                                                    className="h-7 w-7 text-muted-foreground hover:text-destructive"
                                                    onClick={() => removeMember(i)}
                                                >
                                                    <X size={14} />
                                                </Button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                    <DialogFooter className="gap-2 sm:gap-0">
                        <Button variant="outline" onClick={() => setTeamDialogOpen(false)}>Cancel</Button>
                        <Button onClick={handleSaveTeam} disabled={teamSaving}>
                            {teamSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {teamEditingId ? "Save Changes" : "Create Team"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            <Dialog open={factoryDialogOpen} onOpenChange={setFactoryDialogOpen}>
                <DialogContent className="max-w-xl">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                                <Users size={20} />
                            </div>
                            {factoryEditingId ? "Edit Factory Team" : "Add Factory Team"}
                        </DialogTitle>
                        <DialogDescription>
                            {factoryEditingId ? "Update factory team information below." : "Enter team details to create a new factory team."}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label className="text-sm font-medium">Name</Label>
                                <Input
                                    value={factoryFormData.name}
                                    onChange={e => setFactoryFormData({ ...factoryFormData, name: e.target.value })}
                                    placeholder="Team Name"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label className="text-sm font-medium">Team Code</Label>
                                <Input
                                    value={factoryFormData.code}
                                    onChange={e => setFactoryFormData({ ...factoryFormData, code: e.target.value })}
                                    placeholder="Team Code"
                                />
                            </div>
                        </div>

                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <Label className="text-sm font-medium">Team Members</Label>
                                <Button size="sm" variant="secondary" onClick={addEmptyFactoryMember} type="button">
                                    <Plus size={14} className="mr-1" /> Add Member
                                </Button>
                            </div>

                            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                {factoryFormData.members.length === 0 ? (
                                    <div className="text-center py-6 border rounded-lg border-dashed text-muted-foreground text-sm">
                                        No members added yet.
                                    </div>
                                ) : (
                                    factoryFormData.members.map((m, i) => (
                                        <div key={m.id || i} className="flex gap-2 items-start p-2 rounded-lg border bg-muted/20">
                                            <div className="grid gap-2 flex-1 sm:grid-cols-3">
                                                <Input
                                                    value={m.name}
                                                    onChange={e => updateFactoryMemberField(i, "name", e.target.value)}
                                                    placeholder="Name"
                                                    className="h-8"
                                                />
                                                <Input
                                                    value={m.code}
                                                    onChange={e => updateFactoryMemberField(i, "code", e.target.value)}
                                                    placeholder="Member Code"
                                                    className="h-8"
                                                />
                                                <Input
                                                    value={m.phone || ""}
                                                    onChange={e => updateFactoryMemberField(i, "phone", e.target.value)}
                                                    placeholder="Phone (optional)"
                                                    className="h-8"
                                                />
                                            </div>
                                            <div className="flex items-center gap-1 pt-0.5">
                                                <Switch
                                                    checked={m.is_active !== false}
                                                    onCheckedChange={c => updateFactoryMemberField(i, "is_active", c)}
                                                    className="scale-75"
                                                    title="Active Status"
                                                />
                                                <Button
                                                    size="icon"
                                                    variant="ghost"
                                                    className="h-7 w-7 text-muted-foreground hover:text-destructive"
                                                    onClick={() => removeFactoryMember(i)}
                                                >
                                                    <X size={14} />
                                                </Button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                    <DialogFooter className="gap-2 sm:gap-0">
                        <Button variant="outline" onClick={() => setFactoryDialogOpen(false)}>Cancel</Button>
                        <Button onClick={handleSaveFactoryTeam} disabled={factorySaving}>
                            {factorySaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {factoryEditingId ? "Save Changes" : "Create Team"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
