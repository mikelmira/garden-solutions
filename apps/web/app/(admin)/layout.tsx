"use client";

import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Sidebar } from "@/components/admin/Sidebar";

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!isLoading) {
            if (!user) {
                router.push("/login");
            } else if (user.role !== "admin") {
                router.push("/unauthorized");
            }
        }
    }, [user, isLoading, router]);

    if (isLoading || !user || user.role !== "admin") {
        return <div className="flex h-screen items-center justify-center">Loading Admin Access...</div>;
    }

    return (
        <div className="min-h-screen bg-background text-foreground">
            <Sidebar />
            <main className="lg:pl-64 min-h-screen">
                {/* Add top padding on mobile for the fixed header bar */}
                <div className="p-4 pt-16 lg:p-8 max-w-7xl mx-auto">
                    {children}
                </div>
            </main>
        </div>
    );
}
