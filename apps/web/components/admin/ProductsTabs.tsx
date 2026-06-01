"use client";

/**
 * ProductsTabs — shared header for the unified Products section.
 *
 * Renders three tabs that link between the existing pages without changing
 * their URLs:
 *   /admin/products            → All Products  (internal catalog)
 *   /admin/shopify             → Shopify       (integration status / sync)
 *   /admin/shopify-products    → Shopify Products (push-back editor)
 *
 * Each of those pages renders <ProductsTabs /> at the top.
 */
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Package, ShoppingCart, Boxes } from "lucide-react";
import type { LucideIcon } from "lucide-react";

type Tab = { label: string; href: string; icon: LucideIcon };

const TABS: Tab[] = [
    { label: "All Products", href: "/admin/products", icon: Package },
    { label: "Shopify", href: "/admin/shopify", icon: ShoppingCart },
    { label: "Shopify Products", href: "/admin/shopify-products", icon: Boxes },
];

function isActive(pathname: string, href: string): boolean {
    return pathname === href || pathname.startsWith(href + "/");
}

export function ProductsTabs() {
    const pathname = usePathname();

    return (
        <div className="border-b border-border/60 -mx-1 mb-4">
            <nav className="flex items-end gap-1 overflow-x-auto" aria-label="Products tabs">
                {TABS.map(tab => {
                    const active = isActive(pathname, tab.href);
                    return (
                        <Link
                            key={tab.href}
                            href={tab.href}
                            className={cn(
                                "inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px",
                                active
                                    ? "border-primary text-foreground"
                                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                            )}
                            aria-current={active ? "page" : undefined}
                        >
                            <tab.icon className="h-4 w-4" />
                            {tab.label}
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
}
