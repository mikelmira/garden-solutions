"use client";

import { useEffect, useState } from "react";
import { Client } from "@/types";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Plus, Search, Pencil, Trash2, User, Loader2, Users, MapPin, Store as StoreIcon, ShoppingBag, Phone, Mail } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { PageHeader } from "@/components/ui/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface Store {
    id: string;
    name: string;
    code: string;
    store_type: string;
    is_active: boolean;
    price_tier_id?: string;
}

export default function AdminClientsPage() {
    const { toast } = useToast();
    const [clients, setClients] = useState<Client[]>([]);
    const [stores, setStores] = useState<Store[]>([]);
    const [customers, setCustomers] = useState<any[]>([]);
    const [tiers, setTiers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [viewMode, setViewMode] = useState<"all" | "clients" | "stores" | "customers">("all");

    // Form State
    const [editingId, setEditingId] = useState<string | null>(null);
    const [formData, setFormData] = useState({ name: "", price_tier_id: "", address: "" });
    const [saving, setSaving] = useState(false);

    // Store Form State
    const [storeDialogOpen, setStoreDialogOpen] = useState(false);
    const [storeEditingId, setStoreEditingId] = useState<string | null>(null);
    const [storeFormData, setStoreFormData] = useState<Partial<Store> & { price_tier_id?: string }>({
        name: "", code: "", store_type: "nursery", is_active: true, price_tier_id: ""
    });
    const [storeSaving, setStoreSaving] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [clientsData, tiersData, storesData, customersData] = await Promise.all([
                apiService.clients.list(),
                apiService.priceTiers.list(),
                apiService.stores.list(),
                apiService.shopify.getCustomers().catch(() => []),
            ]);
            setClients(clientsData);
            setTiers(tiersData.filter(t => t.is_active));
            setStores(storesData);
            setCustomers(customersData);

            // Set default tier if needed
            if (tiersData.length > 0 && !formData.price_tier_id) {
                // Check if existing "A" is valid, otherwise use first
                const defaultId = tiersData[0].id;
                setFormData(prev => ({ ...prev, price_tier_id: defaultId }));
            }
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load data", description: error.message });
        } finally {
            setLoading(false);
        }
    };

    const filteredClients = clients.filter(c => c.name.toLowerCase().includes(search.toLowerCase()));
    const filteredStores = stores.filter(s => s.name.toLowerCase().includes(search.toLowerCase()) || s.code.toLowerCase().includes(search.toLowerCase()));
    const filteredCustomers = customers.filter(c =>
        (c.name || "").toLowerCase().includes(search.toLowerCase()) ||
        (c.email || "").toLowerCase().includes(search.toLowerCase()) ||
        (c.phone || "").toLowerCase().includes(search.toLowerCase())
    );

    const handleOpen = (client?: Client) => {
        if (client) {
            setEditingId(client.id);
            setFormData({ name: client.name, price_tier_id: client.price_tier_id, address: client.address || "" });
        } else {
            setEditingId(null);
            const defaultTier = tiers.length > 0 ? tiers[0].id : "";
            setFormData({ name: "", price_tier_id: defaultTier, address: "" });
        }
        setIsDialogOpen(true);
    };

    const handleOpenStore = (store?: Store & { price_tier_id?: string }) => {
        if (store) {
            setStoreEditingId(store.id);
            setStoreFormData({ ...store });
        } else {
            setStoreEditingId(null);
            const defaultTier = tiers.length > 0 ? tiers[0].id : "";
            setStoreFormData({ name: "", code: "", store_type: "nursery", is_active: true, price_tier_id: defaultTier });
        }
        setStoreDialogOpen(true);
    };

    const handleSave = async () => {
        if (!formData.name) return;

        try {
            setSaving(true);
            if (editingId) {
                await apiService.clients.update(editingId, formData);
                toast({ title: "Client Updated" });
            } else {
                await apiService.clients.create(formData);
                toast({ title: "Client Created" });
            }
            setIsDialogOpen(false);
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error saving client", description: error.message });
        } finally {
            setSaving(false);
        }
    };

    const handleStoreSave = async () => {
        if (!storeFormData.name || !storeFormData.code) return;

        try {
            setStoreSaving(true);
            if (storeEditingId) {
                await apiService.stores.update(storeEditingId, storeFormData);
                toast({ title: "Store Updated" });
            } else {
                await apiService.stores.create(storeFormData);
                toast({ title: "Store Created" });
            }
            setStoreDialogOpen(false);
            loadData();
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error saving store", description: error.message });
        } finally {
            setStoreSaving(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (confirm("Delete this client?")) {
            try {
                await apiService.clients.delete(id);
                toast({ title: "Client Deleted" });
                loadData();
            } catch (error: any) {
                toast({ variant: "destructive", title: "Error deleting client", description: error.message });
            }
        }
    };

    const handleStoreDelete = async (id: string) => {
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
                title="Clients"
                description="Manage client directory and pricing tiers."
            >
                <div className="flex gap-2">
                    {(viewMode === "clients" || viewMode === "all") && (
                        <Button onClick={() => handleOpen()} className="gap-2">
                            <Plus size={16} /> Add Client
                        </Button>
                    )}
                    {(viewMode === "stores" || viewMode === "all") && (
                        <Button variant="outline" onClick={() => handleOpenStore()} className="gap-2">
                            <Plus size={16} /> Add Store
                        </Button>
                    )}
                    {viewMode === "customers" && (
                        <span className="text-sm text-muted-foreground self-center">
                            {customers.length} customer{customers.length !== 1 ? "s" : ""} from Shopify
                        </span>
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
                            variant={viewMode === "clients" ? "default" : "outline"}
                            onClick={() => setViewMode("clients")}
                        >
                            Clients
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            variant={viewMode === "stores" ? "default" : "outline"}
                            onClick={() => setViewMode("stores")}
                        >
                            Stores
                        </Button>
                        <Button
                            type="button"
                            size="sm"
                            variant={viewMode === "customers" ? "default" : "outline"}
                            onClick={() => setViewMode("customers")}
                        >
                            Customers
                        </Button>
                    </div>
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder={viewMode === "customers" ? "Search customers..." : viewMode === "stores" ? "Search stores..." : "Search clients..."}
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
                    {(viewMode === "clients" || viewMode === "all") && (
                        <>
                            {filteredClients.length === 0 ? (
                                <EmptyState
                                    icon={Users}
                                    title="No clients found"
                                    description="No clients match your search. Try adjusting your search criteria or add a new client."
                                />
                            ) : (
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {filteredClients.map(client => (
                                        <Card key={client.id} className="group hover:shadow-md transition-shadow">
                                            <CardContent className="p-5">
                                                <div className="flex justify-between items-start mb-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className="h-10 w-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
                                                            <User size={18} />
                                                        </div>
                                                        <div>
                                                            <h3 className="font-semibold text-foreground">{client.name}</h3>
                                                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-secondary text-secondary-foreground mt-1">
                                                                {tiers.find(t => t.id === client.price_tier_id)?.name || "Unknown"}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleOpen(client)}>
                                                            <Pencil size={14} />
                                                        </Button>
                                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => handleDelete(client.id)}>
                                                            <Trash2 size={14} />
                                                        </Button>
                                                    </div>
                                                </div>
                                                {client.address && (
                                                    <div className="text-sm text-muted-foreground flex items-start gap-2">
                                                        <MapPin size={14} className="mt-0.5 flex-shrink-0" />
                                                        <span>{client.address}</span>
                                                    </div>
                                                )}
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            )}
                        </>
                    )}

                    {(viewMode === "stores" || viewMode === "all") && (
                        <>
                            {filteredStores.length === 0 ? (
                                <EmptyState
                                    icon={StoreIcon}
                                    title="No stores found"
                                    description="No stores match your search. Try adjusting your criteria or add a new store."
                                />
                            ) : (
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {filteredStores.map(store => (
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
                                                            {store.price_tier_id && (
                                                                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-secondary text-secondary-foreground">
                                                                    {tiers.find(t => t.id === store.price_tier_id)?.name}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleOpenStore(store)}>
                                                            <Pencil size={14} />
                                                        </Button>
                                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => handleStoreDelete(store.id)}>
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
                        </>
                    )}

                    {viewMode === "customers" && (
                        <>
                            {filteredCustomers.length === 0 ? (
                                <EmptyState
                                    icon={ShoppingBag}
                                    title="No customers found"
                                    description="No Shopify customers match your search."
                                />
                            ) : (
                                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                                    {filteredCustomers.map((customer, idx) => (
                                        <Card key={customer.email || idx} className="group hover:shadow-md transition-shadow">
                                            <CardContent className="p-5">
                                                <div className="flex items-center gap-3 mb-4">
                                                    <div className="h-10 w-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center text-orange-600 dark:text-orange-400">
                                                        <ShoppingBag size={18} />
                                                    </div>
                                                    <div>
                                                        <h3 className="font-semibold text-foreground">{customer.name || "Unknown"}</h3>
                                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 mt-1">
                                                            Shopify Customer
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="space-y-2 text-sm text-muted-foreground">
                                                    {customer.email && (
                                                        <div className="flex items-center gap-2">
                                                            <Mail size={14} className="flex-shrink-0" />
                                                            <span className="truncate">{customer.email}</span>
                                                        </div>
                                                    )}
                                                    {customer.phone && (
                                                        <div className="flex items-center gap-2">
                                                            <Phone size={14} className="flex-shrink-0" />
                                                            <span>{customer.phone}</span>
                                                        </div>
                                                    )}
                                                    {customer.address && (
                                                        <div className="flex items-start gap-2">
                                                            <MapPin size={14} className="mt-0.5 flex-shrink-0" />
                                                            <span className="line-clamp-2">{customer.address}</span>
                                                        </div>
                                                    )}
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
                            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                                <User size={20} />
                            </div>
                            {editingId ? "Edit Client" : "Add Client"}
                        </DialogTitle>
                        <DialogDescription>
                            {editingId ? "Update client information below." : "Enter client details to add them to the directory."}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Name</Label>
                            <Input
                                value={formData.name}
                                onChange={e => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Client name"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Price Tier</Label>
                            <select
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                value={formData.price_tier_id}
                                onChange={e => setFormData({ ...formData, price_tier_id: e.target.value })}
                            >
                                <option value="" disabled>Select a tier</option>
                                {tiers.map(t => (
                                    <option key={t.id} value={t.id}>
                                        {t.name} ({(t.discount_percentage * 100).toFixed(0)}%)
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Address</Label>
                            <Input
                                value={formData.address}
                                onChange={e => setFormData({ ...formData, address: e.target.value })}
                                placeholder="Client address (optional)"
                            />
                        </div>
                    </div>
                    <DialogFooter className="gap-2 sm:gap-0">
                        <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                        <Button onClick={handleSave} disabled={saving}>
                            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {editingId ? "Save Changes" : "Add Client"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            <Dialog open={storeDialogOpen} onOpenChange={setStoreDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
                                <StoreIcon size={20} />
                            </div>
                            {storeEditingId ? "Edit Store" : "Add Store"}
                        </DialogTitle>
                        <DialogDescription>
                            {storeEditingId ? "Update store information below." : "Enter store details to add it to the system."}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Name</Label>
                            <Input
                                value={storeFormData.name}
                                onChange={e => setStoreFormData({ ...storeFormData, name: e.target.value })}
                                placeholder="Store name"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Code</Label>
                            <Input
                                value={storeFormData.code}
                                onChange={e => setStoreFormData({ ...storeFormData, code: e.target.value })}
                                placeholder="Store code"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Type</Label>
                            <Select value={storeFormData.store_type} onValueChange={v => setStoreFormData({ ...storeFormData, store_type: v })}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="nursery">Nursery</SelectItem>
                                    <SelectItem value="shopify">Shopify</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <Label className="text-sm font-medium">Price Tier</Label>
                            <select
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                value={storeFormData.price_tier_id}
                                onChange={e => setStoreFormData({ ...storeFormData, price_tier_id: e.target.value })}
                            >
                                <option value="" disabled>Select a tier</option>
                                {tiers.map(t => (
                                    <option key={t.id} value={t.id}>
                                        {t.name} ({(t.discount_percentage * 100).toFixed(0)}%)
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <DialogFooter className="gap-2 sm:gap-0">
                        <Button variant="outline" onClick={() => setStoreDialogOpen(false)}>Cancel</Button>
                        <Button onClick={handleStoreSave} disabled={storeSaving}>
                            {storeSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            {storeEditingId ? "Save Changes" : "Add Store"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
