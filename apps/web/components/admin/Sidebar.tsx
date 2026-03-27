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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";

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

    return (
        <aside className="w-64 border-r border-border/50 bg-card h-screen fixed left-0 top-0 flex flex-col">
            {/* Brand Header */}
            <div className="p-5 border-b border-border/50">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-white rounded-xl flex items-center justify-center border">
                        <img src="/logo.avif" alt="Garden Solutions" className="h-6 w-6 object-contain" />
                    </div>
                    <div>
                        <h1 className="text-base font-heading font-semibold text-foreground">Garden Admin</h1>
                        <p className="text-[11px] text-muted-foreground">Operations Portal</p>
                    </div>
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
        </aside>
    );
}
