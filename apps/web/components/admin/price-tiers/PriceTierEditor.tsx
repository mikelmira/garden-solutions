import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { Check, Loader2, AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
    FormDescription,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";

import { PriceTier } from "@/types";
import { apiService } from "@/lib/api";

interface PriceTierEditorProps {
    tier?: PriceTier;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: () => void;
}

interface FormValues {
    name: string;
    discount_percentage: number;
    is_active: boolean;
}

export function PriceTierEditor({ tier, open, onOpenChange, onSuccess }: PriceTierEditorProps) {
    const { toast } = useToast();
    const [loading, setLoading] = useState(false);
    const [checkingUsage, setCheckingUsage] = useState(false);
    const [usageWarning, setUsageWarning] = useState<{ client_count: number; store_count: number } | null>(null);
    const [confirmedUsage, setConfirmedUsage] = useState(false);

    const form = useForm<FormValues>({
        defaultValues: {
            name: "",
            discount_percentage: 0,
            is_active: true,
        },
    });

    useEffect(() => {
        if (open) {
            form.reset({
                name: tier?.name || "",
                discount_percentage: tier ? Number(tier.discount_percentage) : 0.0, // Ensure number
                is_active: tier?.is_active ?? true,
            });
            setUsageWarning(null);
            setConfirmedUsage(false);
        }
    }, [tier, open, form]);

    const checkUsage = async () => {
        if (!tier) return false;
        try {
            setCheckingUsage(true);
            const usage = await apiService.priceTiers.getUsage(tier.id);
            if (usage.client_count > 0 || usage.store_count > 0) {
                setUsageWarning(usage);
                return true; // Has usage
            }
            return false;
        } catch (error) {
            console.error("Failed to check usage", error);
            return false;
        } finally {
            setCheckingUsage(false);
        }
    };

    const onSubmit = async (values: FormValues) => {
        // If editing and hasn't confirmed warning yet, check usage
        if (tier && !confirmedUsage) {
            const hasUsage = await checkUsage();
            if (hasUsage) {
                return; // Stop here, show warning
            }
        }

        try {
            setLoading(true);
            if (tier) {
                await apiService.priceTiers.update(tier.id, values);
                toast({ title: "Tier updated" });
            } else {
                await apiService.priceTiers.create(values);
                toast({ title: "Tier created" });
            }
            onSuccess();
            onOpenChange(false);
        } catch (error: any) {
            toast({
                variant: "destructive",
                title: "Error",
                description: error.message || "Failed to save tier"
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>{tier ? "Edit Price Tier" : "New Price Tier"}</DialogTitle>
                    <DialogDescription>
                        {tier ? "Update discount structure." : "Create a new discount tier."}
                    </DialogDescription>
                </DialogHeader>

                {usageWarning && !confirmedUsage ? (
                    <div className="space-y-4">
                        <div className="rounded-md bg-yellow-50 p-4">
                            <div className="flex">
                                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                                <div className="ml-3">
                                    <h3 className="text-sm font-medium text-yellow-800">Warning: Active Usage</h3>
                                    <div className="mt-2 text-sm text-yellow-700">
                                        <p>
                                            This tier is currently assigned to <strong>{usageWarning.client_count} clients</strong> and <strong>{usageWarning.store_count} stores</strong>.
                                        </p>
                                        <p className="mt-1">
                                            Updating the name or discount will immediately affect all existing orders and invoices calculated from this point forward.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setUsageWarning(null)}>Cancel</Button>
                            <Button
                                variant="destructive"
                                onClick={() => {
                                    setConfirmedUsage(true);
                                    // Re-submit immediately
                                    form.handleSubmit(onSubmit)();
                                }}
                            >
                                I Understand, Update Anyway
                            </Button>
                        </DialogFooter>
                    </div>
                ) : (
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                            <FormField
                                control={form.control}
                                name="name"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Name</FormLabel>
                                        <FormControl>
                                            <Input placeholder="e.g. Tier A" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="discount_percentage"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Discount Percentage</FormLabel>
                                        <FormControl>
                                            <Input
                                                type="number"
                                                step="0.01"
                                                min="0"
                                                max="1"
                                                placeholder="0.10"
                                                {...field}
                                                onChange={e => field.onChange(parseFloat(e.target.value))}
                                            />
                                        </FormControl>
                                        <FormDescription>
                                            Enter as decimal (0.10 = 10% off)
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="is_active"
                                render={({ field }) => (
                                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm">
                                        <div className="space-y-0.5">
                                            <FormLabel>Active</FormLabel>
                                            <FormDescription>
                                                Available for assignment
                                            </FormDescription>
                                        </div>
                                        <FormControl>
                                            <Switch
                                                checked={field.value}
                                                onCheckedChange={field.onChange}
                                            />
                                        </FormControl>
                                    </FormItem>
                                )}
                            />
                            <DialogFooter>
                                <Button type="submit" disabled={loading || checkingUsage}>
                                    {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                    Save
                                </Button>
                            </DialogFooter>
                        </form>
                    </Form>
                )}
            </DialogContent>
        </Dialog>
    );
}
