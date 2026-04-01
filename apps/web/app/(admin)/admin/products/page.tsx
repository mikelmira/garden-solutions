"use client";

import { useEffect, useState, useMemo } from "react";
import { apiService } from "@/lib/api";
import { Product, Order } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Plus, Search, Loader2, Upload, Package, Truck, ClipboardList } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { ProductEditor } from "@/components/admin/products/ProductEditor";
import { BulkImport } from "@/components/admin/products/BulkImport";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";

const CATEGORIES = ["All", "Concrete Pot", "Water Feature", "Plastic Pot"];

export default function ProductsPage() {
    const { toast } = useToast();
    const [products, setProducts] = useState<Product[]>([]);
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [categoryFilter, setCategoryFilter] = useState("All");
    const [importOpen, setImportOpen] = useState(false);

    // Edit Modal State
    const [editingProduct, setEditingProduct] = useState<Product | null>(null);
    const [editOpen, setEditOpen] = useState(false);
    const [createOpen, setCreateOpen] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [productsData, ordersData] = await Promise.all([
                apiService.products.list({ is_active: null }),
                apiService.orders.list({ size: 100 }) // Fetch enough orders for summary
            ]);
            setProducts(productsData);
            setOrders(ordersData);
        } catch (error) {
            console.error("Failed to load data", error);
            toast({ variant: "destructive", title: "Failed to load data" });
        } finally {
            setLoading(false);
        }
    };

    const handleToggleActive = async (product: Product, checked: boolean) => {
        // Optimistic update
        const originalStatus = product.is_active;
        setProducts(products.map(p => p.id === product.id ? { ...p, is_active: checked } : p));

        try {
            await apiService.products.update(product.id, { is_active: checked });
            toast({ title: "Updated", description: `${product.name} is now ${checked ? 'Active' : 'Disabled'}` });
        } catch (error) {
            // Revert
            setProducts(products.map(p => p.id === product.id ? { ...p, is_active: originalStatus } : p));
            toast({ title: "Error", description: "Failed to update status", variant: "destructive" });
        }
    };

    const handleEditClick = (product: Product) => {
        setEditingProduct(product);
        setEditOpen(true);
    };

    const filteredProducts = products.filter(product => {
        const matchesSearch = product.name.toLowerCase().includes(search.toLowerCase()) ||
            product.category?.toLowerCase().includes(search.toLowerCase());

        const matchesCategory = categoryFilter === "All" || product.category === categoryFilter;

        return matchesSearch && matchesCategory;
    });

    // Summary Calculations
    const totalStockUnits = useMemo(() => {
        return products.reduce((sum, product) => {
            return sum + product.skus.reduce((skuSum, sku) => skuSum + (sku.stock_quantity || 0), 0);
        }, 0);
    }, [products]);

    const totalAssignedUnits = useMemo(() => {
        return orders
            .filter(order => order.delivery_team_id)
            .reduce((sum, order) => {
                const orderQty = (order.items || []).reduce((itemSum, item) => itemSum + item.quantity_ordered, 0);
                return sum + orderQty;
            }, 0);
    }, [orders]);

    const totalRemainingUnits = Math.max(totalStockUnits - totalAssignedUnits, 0);

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-heading font-bold tracking-tight">Products</h1>
                    <p className="text-muted-foreground">Manage your catalogue and inventory.</p>
                </div>
                <div className="flex gap-2">
                    <Dialog open={importOpen} onOpenChange={setImportOpen}>
                        <DialogTrigger asChild>
                            <Button variant="outline">
                                <Upload className="mr-2 h-4 w-4" /> Import CSV
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-md">
                            <DialogHeader>
                                <DialogTitle>Bulk Import Products</DialogTitle>
                                <DialogDescription>
                                    Upload a CSV file to add or update products in bulk.
                                </DialogDescription>
                            </DialogHeader>
                            <BulkImport onSuccess={() => { loadData(); setImportOpen(false); }} />
                        </DialogContent>
                    </Dialog>

                    <Button onClick={() => { setEditingProduct(null); setCreateOpen(true); }}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add Product
                    </Button>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                <div className="stat-card">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="stat-card-label">Products On Hand</p>
                            <p className="stat-card-value text-2xl font-bold">{totalStockUnits.toLocaleString()}</p>
                        </div>
                        <div className="stat-card-icon bg-emerald-100 p-2 rounded-full">
                            <Package className="h-5 w-5 text-emerald-600" />
                        </div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="stat-card-label">Assigned to Deliveries</p>
                            <p className="stat-card-value text-2xl font-bold">{totalAssignedUnits.toLocaleString()}</p>
                        </div>
                        <div className="stat-card-icon bg-blue-100 p-2 rounded-full">
                            <Truck className="h-5 w-5 text-blue-600" />
                        </div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="flex items-start justify-between">
                        <div>
                            <p className="stat-card-label">Products Remaining</p>
                            <p className="stat-card-value text-2xl font-bold">{totalRemainingUnits.toLocaleString()}</p>
                        </div>
                        <div className="stat-card-icon bg-slate-100 p-2 rounded-full">
                            <ClipboardList className="h-5 w-5 text-slate-600" />
                        </div>
                    </div>
                </div>
            </div>

            <Card>
                <CardHeader className="pb-3">
                    <CardTitle>Inventory</CardTitle>
                    <CardDescription>
                        {products.length} total products found.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-col sm:flex-row gap-4 mb-6">
                        <div className="relative flex-1">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search products..."
                                className="pl-8"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                            />
                        </div>
                        <div className="w-full sm:w-[200px]">
                            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Category" />
                                </SelectTrigger>
                                <SelectContent>
                                    {CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    {loading ? (
                        <div className="flex justify-center p-8">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : (
                        <div className="border rounded-md overflow-x-auto">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-[60px] sm:w-[80px]">Active</TableHead>
                                        <TableHead className="w-[60px] sm:w-[80px] hidden sm:table-cell">Photo</TableHead>
                                        <TableHead>Name</TableHead>
                                        <TableHead className="hidden md:table-cell">Category</TableHead>
                                        <TableHead className="text-right">Stock</TableHead>
                                        {/* Removed SKUs Column */}
                                        <TableHead className="text-right hidden sm:table-cell">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredProducts.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                                                No products found matching your filters.
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        filteredProducts.map((product) => {
                                            const totalStock = product.skus.reduce((sum, sku) => sum + (sku.stock_quantity || 0), 0);
                                            return (
                                                <TableRow key={product.id}>
                                                    <TableCell>
                                                        <Switch
                                                            checked={product.is_active}
                                                            onCheckedChange={(checked) => handleToggleActive(product, checked)}
                                                            className="data-[state=checked]:bg-green-600"
                                                        />
                                                    </TableCell>
                                                    <TableCell className="hidden sm:table-cell">
                                                        {product.image_url ? (
                                                            <img
                                                                src={product.image_url}
                                                                alt={product.name}
                                                                className="h-10 w-10 rounded-md object-cover border bg-muted"
                                                            />
                                                        ) : (
                                                            <div className="h-10 w-10 rounded-md border bg-muted" />
                                                        )}
                                                    </TableCell>
                                                    <TableCell className="font-medium">
                                                        <button
                                                            onClick={() => handleEditClick(product)}
                                                            className="hover:underline text-primary text-left font-semibold"
                                                        >
                                                            {product.name}
                                                        </button>
                                                    </TableCell>
                                                    <TableCell className="hidden md:table-cell">
                                                        <Badge variant="secondary" className="font-normal">
                                                            {product.category || "Uncategorized"}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell className="text-right font-medium">
                                                        {totalStock.toLocaleString()}
                                                    </TableCell>
                                                    <TableCell className="text-right hidden sm:table-cell">
                                                        <Button variant="outline" size="sm" onClick={() => handleEditClick(product)}>
                                                            Edit
                                                        </Button>
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </CardContent>
            </Card>

            {editingProduct && (
                <ProductEditor
                    product={editingProduct}
                    open={editOpen}
                    onOpenChange={setEditOpen}
                    onSuccess={loadData}
                />
            )}

            <ProductEditor
                product={null}
                open={createOpen}
                onOpenChange={setCreateOpen}
                onSuccess={loadData}
            />
        </div>
    );
}
