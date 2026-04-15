# GreenThumb — Cloud Backend

Cloud-side services that aggregate data from all Pi nodes, manage user accounts, and serve the fleet admin dashboard.

## Architecture

```
cloud/
├── greenthumb-api/        # FastAPI — admin CRUD + Pi sync routes (:8000)
├── auth-service/          # Java Spring Boot — JWT login & validation (:8081)
├── account-service/       # Java Spring Boot — user account management (:8082)
├── gateway/               # Spring Cloud Gateway — single ingress (:80)
├── admin-dashboard/       # React + Vite + Tailwind SPA (:3000)
├── k8s/                   # Kubernetes manifests
└── compose.yaml           # Local development Docker Compose
```

### Services

| Service | Port | Language | Description |
|---------|------|----------|-------------|
| `gateway` | 80 | Java (Spring Cloud) | Routes requests to backend services |
| `greenthumb-api` | 8000 | Python (FastAPI) | Admin CRUD + Pi sync endpoints |
| `auth-service` | 8081 | Java (Spring Boot) | JWT issuance and validation |
| `account-service` | 8082 | Java (Spring Boot) | User account management |
| `admin-dashboard` | 3000 | React (nginx) | Fleet admin SPA |
| `db` | 5432 (internal) / 5433 (host) | PostgreSQL 17 | Cloud database |

### Gateway Routing

| Path prefix | Backend | Auth |
|-------------|---------|------|
| `/auth/**` | auth-service | Public |
| `/accounts/**` | account-service | JWT |
| `/admin/**` | greenthumb-api | JWT |
| `/sync/**` | greenthumb-api | Device bearer token |

## Quick Start (Local Development)

```bash
cd cloud
cp .env.example .env
# Optional: set DEV_AUTH_BYPASS=true to skip JWT checks during development

docker compose up --build
```

| URL | Service |
|-----|---------|
| `http://localhost:3000` | Admin dashboard |
| `http://localhost:8000/docs` | API Swagger docs |
| `http://localhost:80` | Gateway |

## Environment Variables

### `cloud/.env`

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_USER` | `postgres` | PostgreSQL user |
| `DB_PASSWORD` | `password` | PostgreSQL password |
| `DB_NAME` | `greenthumb` | Database name |
| `JWT_SECRET` | `change-me-in-production` | JWT signing secret |
| `DEV_AUTH_BYPASS` | `false` | Skip JWT validation (development only) |

## Authentication

**Users** (admin dashboard) authenticate via `POST /auth/login` → receive a JWT → include as `Authorization: Bearer <jwt>` on all `/admin/**` and `/accounts/**` calls.

**Pi devices** authenticate with a per-device token stored in `device.device_token`. Generated via the admin dashboard → **Devices → Rotate Token**. Sent as `Authorization: Bearer <device_token>` on all `/sync/**` calls.

## Admin Dashboard Pages

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | Email/password → JWT |
| Fleet | `/fleet` | Online/stale/offline device status |
| Devices | `/devices` | Register devices, rotate tokens |
| Species | `/species` | Plant species + growth phase templates |
| Cultivations | `/cultivations` | Cultivation list + threshold CRUD |
| Hardware | `/hardware` | Sensor/actuator model catalog |
| Data Explorer | `/data` | Charts + CSV export |
| Photos | `/photos` | Photo gallery with lightbox |

## Shared Models

`greenthumb-api` imports models from `rasp5/greenthumb-models/` — the same package used by the Pi API. The cloud Dockerfile copies the package from the repo root:

```dockerfile
COPY rasp5/greenthumb-models/ /tmp/greenthumb-models/
RUN pip install /tmp/greenthumb-models
```

This ensures both tiers use identical table definitions and sync schemas.

## Kubernetes

Production Kubernetes manifests are in `k8s/`. Apply in order:

```bash
kubectl apply -f cloud/k8s/secrets.yaml        # credentials first
kubectl apply -f cloud/k8s/                    # remaining manifests
```

## API Reference

Full endpoint documentation: see `cloud/greenthumb-api` at `http://localhost:8000/docs`, or the [API Reference](../docs-repo/docs/api/reference.md) in the docs repository.
