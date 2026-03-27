import { Order, Client, Product, SalesAgent, DeliveryTeam } from "@/types";

// Types for our Mock DB
export interface MockStore {
    id: string;
    name: string;
    code: string;
    store_type: "nursery" | "shopify";
    is_active: boolean;
}

const STORAGE_KEYS = {
    ORDERS: "garden_demo_orders",
    CLIENTS: "garden_demo_clients",
    STORES: "garden_demo_stores",
    SALES_AGENTS: "garden_demo_sales_agents",
    DELIVERY_TEAMS: "garden_demo_delivery_teams",
    PRODUCTS: "garden_demo_products",
};

// Seed Data — Real Garden Solutions customers
const SEED_CLIENTS: Client[] = [
    { id: "c1", name: "Pot & Planter (Pty) Ltd t/a The Pot Shack", price_tier_id: "A" },
    { id: "c2", name: "Adeo/Leroy Merlin South Africa (Pty) Ltd", price_tier_id: "B" },
    { id: "c3", name: "STODELS NURSERIES", price_tier_id: "B" },
    { id: "c4", name: "LIFESTYLE GARDEN CENTRE (PTY) LTD", price_tier_id: "B" },
    { id: "c5", name: "Starke Ayres (Rosebank)", price_tier_id: "C" },
    { id: "c6", name: "Burgess Landscapes Coastal (Pty) Ltd", price_tier_id: "C" },
    { id: "c7", name: "ECKARDS GARDEN PAVILION", price_tier_id: "A" },
    { id: "c8", name: "SAFARI GARDEN CENTRE", price_tier_id: "A" },
    { id: "c9", name: "Life Green Group t/a Life Indoors", price_tier_id: "B" },
    { id: "c10", name: "FYNBOS LANDSCAPES", price_tier_id: "C" },
    { id: "c11", name: "Bidvest ExecuFlora JHB", price_tier_id: "B" },
    { id: "c12", name: "LOTS OF POTS", price_tier_id: "A" },
    { id: "c13", name: "Greenery Guru", price_tier_id: "C" },
    { id: "c14", name: "Coenique Landscaping", price_tier_id: "C" },
    { id: "c15", name: "GARDENSHOP PARKTOWN", price_tier_id: "A" },
    { id: "c16", name: "AE NEL t/a PLANT PLEASURE", price_tier_id: "B" },
    { id: "c17", name: "Arlene Stone interiors", price_tier_id: "C" },
    { id: "c18", name: "B.T. Decor cc", price_tier_id: "C" },
    { id: "c19", name: "Bar Events", price_tier_id: "C" },
    { id: "c20", name: "BBR INVESTMENT HOLDING PTY LTD", price_tier_id: "B" },
    { id: "c21", name: "Blend Property 20 (Pty) Ltd", price_tier_id: "C" },
    { id: "c22", name: "BluePrint Business Corp", price_tier_id: "C" },
    { id: "c23", name: "Botanical Haven", price_tier_id: "B" },
    { id: "c24", name: "BROADACRES LANDSCAPES", price_tier_id: "C" },
    { id: "c25", name: "BUDS AND PETALS PTY LTD", price_tier_id: "B" },
    { id: "c26", name: "CONCRETE & GARDEN CREATIONS", price_tier_id: "C" },
    { id: "c27", name: "Create a Landscape", price_tier_id: "C" },
    { id: "c28", name: "Exclusive Landscapes", price_tier_id: "C" },
    { id: "c29", name: "Fourways Airconditioning Cape (PTY) Ltd", price_tier_id: "B" },
    { id: "c30", name: "Fresh Earth Gardens", price_tier_id: "C" },
    { id: "c31", name: "Garden Heart cc", price_tier_id: "B" },
    { id: "c32", name: "Garden Mechanix", price_tier_id: "C" },
    { id: "c33", name: "GARDEN VALE", price_tier_id: "B" },
    { id: "c34", name: "GOODIES FOR GARDENS KEMPTON PARK", price_tier_id: "A" },
    { id: "c35", name: "Hadland Business Pty Ltd t/a Working Hands", price_tier_id: "B" },
    { id: "c36", name: "Builders Warehouse Strubens Valley", price_tier_id: "A" },
    { id: "c37", name: "Builders Warehouse Centurion", price_tier_id: "A" },
    { id: "c38", name: "Builders Warehouse Rivonia", price_tier_id: "A" },
    { id: "c39", name: "Builders Express Southgate", price_tier_id: "A" },
    { id: "c40", name: "Builders Express Lynnwood", price_tier_id: "A" },
    { id: "c41", name: "Builders Express Wonderpark", price_tier_id: "A" },
    { id: "c42", name: "Builders Express Vredenburg", price_tier_id: "A" },
    { id: "c43", name: "Alan Maher", price_tier_id: "C" },
    { id: "c44", name: "Alicia Coetzee", price_tier_id: "C" },
    { id: "c45", name: "Alicia Lesch", price_tier_id: "C" },
    { id: "c46", name: "Allison Van Manen", price_tier_id: "C" },
    { id: "c47", name: "Bob Bhaga", price_tier_id: "C" },
    { id: "c48", name: "BRYAN", price_tier_id: "C" },
    { id: "c49", name: "C-Pac Co Packers", price_tier_id: "B" },
    { id: "c50", name: "Hadland Business Pty Ltd", price_tier_id: "B" },
];

const SEED_PRODUCTS: Product[] = [
    {
        id: "p1",
        name: "Premium Bolivia Trough Plant Pot",
        category: "Concrete Pots",
        image_url: null,
        is_active: true,
        skus: [
            { id: "sku1", product_id: "p1", code: "PBOLTRPP-LG-AMP", size: "Large | 280mm x 325mm x 715mm", color: "Amper", base_price_rands: 901, stock_quantity: 0 },
            { id: "sku2", product_id: "p1", code: "PBOLTRPP-LG-FWH", size: "Large | 280mm x 325mm x 715mm", color: "Flinted White", base_price_rands: 901, stock_quantity: 0 },
            { id: "sku3", product_id: "p1", code: "PBOLTRPP-LG-ROC", size: "Large | 280mm x 325mm x 715mm", color: "Rock", base_price_rands: 901, stock_quantity: 0 },
        ],
    },
    {
        id: "p2",
        name: "Premium Chunky Trough Plant Pot",
        category: "Concrete Pot",
        image_url: null,
        is_active: true,
        skus: [
            { id: "sku4", product_id: "p2", code: "PCHUTRPP-SM-AMP", size: "Small | 310mm X 300mm X 600mm", color: "Amper", base_price_rands: 812, stock_quantity: 0 },
            { id: "sku5", product_id: "p2", code: "PCHUTRPP-SM-FWH", size: "Small | 310mm X 300mm X 600mm", color: "Flinted White", base_price_rands: 812, stock_quantity: 0 },
            { id: "sku6", product_id: "p2", code: "PCHUTRPP-MD-AMP", size: "Medium | 340mm x 340mm x 800mm", color: "Amper", base_price_rands: 1053, stock_quantity: 0 },
        ],
    },
    {
        id: "p3",
        name: "Amazon Plant Pot",
        category: "Concrete Pot",
        image_url: null,
        is_active: true,
        skus: [
            { id: "sku7", product_id: "p3", code: "AMACPOT-LG-AMP", size: "Large | 840mm X 500mm", color: "Amper", base_price_rands: 1868, stock_quantity: 0 },
            { id: "sku8", product_id: "p3", code: "AMACPOT-LG-FWH", size: "Large | 840mm X 500mm", color: "Flinted White", base_price_rands: 1868, stock_quantity: 0 },
        ],
    },
    {
        id: "p4",
        name: "Baobab Concrete Pot",
        category: "Concrete Pot",
        image_url: null,
        is_active: true,
        skus: [
            { id: "sku9", product_id: "p4", code: "BOACPOT-LG-AMP", size: "Large | 560mm X 480mm", color: "Amper", base_price_rands: 995, stock_quantity: 0 },
            { id: "sku10", product_id: "p4", code: "BOACPOT-LG-FWH", size: "Large | 560mm X 480mm", color: "Flinted White", base_price_rands: 995, stock_quantity: 0 },
        ],
    },
    {
        id: "p5",
        name: "Premium Windsor Plant Pot",
        category: "Concrete Pot",
        image_url: null,
        is_active: true,
        skus: [
            { id: "sku11", product_id: "p5", code: "PWINPP-SM-AMP", size: "Small | 370mm x 240mm", color: "Amper", base_price_rands: 450, stock_quantity: 0 },
            { id: "sku12", product_id: "p5", code: "PWINPP-SM-FWH", size: "Small | 370mm x 240mm", color: "Flinted White", base_price_rands: 450, stock_quantity: 0 },
            { id: "sku13", product_id: "p5", code: "PWINPP-SM-GRA", size: "Small | 370mm x 240mm", color: "Granite", base_price_rands: 450, stock_quantity: 0 },
        ],
    },
    {
        id: "p6",
        name: "Geni Concrete Pot",
        category: "Concrete Pot",
        image_url: null,
        is_active: true,
        skus: [
            { id: "sku14", product_id: "p6", code: "GENCPOT-XL-AMP", size: "Extra Large | 1300mm x 840mm", color: "Amper", base_price_rands: 4539, stock_quantity: 0 },
            { id: "sku15", product_id: "p6", code: "GENCPOT-XL-FWH", size: "Extra Large | 1300mm x 840mm", color: "Flinted White", base_price_rands: 4539, stock_quantity: 0 },
        ],
    },
    {
        id: "p7",
        name: "Jessica Plant Pot",
        category: "Concrete Pot",
        image_url: null,
        is_active: true,
        skus: [
            { id: "sku16", product_id: "p7", code: "JESCPOT-600-AMP", size: "Jumbo | 600mm X 710mm", color: "Amper", base_price_rands: 1566, stock_quantity: 0 },
            { id: "sku17", product_id: "p7", code: "JESCPOT-600-FWH", size: "Jumbo | 600mm X 710mm", color: "Flinted White", base_price_rands: 1566, stock_quantity: 0 },
        ],
    },
    {
        id: "p8",
        name: "Drip Tray",
        category: "Concrete Tray",
        image_url: null,
        is_active: true,
        skus: [
            { id: "sku18", product_id: "p8", code: "DRITY-LG-AMP", size: "Large | 600mm", color: "Amper", base_price_rands: 197, stock_quantity: 0 },
            { id: "sku19", product_id: "p8", code: "DRITY-LG-FWH", size: "Large | 600mm", color: "Flinted White", base_price_rands: 197, stock_quantity: 0 },
        ],
    },
    {
        id: "p9",
        name: "Kathy Plant Pot",
        category: "Concrete Pot",
        image_url: null,
        is_active: true,
        skus: [
            { id: "sku20", product_id: "p9", code: "KATCPOT-LG-AMP", size: "Large | 530mm x 555mm", color: "Amper", base_price_rands: 1052, stock_quantity: 0 },
            { id: "sku21", product_id: "p9", code: "KATCPOT-LG-ROC", size: "Large | 530mm x 555mm", color: "Rock", base_price_rands: 1052, stock_quantity: 0 },
        ],
    },
    {
        id: "p10",
        name: "Round Tray",
        category: "Concrete Tray",
        image_url: null,
        is_active: true,
        skus: [
            { id: "sku22", product_id: "p10", code: "ROUTY-SM-AMP", size: "Small | 380mm", color: "Amper", base_price_rands: 119, stock_quantity: 0 },
            { id: "sku23", product_id: "p10", code: "ROUTY-SM-FWH", size: "Small | 380mm", color: "Flinted White", base_price_rands: 119, stock_quantity: 0 },
        ],
    },
];

const SEED_STORES: MockStore[] = [
    { id: "s1", name: "Pot and Planter - Church Street", code: "POT-JHB-CHURCH", store_type: "nursery", is_active: true },
    { id: "s2", name: "Pot and Planter - Cornubia Mall", code: "POT-KZN-CORNUBIA", store_type: "nursery", is_active: true },
    { id: "s3", name: "Pot and Planter - Table Bay Mall", code: "POT-CPT-TABLEBAY", store_type: "nursery", is_active: true },
    { id: "s4", name: "Pot and Planter - Cedar", code: "POT-JHB-CEDAR", store_type: "nursery", is_active: true },
    { id: "s5", name: "PotShack Online Store", code: "SHOP-ONLINE", store_type: "shopify", is_active: true },
];

const SEED_SALES_AGENTS: SalesAgent[] = [
    { id: "sa1", name: "Sue Elmira", code: "4500" },
];

const SEED_DELIVERY_TEAMS: DeliveryTeam[] = [
    {
        id: "dt1",
        name: "Delivery Team Alpha",
        code: "D-4501",
        members: [
            { id: "m1", delivery_team_id: "dt1", name: "Aiden Driver", is_active: true },
            { id: "m2", delivery_team_id: "dt1", name: "Lea Runner", is_active: true },
            { id: "m3", delivery_team_id: "dt1", name: "Sam Loader", is_active: true }
        ]
    },
    {
        id: "dt2",
        name: "Delivery Team Bravo",
        code: "D-4502",
        members: [
            { id: "m4", delivery_team_id: "dt2", name: "Nia Driver", is_active: true },
            { id: "m5", delivery_team_id: "dt2", name: "Tariq Runner", is_active: true },
            { id: "m6", delivery_team_id: "dt2", name: "Olivia Loader", is_active: true }
        ]
    },
    {
        id: "dt3",
        name: "Delivery Team Charlie",
        code: "D-4503",
        members: [
            { id: "m7", delivery_team_id: "dt3", name: "Ben Driver", is_active: true },
            { id: "m8", delivery_team_id: "dt3", name: "Zara Runner", is_active: true },
            { id: "m9", delivery_team_id: "dt3", name: "Mila Loader", is_active: true }
        ]
    },
];

const SEED_ORDERS: Order[] = [
    {
        id: "ORD-001",
        client_id: "c1",
        client_name: "Pot & Planter (Pty) Ltd t/a The Pot Shack",
        created_at: new Date().toISOString(),
        delivery_date: "2026-04-01",
        status: "Pending Approval",
        total_price_rands: 1500,
        items: [
            { id: "i1", sku_id: "sku1", quantity_ordered: 10, unit_price_rands: 901, quantity_manufactured: 5, quantity_delivered: 0 }
        ]
    },
    {
        id: "ORD-002",
        client_id: "s5",
        client_name: "PotShack Online Store",
        created_at: new Date(Date.now() - 86400000).toISOString(),
        delivery_date: "2026-04-05",
        status: "Approved",
        total_price_rands: 18020,
        items: [
            { id: "i2", sku_id: "sku4", quantity_ordered: 20, unit_price_rands: 812, quantity_manufactured: 20, quantity_delivered: 0 }
        ]
    },
    {
        id: "ORD-003",
        client_id: "c2",
        client_name: "Adeo/Leroy Merlin South Africa (Pty) Ltd",
        created_at: new Date(Date.now() - 172800000).toISOString(),
        delivery_date: "2026-04-10",
        status: "Pending Approval",
        total_price_rands: 28020,
        items: [
            { id: "i3", sku_id: "sku7", quantity_ordered: 15, unit_price_rands: 1868, quantity_manufactured: 0, quantity_delivered: 0 }
        ]
    },
    {
        id: "ORD-004",
        client_id: "c3",
        client_name: "STODELS NURSERIES",
        created_at: new Date(Date.now() - 259200000).toISOString(),
        delivery_date: "2026-04-12",
        status: "Delivered",
        total_price_rands: 49750,
        items: [
            { id: "i4", sku_id: "sku9", quantity_ordered: 50, unit_price_rands: 995, quantity_manufactured: 50, quantity_delivered: 50 }
        ]
    },
    {
        id: "ORD-005",
        client_id: "c4",
        client_name: "LIFESTYLE GARDEN CENTRE (PTY) LTD",
        created_at: new Date(Date.now() - 345600000).toISOString(),
        delivery_date: "2026-04-15",
        status: "In Production",
        total_price_rands: 5400,
        items: [
            { id: "i5", sku_id: "sku11", quantity_ordered: 12, unit_price_rands: 450, quantity_manufactured: 6, quantity_delivered: 0 }
        ]
    }
];

// Helper to get from storage or seed
const getStorage = <T>(key: string, seed: T[]): T[] => {
    if (typeof window === "undefined") return seed;
    const stored = localStorage.getItem(key);
    if (!stored) {
        localStorage.setItem(key, JSON.stringify(seed));
        return seed;
    }
    return JSON.parse(stored);
};

const setStorage = <T>(key: string, data: T[]) => {
    if (typeof window === "undefined") return;
    localStorage.setItem(key, JSON.stringify(data));
};

export const mockDb = {
    reset: () => {
        if (typeof window === "undefined") return;
        Object.values(STORAGE_KEYS).forEach(key => localStorage.removeItem(key));
        window.location.reload();
    },

    orders: {
        list: () => getStorage(STORAGE_KEYS.ORDERS, SEED_ORDERS),
        update: (updated: Order) => {
            const list = getStorage(STORAGE_KEYS.ORDERS, SEED_ORDERS);
            const next = list.map(o => o.id === updated.id ? updated : o);
            setStorage(STORAGE_KEYS.ORDERS, next);
            return updated;
        },
        create: (order: Order) => {
            const list = getStorage(STORAGE_KEYS.ORDERS, SEED_ORDERS);
            const next = [order, ...list];
            setStorage(STORAGE_KEYS.ORDERS, next);
            return order;
        }
    },

    clients: {
        list: () => getStorage(STORAGE_KEYS.CLIENTS, SEED_CLIENTS),
        create: (item: Client) => {
            const list = getStorage(STORAGE_KEYS.CLIENTS, SEED_CLIENTS);
            const next = [...list, { ...item, id: `c${Date.now()}` }];
            setStorage(STORAGE_KEYS.CLIENTS, next);
        },
        update: (item: Client) => {
            const list = getStorage(STORAGE_KEYS.CLIENTS, SEED_CLIENTS);
            const next = list.map(i => i.id === item.id ? item : i);
            setStorage(STORAGE_KEYS.CLIENTS, next);
        },
        delete: (id: string) => {
            const list = getStorage(STORAGE_KEYS.CLIENTS, SEED_CLIENTS);
            const next = list.filter(i => i.id !== id); // Hard delete for demo simplicity or soft if preferred
            setStorage(STORAGE_KEYS.CLIENTS, next);
        }
    },
    products: {
        list: () => getStorage(STORAGE_KEYS.PRODUCTS, SEED_PRODUCTS),
        create: (item: Product) => {
            const list = getStorage(STORAGE_KEYS.PRODUCTS, SEED_PRODUCTS);
            const next = [...list, { ...item, id: `p${Date.now()}` }];
            setStorage(STORAGE_KEYS.PRODUCTS, next);
        },
        update: (item: Product) => {
            const list = getStorage(STORAGE_KEYS.PRODUCTS, SEED_PRODUCTS);
            const next = list.map(i => i.id === item.id ? item : i);
            setStorage(STORAGE_KEYS.PRODUCTS, next);
        },
        delete: (id: string) => {
            const list = getStorage(STORAGE_KEYS.PRODUCTS, SEED_PRODUCTS);
            const next = list.filter(i => i.id !== id);
            setStorage(STORAGE_KEYS.PRODUCTS, next);
        }
    },
    stores: {
        list: () => getStorage<MockStore>(STORAGE_KEYS.STORES, SEED_STORES),
        create: (item: Omit<MockStore, "id">) => {
            const list = getStorage<MockStore>(STORAGE_KEYS.STORES, SEED_STORES);
            const next = [...list, { ...item, id: `s${Date.now()}` }];
            setStorage(STORAGE_KEYS.STORES, next);
        },
        update: (item: MockStore) => {
            const list = getStorage<MockStore>(STORAGE_KEYS.STORES, SEED_STORES);
            const next = list.map(i => i.id === item.id ? item : i);
            setStorage(STORAGE_KEYS.STORES, next);
        },
        delete: (id: string) => {
            const list = getStorage<MockStore>(STORAGE_KEYS.STORES, SEED_STORES);
            const next = list.filter(i => i.id !== id);
            setStorage(STORAGE_KEYS.STORES, next);
        }
    },
    salesAgents: {
        list: () => getStorage(STORAGE_KEYS.SALES_AGENTS, SEED_SALES_AGENTS),
        create: (item: SalesAgent) => {
            const list = getStorage(STORAGE_KEYS.SALES_AGENTS, SEED_SALES_AGENTS);
            const next = [...list, { ...item, id: `sa${Date.now()}` }];
            setStorage(STORAGE_KEYS.SALES_AGENTS, next);
        },
        update: (item: SalesAgent) => {
            const list = getStorage(STORAGE_KEYS.SALES_AGENTS, SEED_SALES_AGENTS);
            const next = list.map(i => i.id === item.id ? item : i);
            setStorage(STORAGE_KEYS.SALES_AGENTS, next);
        },
        delete: (id: string) => {
            const list = getStorage(STORAGE_KEYS.SALES_AGENTS, SEED_SALES_AGENTS);
            const next = list.filter(i => i.id !== id);
            setStorage(STORAGE_KEYS.SALES_AGENTS, next);
        }
    },
    deliveryTeams: {
        list: () => getStorage(STORAGE_KEYS.DELIVERY_TEAMS, SEED_DELIVERY_TEAMS),
        create: (item: DeliveryTeam) => {
            const list = getStorage(STORAGE_KEYS.DELIVERY_TEAMS, SEED_DELIVERY_TEAMS);
            const next = [...list, { ...item, id: `dt${Date.now()}` }];
            setStorage(STORAGE_KEYS.DELIVERY_TEAMS, next);
        },
        update: (item: DeliveryTeam) => {
            const list = getStorage(STORAGE_KEYS.DELIVERY_TEAMS, SEED_DELIVERY_TEAMS);
            const next = list.map(i => i.id === item.id ? item : i);
            setStorage(STORAGE_KEYS.DELIVERY_TEAMS, next);
        },
        delete: (id: string) => {
            const list = getStorage(STORAGE_KEYS.DELIVERY_TEAMS, SEED_DELIVERY_TEAMS);
            const next = list.filter(i => i.id !== id);
            setStorage(STORAGE_KEYS.DELIVERY_TEAMS, next);
        }
    }
};
