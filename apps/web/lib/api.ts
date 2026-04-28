import axios, { AxiosError } from "axios";
import { CreateOrderPayload, Order, Client, Product, UserProfile, PriceTier, OutstandingDemandResponse, ManufacturingDay, ManufacturingDayCreatePayload, ManufacturingDayItem } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 30000, // 30 second timeout
});

// Request Interceptor: Auth Token
api.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
        const token = localStorage.getItem("access_token");
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
});

// Response Interceptor: Global Error Handling
api.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        // 401 errors are handled by the auth context (which attempts token refresh).
        // Only force-redirect if we're not on the login page and the error isn't from /auth/ endpoints.
        if (error.response?.status === 401) {
            if (typeof window !== "undefined") {
                const isAuthEndpoint = error.config?.url?.includes("/auth/");
                if (!isAuthEndpoint && !window.location.pathname.startsWith("/login")) {
                    localStorage.removeItem("access_token");
                    localStorage.removeItem("refresh_token");
                    window.location.href = "/login";
                }
            }
        }
        // Extract useful error message from API standard envelope { detail: ... }
        if (error.response?.data && typeof error.response.data === "object") {
            const data = error.response.data as any;
            if (data.detail) {
                // Handle Pydantic array errors or simple string
                const message = Array.isArray(data.detail)
                    ? data.detail.map((e: any) => e.msg).join(", ")
                    : data.detail;
                // Attach to error object so UI can use it
                error.message = message;
            }
        }
        return Promise.reject(error);
    }
);

// Mappers to isolate frontend from backend changes
function mapClientFromApi(data: any): Client {
    return {
        id: data.id,
        name: data.name,
        address: data.address,
        price_tier_id: data.tier_id ?? data.price_tier_id,
        price_tier: data.price_tier ? mapPriceTierFromApi(data.price_tier) : undefined,
    };
}

function mapPriceTierFromApi(data: any): PriceTier {
    return {
        id: data.id,
        name: data.name,
        discount_percentage: data.discount_percentage,
        is_active: data.is_active,
    };
}

function mapSkuFromApi(data: any): any { // Typed as any in return to match SKU interface but be flexible
    return {
        id: data.id,
        product_id: data.product_id,
        code: data.code,
        size: data.size,
        color: data.color,
        base_price_rands: data.base_price_rands,
        stock_quantity: data.stock_quantity,
        is_active: data.is_active !== undefined ? data.is_active : true, // Default true if missing
        created_at: data.created_at,
        updated_at: data.updated_at,
    };
}

function resolveImageUrl(url: string | null | undefined): string | null {
    if (!url) return null;
    if (url.startsWith("http")) return url;
    // Relative path from backend - prepend backend base
    const backendBase = process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") || "http://localhost:8000";
    return `${backendBase}${url}`;
}

function mapProductFromApi(data: any): Product {
    return {
        id: data.id,
        name: data.name,
        description: data.description,
        category: data.category,
        image_url: resolveImageUrl(data.image_url),
        is_active: data.is_active,
        created_at: data.created_at,
        updated_at: data.updated_at,
        skus: (data.skus || []).map(mapSkuFromApi),
    };
}

function mapOrderItemFromApi(data: any): any {
    return {
        id: data.id, // OrderItem.id - required for manufacturing updates
        sku_id: data.sku_id,
        quantity_ordered: data.quantity_ordered,
        unit_price_rands: data.unit_price_rands,
        quantity_manufactured: data.quantity_manufactured,
        quantity_allocated: data.quantity_allocated ?? 0,
        quantity_delivered: data.quantity_delivered,
        // Map nested details if available (backend dependent)
        product_name: data.product_name || data.sku?.product?.name,
        product_image: data.product_image || data.sku?.product?.image_url,
        sku_code: data.sku_code || data.sku?.code,
    };
}

function mapStatusFromApi(status: string): string {
    const map: Record<string, string> = {
        "draft": "Draft",
        "pending_approval": "Pending Approval",
        "approved": "Approved",
        "in_production": "In Production",
        "ready_for_delivery": "Ready for Delivery",
        "out_for_delivery": "Out for Delivery",
        "partially_delivered": "Partially Delivered",
        "completed": "Completed",
        "cancelled": "Cancelled",
    };
    return map[status] || status;
}

function mapStatusToApi(status: string): string {
    const map: Record<string, string> = {
        "Draft": "draft",
        "Pending Approval": "pending_approval",
        "Approved": "approved",
        "In Production": "in_production",
        "Ready for Delivery": "ready_for_delivery",
        "Out for Delivery": "out_for_delivery",
        "Partially Delivered": "partially_delivered",
        "Completed": "completed",
        "Cancelled": "cancelled",
    };
    return map[status] || status;
}

function mapOrderFromApi(data: any): Order {
    return {
        id: data.id,
        client_id: data.client_id,
        created_at: data.created_at,
        delivery_date: data.delivery_date,
        status: mapStatusFromApi(data.status),
        total_price_rands: Number(data.total_price_rands),
        items: (data.items || []).map(mapOrderItemFromApi),
        client: data.client ? mapClientFromApi(data.client) : undefined,
        client_name: data.client_name,
        is_ready_for_delivery: data.is_ready_for_delivery ?? false,
        delivery_team_id: data.delivery_team_id ?? null,
        delivery_status: data.delivery_status ?? null,
        delivery_paused: data.delivery_paused ?? false,
        delivered_at: data.delivered_at ?? null,
    };
}

// ... existing mapUserProfileFromApi ...
function mapUserProfileFromApi(data: any): UserProfile {
    return {
        id: data.id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
    };
}

export const apiService = {
    ops: {
        getMetrics: async (): Promise<any> => {
            const res = await api.get("/ops/metrics");
            return res.data.data;
        },
        getAuditLog: async (params?: { limit?: number; entity_type?: string; action?: string }): Promise<any[]> => {
            const res = await api.get("/ops/audit-log", { params });
            return res.data.data;
        },
    },
    analytics: {
        // Phase 1: Demand Forecasting
        getTopSkus: async (params?: { days?: number; limit?: number }): Promise<any[]> => {
            const res = await api.get("/analytics/demand/top-skus", { params });
            return res.data.data;
        },
        getDemandForecast: async (): Promise<any[]> => {
            const res = await api.get("/analytics/demand/forecast");
            return res.data.data;
        },
        // Phase 2: Manufacturing Suggestions
        getManufacturingSuggestions: async (): Promise<any> => {
            const res = await api.get("/analytics/manufacturing/suggestions");
            return res.data.data;
        },
        // Phase 3: Delivery Operations
        getDeliveryOperations: async (): Promise<any> => {
            const res = await api.get("/analytics/delivery/operations");
            return res.data.data;
        },
        // Phase 4: Alerts
        getAlerts: async (): Promise<any> => {
            const res = await api.get("/analytics/alerts");
            return res.data.data;
        },
        // Phase 5: Business Analytics
        getBusinessOverview: async (): Promise<any> => {
            const res = await api.get("/analytics/business/overview");
            return res.data.data;
        },
    },
    auth: {
        login: async (formData: FormData): Promise<{ access_token: string; refresh_token: string; token_type: string }> => {
            // Convert FormData to URLSearchParams for application/x-www-form-urlencoded
            // This is more reliable for OAuth2PasswordRequestForm
            const params = new URLSearchParams();
            formData.forEach((value, key) => {
                params.append(key, value as string);
            });
            const res = await api.post("/auth/login", params, {
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
            });
            return res.data.data; // Unwrap data per smoke test discovery
        },
        me: async (): Promise<UserProfile> => {
            const res = await api.get("/auth/me");
            return mapUserProfileFromApi(res.data.data); // Unwrap data
        },
        refresh: async (refreshToken: string): Promise<{ access_token: string; refresh_token: string }> => {
            const res = await api.post("/auth/refresh", { refresh_token: refreshToken });
            return res.data.data;
        },
    },
    clients: {
        list: async (): Promise<Client[]> => {
            const res = await api.get("/clients");
            return res.data.data.map(mapClientFromApi);
        },
        create: async (data: Partial<Client>): Promise<Client> => {
            const payload = {
                ...data,
                tier_id: data.price_tier_id,
            };
            delete (payload as any).price_tier_id;
            const res = await api.post("/clients", payload);
            return mapClientFromApi(res.data.data);
        },
        update: async (id: string, data: Partial<Client>): Promise<Client> => {
            const payload = {
                ...data,
                tier_id: data.price_tier_id,
            };
            delete (payload as any).price_tier_id;
            const res = await api.patch(`/clients/${id}`, payload);
            return mapClientFromApi(res.data.data);
        },
        delete: async (id: string): Promise<void> => {
            // Soft delete via is_active = false
            await api.patch(`/clients/${id}`, { is_active: false });
        }
    },
    stores: {
        list: async (): Promise<any[]> => {
            const res = await api.get("/stores");
            return res.data.data;
        },
        create: async (data: any): Promise<any> => {
            const res = await api.post("/stores", data);
            return res.data.data;
        },
        update: async (id: string, data: any): Promise<any> => {
            const res = await api.patch(`/stores/${id}`, data);
            return res.data.data;
        },
        delete: async (id: string): Promise<void> => {
            await api.patch(`/stores/${id}`, { is_active: false });
        }
    },
    products: {
        list: async (params?: { is_active?: boolean | null; size?: number }): Promise<Product[]> => {
            const queryParams: Record<string, any> = { size: params?.size ?? 100 };
            if (params?.is_active !== undefined && params?.is_active !== null) {
                queryParams.is_active = params.is_active;
            }
            const res = await api.get("/products", { params: queryParams });
            return res.data.data.map(mapProductFromApi);
        },
        get: async (id: string): Promise<Product> => {
            const res = await api.get(`/products/${id}`);
            return mapProductFromApi(res.data.data);
        },
        importCsv: async (formData: FormData): Promise<any> => {
            const res = await api.post("/products/import-csv", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            return res.data;
        },
        create: async (data: Partial<Product>): Promise<Product> => {
            const res = await api.post("/products", data);
            return mapProductFromApi(res.data.data);
        },
        update: async (id: string, data: Partial<Product>): Promise<Product> => {
            const res = await api.patch(`/products/${id}`, data);
            return mapProductFromApi(res.data.data);
        },
        delete: async (id: string): Promise<void> => {
            await api.patch(`/products/${id}`, { is_active: false });
        },
        // SKU Management
        addSku: async (productId: string, data: any): Promise<Product> => {
            await api.post(`/products/${productId}/skus`, data);
            // Return updated product to refresh UI
            const res = await api.get(`/products/${productId}`);
            return mapProductFromApi(res.data.data);
        },
        updateSku: async (skuId: string, data: any): Promise<void> => {
            await api.patch(`/skus/${skuId}`, data);
        },
        deleteSku: async (skuId: string): Promise<void> => {
            await api.patch(`/skus/${skuId}`, { is_active: false });
        },
        uploadImage: async (id: string, file: File): Promise<Product> => {
            const formData = new FormData();
            formData.append("file", file);
            const res = await api.post(`/products/${id}/image`, formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            return mapProductFromApi(res.data.data);
        },
        deleteImage: async (id: string): Promise<Product> => {
            const res = await api.delete(`/products/${id}/image`);
            return mapProductFromApi(res.data.data);
        }
    },
    priceTiers: {
        list: async (): Promise<PriceTier[]> => {
            const res = await api.get("/price-tiers");
            return res.data.data.map(mapPriceTierFromApi); // Unwrap data
        },
        create: async (data: Partial<PriceTier>): Promise<PriceTier> => {
            const res = await api.post("/price-tiers", data);
            return mapPriceTierFromApi(res.data.data);
        },
        update: async (id: string, data: Partial<PriceTier>): Promise<PriceTier> => {
            const res = await api.patch(`/price-tiers/${id}`, data);
            return mapPriceTierFromApi(res.data.data);
        },
        delete: async (id: string): Promise<void> => {
            await api.delete(`/price-tiers/${id}`);
        },
        getUsage: async (id: string): Promise<{ client_count: number; store_count: number }> => {
            const res = await api.get(`/price-tiers/${id}/usage`);
            return res.data.data;
        }
    },
    orders: {
        list: async (filters?: { status?: string; page?: number; size?: number }): Promise<Order[]> => {
            const params = filters ? { ...filters } : {};
            if (params.status) {
                params.status = mapStatusToApi(params.status);
            }
            const res = await api.get("/orders", { params });
            return res.data.data.map(mapOrderFromApi); // Unwrap data
        },
        get: async (id: string): Promise<Order> => {
            const res = await api.get(`/orders/${id}`);
            return mapOrderFromApi(res.data.data); // Unwrap data
        },
        create: async (payload: CreateOrderPayload): Promise<Order> => {
            const res = await api.post("/orders", payload);
            return mapOrderFromApi(res.data.data); // Unwrap data
        },
        updateStatus: async (id: string, status: string): Promise<Order> => {
            const apiStatus = mapStatusToApi(status);
            const res = await api.patch(`/orders/${id}/status`, { status: apiStatus });
            return mapOrderFromApi(res.data.data); // Unwrap data
        },
        delete: async (id: string): Promise<void> => {
            await api.delete(`/orders/${id}`);
        },
    },
    orderItems: {
        updateManufactured: async (id: string, quantity: number): Promise<any> => {
            const res = await api.patch(`/order-items/${id}/manufactured`, { quantity_manufactured: quantity });
            return res.data.data;
        },
    },
    delivery: {
        queue: async (): Promise<Order[]> => {
            const res = await api.get("/delivery/queue");
            return res.data.data.map(mapOrderFromApi);
        },
        partialDelivery: async (id: string, items: { id: string; quantity: number }[], receiver_name: string, reason: string): Promise<void> => {
            // Map frontend shape to backend DeliveryPartial schema
            await api.patch(`/delivery/orders/${id}/partial`, {
                receiver_name,
                reason,
                items: items.map(i => ({ order_item_id: i.id, quantity_delivered: i.quantity }))
            });
        },
        completeDelivery: async (id: string, receiver_name: string): Promise<void> => {
            // Backend DeliveryComplete only accepts receiver_name
            await api.patch(`/delivery/orders/${id}/complete`, {
                receiver_name
            });
        }
    },
    public: {
        salesAgents: {
            resolve: async (code: string): Promise<{ id: string; name: string; code: string }> => {
                const res = await api.post("/sales-agents/resolve", { code });
                return res.data.data; // Unwrap data.data
            }
        },
        deliveryTeams: {
            resolve: async (code: string): Promise<{ id: string; name: string; code: string }> => {
                const res = await api.post("/delivery-teams/resolve", { code });
                return res.data.data;
            }
        },
        stores: {
            resolve: async (code: string): Promise<{ id: string; name: string; code: string; store_type: string }> => {
                const res = await api.post("/stores/resolve", { code });
                return res.data.data;
            }
        },
        orders: {
            create: async (payload: import("../types").PublicOrderPayload): Promise<Order> => {
                const res = await api.post("/public/orders", payload);
                return mapOrderFromApi(res.data.data);
            }
        },
        delivery: {
            queue: async (teamCode: string, date?: string): Promise<Order[]> => {
                const params: any = { team_code: teamCode };
                if (date) params.date = date;
                const res = await api.get("/public/delivery/queue", { params });
                return res.data.data.map(mapOrderFromApi);
            },
            setOutcome: async (id: string, payload: import("../types").DeliveryOutcomePayload): Promise<void> => {
                const outcomeMap: Record<string, string> = {
                    "Delivered": "delivered",
                    "Partially Delivered": "partial",
                    "Not Delivered": "not_delivered"
                };

                const apiPayload = {
                    ...payload,
                    outcome: outcomeMap[payload.outcome] || payload.outcome
                };

                await api.patch(`/public/delivery/orders/${id}/outcome`, apiPayload);
            }
        },
        // Public data endpoints for /order page (no auth required)
        data: {
            clients: async (): Promise<Client[]> => {
                const res = await api.get("/public/clients");
                return res.data.data.map(mapClientFromApi);
            },
            products: async (): Promise<Product[]> => {
                const res = await api.get("/public/products");
                return res.data.data.map(mapProductFromApi);
            }
        }
    },
    manufacturing: {
        // Get outstanding demand aggregated by SKU (for admin)
        getOutstandingDemand: async (): Promise<OutstandingDemandResponse> => {
            const res = await api.get("/manufacturing/outstanding");
            return res.data.data;
        },
        // Get today's manufacturing plan
        getTodayPlan: async (): Promise<ManufacturingDay | null> => {
            const res = await api.get("/manufacturing/days/today");
            return res.data.data;
        },
        // Get plan by date
        getPlanByDate: async (date: string): Promise<ManufacturingDay | null> => {
            const res = await api.get("/manufacturing/days", { params: { date } });
            return res.data.data;
        },
        // Create a new manufacturing day plan (admin only)
        createPlan: async (payload: ManufacturingDayCreatePayload): Promise<ManufacturingDay> => {
            const res = await api.post("/manufacturing/days", payload);
            return res.data.data;
        },
        // Add items to today's plan (admin only)
        addItemsToPlan: async (payload: { items: { sku_id: string; quantity_planned: number }[] }): Promise<ManufacturingDay> => {
            const res = await api.post("/manufacturing/days/today/items", payload);
            return res.data.data;
        },
    },
    moulding: {
        // Verify factory code
        verifyCode: async (code: string): Promise<{ valid: boolean; code: string }> => {
            const res = await api.post(`/public/moulding/verify?factory_code=${encodeURIComponent(code)}`);
            return res.data.data;
        },
        // Get today's plan for moulding page (public endpoint with factory code header)
        getTodayPlan: async (factoryCode: string): Promise<ManufacturingDay | null> => {
            const res = await api.get("/public/moulding/today", {
                headers: { "X-Factory-Code": factoryCode }
            });
            return res.data.data;
        },
        // Update completion for a plan item (public endpoint with factory code header)
        updateItemCompletion: async (itemId: string, quantityCompleted: number, factoryCode: string): Promise<ManufacturingDayItem> => {
            const res = await api.patch(`/public/moulding/items/${itemId}`,
                { quantity_completed: quantityCompleted },
                { headers: { "X-Factory-Code": factoryCode } }
            );
            return res.data.data;
        },
    },
    admin: {
        salesAgents: {
            list: async (): Promise<any[]> => {
                const res = await api.get("/sales-agents");
                return res.data.data;
            },
            create: async (data: any): Promise<any> => {
                const res = await api.post("/sales-agents", data);
                return res.data.data;
            },
            update: async (id: string, data: any): Promise<any> => {
                const res = await api.patch(`/sales-agents/${id}`, data);
                return res.data.data;
            },
            delete: async (id: string): Promise<void> => {
                // If backend supports is_active, use it. Otherwise, this might need custom logic.
                // Assuming standard soft delete pattern for consistency.
                await api.patch(`/sales-agents/${id}`, { is_active: false });
            }
        },
        deliveryTeams: {
            list: async (): Promise<any[]> => {
                const res = await api.get("/delivery-teams");
                return res.data.data;
            },
            create: async (data: any): Promise<any> => {
                const res = await api.post("/delivery-teams", data);
                return res.data.data;
            },
            update: async (id: string, data: any): Promise<any> => {
                const res = await api.patch(`/delivery-teams/${id}`, data);
                return res.data.data;
            },
            delete: async (id: string): Promise<void> => {
                await api.patch(`/delivery-teams/${id}`, { is_active: false });
            },
            assignOrder: async (orderId: string, teamId: string): Promise<void> => {
                await api.patch(`/orders/${orderId}/assign-delivery-team`, { delivery_team_id: teamId });
            },
            updateAssignment: async (
                orderId: string,
                data: { delivery_team_id?: string | null; delivery_date?: string; paused?: boolean }
            ): Promise<void> => {
                await api.patch(`/orders/${orderId}/delivery-assignment`, data);
            },
            addMember: async (teamId: string, data: { name: string; phone?: string }): Promise<any> => {
                const res = await api.post(`/delivery-teams/${teamId}/members`, data);
                return res.data.data;
            },
            updateMember: async (teamId: string, memberId: string, data: { name?: string; phone?: string; is_active?: boolean }): Promise<any> => {
                const res = await api.patch(`/delivery-teams/${teamId}/members/${memberId}`, data);
                return res.data.data;
            },
            removeMember: async (teamId: string, memberId: string): Promise<void> => {
                await api.delete(`/delivery-teams/${teamId}/members/${memberId}`);
            }
        },
        factoryTeams: {
            list: async (): Promise<any[]> => {
                const res = await api.get("/factory-teams");
                return res.data.data;
            },
            create: async (data: any): Promise<any> => {
                const res = await api.post("/factory-teams", data);
                return res.data.data;
            },
            update: async (id: string, data: any): Promise<any> => {
                const res = await api.patch(`/factory-teams/${id}`, data);
                return res.data.data;
            },
            delete: async (id: string): Promise<void> => {
                await api.patch(`/factory-teams/${id}`, { is_active: false });
            },
            addMember: async (teamId: string, data: { name: string; code: string; phone?: string }): Promise<any> => {
                const res = await api.post(`/factory-teams/${teamId}/members`, data);
                return res.data.data;
            },
            updateMember: async (teamId: string, memberId: string, data: { name?: string; code?: string; phone?: string; is_active?: boolean }): Promise<any> => {
                const res = await api.patch(`/factory-teams/${teamId}/members/${memberId}`, data);
                return res.data.data;
            },
            removeMember: async (teamId: string, memberId: string): Promise<void> => {
                await api.delete(`/factory-teams/${teamId}/members/${memberId}`);
            }
        },
        analytics: {
            getOverview: async (): Promise<any> => {
                // Return empty object, page implements logic
                return {};
            }
        },
        account: {
            changePassword: async (current: string, newPass: string): Promise<void> => {
                await api.post("/auth/change-password", { current_password: current, new_password: newPass });
            }
        },
        shopify: {
            getStatus: async (): Promise<any> => {
                const res = await api.get("/shopify/status");
                return res.data.data;
            },
            getProducts: async (): Promise<any[]> => {
                const res = await api.get("/shopify/products");
                return res.data.data;
            },
            getVariants: async (params?: { status?: string }): Promise<any[]> => {
                const res = await api.get("/shopify/variants", { params });
                return res.data.data;
            },
            mapVariant: async (variantId: string, skuId: string): Promise<any> => {
                const res = await api.post(`/shopify/variants/${variantId}/map`, { sku_id: skuId });
                return res.data.data;
            },
            ignoreVariant: async (variantId: string): Promise<any> => {
                const res = await api.post(`/shopify/variants/${variantId}/ignore`);
                return res.data.data;
            },
            getOrders: async (params?: { sync_status?: string }): Promise<any[]> => {
                const res = await api.get("/shopify/orders", { params });
                return res.data.data;
            },
            syncProducts: async (products: any[]): Promise<any> => {
                const res = await api.post("/shopify/sync/products", { products });
                return res.data.data;
            },
            syncOrders: async (orders: any[]): Promise<any> => {
                const res = await api.post("/shopify/sync/orders", { orders });
                return res.data.data;
            },
            reconcileMappings: async (): Promise<any> => {
                const res = await api.post("/shopify/reconcile/mappings");
                return res.data.data;
            },
            reconcileOrders: async (): Promise<any> => {
                const res = await api.post("/shopify/reconcile/orders");
                return res.data.data;
            },
            getRecentWebhooks: async (): Promise<any[]> => {
                const res = await api.get("/shopify/webhooks/recent");
                return res.data.data;
            },
            searchSkus: async (q: string): Promise<any[]> => {
                const res = await api.get("/shopify/internal-skus", { params: { q } });
                return res.data.data;
            },
            getCustomers: async (q?: string): Promise<any[]> => {
                const res = await api.get("/shopify/customers", { params: q ? { q } : {} });
                return res.data.data;
            },
        },
    }
};
