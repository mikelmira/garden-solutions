import { SKU } from "../../types";
import { Button } from "@/components/ui/button";

interface CartItem {
    sku: SKU;
    quantity: number;
    effectivePrice: number;
}

interface Props {
    items: CartItem[];
    onSubmit: () => void;
    isSubmitting: boolean;
    onRemove: (skuId: string) => void;
}

export function CartSummary({ items, onSubmit, isSubmitting }: Props) {
    const total = items.reduce((sum, item) => sum + (item.effectivePrice * item.quantity), 0);

    if (items.length === 0) return null;

    return (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4 shadow-lg pb-safe z-10">
            <div className="max-w-md mx-auto space-y-3">
                <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-700">{items.reduce((a, b) => a + b.quantity, 0)} Items</span>
                    <span className="font-bold text-xl text-green-700">R {total.toFixed(2)}</span>
                </div>

                <Button
                    onClick={onSubmit}
                    disabled={isSubmitting}
                    className="w-full h-12 text-lg font-bold bg-green-600 hover:bg-green-700"
                >
                    {isSubmitting ? "Submitting..." : "Place Order"}
                </Button>
            </div>
        </div>
    );
}
