"use client";

import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function SalesLayout({
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
            } else if (user.role !== "sales" && user.role !== "admin") {
                router.push("/unauthorized");
            }
        }
    }, [user, isLoading, router]);

    if (isLoading || !user || (user.role !== "sales" && user.role !== "admin")) {
        return <div className="flex h-screen items-center justify-center">Loading Sales Access...</div>;
    }

    // Mobile-first layout structure
    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            <header className="bg-green-700 text-white p-4 shadow">
                <h1 className="text-lg font-bold">Garden Sales</h1>
            </header>
            <main className="p-4">
                {children}
            </main>
            <nav className="fixed bottom-0 w-full bg-white border-t flex justify-around p-4 text-xs font-medium text-gray-600">
                <div className="text-green-700">Home</div>
                <div>New Order</div>
                <div>Clients</div>
                <div>Profile</div>
            </nav>
        </div>
    );
}
