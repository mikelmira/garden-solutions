"use client";

import { useState, useEffect } from "react";
import { apiService } from "@/lib/api";
import { Product } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Loader2, ArrowRight, ArrowLeft, CheckCircle, Package, ShoppingCart, FileText, Store, Search, ChevronDown } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

type Step = "gate" | "products" | "review" | "done";

export default function StoreOrderPage() {
    const { toast } = useToast();
    const [step, setStep] = useState<Step>("gate");
    const [loading, setLoading] = useState(false);
    // Data State
    const [storeCode, setStoreCode] = useState("");
    const [storeName, setStoreName] = useState("");
    const [products, setProducts] = useState<Product[]>([]);
    const [orderId, setOrderId] = useState<string | null>(null);

    // Form State
    const [cart, setCart] = useState<{ skuId: string, quantity: number, productName: string, skuCode: string, size: string, color: string, productImage?: string | null }[]>([]);
    const [notes, setNotes] = useState("");

    // UI State
    const [searchTerm, setSearchTerm] = useState("");
    const [expandedProduct, setExpandedProduct] = useState<string | null>(null);

    const filteredProducts = products.filter(p =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    useEffect(() => {
        // Hydrate store from local storage
        const savedCode = localStorage.getItem("garden_store_code");
        if (savedCode) {
            verifyCode(savedCode, true);
        }
    }, []);

    const verifyCode = async (code: string, silent = false) => {
        if (!code) return;
        setLoading(true);

        try {
            const data = await apiService.public.stores.resolve(code);
            setStoreCode(data.code);
            setStoreName(data.name);
            localStorage.setItem("garden_store_code", data.code);
            setStep("products");

            // Reload products data whenever we re-verify/enter check
            loadData();
        } catch (error) {
            if (!silent) {
                toast({ variant: "destructive", title: "Invalid Store Code", description: "Store not found." });
            }
            localStorage.removeItem("garden_store_code");
            setStoreName("");
        } finally {
            setLoading(false);
        }
    };

    const loadData = async () => {
        try {
            const p = await apiService.public.data.products();
            setProducts(p);
        } catch (error) {
            console.error("Failed to load products", error);
            // toast({ variant: "destructive", title: "Error", description: "Failed to load products." });
        }
    };

    const handleAddToCart = (skuId: string, quantity: number, productName: string, skuCode: string, size: string, color: string, productImage?: string | null) => {
        if (quantity <= 0) {
            setCart(prev => prev.filter(i => i.skuId !== skuId));
            return;
        }
        setCart(prev => {
            const existing = prev.find(i => i.skuId === skuId);
            if (existing) {
                return prev.map(i => i.skuId === skuId ? { ...i, quantity } : i);
            }
            return [...prev, { skuId, quantity, productName, skuCode, size, color, productImage }];
        });
    };

    const handleSubmit = async () => {
        if (!storeCode || cart.length === 0) return;
        setLoading(true);
        try {
            const order = await apiService.public.orders.create({
                store_code: storeCode,
                delivery_date: (() => {
                    const d = new Date();
                    d.setDate(d.getDate() + 14);
                    return d.toISOString().split("T")[0];
                })(),
                items: cart.map(i => ({ sku_id: i.skuId, quantity_ordered: i.quantity })),
                notes
            });
            setOrderId(order.id);
            setStep("done");
        } catch (error: any) {
            toast({ variant: "destructive", title: "Submission Failed", description: error.message || "Could not submit order." });
        } finally {
            setLoading(false);
        }
    };

    const reset = () => {
        setCart([]);
        setNotes("");
        setStep("products");
    };

    const clearCode = () => {
        localStorage.removeItem("garden_store_code");
        setStoreCode("");
        setStep("gate");
    };

    if (step === "gate") {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-gradient-to-b from-background to-muted/30">
                <div className="w-full max-w-sm space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    {/* Logo */}
                    <div className="flex justify-center">
                        <div className="h-16 w-16 bg-white rounded-2xl flex items-center justify-center shadow-lg border">
                            <img src="/logo.avif" alt="Garden Solutions" className="h-10 w-10 object-contain" />
                        </div>
                    </div>
                    <div className="text-center space-y-2">
                        <h1 className="text-3xl font-heading font-semibold tracking-tight text-foreground">Store Portal</h1>
                        <p className="text-muted-foreground">Enter your store code to place an order</p>
                    </div>
                    <Card className="border shadow-xl shadow-black/5">
                        <CardContent className="pt-6 space-y-4">
                            <Input
                                className="text-center text-lg tracking-widest font-mono uppercase h-12"
                                placeholder="XXX-XXX"
                                value={storeCode}
                                onChange={e => setStoreCode(e.target.value)}
                                onKeyDown={e => e.key === "Enter" && verifyCode(storeCode)}
                            />
                            <Button
                                className="w-full h-12 text-base font-medium bg-purple-600 hover:bg-purple-700"
                                onClick={() => verifyCode(storeCode)}
                                disabled={loading || !storeCode}
                            >
                                {loading && <Loader2 className="mr-2 h-5 w-5 animate-spin" />}
                                Continue
                                {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    if (step === "done") {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center space-y-8 bg-gradient-to-b from-background to-muted/30">
                <div className="rounded-full bg-green-100 dark:bg-green-900/30 p-8 animate-in zoom-in duration-500">
                    <CheckCircle className="h-16 w-16 text-green-600 dark:text-green-400" />
                </div>
                <div className="space-y-3">
                    <h2 className="text-3xl font-heading font-bold text-foreground">Order Received</h2>
                    <p className="text-lg text-muted-foreground max-w-sm">
                        Your order <span className="font-mono text-foreground">#{orderId?.slice(0, 8)}</span> has been submitted successfully.
                    </p>
                </div>
                <Button onClick={reset} size="lg" className="w-full max-w-xs h-14 text-base font-medium bg-purple-600 hover:bg-purple-700">
                    Start New Order
                </Button>
            </div>
        );
    }

    // Step indicator
    const steps = [
        { key: "products", label: "Products", icon: Package },
        { key: "review", label: "Review", icon: FileText },
    ];
    const currentStepIndex = steps.findIndex(s => s.key === step);

    // Wizard Layout
    return (
        <div className="min-h-screen pb-32 bg-background">
            {/* Header */}
            <div className="bg-background/95 backdrop-blur-lg border-b sticky top-0 z-10">
                <div className="max-w-2xl mx-auto px-6 py-4">
                    <div className="flex justify-between items-center mb-4">
                        <div className="flex items-center gap-3">
                            <div className="h-9 w-9 bg-purple-600 rounded-xl flex items-center justify-center">
                                <Store className="h-5 w-5 text-white" />
                            </div>
                            <span className="font-heading font-semibold text-lg">Store Order</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="text-sm font-medium text-muted-foreground bg-muted px-3 py-1.5 rounded-full">
                                {storeName || storeCode}
                            </div>
                            <Button variant="ghost" size="sm" onClick={clearCode} className="h-8 text-xs text-muted-foreground hover:text-destructive">
                                Logout
                            </Button>
                        </div>
                    </div>
                    {/* Step Indicator */}
                    <div className="flex items-center justify-center gap-4">
                        {steps.map((s, i) => (
                            <div key={s.key} className="flex items-center">
                                <div className={cn(
                                    "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors",
                                    i === currentStepIndex ? "bg-purple-600 text-white" :
                                        i < currentStepIndex ? "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400" :
                                            "bg-muted text-muted-foreground"
                                )}>
                                    <s.icon size={16} />
                                    <span>{s.label}</span>
                                </div>
                                {i < steps.length - 1 && (
                                    <div className={cn(
                                        "w-12 h-0.5 mx-2",
                                        i < currentStepIndex ? "bg-purple-600" : "bg-muted"
                                    )} />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="p-6 max-w-lg mx-auto space-y-6">

                {step === "products" && (
                    <div className="space-y-5">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-heading font-semibold text-foreground">Add Products</h2>
                                <p className="text-sm text-muted-foreground">Select products to add to your order.</p>
                            </div>
                            <div className="bg-purple-600/10 text-purple-600 font-bold px-4 py-2 rounded-xl text-lg min-w-[3rem] text-center">
                                {cart.reduce((acc, item) => acc + item.quantity, 0)}
                            </div>
                        </div>

                        {/* Search Bar */}
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search products..."
                                className="pl-9"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>

                        <div className="space-y-3">
                            {filteredProducts.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground border border-dashed rounded-xl">
                                    No products found matching "{searchTerm}"
                                </div>
                            ) : (
                                filteredProducts.map(product => {
                                    const isExpanded = expandedProduct === product.id;
                                    const productQty = product.skus.reduce((acc, sku) => {
                                        return acc + (cart.find(i => i.skuId === sku.id)?.quantity || 0);
                                    }, 0);

                                    return (
                                        <Card
                                            key={product.id}
                                            className={cn(
                                                "overflow-hidden transition-all duration-200",
                                                isExpanded ? "ring-2 ring-purple-600/20 border-purple-600 shadow-md" : "hover:border-purple-600/50",
                                                productQty > 0 && !isExpanded && "border-purple-600/50 bg-purple-50/50"
                                            )}
                                        >
                                            <div
                                                className="p-4 flex items-center justify-between cursor-pointer active:bg-muted/50 transition-colors"
                                                onClick={() => setExpandedProduct(isExpanded ? null : product.id)}
                                            >
                                                <div className="flex items-center gap-4">
                                                    {product.image_url ? (
                                                        <img src={product.image_url} alt={product.name} className="w-14 h-14 rounded-md object-cover border bg-muted" />
                                                    ) : (
                                                        <div className="w-14 h-14 bg-muted rounded-md border flex items-center justify-center">
                                                            <Package size={24} className="text-muted-foreground" />
                                                        </div>
                                                    )}
                                                    <div>
                                                        <h3 className="font-semibold text-foreground text-lg">{product.name}</h3>
                                                        {productQty > 0 && (
                                                            <div className="text-sm text-purple-600 font-medium mt-1">
                                                                {productQty} items selected
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-3">
                                                    <div className={cn("transition-transform duration-200", isExpanded && "rotate-180")}>
                                                        <ChevronDown className="h-5 w-5 text-muted-foreground" />
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Dropdown Content */}
                                            {isExpanded && (
                                                <div className="border-t bg-muted/30 p-3 space-y-2 animate-in slide-in-from-top-2 duration-200">
                                                    {product.skus.map(sku => {
                                                        const qty = cart.find(i => i.skuId === sku.id)?.quantity || 0;
                                                        return (
                                                            <div
                                                                key={sku.id}
                                                                className={cn(
                                                                    "flex items-center justify-between p-3 rounded-lg border bg-card transition-colors",
                                                                    qty > 0 ? "border-purple-600/30 shadow-sm" : "border-transparent shadow-sm"
                                                                )}
                                                            >
                                                                <div className="flex flex-col">
                                                                    <span className="font-medium text-foreground">
                                                                        {sku.size} {sku.color ? `• ${sku.color}` : ""}
                                                                    </span>
                                                                    {/* Price and Code hidden as requested */}
                                                                </div>

                                                                <div className="flex items-center gap-3">
                                                                    <Button
                                                                        variant="outline" size="icon" className="h-8 w-8 rounded-lg"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            handleAddToCart(sku.id, qty - 1, product.name, sku.code, sku.size, sku.color, product.image_url);
                                                                        }}
                                                                        disabled={qty === 0}
                                                                    >-</Button>
                                                                    <span className="w-8 text-center font-bold text-foreground tabular-nums">{qty}</span>
                                                                    <Button
                                                                        variant="outline" size="icon" className="h-8 w-8 rounded-lg"
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            handleAddToCart(sku.id, qty + 1, product.name, sku.code, sku.size, sku.color, product.image_url);
                                                                        }}
                                                                    >+</Button>
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            )}
                                        </Card>
                                    );
                                })
                            )}
                        </div>
                    </div>
                )}

                {step === "review" && (
                    <div className="space-y-6">
                        <div>
                            <h2 className="text-xl font-heading font-semibold text-foreground">Review Order</h2>
                            <p className="text-sm text-muted-foreground mt-1">Confirm your order details before submission</p>
                        </div>

                        <Card>
                            <CardContent className="p-5 space-y-4">
                                <div className="flex items-center gap-3 pb-4 border-b">
                                    <div className="h-10 w-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
                                        <Store size={18} />
                                    </div>
                                    <div>
                                        <div className="text-xs text-muted-foreground">Store</div>
                                        <div className="font-semibold text-foreground">{storeName || storeCode}</div>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label className="text-sm font-medium flex items-center gap-2">
                                        <FileText size={14} className="text-muted-foreground" />
                                        Notes
                                    </Label>
                                    <Input
                                        value={notes}
                                        onChange={e => setNotes(e.target.value)}
                                        placeholder="Optional comments..."
                                    />
                                </div>
                            </CardContent>
                        </Card>

                        <div className="space-y-3">
                            <Label className="text-sm font-medium flex items-center gap-2">
                                <ShoppingCart size={14} className="text-muted-foreground" />
                                Order Items ({cart.reduce((acc, item) => acc + item.quantity, 0)})
                            </Label>
                            <Card>
                                <CardContent className="p-0 divide-y">
                                    {Object.entries(cart.reduce((groups, item) => {
                                        if (!groups[item.productName]) groups[item.productName] = { image: item.productImage, items: [] };
                                        groups[item.productName].items.push(item);
                                        return groups;
                                    }, {} as Record<string, { image?: string | null, items: typeof cart }>)).map(([productName, group]) => (
                                        <div key={productName} className="p-4 space-y-3">
                                            <div className="flex items-center gap-3">
                                                {group.image ? (
                                                    <img src={group.image} alt={productName} className="w-10 h-10 rounded-lg object-cover border bg-muted" />
                                                ) : (
                                                    <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                                                        <Package size={16} className="text-muted-foreground" />
                                                    </div>
                                                )}
                                                <div className="font-medium text-foreground">{productName}</div>
                                            </div>
                                            <div className="pl-[52px] space-y-2">
                                                {group.items.map(item => (
                                                    <div key={item.skuId} className="flex justify-between items-center text-sm bg-muted/30 p-2 rounded-md">
                                                        <div className="text-muted-foreground">
                                                            {item.size} {item.color ? `• ${item.color}` : ""}
                                                        </div>
                                                        <span className="font-bold text-foreground">×{item.quantity}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                )}
            </div>

            {/* Bottom Nav */}
            <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur-lg border-t p-4 z-20">
                <div className="flex justify-between items-center max-w-lg mx-auto w-full">
                    {step === "products" ? (
                        <div />
                    ) : (
                        <Button variant="ghost" onClick={() => setStep("products")}>
                            <ArrowLeft className="mr-2 h-4 w-4" /> Back
                        </Button>
                    )}

                    {step === "products" && (
                        <Button onClick={() => setStep("review")} disabled={cart.length === 0} className="ml-auto min-w-[140px] bg-purple-600 hover:bg-purple-700">
                            Review <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                    )}
                    {step === "review" && (
                        <Button onClick={handleSubmit} disabled={loading} className="ml-auto min-w-[140px] bg-purple-600 hover:bg-purple-700">
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Submit Order
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
}
