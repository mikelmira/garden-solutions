"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function DeliveryLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user, isLoading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (isLoading) return;

        if (!user) {
            router.push("/login");
            return;
        }

        if (user.role !== "delivery" && user.role !== "admin") {
            router.push("/unauthorized");
        }
    }, [user, isLoading, router]);

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="text-gray-500">Loading...</div>
            </div>
        );
    }

    if (!user || (user.role !== "delivery" && user.role !== "admin")) {
        return null;
    }

    return <div className="min-h-screen bg-gray-50/50">{children}</div>;
}
