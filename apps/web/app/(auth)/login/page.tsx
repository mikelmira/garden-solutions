"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { apiService } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

/**
 * Determines the dashboard route based on user role.
 */
function getDashboardRoute(role: string): string {
    switch (role) {
        case "admin":
            return "/admin";
        case "sales":
            return "/sales-dashboard";
        case "manufacturing":
            return "/manufacturing-dashboard";
        case "delivery":
            return "/delivery-dashboard";
        default:
            return "/";
    }
}

export default function LoginPage() {
    const { register, handleSubmit, formState: { errors } } = useForm();
    const [error, setError] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { login, user, isLoading } = useAuth();
    const router = useRouter();

    // Single deterministic redirect effect - only runs when auth state is resolved
    useEffect(() => {
        // Wait until auth loading is complete
        if (isLoading) return;

        // If user is authenticated, redirect to their dashboard
        if (user) {
            router.push(getDashboardRoute(user.role));
        }
    }, [user, isLoading, router]);

    const onSubmit = async (data: any) => {
        try {
            setError("");
            setIsSubmitting(true);
            const formData = new FormData();
            formData.append("username", data.email);
            formData.append("password", data.password);

            const res = await apiService.auth.login(formData);
            login(res.access_token, res.refresh_token);
            // AuthProvider will fetch /me and update user state, triggering the useEffect redirect
        } catch (err: any) {
            console.error(err);
            setError("Invalid email or password. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    // Show loading while checking auth state
    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-surface">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    // Don't render login form if already logged in (redirect in progress)
    if (user) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-surface">
                <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Redirecting...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-surface p-4">
            <div className="w-full max-w-sm space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {/* Brand Header */}
                <div className="text-center space-y-2">
                    <div className="flex justify-center mb-4">
                        <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center shadow-lg border">
                            <img src="/logo.avif" alt="Garden Solutions" className="h-9 w-9 object-contain" />
                        </div>
                    </div>
                    <h1 className="text-2xl font-heading font-semibold tracking-tight">Garden Solutions</h1>
                    <p className="text-muted-foreground text-sm">Sign in to your account</p>
                </div>

                <Card className="border-0 shadow-xl shadow-black/5">
                    <CardContent className="pt-6">
                        {error && (
                            <div className="mb-4 p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    {...register("email", { required: true })}
                                    type="email"
                                    placeholder="you@example.com"
                                    autoComplete="email"
                                    className={errors.email ? "border-red-300 focus-visible:ring-red-500" : ""}
                                />
                                {errors.email && (
                                    <p className="text-xs text-red-500">Email is required</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="password">Password</Label>
                                <Input
                                    id="password"
                                    {...register("password", { required: true })}
                                    type="password"
                                    placeholder="••••••••"
                                    autoComplete="current-password"
                                    className={errors.password ? "border-red-300 focus-visible:ring-red-500" : ""}
                                />
                                {errors.password && (
                                    <p className="text-xs text-red-500">Password is required</p>
                                )}
                            </div>

                            <Button type="submit" className="w-full h-11" disabled={isSubmitting}>
                                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Sign In
                            </Button>
                        </form>
                    </CardContent>
                </Card>

                <p className="text-center text-xs text-muted-foreground">
                    Operations Management System
                </p>
            </div>
        </div>
    );
}
