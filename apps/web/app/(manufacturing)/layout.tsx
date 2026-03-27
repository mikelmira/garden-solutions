"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function ManufacturingLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        // Wait for auth to finish loading
        if (isLoading) return;

        // Redirect to login if not authenticated
        if (!user) {
            router.push("/login");
            return;
        }

        // Redirect if user doesn't have manufacturing or admin role
        if (user.role !== "manufacturing" && user.role !== "admin") {
            router.push("/unauthorized");
        }
    }, [user, isLoading, router]);

    // Show loading state while checking auth
    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="text-gray-500">Loading...</div>
            </div>
        );
    }

    // Don't render children if not authenticated or wrong role
    if (!user || (user.role !== "manufacturing" && user.role !== "admin")) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="text-gray-500">Redirecting...</div>
            </div>
        );
    }

    return <>{children}</>;
}
