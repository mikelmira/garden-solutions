export interface PriceTier {
    id: string;
    name: string;
    discount_percentage: number;
    is_active: boolean;
}

export interface Client {
    id: string;
    name: string;
    address?: string; // Optional - may not be present in all responses
    price_tier_id: string;
    price_tier?: PriceTier;
}

export interface SKU {
    id: string;
    product_id: string;
    code: string;
    size: string;
    color: string;
    base_price_rands: number;
    stock_quantity: number;
    is_active?: boolean;
    created_at?: string;
    updated_at?: string;
}

export interface Product {
    id: string;
    name: string;
    description?: string;
    category?: string;
    image_url?: string | null;
    is_active: boolean;
    created_at?: string;
    updated_at?: string;
    skus: SKU[];
}

export interface OrderItem {
    id: string; // Required for all persisted items (manufacturing/delivery)
    sku_id: string;
    quantity_ordered: number;
    unit_price_rands: number;
    quantity_manufactured?: number;
    quantity_allocated?: number; // Inventory allocated to this item
    quantity_delivered: number; // Required for delivery tracking (default 0 from API)
    product_name?: string;
    product_image?: string | null;
    sku_code?: string;
}

export interface Order {
    id: string;
    client_id: string;
    created_at: string;
    delivery_date: string;
    status: string; // Draft, Pending Approval, Approved, Cancelled, etc.
    total_price_rands: number;
    items?: OrderItem[];
    client?: Client;
    client_name?: string;
    is_ready_for_delivery?: boolean; // Computed: all items fully allocated
    delivery_team_id?: string | null;
    delivery_status?: string | null; // outstanding | delivered | partial | not_delivered
    delivery_paused?: boolean;
    delivered_at?: string | null;
}

export type CreateOrderPayload = {
    client_id: string;
    delivery_date: string;
    items: { sku_id: string; quantity_ordered: number }[];
};

export type PublicOrderPayload = {
    sales_agent_code?: string;
    client_id?: string;
    store_code?: string; // For store orders
    delivery_date: string;
    items: { sku_id: string; quantity_ordered: number }[];
    notes?: string;
};

export interface SalesAgent {
    id: string;
    name: string;
    code: string;
}

export interface DeliveryTeamMember {
    id: string;
    delivery_team_id: string;
    name: string;
    phone?: string;
    is_active?: boolean;
}

export interface DeliveryTeam {
    id: string;
    name: string;
    code: string;
    members?: DeliveryTeamMember[];
}

export interface FactoryTeamMember {
    id: string;
    factory_team_id: string;
    name: string;
    code: string;
    phone?: string;
    is_active?: boolean;
}

export interface FactoryTeam {
    id: string;
    name: string;
    code: string;
    members?: FactoryTeamMember[];
}

export interface DeliveryOutcomePayload {
    team_code: string;
    outcome: "Delivered" | "Partially Delivered" | "Not Delivered";
    receiver_name?: string;
    reason?: string;
    items?: { order_item_id: string; quantity_delivered: number }[];
}

export interface UserProfile {
    id: string;
    email: string;
    full_name: string;
    role: string;
}

// Canonical Error Envelope from API_REFERENCE (implied/standard)
export interface ApiError {
    detail: string | { loc: unknown[]; msg: string; type: string }[];
}

// ==== Manufacturing Types ====

export interface OutstandingOrderBreakdown {
    order_id: string;
    order_created_at: string;
    client_or_store_label: string;
    client_or_store_type: "client" | "store" | "unknown";
    quantity_outstanding: number;
}

export interface OutstandingSKUDemand {
    sku_id: string;
    sku_code: string;
    product_name: string;
    size: string;
    color: string;
    total_outstanding: number;
    display_string: string; // e.g., "15x Egg Pot - Small Green"
    breakdown: OutstandingOrderBreakdown[];
}

export interface OutstandingDemandResponse {
    skus: OutstandingSKUDemand[];
    total_skus: number;
    total_units: number;
}

export interface ManufacturingDayItem {
    id: string;
    sku_id: string;
    sku_code: string;
    product_name: string;
    size: string;
    color: string;
    quantity_planned: number;
    quantity_completed: number;
    display_string: string;
    remaining: number;
}

export interface ManufacturingDay {
    id: string;
    plan_date: string;
    created_by: string;
    created_at: string;
    items: ManufacturingDayItem[];
    total_planned: number;
    total_completed: number;
}

export interface ManufacturingDayCreatePayload {
    plan_date?: string;
    items: { sku_id: string; quantity_planned: number }[];
}
