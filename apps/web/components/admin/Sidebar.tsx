"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    ShoppingBag,
    Factory,
    Users,
    Briefcase,
    Truck,
    Settings,
    LogOut,
    Package,
    Tag,
    BarChart3,
    Store,
    ShoppingCart,
    Menu,
    X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { useState, useEffect } from "react";

const menuItems = [
    { label: "Overview", href: "/admin", icon: LayoutDashboard },
    { label: "Products", href: "/admin/products", icon: Package },
    { label: "Orders", href: "/admin/orders", icon: ShoppingBag },
    { label: "Manufacture", href: "/admin/manufacture", icon: Factory },
    { label: "Clients", href: "/admin/clients", icon: Users },
    { label: "Price Tiers", href: "/admin/price-tiers", icon: Tag },
    { label: "Teams", href: "/admin/sales-team", icon: Briefcase },
    { label: "Deliveries", href: "/admin/delivery-team", icon: Truck },
    { label: "Stores", href: "/admin/stores", icon: Store },
    { label: "Shopify", href: "/admin/shopify", icon: ShoppingCart },
    { label: "Intelligence", href: "/admin/analytics", icon: BarChart3 },
    { label: "Account", href: "/admin/account", icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();
    const { logout } = useAuth();
    const [mobileOpen, setMobileOpen] = useState(false);

    // Close mobile menu on route change
    useEffect(() => {
        setMobileOpen(false);
    }, [pathname]);

    // Prevent body scroll when mobile menu is open
    useEffect(() => {
        if (mobileOpen) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "";
        }
        return () => { document.body.style.overflow = ""; };
    }, [mobileOpen]);

    const sidebarContent = (
        <>
            {/* Brand Header */}
            <div className="p-5 border-b border-border/50">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-white rounded-xl flex items-center justify-center border">
                            <img src="/logo.avif" alt="Garden Solutions" className="h-6 w-6 object-contain" />
                        </div>
                        <div>
                            <h1 className="text-base font-heading font-semibold text-foreground">Garden Admin</h1>
                            <p className="text-[11px] text-muted-foreground">Operations Portal</p>
                        </div>
                    </div>
                    {/* Close button - mobile only */}
                    <button
                        onClick={() => setMobileOpen(false)}
                        className="lg:hidden p-2 rounded-lg hover:bg-muted transition-colors"
                        aria-label="Close menu"
                    >
                        <X className="h-5 w-5 text-muted-foreground" />
                    </button>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                {menuItems.map((item) => {
                    const isActive = pathname === item.href ||
                        (item.href !== "/admin" && pathname.startsWith(item.href));
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                                isActive
                                    ? "bg-primary text-primary-foreground shadow-sm"
                                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                            )}
                        >
                            <item.icon className={cn("h-4 w-4", isActive ? "text-primary-foreground" : "text-muted-foreground")} />
                            {item.label}
                        </Link>
                    );
                })}
            </nav>

            {/* Footer */}
            <div className="p-3 border-t border-border/50">
                <Button
                    variant="ghost"
                    className="w-full justify-start text-muted-foreground hover:text-destructive hover:bg-red-50"
                    onClick={logout}
                >
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign Out
                </Button>
            </div>
        </>
    );

    return (
        <>
            {/* Mobile top bar */}
            <div className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-card border-b border-border/50 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center border">
                        <img src="/logo.avif" alt="Garden Solutions" className="h-5 w-5 object-contain" />
                    </div>
                    <h1 className="text-sm font-heading font-semibold text-foreground">Garden Admin</h1>
                </div>
                <button
                    onClick={() => setMobileOpen(true)}
                    className="p-2 rounded-lg hover:bg-muted transition-colors"
                    aria-label="Open menu"
                >
                    <Menu className="h-5 w-5 text-foreground" />
                </button>
            </div>

            {/* Mobile overlay */}
            {mobileOpen && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/50 z-40 transition-opacity"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* Mobile sidebar drawer */}
            <aside
                className={cn(
                    "lg:hidden fixed left-0 top-0 bottom-0 w-72 bg-card z-50 flex flex-col transition-transform duration-300 ease-in-out",
                    mobileOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                {sidebarContent}
            </aside>

            {/* Desktop sidebar */}
            <aside className="hidden lg:flex w-64 border-r border-border/50 bg-card h-screen fixed left-0 top-0 flex-col">
                {sidebarContent}
            </aside>
        </>
    );
}
