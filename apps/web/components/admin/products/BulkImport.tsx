"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Upload, Loader2, AlertCircle, FileText, CheckCircle2 } from "lucide-react";
import { apiService } from "@/lib/api";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export function BulkImport({ onSuccess }: { onSuccess: () => void }) {
    const { toast } = useToast();
    const [file, setFile] = useState<File | null>(null);
    const [previewData, setPreviewData] = useState<string[][]>([]);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<any>(null);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (!selectedFile) return;

        setFile(selectedFile);
        setResult(null);

        // Parse for preview (First 5 lines)
        const text = await selectedFile.text();
        const rows = text.split(/\r?\n/).filter(r => r.trim() !== "").slice(0, 6);
        const parsed = rows.map(r => r.split(',').map(c => c.trim()));
        setPreviewData(parsed);
    };

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await apiService.products.importCsv(formData);
            setResult(response);
            toast({ title: "Import Processed", description: "Check results below." });
            if (response.success_count > 0) {
                onSuccess(); // Trigger refresh on parent
            }
        } catch (error: any) {
            toast({
                title: "Upload Failed",
                description: error.message || "Failed to upload file.",
                variant: "destructive"
            });
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-6">
            {!result ? (
                <div className="space-y-4">
                    <div className="grid w-full max-w-sm items-center gap-1.5">
                        <Label htmlFor="csv-file">CSV File</Label>
                        <Input id="csv-file" type="file" accept=".csv" onChange={handleFileChange} />
                        <p className="text-xs text-muted-foreground">
                            Required columns: product_name, category, sku_code, base_price_rands...
                        </p>
                    </div>

                    {previewData.length > 0 && (
                        <div className="border rounded-md">
                            <div className="p-2 bg-muted/50 text-xs font-medium border-b">File Preview (First 5 rows)</div>
                            <Table>
                                <TableBody>
                                    {previewData.slice(0, 5).map((row, idx) => (
                                        <TableRow key={idx}>
                                            {row.slice(0, 4).map((cell, cIdx) => (
                                                <TableCell key={cIdx} className="text-xs py-2">{cell}</TableCell>
                                            ))}
                                            {row.length > 4 && <TableCell className="text-xs py-2 text-muted-foreground">...</TableCell>}
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}

                    <Button onClick={handleUpload} disabled={!file || uploading} className="w-full">
                        {uploading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        <Upload className="mr-2 h-4 w-4" /> Import Products
                    </Button>
                </div>
            ) : (
                <div className="space-y-4">
                    <Alert variant={result.errors?.length > 0 ? "destructive" : "default"} className="border-green-200 bg-green-50">
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                        <AlertTitle className="text-green-800">Import Completed</AlertTitle>
                        <AlertDescription className="text-green-700">
                            Processed {result.total_processed} rows. <br />
                            Success: {result.success_count} | Skipped: {result.skipped_count} | Errors: {result.errors?.length || 0}
                        </AlertDescription>
                    </Alert>

                    {result.errors.length > 0 && (
                        <div className="max-h-60 overflow-y-auto border rounded bg-gray-50 p-2">
                            <p className="text-sm font-bold text-red-700 mb-2">Errors Details:</p>
                            <ul className="text-xs space-y-1 text-red-600 font-mono">
                                {result.errors.map((err: any, idx: number) => (
                                    <li key={idx}>Row {err.row}: {err.message}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <Button variant="outline" onClick={() => { setFile(null); setResult(null); setPreviewData([]); }} className="w-full">
                        Import Another File
                    </Button>
                </div>
            )}
        </div>
    );
}
