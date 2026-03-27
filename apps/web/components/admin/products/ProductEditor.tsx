"use client";

import { useEffect, useState } from "react";
import { apiService } from "@/lib/api";
import { Product, SKU } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, Trash2, Edit2, X } from "lucide-react";
import { Switch } from "@/components/ui/switch"; // User asked for toggle, usually Switch
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
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
    TableRow
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

// Controlled categories
const INITIAL_CATEGORIES = ["Concrete Pot", "Water Feature", "Plastic Pot"];

interface ProductEditorProps {
    product: Product | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

const emptyProduct: Product = {
    id: "",
    name: "",
    description: "",
    category: "",
    image_url: null,
    is_active: true,
    skus: [],
    created_at: "",
    updated_at: "",
};

export function ProductEditor({ product: initialProduct, open, onOpenChange, onSuccess }: ProductEditorProps) {
    const { toast } = useToast();
    const isCreateMode = !initialProduct;
    const [product, setProduct] = useState<Product>(initialProduct || emptyProduct);
    const [loading, setLoading] = useState(false);
    const [categories, setCategories] = useState(INITIAL_CATEGORIES);
    const [newCategory, setNewCategory] = useState("");
    const [showNewCatInput, setShowNewCatInput] = useState(false);

    // SKU Modal State
    const [skuModalOpen, setSkuModalOpen] = useState(false);
    const [editingSku, setEditingSku] = useState<SKU | null>(null);
    const [skuForm, setSkuForm] = useState({
        code: "",
        size: "",
        color: "",
        base_price_rands: 0,
        stock_quantity: 0,
    });

    useEffect(() => {
        setProduct(initialProduct || emptyProduct);
        // Ensure category is in list if it exists and not in default set
        if (initialProduct?.category && !categories.includes(initialProduct.category)) {
            setCategories(prev => [...prev, initialProduct.category!]);
        }
    }, [initialProduct, open]);

    const handleProductUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!product.name.trim()) {
            toast({ title: "Error", description: "Product name is required.", variant: "destructive" });
            return;
        }
        setLoading(true);
        try {
            if (isCreateMode) {
                const created = await apiService.products.create({
                    name: product.name,
                    category: product.category || undefined,
                    description: product.description || undefined,
                });
                toast({ title: "Success", description: "Product created." });
                onSuccess();
                onOpenChange(false);
            } else {
                await apiService.products.update(product.id, {
                    name: product.name,
                    category: product.category,
                    description: product.description,
                    is_active: product.is_active,
                });
                toast({ title: "Success", description: "Product updated." });
                onSuccess();
                onOpenChange(false);
            }
        } catch (error: any) {
            toast({ title: "Error", description: error.message || "Operation failed.", variant: "destructive" });
        } finally {
            setLoading(false);
        }
    };

    const handleAddCategory = () => {
        if (newCategory && !categories.includes(newCategory)) {
            setCategories([...categories, newCategory]);
            setProduct({ ...product, category: newCategory });
            setNewCategory("");
            setShowNewCatInput(false);
        }
    };

    // SKU Handlers (Copied/Refined from old page)
    const handleSkuSubmit = async () => {
        try {
            if (editingSku) {
                await apiService.products.updateSku(editingSku.id, skuForm);
                toast({ title: "Success", description: "SKU updated." });
            } else {
                await apiService.products.addSku(product.id, skuForm);
                toast({ title: "Success", description: "SKU added." });
            }
            setSkuModalOpen(false);
            resetSkuForm();
            // Refresh product data to show new SKU
            const updated = await apiService.products.get(product.id);
            setProduct(updated);
        } catch (error: any) {
            toast({ title: "Error", description: error.message || "Operation failed.", variant: "destructive" });
        }
    };

    const handleDeleteSku = async (skuId: string) => {
        if (!confirm("Are you sure you want to delete this SKU?")) return;
        try {
            await apiService.products.deleteSku(skuId);
            toast({ title: "Success", description: "SKU deleted." });
            // Refresh product data
            const updated = await apiService.products.get(product.id);
            setProduct(updated);
        } catch (error: any) {
            toast({ title: "Error", description: error.message || "Failed delete.", variant: "destructive" });
        }
    };

    const openNewSkuModal = () => {
        setEditingSku(null);
        resetSkuForm();
        setSkuModalOpen(true);
    };

    const openEditSkuModal = (sku: SKU) => {
        setEditingSku(sku);
        setSkuForm({
            code: sku.code,
            size: sku.size || "",
            color: sku.color || "",
            base_price_rands: sku.base_price_rands,
            stock_quantity: sku.stock_quantity
        });
        setSkuModalOpen(true);
    };

    const resetSkuForm = () => {
        setSkuForm({ code: "", size: "", color: "", base_price_rands: 0, stock_quantity: 0 });
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>{isCreateMode ? "Add New Product" : `Edit Product: ${product.name}`}</DialogTitle>
                    <DialogDescription>{isCreateMode ? "Enter product details. You can add SKUs after creating." : "Update details and manage SKUs."}</DialogDescription>
                </DialogHeader>

                <div className={`grid ${isCreateMode ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2'} gap-6 py-4`}>
                    {/* Left Col: Details */}
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Name</Label>
                            <Input
                                id="name"
                                value={product.name}
                                onChange={e => setProduct({ ...product, name: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Category</Label>
                            {!showNewCatInput ? (
                                <div className="flex gap-2">
                                    <Select
                                        value={product.category}
                                        onValueChange={(val) => setProduct({ ...product, category: val })}
                                    >
                                        <SelectTrigger className="w-full">
                                            <SelectValue placeholder="Select category" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {categories.map(c => (
                                                <SelectItem key={c} value={c}>{c}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <Button variant="outline" size="icon" onClick={() => setShowNewCatInput(true)} title="Add New Category">
                                        <Plus className="h-4 w-4" />
                                    </Button>
                                </div>
                            ) : (
                                <div className="flex gap-2">
                                    <Input
                                        value={newCategory}
                                        onChange={e => setNewCategory(e.target.value)}
                                        placeholder="New Category Name"
                                    />
                                    <Button size="sm" onClick={handleAddCategory}>Add</Button>
                                    <Button size="sm" variant="ghost" onClick={() => setShowNewCatInput(false)}><X className="h-4 w-4" /></Button>
                                </div>
                            )}
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Input
                                id="description"
                                value={product.description || ""}
                                onChange={e => setProduct({ ...product, description: e.target.value })}
                            />
                        </div>

                        {/* Active Toggle (Also in table, but good here too) */}
                        <div className="flex items-center justify-between border p-3 rounded-md">
                            <Label htmlFor="active-mode">Active Status</Label>
                            <Switch
                                id="active-mode"
                                checked={product.is_active}
                                onCheckedChange={checked => setProduct({ ...product, is_active: checked })}
                            />
                        </div>

                        {/* Image Management - only in edit mode */}
                        {!isCreateMode && (
                        <div className="space-y-2">
                            <Label>Product Image</Label>
                            <div className="flex items-start gap-4">
                                {product.image_url && (
                                    <img
                                        src={product.image_url}
                                        alt={product.name}
                                        className="h-20 w-20 object-cover rounded-md border"
                                    />
                                )}
                                <div className="space-y-2 flex-1">
                                    <Input
                                        type="file"
                                        accept="image/*"
                                        onChange={async (e) => {
                                            const file = e.target.files?.[0];
                                            if (!file) return;
                                            setLoading(true);
                                            try {
                                                const updated = await apiService.products.uploadImage(product.id, file);
                                                setProduct(updated);
                                                toast({ title: "Image Uploaded", description: "Product image updated successfully." });
                                            } catch (error: any) {
                                                toast({ title: "Upload Failed", description: error.message, variant: "destructive" });
                                            } finally {
                                                setLoading(false);
                                            }
                                        }}
                                    />
                                    <p className="text-xs text-muted-foreground">Upload a new image to replace the current one.</p>
                                </div>
                            </div>
                        </div>
                        )}
                    </div>

                    {/* Right Col: SKUs - only in edit mode */}
                    {!isCreateMode && <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <Label className="text-base font-semibold">SKUs</Label>
                            <Button size="sm" variant="outline" onClick={openNewSkuModal}>
                                <Plus className="mr-2 h-4 w-4" /> Add SKU
                            </Button>
                        </div>
                        <div className="border rounded-md overflow-hidden">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="py-2">Code</TableHead>
                                        <TableHead className="py-2 text-right">Stock</TableHead>
                                        <TableHead className="py-2 text-right">Act</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {product.skus?.filter(s => s.is_active !== false).length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={3} className="text-center text-muted-foreground text-xs py-4">No SKUs</TableCell>
                                        </TableRow>
                                    )}
                                    {product.skus?.filter(s => s.is_active !== false).map(sku => (
                                        <TableRow key={sku.id}>
                                            <TableCell className="py-2 text-xs font-mono">
                                                {sku.code}<br />
                                                <span className="text-muted-foreground">{sku.size} {sku.color}</span>
                                            </TableCell>
                                            <TableCell className="py-2 text-xs text-right">{sku.stock_quantity}</TableCell>
                                            <TableCell className="py-2 text-right">
                                                <div className="flex justify-end gap-1">
                                                    <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => openEditSkuModal(sku)}>
                                                        <Edit2 className="h-3 w-3" />
                                                    </Button>
                                                    <Button variant="ghost" size="icon" className="h-6 w-6 text-red-500" onClick={() => handleDeleteSku(sku.id)}>
                                                        <Trash2 className="h-3 w-3" />
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </div>}
                </div>

                <DialogFooter className="sm:justify-between">
                    <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
                    <Button onClick={handleProductUpdate} disabled={loading}>
                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        {isCreateMode ? "Create Product" : "Save Changes"}
                    </Button>
                </DialogFooter>
            </DialogContent>

            {/* Nested SKU Dialog */}
            <Dialog open={skuModalOpen} onOpenChange={setSkuModalOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>{editingSku ? "Edit SKU" : "Add New SKU"}</DialogTitle>
                        <DialogDescription>
                            {editingSku ? "Update SKU details." : "Enter details for the new SKU."}
                        </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                            <Label>Code</Label>
                            <Input value={skuForm.code} onChange={e => setSkuForm({ ...skuForm, code: e.target.value })} />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label>Size</Label>
                                <Input value={skuForm.size} onChange={e => setSkuForm({ ...skuForm, size: e.target.value })} />
                            </div>
                            <div className="grid gap-2">
                                <Label>Color</Label>
                                <Input value={skuForm.color} onChange={e => setSkuForm({ ...skuForm, color: e.target.value })} />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label>Price (R)</Label>
                                <Input type="number" step="0.01" value={skuForm.base_price_rands} onChange={e => setSkuForm({ ...skuForm, base_price_rands: parseFloat(e.target.value) || 0 })} />
                            </div>
                            <div className="grid gap-2">
                                <Label>Stock</Label>
                                <Input type="number" value={skuForm.stock_quantity} onChange={e => setSkuForm({ ...skuForm, stock_quantity: parseInt(e.target.value) || 0 })} />
                            </div>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setSkuModalOpen(false)}>Cancel</Button>
                        <Button onClick={handleSkuSubmit}>Save SKU</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </Dialog>
    );
}
