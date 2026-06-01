"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Save, Plus, Trash2, Box, ArrowLeft } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";

interface Variant {
    id: string;
    title?: string | null;
    shopify_sku?: string | null;
    price?: string | null;
    option1?: string | null;
    option2?: string | null;
    option3?: string | null;
    inventory_quantity?: number | null;
    inventory_item_id?: number | null;
    mapping_status?: string;
}

interface Product {
    id: string;
    shopify_product_id: number;
    title: string;
    product_type?: string | null;
    vendor?: string | null;
    shopify_status?: string | null;
    shopify_handle?: string | null;
    variants: Variant[];
}

export default function AdminShopifyProductDetailPage() {
    const params = useParams();
    const router = useRouter();
    const { toast } = useToast();
    const productId = params?.id as string;

    const [product, setProduct] = useState<Product | null>(null);
    const [loading, setLoading] = useState(true);
    const [savingProduct, setSavingProduct] = useState(false);

    // Edit buffers
    const [pForm, setPForm] = useState<{ title: string; product_type: string; vendor: string; status: string }>({
        title: "",
        product_type: "",
        vendor: "",
        status: "active",
    });

    // Variant edit state — keyed by variant id. Partial<Variant> already covers
    // every editable field (title/price/sku/options + inventory_quantity).
    const [variantBuffers, setVariantBuffers] = useState<Record<string, Partial<Variant>>>({});
    const [savingVariantId, setSavingVariantId] = useState<string | null>(null);

    // Add variant dialog
    const [addOpen, setAddOpen] = useState(false);
    const [addForm, setAddForm] = useState<{ title: string; price: string; sku: string; option1: string; option2: string; option3: string }>({
        title: "",
        price: "0.00",
        sku: "",
        option1: "",
        option2: "",
        option3: "",
    });
    const [addSaving, setAddSaving] = useState(false);

    useEffect(() => { if (productId) load(); }, [productId]);

    const load = async () => {
        try {
            setLoading(true);
            const data = await apiService.admin.shopify.getProduct(productId);
            setProduct(data);
            setPForm({
                title: data.title || "",
                product_type: data.product_type || "",
                vendor: data.vendor || "",
                status: data.shopify_status || "active",
            });
            setVariantBuffers({});
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load product", description: error.message });
        } finally {
            setLoading(false);
        }
    };

    const saveProduct = async () => {
        if (!product) return;
        try {
            setSavingProduct(true);
            const updated = await apiService.admin.shopify.updateProduct(product.id, pForm);
            setProduct(updated);
            toast({ title: "Saved", description: "Product pushed to Shopify." });
        } catch (error: any) {
            toast({ variant: "destructive", title: "Push failed", description: error.message });
        } finally {
            setSavingProduct(false);
        }
    };

    const updateVariantBuffer = (variantId: string, patch: Partial<Variant>) => {
        setVariantBuffers(prev => ({ ...prev, [variantId]: { ...prev[variantId], ...patch } }));
    };

    const saveVariant = async (v: Variant) => {
        const buffer = variantBuffers[v.id] || {};
        // Split: title/price/sku/options go via updateVariant; inventory_quantity via setInventory
        const editable: any = {
            title: buffer.title,
            price: buffer.price,
            sku: buffer.shopify_sku,
            option1: buffer.option1,
            option2: buffer.option2,
            option3: buffer.option3,
        };
        // Drop undefined
        Object.keys(editable).forEach(k => editable[k] === undefined && delete editable[k]);

        try {
            setSavingVariantId(v.id);

            let updated = v;
            if (Object.keys(editable).length > 0) {
                updated = await apiService.admin.shopify.updateVariant(v.id, editable);
            }
            // Inventory separately
            if (buffer.inventory_quantity !== undefined && buffer.inventory_quantity !== v.inventory_quantity) {
                updated = await apiService.admin.shopify.setInventory(v.id, Number(buffer.inventory_quantity));
            }

            setProduct(prev => prev ? { ...prev, variants: prev.variants.map(x => x.id === v.id ? { ...x, ...updated } : x) } : prev);
            setVariantBuffers(prev => { const next = { ...prev }; delete next[v.id]; return next; });
            toast({ title: "Variant pushed to Shopify" });
        } catch (error: any) {
            toast({ variant: "destructive", title: "Push failed", description: error.message });
        } finally {
            setSavingVariantId(null);
        }
    };

    const deleteVariant = async (v: Variant) => {
        if (!product) return;
        if (!confirm(`Delete variant "${v.title || v.shopify_sku || v.id}" from Shopify? This cannot be undone.`)) return;
        try {
            await apiService.admin.shopify.deleteVariant(v.id);
            setProduct(prev => prev ? { ...prev, variants: prev.variants.filter(x => x.id !== v.id) } : prev);
            toast({ title: "Variant deleted" });
        } catch (error: any) {
            toast({ variant: "destructive", title: "Delete failed", description: error.message });
        }
    };

    const createVariant = async () => {
        if (!product) return;
        try {
            setAddSaving(true);
            const newV = await apiService.admin.shopify.createVariant(product.id, addForm);
            setProduct(prev => prev ? { ...prev, variants: [...prev.variants, newV] } : prev);
            setAddOpen(false);
            setAddForm({ title: "", price: "0.00", sku: "", option1: "", option2: "", option3: "" });
            toast({ title: "Variant created on Shopify" });
        } catch (error: any) {
            toast({ variant: "destructive", title: "Create failed", description: error.message });
        } finally {
            setAddSaving(false);
        }
    };

    if (loading || !product) {
        return (
            <div className="flex h-[40vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between gap-4">
                <Button variant="ghost" size="sm" onClick={() => router.back()} className="gap-1">
                    <ArrowLeft className="h-4 w-4" /> Back
                </Button>
                <div className="text-xs text-muted-foreground font-mono">
                    shopify_product_id: {product.shopify_product_id}
                </div>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Product</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    <div>
                        <Label htmlFor="p-title">Title</Label>
                        <Input id="p-title" value={pForm.title} onChange={e => setPForm(p => ({ ...p, title: e.target.value }))} />
                    </div>
                    <div className="grid sm:grid-cols-3 gap-3">
                        <div>
                            <Label htmlFor="p-type">Product type</Label>
                            <Input id="p-type" value={pForm.product_type} onChange={e => setPForm(p => ({ ...p, product_type: e.target.value }))} />
                        </div>
                        <div>
                            <Label htmlFor="p-vendor">Vendor</Label>
                            <Input id="p-vendor" value={pForm.vendor} onChange={e => setPForm(p => ({ ...p, vendor: e.target.value }))} />
                        </div>
                        <div>
                            <Label>Status</Label>
                            <Select value={pForm.status} onValueChange={v => setPForm(p => ({ ...p, status: v }))}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="active">Active</SelectItem>
                                    <SelectItem value="draft">Draft</SelectItem>
                                    <SelectItem value="archived">Archived</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <div className="flex justify-end pt-2">
                        <Button onClick={saveProduct} disabled={savingProduct}>
                            {savingProduct ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                            Push to Shopify
                        </Button>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                    <CardTitle className="flex items-center gap-2">
                        <Box className="h-5 w-5 text-muted-foreground" />
                        Variants ({product.variants.length})
                    </CardTitle>
                    <Button size="sm" onClick={() => setAddOpen(true)}>
                        <Plus className="h-4 w-4 mr-1" /> Add variant
                    </Button>
                </CardHeader>
                <CardContent className="space-y-3">
                    {product.variants.length === 0 && (
                        <div className="text-sm text-muted-foreground py-6 text-center">No variants yet.</div>
                    )}
                    {product.variants.map(v => {
                        const buf = variantBuffers[v.id] || {};
                        const value = (k: keyof Variant) => (buf as any)[k] ?? (v as any)[k] ?? "";
                        const inventoryValue = buf.inventory_quantity ?? v.inventory_quantity ?? 0;
                        const hasChanges = Object.keys(buf).some(k => (buf as any)[k] !== undefined && (buf as any)[k] !== (v as any)[k]);
                        return (
                            <div key={v.id} className="border rounded-lg p-3 space-y-3">
                                <div className="grid sm:grid-cols-3 gap-3">
                                    <div>
                                        <Label>Title</Label>
                                        <Input
                                            value={value("title")}
                                            onChange={e => updateVariantBuffer(v.id, { title: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label>SKU</Label>
                                        <Input
                                            value={value("shopify_sku")}
                                            onChange={e => updateVariantBuffer(v.id, { shopify_sku: e.target.value })}
                                            className="font-mono"
                                        />
                                    </div>
                                    <div>
                                        <Label>Price (ZAR)</Label>
                                        <Input
                                            type="number"
                                            step="0.01"
                                            value={value("price")}
                                            onChange={e => updateVariantBuffer(v.id, { price: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <div className="grid sm:grid-cols-4 gap-3">
                                    <div>
                                        <Label>Option 1</Label>
                                        <Input
                                            value={value("option1")}
                                            onChange={e => updateVariantBuffer(v.id, { option1: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label>Option 2</Label>
                                        <Input
                                            value={value("option2")}
                                            onChange={e => updateVariantBuffer(v.id, { option2: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label>Option 3</Label>
                                        <Input
                                            value={value("option3")}
                                            onChange={e => updateVariantBuffer(v.id, { option3: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <Label>Stock on hand</Label>
                                        <Input
                                            type="number"
                                            value={inventoryValue}
                                            onChange={e => updateVariantBuffer(v.id, { inventory_quantity: Number(e.target.value) })}
                                        />
                                    </div>
                                </div>
                                <div className="flex items-center justify-between">
                                    <div className="text-xs text-muted-foreground font-mono">
                                        variant_id: {v.id.slice(0, 8)}…
                                        {v.inventory_item_id ? ` · inventory_item_id: ${v.inventory_item_id}` : " · no inventory_item_id (sync first)"}
                                    </div>
                                    <div className="flex gap-2">
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => deleteVariant(v)}
                                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                        >
                                            <Trash2 className="h-4 w-4 mr-1" /> Delete
                                        </Button>
                                        <Button
                                            size="sm"
                                            onClick={() => saveVariant(v)}
                                            disabled={savingVariantId === v.id || !hasChanges}
                                        >
                                            {savingVariantId === v.id ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                                            Push to Shopify
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </CardContent>
            </Card>

            <Dialog open={addOpen} onOpenChange={setAddOpen}>
                <DialogContent className="sm:max-w-lg">
                    <DialogHeader>
                        <DialogTitle>Add variant</DialogTitle>
                        <DialogDescription>This will create the variant on Shopify immediately.</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <Label>Title</Label>
                                <Input value={addForm.title} onChange={e => setAddForm(f => ({ ...f, title: e.target.value }))} />
                            </div>
                            <div>
                                <Label>Price (ZAR)</Label>
                                <Input type="number" step="0.01" value={addForm.price} onChange={e => setAddForm(f => ({ ...f, price: e.target.value }))} />
                            </div>
                        </div>
                        <div>
                            <Label>SKU</Label>
                            <Input value={addForm.sku} onChange={e => setAddForm(f => ({ ...f, sku: e.target.value }))} className="font-mono" />
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                            <div>
                                <Label>Option 1</Label>
                                <Input value={addForm.option1} onChange={e => setAddForm(f => ({ ...f, option1: e.target.value }))} />
                            </div>
                            <div>
                                <Label>Option 2</Label>
                                <Input value={addForm.option2} onChange={e => setAddForm(f => ({ ...f, option2: e.target.value }))} />
                            </div>
                            <div>
                                <Label>Option 3</Label>
                                <Input value={addForm.option3} onChange={e => setAddForm(f => ({ ...f, option3: e.target.value }))} />
                            </div>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setAddOpen(false)} disabled={addSaving}>Cancel</Button>
                        <Button onClick={createVariant} disabled={addSaving}>
                            {addSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                            Create on Shopify
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
