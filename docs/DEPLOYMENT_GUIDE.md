# Garden Solutions — Deployment Guide

A step-by-step guide to getting the platform live on a VPS with Docker.

---

## What You Need Before Starting

| Item | Action | Est. Cost |
|------|--------|-----------|
| **VPS server** | Sign up at Hetzner Cloud (hetzner.com/cloud) or DigitalOcean | €4–7/mo (Hetzner CX22, 2 vCPU / 4GB RAM) or $12/mo (DigitalOcean 2GB) |
| **Domain name** | Register at domains.co.za, Afrihost, or any registrar | ~R50/year for .co.za |
| **Your codebase** | Push to a private Git repo (GitHub, GitLab, etc.) | Free |
| **30–60 minutes** | For the full setup below | — |

**Recommended server:** Hetzner CX22 (2 vCPU, 4GB RAM, 40GB SSD) at ~€4.15/month. This comfortably runs PostgreSQL + FastAPI + Next.js for an internal team of 10–20 users. You can upgrade later without data loss.

**Recommended location:** Nuremberg (EU) or Falkenstein (EU). Hetzner doesn't have SA data centres, but latency from SA to EU is typically 150–180ms which is fine for an internal operations tool.

---

## Step 1: Create the Server

### Hetzner Cloud (Recommended)

1. Go to https://console.hetzner.cloud and create an account
2. Create a new project called "Garden Solutions"
3. Click **Add Server**
4. Choose: **Location** → Nuremberg, **Image** → Ubuntu 24.04, **Type** → CX22 (Shared vCPU, 2 vCPU, 4GB RAM)
5. Under **SSH Keys**, add your public key (if you don't have one, see "Generate SSH Key" below)
6. Give it a name like `garden-solutions`
7. Click **Create & Buy Now**
8. Note the IP address shown (e.g. `162.55.xxx.xxx`)

### Generate SSH Key (if you don't have one)

On your Mac/PC terminal:

```bash
ssh-keygen -t ed25519 -C "mike@gardensolutions"
# Press Enter to accept default location
# Set a passphrase (or leave blank)
cat ~/.ssh/id_ed25519.pub
# Copy this entire output — that's your public key
```

---

## Step 2: Point Your Domain

1. Register your domain (e.g. `gardensolutions.co.za` or `app.potshack.co.za`)
2. In your domain registrar's DNS settings, add an **A record**:
   - **Name:** `@` (or `app` if using a subdomain like `app.gardensolutions.co.za`)
   - **Type:** A
   - **Value:** Your server's IP address
   - **TTL:** 300
3. DNS propagation takes 5–30 minutes. You can check with: `dig app.gardensolutions.co.za`

---

## Step 3: Set Up the Server

SSH into your new server:

```bash
ssh root@YOUR_SERVER_IP
```

Then run these commands to install everything needed:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose plugin
apt install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Install Git
apt install -y git

# Create a deploy user (don't run the app as root)
adduser --disabled-password --gecos "" deploy
usermod -aG docker deploy

# Switch to deploy user
su - deploy
```

---

## Step 4: Clone and Configure

As the `deploy` user:

```bash
# Clone your repo (replace with your actual repo URL)
git clone https://github.com/YOUR_USERNAME/garden-solutions.git
cd garden-solutions

# Create the production environment file
cp apps/api/.env.example .env
```

Now edit the `.env` file with real production values:

```bash
nano .env
```

Paste this content, replacing the placeholder values:

```env
# ── Environment ──────────────────────────
ENVIRONMENT=production

# ── Database ─────────────────────────────
POSTGRES_USER=garden_admin
POSTGRES_PASSWORD=GENERATE_A_STRONG_PASSWORD_HERE
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=garden_solutions

# ── Auth ─────────────────────────────────
# Generate with: openssl rand -hex 32
SECRET_KEY=PASTE_YOUR_GENERATED_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── CORS ─────────────────────────────────
CORS_ORIGINS=https://YOUR_DOMAIN_HERE

# ── Ports ────────────────────────────────
API_PORT=8000
WEB_PORT=3000
DB_PORT=5432

# ── API URL (used by Next.js) ────────────
API_URL=https://YOUR_DOMAIN_HERE/api/v1

# ── Schema ───────────────────────────────
SCHEMA_VERSION=1

# ── Shopify (add later when ready) ──────
SHOPIFY_SHOP_DOMAIN=
SHOPIFY_ACCESS_TOKEN=
SHOPIFY_WEBHOOK_SECRET=
SHOPIFY_API_VERSION=2024-01
```

Generate your passwords and secret key:

```bash
# Generate a strong database password
openssl rand -base64 24

# Generate the JWT secret key
openssl rand -hex 32
```

Copy those values into the `.env` file, then save (Ctrl+X → Y → Enter in nano).

---

## Step 5: Set Up the Reverse Proxy (Caddy)

Caddy automatically handles HTTPS certificates (free via Let's Encrypt) and routes traffic to your containers. We'll add it to the Docker setup.

Create a file called `Caddyfile` in the project root:

```bash
nano Caddyfile
```

Paste this (replace `YOUR_DOMAIN_HERE` with your actual domain):

```
YOUR_DOMAIN_HERE {
    # Frontend
    handle {
        reverse_proxy web:3000
    }

    # API requests
    handle /api/* {
        reverse_proxy api:8000
    }

    # API health check
    handle /health {
        reverse_proxy api:8000
    }

    # Uploaded images / static files from API
    handle /uploads/* {
        reverse_proxy api:8000
    }

    handle /static/* {
        reverse_proxy api:8000
    }
}
```

Now create a production docker-compose file that includes Caddy. Create `docker-compose.live.yml`:

```bash
nano docker-compose.live.yml
```

```yaml
version: '3.8'

services:
  caddy:
    image: caddy:2-alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - web
      - api

  db:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    restart: always
    env_file: .env
    environment:
      POSTGRES_SERVER: db
      POSTGRES_PORT: "5432"
    volumes:
      - api_uploads:/app/uploads
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    build:
      context: .
      dockerfile: ./apps/web/Dockerfile
    restart: always
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL}
    depends_on:
      api:
        condition: service_healthy

volumes:
  postgres_data:
  api_uploads:
  caddy_data:
  caddy_config:
```

---

## Step 6: Fix the Next.js Config for Production

Your Next.js config needs `output: 'standalone'` for the Docker build to work (the Dockerfile expects it), and the image domains need to point to your production URL. This is a code change you'll need to make before deploying.

In `apps/web/next.config.js`, update to:

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: 'YOUR_DOMAIN_HERE',
                pathname: '/uploads/**',
            },
            {
                protocol: 'https',
                hostname: 'YOUR_DOMAIN_HERE',
                pathname: '/static/**',
            },
            {
                // Keep localhost for development
                protocol: 'http',
                hostname: 'localhost',
                port: '8000',
                pathname: '/uploads/**',
            },
            {
                protocol: 'http',
                hostname: 'localhost',
                port: '8000',
                pathname: '/static/**',
            },
        ],
    },
};

module.exports = nextConfig;
```

Commit and push this change before deploying.

---

## Step 7: Build and Launch

```bash
# Build all containers (first time takes 5–10 minutes)
docker compose -f docker-compose.live.yml build

# Start everything
docker compose -f docker-compose.live.yml up -d

# Watch the logs to make sure everything starts cleanly
docker compose -f docker-compose.live.yml logs -f
```

You should see:
- `db` starting and passing health checks
- `api` starting, connecting to the database
- `web` starting on port 3000
- `caddy` obtaining your HTTPS certificate automatically

---

## Step 8: Run Database Migrations

```bash
# Run Alembic migrations inside the API container
docker compose -f docker-compose.live.yml exec api alembic upgrade head
```

This creates all your database tables.

---

## Step 9: Create the Admin User

You need at least one admin user to log in. Run this inside the API container:

```bash
docker compose -f docker-compose.live.yml exec api python -c "
from app.core.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

admin = User(
    email='mikee@dsg.co.za',
    full_name='Mike',
    hashed_password=pwd.hash('CHOOSE_A_STRONG_PASSWORD'),
    role='admin',
    is_active=True,
)
db.add(admin)
db.commit()
print('Admin user created successfully')
db.close()
"
```

Replace `CHOOSE_A_STRONG_PASSWORD` with your actual password.

---

## Step 10: Verify Everything Works

1. Open `https://YOUR_DOMAIN` in your browser — you should see the login page
2. Log in with your admin credentials
3. Check the admin dashboard loads
4. Navigate to Products, Orders, Manufacturing to verify pages load
5. Check `https://YOUR_DOMAIN/health` returns a response from the API

---

## Day-to-Day Operations

### View logs

```bash
cd ~/garden-solutions
docker compose -f docker-compose.live.yml logs -f          # All services
docker compose -f docker-compose.live.yml logs -f api      # API only
docker compose -f docker-compose.live.yml logs -f web      # Frontend only
```

### Deploy updates

```bash
cd ~/garden-solutions
git pull
docker compose -f docker-compose.live.yml build
docker compose -f docker-compose.live.yml up -d

# If there are new migrations:
docker compose -f docker-compose.live.yml exec api alembic upgrade head
```

### Restart services

```bash
docker compose -f docker-compose.live.yml restart           # All
docker compose -f docker-compose.live.yml restart api       # Just API
```

### Database backup (IMPORTANT — do this regularly)

```bash
# Create a backup
docker compose -f docker-compose.live.yml exec db pg_dump -U garden_admin garden_solutions > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup (if needed)
cat backup_file.sql | docker compose -f docker-compose.live.yml exec -T db psql -U garden_admin garden_solutions
```

### Set up automated daily backups

```bash
# As the deploy user, add a cron job
crontab -e

# Add this line (backs up at 2am daily, keeps in ~/backups/)
0 2 * * * mkdir -p ~/backups && cd ~/garden-solutions && docker compose -f docker-compose.live.yml exec -T db pg_dump -U garden_admin garden_solutions | gzip > ~/backups/gs_$(date +\%Y\%m\%d).sql.gz

# Clean up backups older than 30 days
5 2 * * * find ~/backups -name "gs_*.sql.gz" -mtime +30 -delete
```

---

## Connecting Shopify (When Ready)

Once the platform is live and working:

1. Add your Shopify credentials to `.env`:
   ```
   SHOPIFY_SHOP_DOMAIN=pot-shack.myshopify.com
   SHOPIFY_ACCESS_TOKEN=shpat_your_actual_token
   SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
   ```

2. Restart the API: `docker compose -f docker-compose.live.yml restart api`

3. In Shopify Admin → Settings → Notifications → Webhooks, register:
   - Order creation → `https://YOUR_DOMAIN/api/v1/webhooks/shopify/orders/create`
   - Order update → `https://YOUR_DOMAIN/api/v1/webhooks/shopify/orders/updated`
   - Order cancellation → `https://YOUR_DOMAIN/api/v1/webhooks/shopify/orders/cancelled`
   - Product creation → `https://YOUR_DOMAIN/api/v1/webhooks/shopify/products/create`
   - Product update → `https://YOUR_DOMAIN/api/v1/webhooks/shopify/products/update`

---

## Troubleshooting

**"502 Bad Gateway"** — The API or web container hasn't started yet. Check logs: `docker compose -f docker-compose.live.yml logs api`

**"HTTPS certificate error"** — Make sure your domain's DNS A record points to the server IP and has propagated. Caddy retries automatically.

**"Cannot connect to database"** — Check the db container is healthy: `docker compose -f docker-compose.live.yml ps`. Verify your .env credentials match.

**"CORS error in browser"** — Make sure `CORS_ORIGINS` in .env matches your exact domain including `https://`.

**API container keeps restarting** — Likely a missing or invalid `SECRET_KEY`. Check: `docker compose -f docker-compose.live.yml logs api | head -50`

**Images not loading** — The `api_uploads` volume persists uploaded images. Make sure the Caddyfile routes `/uploads/*` to the API.

---

## Cost Summary

| Item | Monthly Cost |
|------|-------------|
| Hetzner CX22 (2 vCPU, 4GB RAM) | ~R85 (€4.15) |
| Domain (.co.za) | ~R4/mo (R50/year) |
| HTTPS (Let's Encrypt via Caddy) | Free |
| **Total** | **~R90/month** |

---

## Security Notes

- The server firewall should only allow ports 80, 443, and 22 (SSH)
- Database is NOT exposed externally (no port mapping in docker-compose.live.yml)
- All traffic goes through Caddy (HTTPS enforced)
- JWT secret key must be unique and secret
- Change the admin password after first login
- Consider disabling root SSH login and using key-only auth
