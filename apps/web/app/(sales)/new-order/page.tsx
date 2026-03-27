"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiService } from "@/lib/api";
import { Client, Product, SKU } from "@/types";
import { ClientCard } from "@/components/sales/ClientCard";
import { ProductCard } from "@/components/sales/ProductCard";
import { CartSummary } from "@/components/sales/CartSummary";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";

// Default delivery lead time in days
// TODO: This should be configurable from server in future sprints
const DEFAULT_DELIVERY_LEAD_DAYS = 14;

interface CartItem {
    sku: SKU;
    quantity: number;
    effectivePrice: number;
}

export default function NewOrderPage() {
    const router = useRouter();
    const { toast } = useToast();
    const [step, setStep] = useState<"CLIENT" | "CATALOGUE">("CLIENT");

    const [clients, setClients] = useState<Client[]>([]);
    const [products, setProducts] = useState<Product[]>([]);

    const [selectedClient, setSelectedClient] = useState<Client | null>(null);
    const [cart, setCart] = useState<CartItem[]>([]);

    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        Promise.all([
            apiService.clients.list(),
            apiService.products.list()
        ]).then(([fetchedClients, fetchedProducts]) => {
            setClients(fetchedClients);
            setProducts(fetchedProducts);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            toast({
                title: "Error",
                description: "Failed to load data.",
                variant: "destructive"
            });
        });
    }, [toast]);

    const handleClientSelect = (client: Client) => {
        setSelectedClient(client);
        setStep("CATALOGUE");
    };

    const handleAddToCart = (skuId: string, quantity: number) => {
        // Validate quantity - must be positive
        if (!quantity || quantity <= 0) {
            toast({
                variant: "destructive",
                title: "Invalid Quantity",
                description: "Quantity must be greater than zero.",
            });
            return;
        }

        let foundSku: SKU | undefined;
        for (const p of products) {
            foundSku = p.skus.find(s => s.id === skuId);
            if (foundSku) break;
        }

        if (!foundSku || !selectedClient) return;

        const discount = selectedClient.price_tier?.discount_percentage || 0;
        const effectivePrice = foundSku.base_price_rands * (1 - discount);

        setCart(prev => {
            const existing = prev.find(item => item.sku.id === skuId);
            if (existing) {
                return prev.map(item => item.sku.id === skuId
                    ? { ...item, quantity: item.quantity + quantity }
                    : item
                );
            }
            toast({ title: "Added to Cart", description: `${foundSku?.code} x ${quantity}` });
            return [...prev, { sku: foundSku!, quantity, effectivePrice }];
        });
    };

    const handleSubmit = async () => {
        if (!selectedClient || cart.length === 0) return;
        setSubmitting(true);
        try {
            await apiService.orders.create({
                client_id: selectedClient.id,
                delivery_date: new Date(Date.now() + DEFAULT_DELIVERY_LEAD_DAYS * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                items: cart.map(item => ({ sku_id: item.sku.id, quantity_ordered: item.quantity }))
            });
            toast({ title: "Success", description: "Order placed successfully!" });
            router.push("/sales-dashboard"); // Redirect to dashboard
        } catch (error) {
            console.error(error);
            toast({ title: "Error", description: "Failed to place order.", variant: "destructive" });
        } finally {
            setSubmitting(false);
        }
    };

    const handleRemove = (skuId: string) => {
        setCart(prev => prev.filter(item => item.sku.id !== skuId));
    };

    if (loading) return <div className="p-4 text-center text-muted-foreground">Loading data...</div>;

    return (
        <div className="pb-40 container mx-auto px-4 max-w-2xl mt-4">
            {step === "CLIENT" && (
                <div className="space-y-4">
                    <h2 className="text-2xl font-bold tracking-tight">Select Client</h2>
                    <div className="grid gap-3">
                        {clients.map(client => (
                            <ClientCard
                                key={client.id}
                                client={client}
                                onSelect={handleClientSelect}
                            />
                        ))}
                    </div>
                </div>
            )}

            {step === "CATALOGUE" && selectedClient && (
                <div className="space-y-6">
                    <Card className="bg-muted/50">
                        <CardContent className="p-4 flex justify-between items-center">
                            <div>
                                <div className="text-xs text-muted-foreground uppercase tracking-wider font-bold">Ordering for</div>
                                <div className="font-bold">{selectedClient.name}</div>
                            </div>
                            <Button
                                variant="link"
                                onClick={() => { setStep("CLIENT"); setCart([]); }}
                                className="text-blue-600"
                            >
                                Change
                            </Button>
                        </CardContent>
                    </Card>

                    <h2 className="text-2xl font-bold tracking-tight">Catalogue</h2>
                    <div className="grid gap-4">
                        {products.map(product => (
                            <ProductCard
                                key={product.id}
                                product={product}
                                priceTierDiscount={selectedClient.price_tier?.discount_percentage || 0}
                                onAddToCart={handleAddToCart}
                            />
                        ))}
                    </div>

                    <CartSummary
                        items={cart}
                        onSubmit={handleSubmit}
                        isSubmitting={submitting}
                        onRemove={handleRemove}
                    />
                </div>
            )}
        </div>
    );
}
