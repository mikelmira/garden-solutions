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
    Brush,
    Mail,
    Menu,
    X,
    ChevronDown,
    type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { useState, useEffect, useMemo } from "react";

type MenuChild = { label: string; href: string; icon: LucideIcon };
type MenuItem =
    | { label: string; href: string; icon: LucideIcon; children?: undefined }
    | { label: string; icon: LucideIcon; children: MenuChild[]; href?: undefined };

// Order reflects the operations workflow: Orders → Manufacture → Deliveries.
const menuItems: MenuItem[] = [
    { label: "Overview", href: "/admin", icon: LayoutDashboard },
    { label: "Orders", href: "/admin/orders", icon: ShoppingBag },
    {
        label: "Manufacture",
        icon: Factory,
        children: [
            { label: "Moulding", href: "/admin/manufacture", icon: Factory },
            { label: "Painting", href: "/admin/painting", icon: Brush },
        ],
    },
    { label: "Deliveries", href: "/admin/delivery-team", icon: Truck },
    // Products section — internal page renders tabs for All Products / Shopify / Shopify Products.
    { label: "Products", href: "/admin/products", icon: Package },
    { label: "Clients", href: "/admin/clients", icon: Users },
    { label: "Stores", href: "/admin/stores", icon: Store },
    { label: "Price Tiers", href: "/admin/price-tiers", icon: Tag },
    { label: "Teams", href: "/admin/sales-team", icon: Briefcase },
    { label: "Automations", href: "/admin/automations", icon: Mail },
    { label: "Intelligence", href: "/admin/analytics", icon: BarChart3 },
    { label: "Account", href: "/admin/account", icon: Settings },
];

// Routes that belong to the unified Products section — selecting any of these
// keeps the "Products" sidebar entry highlighted.
const PRODUCTS_SECTION_PREFIXES = ["/admin/products", "/admin/shopify", "/admin/shopify-products"];

function isProductsRoute(pathname: string): boolean {
    return PRODUCTS_SECTION_PREFIXES.some(p => pathname === p || pathname.startsWith(p + "/"));
}

function isChildActive(pathname: string, href: string): boolean {
    return pathname === href || pathname.startsWith(href + "/");
}

export function Sidebar() {
    const pathname = usePathname();
    const { logout } = useAuth();
    const [mobileOpen, setMobileOpen] = useState(false);

    // Track which dropdown parents are expanded. Auto-expand any group whose
    // child is currently active.
    const initialExpanded = useMemo<Record<string, boolean>>(() => {
        const expanded: Record<string, boolean> = {};
        for (const item of menuItems) {
            if (item.children) {
                const hasActive = item.children.some(c => isChildActive(pathname, c.href));
                if (hasActive) expanded[item.label] = true;
            }
        }
        return expanded;
    }, []);  // eslint-disable-line react-hooks/exhaustive-deps
    const [expanded, setExpanded] = useState<Record<string, boolean>>(initialExpanded);

    // If the path changes such that a new group's child becomes active, expand it.
    useEffect(() => {
        setExpanded(prev => {
            const next = { ...prev };
            let changed = false;
            for (const item of menuItems) {
                if (item.children && item.children.some(c => isChildActive(pathname, c.href))) {
                    if (!next[item.label]) {
                        next[item.label] = true;
                        changed = true;
                    }
                }
            }
            return changed ? next : prev;
        });
    }, [pathname]);

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

    const toggleGroup = (label: string) => {
        setExpanded(prev => ({ ...prev, [label]: !prev[label] }));
    };

    const renderLeaf = (item: { label: string; href: string; icon: LucideIcon }) => {
        // Special case: Products entry stays highlighted across the whole Products section
        // (which includes /admin/shopify and /admin/shopify-products tabs).
        const isActive =
            item.href === "/admin/products"
                ? isProductsRoute(pathname)
                : item.href === "/admin"
                    ? pathname === "/admin"
                    : pathname === item.href || pathname.startsWith(item.href + "/");

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
    };

    const renderGroup = (item: { label: string; icon: LucideIcon; children: MenuChild[] }) => {
        const isOpen = !!expanded[item.label];
        const hasActiveChild = item.children.some(c => isChildActive(pathname, c.href));

        return (
            <div key={item.label} className="space-y-1">
                <button
                    type="button"
                    onClick={() => toggleGroup(item.label)}
                    aria-expanded={isOpen}
                    className={cn(
                        "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                        hasActiveChild
                            ? "text-foreground bg-muted/60"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                >
                    <item.icon className="h-4 w-4 text-muted-foreground" />
                    <span className="flex-1 text-left">{item.label}</span>
                    <ChevronDown
                        className={cn(
                            "h-4 w-4 text-muted-foreground transition-transform duration-200",
                            isOpen ? "rotate-0" : "-rotate-90"
                        )}
                    />
                </button>
                {isOpen && (
                    <div className="ml-3 pl-3 border-l border-border/60 space-y-1">
                        {item.children.map(child => {
                            const childActive = isChildActive(pathname, child.href);
                            return (
                                <Link
                                    key={child.href}
                                    href={child.href}
                                    className={cn(
                                        "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200",
                                        childActive
                                            ? "bg-primary text-primary-foreground shadow-sm"
                                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                    )}
                                >
                                    <child.icon className={cn("h-4 w-4", childActive ? "text-primary-foreground" : "text-muted-foreground")} />
                                    {child.label}
                                </Link>
                            );
                        })}
                    </div>
                )}
            </div>
        );
    };

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
                {menuItems.map(item =>
                    item.children ? renderGroup(item) : renderLeaf(item)
                )}
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
