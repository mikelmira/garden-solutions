# Monorepo Structure

## 1. Directory Layout

```
/
├── apps/
│   ├── web/                # Next.js App Router (The single frontend)
│   └── api/                # FastAPI Application
├── packages/
│   ├── ui/                 # Shared React Components (shadcn/ui)
│   ├── themes/             # Tailwind Config & CSS Variables
│   ├── types/              # DIY Interface definitions (shared TS/Python types via generation or manual sync)
│   ├── utils/              # Shared JS/TS helper functions
│   └── eslint-config/      # Shared linting rules
├── docs/                   # Documentation (You are here)
├── turbo.json              # Pipeline config
└── package.json            # Root scripts
```

## 2. Package Responsibilities & Rules

### `apps/web`
- **Purpose**: The user facing application.
- **Contains**: Pages, layouts, data fetching hooks, global store, service workers.
- **Rule**: Must handle 100% of the UI logic.
- **Rule**: Must strictly use `packages/ui` for primitives. Do not re-invent a Button.

### `apps/api`
- **Purpose**: The backend REST API.
- **Contains**: Routes, Models (Pydantic), DB Models (SQLAlchemy), Alembic Migrations.
- **Rule**: Must be the *only* thing talking to the PostgreSQL database.

### `packages/ui`
- **Purpose**: A pure, stateless component library.
- **Allowed**: Radix UI primitives, Tailwind classes, Lucide icons.
- **Forbidden**:
  - API calls (`fetch`, `axios`).
  - Business logic (e.g., "Calculate Price").
  - Global state (`useStore`).
  - Next.js specific imports (`next/navigation`, `next/image` - use standard `<img>` or dependency injection if needed, though `next/image` is acceptable if strictly coupled to Next.js). **Strict Rule: Keep it framework agnostic where possible, but `cva` and `clsx` are permitted.**

### `packages/themes`
- **Purpose**: Source of truth for design tokens.
- **Contains**: `tailwind.config.js` presets, `globals.css` base variables.
- **Forbidden**: React components.

### `packages/utils`
- **Purpose**: Isomorphic helpers.
- **Contains**: Date formatters, Currency formatters, Regex validators.
- **Forbidden**: Secrets, keys, or node-specific modules (fs, path) unless explicitly separated.

## 3. Dependency Graph
- `apps/web` -> depends on `ui`, `themes`, `utils`, `types`.
- `packages/ui` -> depends on `themes`.
- `apps/api` -> independent (Python).
  - *Note*: TypeScript types in `packages/types` must be kept in sync with Pydantic models. Automatic generation (e.g., `datamodel-code-generator`) is recommended but manual sync is authoritative for V1.

## 4. What NEVER lives in shared packages
1.  **Business Logic**: "If Client is Tier A, apply 10%" -> Belongs in `api` (and `web` for optimistic UI), NEVER in `ui`.
2.  **Environment Variables**: `API_URL`, `DB_PASSWORD` -> Belongs in `.env` inside `apps/*`.
3.  **Authorization Logic**: "Can this user see this?" -> Belongs in `apps/*`.
