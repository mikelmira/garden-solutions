# Naming Conventions

This doc is authoritative for naming. If a conflict exists, update this doc first.

## 1. General Naming Rules
- **Files & Directories**:
  - TS/JS utilities: `kebab-case` (e.g., `api.ts`, `date-utils.ts`).
  - React Components: `PascalCase` (e.g., `ClientCard.tsx`).
  - Next.js Routes: `kebab-case` folders (e.g., `new-order`).
  - Python modules: `snake_case` (e.g., `order_service.py`).
- **Variables**:
  - TypeScript: `camelCase` (e.g., `isLoading`, `selectedClient`).
  - Python: `snake_case` (e.g., `user_id`, `is_active`).
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_PAGE_SIZE`).
- **Types/Classes**: `PascalCase` (e.g., `Order`, `UserResponse`, `class OrderService`).

## 2. Frontend (Next.js)
- **Route Groups**: Use parens for role/layout separation.
  - `app/(admin)`, `app/(sales)`, `app/(auth)`.
- **Dashboards (V1)**: Explicit routes are used for dashboards to avoid conflicts.
  - `/admin-dashboard`
  - `/sales-dashboard`
  - *Note: Role-based grouping (e.g. `/admin/dashboard`) may be adopted in V2, but V1 uses the explicit routes above.*
- **Special Files**: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx` (lowercase).
- **Components**:
  - **Primitives**: `apps/web/components/ui/` (Shadcn only).
  - **Features**: `apps/web/components/<feature>/` (e.g., `sales/ProductCard.tsx`).
  - **Wrappers**: `apps/web/components/` (e.g., `Navbar.tsx`).
- **Hooks**: `use` prefix, camelCase (e.g., `useAuth`, `useOrders`).

## 3. Backend (FastAPI)
- **Routers**: `apps/api/app/routers/<resource>.py` (e.g., `orders.py`).
- **Services**: `apps/api/app/services/<resource>_service.py` (e.g., `order_service.py`).
- **Models**: `apps/api/app/models/<resource>.py` (singular, e.g., `user.py`, `order.py`).
- **Schemas**: `apps/api/app/schemas/<resource>.py` (group by resource, e.g., `auth.py`, `orders.py`).

## 4. API + Type Naming
- **Endpoints**: Plural nouns, kebab-case (e.g., `GET /orders`, `POST /orders`, `GET /products/{id}`).
- **JSON Payloads**: **snake_case**.
  - **Reason**: Align with Python/Database default without overhead.
  - **Frontend mapping**: TS Interfaces must define properties in `snake_case` to match API.
  - **Example**:
    ```json
    { "first_name": "Alice", "is_active": true }
    ```
- **DTO Naming**:
  - Request: `<Resource>Create` (POST), `<Resource>Update` (PATCH).
  - Response: `<Resource>Response` (Public), `<Resource>InDB` (Internal).

## 5. Status + Enum Naming
- **Format**: `UPPER_SNAKE_CASE`.
- **Typing**: Use explicit Enum classes, never strings.
- **Locations**:
  - BE: `app/models/enums.py` (or within user/order model files).
  - FE: `types/enums.ts` or `types/index.ts`.

## 6. Examples

### Route
- URL: `/sales/new-order`
- File: `apps/web/app/(sales)/new-order/page.tsx`

### Component
- Name: `OrderSummary`
- File: `apps/web/components/sales/OrderSummary.tsx`

### Hook
- Name: `useCart`
- File: `apps/web/hooks/use-cart.ts`

### API Response Type (TS)
```typescript
interface OrderResponse {
  id: string;
  total_price_rands: number; // snake_case matches API
  created_at: string;
  status: OrderStatus;
}
```

### Backend Schema (Python)
```python
class OrderCreate(BaseModel):
    client_id: UUID
    items: List[OrderItem]
```

### Status Enum
- Value: `PENDING_APPROVAL`
- Usage: `order.status === OrderStatus.PENDING_APPROVAL`
