import { Product, SKU } from "../../types";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Props {
    product: Product;
    priceTierDiscount: number;
    onAddToCart: (skuId: string, quantity: number) => void;
}

export function ProductCard({ product, priceTierDiscount, onAddToCart }: Props) {
    return (
        <Card>
            <CardHeader className="p-4">
                <CardTitle className="text-lg">{product.name}</CardTitle>
                <CardDescription>{product.description}</CardDescription>
            </CardHeader>
            <CardContent className="p-4 pt-0 space-y-4">
                {product.skus.map((sku) => (
                    <SkuRow
                        key={sku.id}
                        sku={sku}
                        discount={priceTierDiscount}
                        onAdd={onAddToCart}
                    />
                ))}
            </CardContent>
        </Card>
    );
}

function SkuRow({ sku, discount, onAdd }: { sku: SKU, discount: number, onAdd: (id: string, q: number) => void }) {
    const effectivePrice = sku.base_price_rands * (1 - discount);
    const [qty, setQty] = useState<string>("");

    const handleAdd = () => {
        const q = parseInt(qty);
        if (q > 0) {
            onAdd(sku.id, q);
            setQty("");
        }
    };

    return (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-t pt-3 first:border-0 first:pt-0 gap-3">
            <div>
                <div className="font-medium text-gray-900">{sku.code}</div>
                <div className="text-xs text-gray-500">{sku.size} / {sku.color}</div>
                <div className="text-sm font-bold text-green-700">R {effectivePrice.toFixed(2)}</div>
            </div>

            <div className="flex items-center space-x-2">
                <Input
                    type="number"
                    min="1"
                    placeholder="Qty"
                    value={qty}
                    onChange={(e) => setQty(e.target.value)}
                    className="w-20 text-center h-9"
                />
                <Button
                    onClick={handleAdd}
                    disabled={!qty || parseInt(qty) <= 0}
                    size="sm"
                    className=""
                >
                    Add
                </Button>
            </div>
        </div>
    );
}
