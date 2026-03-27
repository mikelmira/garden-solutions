"use client";

import { useEffect, useState } from "react";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Plus, Search, Pencil, Trash2, Store as StoreIcon, Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PageHeader } from "@/components/ui/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";

interface Store {
    id: string;
    name: string;
    code: string;
    store_type: string;
    is_active: boolean;
}

export default function AdminStoresPage() {
    const { toast } = useToast();
    const [stores, setStores] = useState<Store[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [isDialogOpen, setIsDialogOpen] = useState(false);

    // Form State
    const [editingId, setEditingId] = useState<string | null>(null);
    const [formData, setFormData] = useState<Partial<Store>>({ name: "", code: "", store_type: "nursery", is_active: true });
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const data = await apiService.stores.list();
            setStores(data);
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load stores", description: error.message });
        } finally {
            setLoading(false);
        }
    };

    const filtered = stores.filter(s => s.name.toLowerCase().includes(search.toLowerCase()) || s.code.toLowerCase().includes(search.toLowerCase()));

    const handleOpen = (store?: Store) => {
        if (store) {
            setEditingId(store.id);
            setFormData({ ...store });
        } else {
            setEditingId(null);
            setFormData({ name: "", code: "", store_type: "nursery", is_active: true });
        }
        setIsDialogOpen(true);
    };

    const handleSave = async () => {
        if (!formData.name || !formData.code) return;

        try {
            setSaving(true);
            if (editingId) {
                await apiService.stores.update(editingId, formData);
                toast({ title: "Store Updated" });
            } else {
                await apiService.stores.create(formData);
                toast({ title: "Store Created" });
            }
            setIsDialogOpen(false);
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error saving store", description: error.message });
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (confirm("Delete this store?")) {
            try {
                await apiService.stores.delete(id);
                toast({ title: "Store Deleted" });
                loadData();
            } catch (error: any) {
                toast({ variant: "destructive", title: "Error deleting store", description: error.message });
            }
        }
    };

    // Get store type badge
    const getTypeBadgeClass = (type: string) => {
        switch (type) {
            case "nursery": return "status-badge-success";
            case "shopify": return "status-badge-info";
            default: return "status-badge-neutral";
        }
    };

    return (
        <div className="space-y-6">
            <PageHeader
                title="Stores"
                description="Manage internal stores and sales channels."
            >
                <Button onClick={() => handleOpen()} className="gap-2">
                    <Plus size={16} /> Add Store
                </Button>
            </PageHeader>

            {/* Search Bar */}
            <div className="filter-bar bg-card border rounded-xl p-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search stores..."
                        className="pl-9 max-w-md"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center py-16">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            ) : filtered.length === 0 ? (
                <EmptyState
                    icon={StoreIcon}
                    title="No stores found"
                    description="No stores match your search. Try adjusting your criteria or add a new store."
                />
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {filtered.map(store => (
                        <Card key={store.id} className="group hover:shadow-md transition-shadow">
                            <CardContent className="p-5">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center text-purple-600 dark:text-purple-400">
                                            <StoreIcon size={18} />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-foreground">{store.name}</h3>
                                            <span className={cn("status-badge mt-1", getTypeBadgeClass(store.store_type))}>
                                                {store.store_type}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleOpen(store)}>
                                            <Pencil size={14} />
                                        </Button>
                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => handleDelete(store.id)}>
                                            <Trash2 size={14} />
                                        </Button>
                                    </div>
                                </div>
                                <div className="text-sm">
                                    <span className="font-mono text-xs bg-muted px-2 py-1 rounded">{store.code}</span>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
                                <StoreIcon size={20} />
                            </div>
                            {editingId ? "Edit Store" : "Add Store"}
                        </DialogTitle>
                        <DialogDescription>
                            {editingId ? "Update store information below." : "Enter store details to add it to the system."}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Name</Label>
                            <Input
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Store name"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Code</Label>
                            <Input
                                value={formData.code}
                                onChange={e => setFormData({ ...formData, code: e.target.value })}
                                placeholder="Store code"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Type</Label>
                            <Select value={formData.store_type} onValueChange={v => setFormData({ ...formData, store_type: v })}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="nursery">Nursery</SelectItem>
                                    <SelectItem value="shopify">Shopify</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter className="gap-2 sm:gap-0">
                        <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                        <Button onClick={handleSave} disabled={saving}>
                            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {editingId ? "Save Changes" : "Add Store"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
