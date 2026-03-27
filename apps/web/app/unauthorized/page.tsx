"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShieldAlert } from "lucide-react";

export default function UnauthorizedPage() {
    return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
            <Card className="max-w-md w-full text-center">
                <CardHeader>
                    <div className="mx-auto bg-red-100 p-3 rounded-full w-fit mb-4">
                        <ShieldAlert className="h-8 w-8 text-red-600" />
                    </div>
                    <CardTitle className="text-2xl font-bold">Access Denied</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <p className="text-muted-foreground">
                        You do not have permission to access this resource.
                        Please contact your administrator if you believe this is an error.
                    </p>
                    <div className="space-x-4">
                        <Button asChild variant="outline">
                            <Link href="/login">Switch Account</Link>
                        </Button>
                        <Button asChild>
                            <Link href="/">Go Home</Link>
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
