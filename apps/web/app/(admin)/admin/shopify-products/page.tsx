"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Search, ShoppingCart, ExternalLink, RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { ProductsTabs } from "@/components/admin/ProductsTabs";

interface ShopifyVariantRow {
    id: string;
    title?: string | null;
    shopify_sku?: string | null;
    price?: string | null;
    option1?: string | null;
    option2?: string | null;
    option3?: string | null;
    inventory_quantity?: number | null;
    mapping_status?: string;
}

interface ShopifyProductRow {
    id: string;
    shopify_product_id: number;
    title: string;
    product_type?: string | null;
    vendor?: string | null;
    shopify_status?: string | null;
    shopify_handle?: string | null;
    variants?: ShopifyVariantRow[];
}

export default function AdminShopifyProductsPage() {
    const { toast } = useToast();
    const [products, setProducts] = useState<ShopifyProductRow[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");

    useEffect(() => { load(); }, []);

    const load = async () => {
        try {
            setLoading(true);
            const data = await apiService.admin.shopify.getProducts();
            setProducts(data || []);
        } catch (error: any) {
            toast({ variant: "destructive", title: "Failed to load Shopify products", description: error.message });
        } finally {
            setLoading(false);
        }
    };

    const filtered = useMemo(() => {
        const s = search.trim().toLowerCase();
        if (!s) return products;
        return products.filter(
            p =>
                p.title.toLowerCase().includes(s) ||
                (p.vendor || "").toLowerCase().includes(s) ||
                (p.product_type || "").toLowerCase().includes(s) ||
                (p.shopify_handle || "").toLowerCase().includes(s)
        );
    }, [products, search]);

    return (
        <div className="space-y-6">
            <ProductsTabs />
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Shopify Products</h1>
                    <p className="text-muted-foreground">Manage Pot Shack products. Edits push to Shopify in real time.</p>
                </div>
                <Button variant="outline" onClick={load} disabled={loading}>
                    <RefreshCw className={loading ? "h-4 w-4 mr-2 animate-spin" : "h-4 w-4 mr-2"} />
                    Refresh
                </Button>
            </div>

            <Card>
                <CardContent className="pt-6">
                    <div className="relative max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search by title, vendor, type..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            className="pl-9"
                        />
                    </div>
                </CardContent>
            </Card>

            {loading ? (
                <div className="flex h-[30vh] items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            ) : filtered.length === 0 ? (
                <Card>
                    <CardContent className="py-16 text-center">
                        <ShoppingCart className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                        <h3 className="font-semibold mb-1">No Shopify products</h3>
                        <p className="text-sm text-muted-foreground">
                            Run a product sync from the Shopify integration page to pull products in.
                        </p>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-3">
                    {filtered.map(p => {
                        const variantCount = p.variants?.length || 0;
                        const totalInv = (p.variants || []).reduce((s, v) => s + (v.inventory_quantity ?? 0), 0);
                        return (
                            <Link
                                key={p.id}
                                href={`/admin/shopify-products/${p.id}`}
                                className="block"
                            >
                                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                                    <CardContent className="pt-4 pb-4 flex items-center gap-4">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <span className="font-medium truncate">{p.title}</span>
                                                {p.shopify_status === "draft" && (
                                                    <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">Draft</span>
                                                )}
                                                {p.shopify_status === "archived" && (
                                                    <span className="text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground">Archived</span>
                                                )}
                                            </div>
                                            <div className="text-xs text-muted-foreground truncate">
                                                {[p.vendor, p.product_type].filter(Boolean).join(" · ") || "—"}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-sm">{variantCount} variant{variantCount === 1 ? "" : "s"}</div>
                                            <div className="text-xs text-muted-foreground">{totalInv} in stock</div>
                                        </div>
                                        <ExternalLink className="h-4 w-4 text-muted-foreground" />
                                    </CardContent>
                                </Card>
                            </Link>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
