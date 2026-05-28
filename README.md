# AgentFlow — Multi-Agent Workflow Automation Platform

```
┌──────────────────────────────────────────────────────────┐
│                    Chat UI (Next.js)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │ Thread View │  │ Approval Q  │  │ Source Visibil.  │  │
│  └─────────────┘  └─────────────┘  └──────────────────┘  │
└──────────────────────────┬───────────────────────────────┘
                           │ user message / agent response
┌──────────────────────────▼───────────────────────────────┐
│              Orchestrator Agent (LangGraph)               │
│  ┌──────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ Router  │  │ Memory Store   │  │ Approval Gate   │   │
│  └──────────┘  └────────────────┘  └──────────────────┘   │
│         │              │                   │              │
│  ┌──────▼───────────────▼───────────────────▼──────────┐  │
│  │            Subagent Pool (N workers)                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │  │
│  │  │ Research │  │ Execute  │  │ Document │  ...      │  │
│  │  │ Agent    │  │ Agent    │  │ Agent    │           │  │
│  │  └──────────┘  └──────────┘  └──────────┘           │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────┬───────────────────────────────┘
                            │ reads / writes
┌───────────────────────────▼───────────────────────────────┐
│              Data Layer (Multi-Tenant)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ PostgreSQL  │  │   Redis      │  │   Weaviate      │  │
│  │ (metadata)  │  │ (session)    │  │ (vector mem.)   │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|---|---|
| Orchestration | LangGraph (Python) |
| Agents | Anthropic agents-sdk compatible patterns |
| Frontend | Next.js 14 (TypeScript) |
| Database | PostgreSQL 15 + RLS |
| Session Store | Redis 7 |
| Vector Store | Weaviate 1.24 |
| Object Storage | S3-compatible (MinIO / AWS S3) |
| Container | Docker + Kubernetes (GKE/EKS) |
| API | FastAPI (Python) |
| Audit | Immutable PostgreSQL ledger |
| Secrets | HashiCorp Vault or AWS Secrets Manager |

## Quick Start

```bash
# Start local dev environment
docker-compose up -d

# View logs
docker-compose logs -f orchestrator

# Run tests
pytest tests/
```

## Project Structure

```
agentflow/
├── orchestrator/       # LangGraph orchestration graph
├── agents/             # Agent registry (Research, Execute, Document, etc.)
├── api/                # FastAPI endpoints
├── db/                 # PostgreSQL schemas, migrations
├── frontend/            # Next.js 14 chat UI
├── helm/               # Kubernetes Helm charts
└── docker-compose.yml  # Local development
```

## Milestones

- **M1:** Architecture & Core Setup (LangGraph, 3 agents, PostgreSQL, Redis, Weaviate, Docker Compose)
- **M2:** Memory & Approval Flow (vector memory, approval gate, audit log, GDPR APIs)
- **M3:** Frontend & Cloud Deployment (Next.js UI, Kubernetes, S3, secrets management)
- **M4:** Documentation & Polish (OpenAPI, plugin guide, GDPR docs, runbook)

## Multi-Tenancy

Row-level security (RLS) in PostgreSQL + tenant_id namespace prefixes in Redis/Weaviate. Every record carries a `tenant_id` foreign key. LangGraph context always threads `tenant_id` through every agent call.

## GDPR Compliance

- EU-region data residency
- Consent tracking via `tenant_consents` table
- Right to erasure (cascade delete across PostgreSQL, Weaviate, Redis)
- Immutable audit ledger

## License

Proprietary — All rights reserved