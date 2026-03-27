"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiService } from "@/lib/api";
import { Loader2 } from "lucide-react";

export default function AdminAccountPage() {
    const { toast } = useToast();
    const { user } = useAuth();

    const [passwords, setPasswords] = useState({ current: "", new: "", confirm: "" });
    const [loading, setLoading] = useState(false);

    const handleChangePassword = async () => {
        if (!passwords.current || !passwords.new || !passwords.confirm) {
            toast({ variant: "destructive", title: "Missing Fields", description: "All fields are required." });
            return;
        }

        if (passwords.new !== passwords.confirm) {
            toast({ variant: "destructive", title: "Mismatch", description: "New passwords do not match." });
            return;
        }

        try {
            setLoading(true);
            await apiService.admin.account.changePassword(passwords.current, passwords.new);
            toast({ title: "Success", description: "Password updated successfully." });
            setPasswords({ current: "", new: "", confirm: "" });
        } catch (error: any) {
            toast({ variant: "destructive", title: "Error", description: error.message || "Failed to update password." });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 max-w-2xl">
            <h1 className="text-3xl font-heading font-bold tracking-tight">Account Settings</h1>

            <Card>
                <CardHeader>
                    <CardTitle>Profile Information</CardTitle>
                    <CardDescription>Manage your admin profile.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Email</Label>
                        <Input value={user?.email || ""} disabled />
                    </div>
                    <div className="space-y-2">
                        <Label>Role</Label>
                        <Input value={user?.role || "Admin"} disabled />
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Change Password</CardTitle>
                    <CardDescription>Update your login password.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Current Password</Label>
                        <Input
                            type="password"
                            value={passwords.current}
                            onChange={e => setPasswords({ ...passwords, current: e.target.value })}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label>New Password</Label>
                        <Input
                            type="password"
                            value={passwords.new}
                            onChange={e => setPasswords({ ...passwords, new: e.target.value })}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label>Confirm New Password</Label>
                        <Input
                            type="password"
                            value={passwords.confirm}
                            onChange={e => setPasswords({ ...passwords, confirm: e.target.value })}
                        />
                    </div>
                </CardContent>
                <CardFooter>
                    <Button onClick={handleChangePassword} disabled={loading}>
                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Update Password
                    </Button>
                </CardFooter>
            </Card>
        </div>
    );
}
