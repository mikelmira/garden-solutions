"use client";

import { useEffect, useState } from "react";
import { PriceTier } from "@/types";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { PageHeader } from "@/components/ui/page-header";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, Pencil, Trash2, Tag, AlertTriangle } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";
import { PriceTierEditor } from "@/components/admin/price-tiers/PriceTierEditor";
import { Badge } from "@/components/ui/badge";

export default function PriceTiersPage() {
    const { toast } = useToast();
    const [tiers, setTiers] = useState<PriceTier[]>([]);
    const [loading, setLoading] = useState(true);
    const [isEditorOpen, setIsEditorOpen] = useState(false);
    const [editingTier, setEditingTier] = useState<PriceTier | undefined>(undefined);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const data = await apiService.priceTiers.list();
            setTiers(data);
        } catch (error: any) {
            toast({
                variant: "destructive",
                title: "Failed to load tiers",
                description: error.message,
            });
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = () => {
        setEditingTier(undefined);
        setIsEditorOpen(true);
    };

    const handleEdit = (tier: PriceTier) => {
        setEditingTier(tier);
        setIsEditorOpen(true);
    };

    const handleDelete = async (tier: PriceTier) => {
        // First check usage if possible, or just try delete and catch 409
        // Based on spec, we should probably warn about usage before delete too, 
        // but backend 409 return is the rigorous check.
        // Let's rely on backend 409 for delete protection as per plan.

        if (!confirm(`Are you sure you want to delete "${tier.name}"?`)) return;

        try {
            await apiService.priceTiers.delete(tier.id);
            toast({ title: "Price tier deleted" });
            loadData();
        } catch (error: any) {
            // Check for 409 in error message or status if available
            // Axios error usually carries message from interceptor
            if (error.message?.includes("assigned") || error.response?.status === 409) {
                toast({
                    variant: "destructive",
                    title: "Cannot Delete Tier",
                    description: error.message || "This tier is assigned to clients or stores. Disable it instead.",
                });
            } else {
                toast({
                    variant: "destructive",
                    title: "Error",
                    description: error.message || "Failed to delete tier",
                });
            }
        }
    };

    return (
        <div className="space-y-6">
            <PageHeader
                title="Price Tiers"
                description="Manage discount tiers for client pricing."
            >
                <Button onClick={handleCreate} className="gap-2">
                    <Plus size={16} /> Create Tier
                </Button>
            </PageHeader>

            {loading ? (
                <div className="flex justify-center py-16">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            ) : tiers.length === 0 ? (
                <EmptyState
                    icon={Tag}
                    title="No price tiers found"
                    description="Create a price tier to get started."
                >
                    <Button onClick={handleCreate} variant="outline" className="mt-4">
                        <Plus size={16} className="mr-2" /> Create First Tier
                    </Button>
                </EmptyState>
            ) : (
                <div className="border rounded-lg overflow-hidden bg-white">
                    <Table>
                        <TableHeader>
                            <TableRow className="bg-muted/30">
                                <TableHead>Name</TableHead>
                                <TableHead>Discount</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {tiers.map((tier) => (
                                <TableRow key={tier.id} className={!tier.is_active ? "opacity-60 bg-muted/10" : ""}>
                                    <TableCell className="font-medium">
                                        {tier.name}
                                        {!tier.is_active && (
                                            <span className="ml-2 text-xs text-muted-foreground">(Inactive)</span>
                                        )}
                                    </TableCell>
                                    <TableCell>{(tier.discount_percentage * 100).toFixed(0)}%</TableCell>
                                    <TableCell>
                                        <Badge variant={tier.is_active ? "default" : "secondary"} className={tier.is_active ? "bg-green-600 hover:bg-green-700" : ""}>
                                            {tier.is_active ? "Active" : "Inactive"}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex justify-end gap-2">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 text-muted-foreground hover:text-foreground"
                                                onClick={() => handleEdit(tier)}
                                            >
                                                <Pencil size={14} />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                                                onClick={() => handleDelete(tier)}
                                            >
                                                <Trash2 size={14} />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            )}

            <PriceTierEditor
                open={isEditorOpen}
                onOpenChange={setIsEditorOpen}
                tier={editingTier}
                onSuccess={loadData}
            />
        </div>
    );
}
