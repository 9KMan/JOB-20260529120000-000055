# SPEC.md — AI Agent Workflow Automation Platform
**Job:** JOB-20260529120000-000055
**Source:** Upwork | **Tier:** HIGH
**Client:** AI Agent Platform (Upwork)
**Updated:** 2026-05-29

---

## 1. System Overview

**Project Name:** AgentFlow — Multi-Agent Workflow Automation Platform

**What It Does:**
An AI-powered platform for SMBs that automates multi-step business workflows end-to-end through a single chat interface. Users interact with a central orchestrator agent that dispatches specialized subagents, manages shared memory, enforces human approval gates before external actions, and maintains full audit traceability.

**Target Users:**
- Small-to-medium business owners and operators
- Non-technical staff managing operational workflows
- Knowledge workers who need to coordinate across departments

**Core Value Proposition:**
Replace brittle automation scripts with an intelligent, extensible agent workforce that reasons, remembers context, and asks humans before acting.

---

## 2. Architecture

### 2.1 High-Level Topology

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

### 2.2 Orchestration Model

**Framework:** LangGraph (explicitly preferred over generic LangChain or CrewAI)

**Graph Nodes:**
- `router` — Interprets user intent, selects agent(s), builds execution plan
- `memory_read` — Reads relevant user profile, business context, past projects from vector store
- `agent_dispatch` — Invokes appropriate subagent(s) with structured input
- `approval_gate` — Halts execution, queues human approval request, resumes on approval
- `memory_write` — Persists results, citations, and updated context to vector store
- `response_synthesizer` — Aggregates agent outputs into a coherent user-facing response

**Graph Edges:**
- Conditional edges from `approval_gate` → `agent_dispatch` (retry) or `response_synthesizer` (skip)
- `memory_read` always runs before `agent_dispatch`

### 2.3 Agent Registry (Extensible)

| Agent | Responsibility | Example Actions |
|---|---|---|
| Research Agent | Gather info from web, docs, DB | "Find my top 10 customers by revenue this quarter" |
| Execute Agent | Perform external actions (send email, create CRM record) | "Create a Stripe invoice for Acme Corp" |
| Document Agent | Draft, summarize, transform documents | "Write a follow-up email based on this ticket" |
| Calendar Agent | Query/schedule meetings | "Schedule a call with Sarah next Tuesday" |
| Data Agent | Run queries, compute metrics | "Show me monthly MRR trend for Q1-Q2" |
| Notify Agent | Send alerts via Slack, email, SMS | "Alert the ops team when inventory drops below threshold" |

New agents are registered via a plugin manifest — no core rebuild required.

---

## 3. Data Architecture

### 3.1 Multi-Tenant Strategy

**Isolation model:** Row-level security (RLS) in PostgreSQL + tenant_id namespace prefixes in Redis/Weaviate.

Every record carries a `tenant_id` foreign key. LangGraph context always threads `tenant_id` through every agent call. No cross-tenant data leakage at the ORM layer.

### 3.2 Storage

| Store | Technology | Purpose |
|---|---|---|
| Metadata / Workflows / Audit | PostgreSQL (Supabase compatible) | persistent operational data |
| Session Memory | Redis | short-term conversation context, TTL 30 days |
| Long-Term Memory | Weaviate (vector DB) | embeddings of user profiles, business context, project history |
| Approval Queue | PostgreSQL (dedicated table) | pending/approved/denied approval records |
| Object Storage | S3-compatible (MinIO or AWS S3) | documents, email attachments, generated artifacts |

### 3.3 Memory / Retrieval Design

```
User Message
    │
    ▼
[Embedding Model — bge-m3 or equivalent]
    │
    ▼
[Weaviate vector search — tenant-scoped]
    │
    ▼ Top-K relevant memories (K=5)
[Memory Read node injects into LangGraph context]
```

- Memory is **tenant-scoped** (Weaviate tenant filter on every search)
- Memory is **asymmetric** per agent: Research Agent gets business context, Execute Agent gets credential references
- Periodic memory consolidation: daily job summarises recent interactions into a user profile entry

### 3.4 GDPR Compliance

- **Data residency:** All PII stored in EU-region PostgreSQL; no cross-border replication unless explicit consent
- **Consent tracking:** `tenant_consents` table records consent per data category (contact, financial, behavioral)
- **Right to erasure:** Deletion API cascades through PostgreSQL (CASCADE delete on tenant_id) + Weaviate (namespace filter delete) + Redis (key delete by tenant prefix)
- **Audit log:** Immutable ledger table (`audit_events`) records who accessed whose data and when
- **Data minimisation:** Agent memory retention TTL enforces automatic expiry of non-essential context

---

## 4. User Interactions & Flows

### 4.1 Chat Interface

- **Thread view:** Full conversation history, grouped by workflow execution
- **Approval queue panel:** Sidebar listing pending approvals with one-click Approve/Deny + optional note
- **Source visibility:** Every agent response cites sources (memory citations, web references, DB queries)
- **Streaming:** Real-time token streaming from orchestrator

### 4.2 Onboarding Flow

1. User signs up → tenant record created with GDPR consent prompt
2. Initial profile setup (company name, industry, key workflows)
3. Warm-up: run a demo workflow ("Find my top 3 customers") so agent can calibrate memory
4. Full feature access unlocked

### 4.3 Approval Flow

```
User: "Send an invoice to Acme Corp for $5,000"
       │
       ▼
Orchestrator detects external-action agent
       │
       ▼
Approval Gate node → pause → DB record created (status=pending)
       │
       ▼ User sees approval card in sidebar
User clicks "Approve" with optional note
       │
       ▼ Resume execution → Execute Agent fires external API
       │
       ▼ Memory write → response synthesised
```

- Deny: agent logs denial, responds to user with alternative suggestion
- Timeout: auto-deny after 48 hours (configurable per agent)

---

## 5. Cloud & Deployment

### 5.1 Container Strategy

- **Docker:** Multi-stage Dockerfile per service (orchestrator, agents, frontend, gateway)
- **Image registry:** ghcr.io / self-hosted Harbor
- **Orchestration:** Kubernetes (GKE or EKS) via Helm charts
- **Config management:** Externalised config maps for tenant-specific settings

### 5.2 Kubernetes Topology

```
┌─────────────────────────────────────┐
│  Namespace: agentflow-prod          │
│  ┌───────────────────────────────┐ │
│  │ Deployment: orchestrator      │ │
│  │ HPA: cpu>60% or memory>70%     │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Deployment: agent-worker-pool │ │
│  │ HPA: queue depth > 10          │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Deployment: nextjs-frontend  │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Deployment: weaviate-vectordb │ │
│  └───────────────────────────────┘ │
│  ┌───────────────────────────────┐ │
│  │ Deployment: redis-session     │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 5.3 Secrets Management

- Kubernetes Secrets for DB credentials, API keys, JWT secret
- Tenant-specific secrets stored in Vault or AWS Secrets Manager
- No secrets in environment variables or container images

---

## 6. Milestone Plan

### M1 — Architecture & Core Setup (Week 1–2)
> *Goal: production-grade foundation, investor/lead-ready*

- [ ] LangGraph orchestration graph (all nodes defined, conditional edges wired)
- [ ] Agent registry with 3 agents: Research, Execute, Document
- [ ] Multi-tenant PostgreSQL schema (RLS enforced, migration scripts)
- [ ] Redis session store + Weaviate vector store (tenant-scoped)
- [ ] Docker Compose local dev environment
- [ ] GitHub repo with project board, README with ASCII architecture diagram

**Deliverable:** Runnable local dev environment; agent can respond to a research query end-to-end

### M2 — Memory & Approval Flow (Week 3–4)
> *Goal: intelligent memory and safe external actions*

- [ ] Memory read/write nodes fully functional (vector search + context injection)
- [ ] Approval gate: pause → queue → approve/deny → resume/reject
- [ ] Audit log table: immutable event ledger
- [ ] Consent tracking table + GDPR deletion API (right to erasure cascade)
- [ ] Memory consolidation job (daily summarisation into user profile)

**Deliverable:** Full approval flow demonstrable end-to-end

### M3 — Frontend & Cloud Deployment (Week 5–7)
> *Goal: shipped and live*

- [ ] Next.js chat UI: thread view, approval queue, source citations, streaming responses
- [ ] Kubernetes Helm charts for all services
- [ ] Deployment to GCP GKE or AWS EKS (one cloud, client's choice)
- [ ] S3-compatible object storage for artifact handling
- [ ] Secrets management via Vault or AWS Secrets Manager

**Deliverable:** Live production deployment; end-user can access the platform

### M4 — Documentation & Polish (Week 8)
> *Goal: maintainable, handoff-ready*

- [ ] API documentation (OpenAPI / Swagger)
- [ ] Agent plugin authoring guide
- [ ] GDPR compliance documentation ( DPA, consent records, erasure procedures)
- [ ] Runbook: onboarding, monitoring, incident response
- [ ] Final code audit: security scan, RLS test suite, load test to 100 concurrent users

**Deliverable:** Complete documentation package; project ready for ongoing internal team

---

## 7. Acceptance Criteria

| Criteria | Definition |
|---|---|
| **Correctness** | Every agent response is traceable to a source (memory citation, DB query, web reference) |
| **Safety** | No external action executes without explicit human approval recorded in the audit log |
| **Multi-tenancy** | Tenant A can never read or infer Tenant B's data, even under adversarial conditions |
| **Scalability** | Orchestrator handles 100 concurrent chat sessions without degradation |
| **GDPR** | Erasure request fulfills within 72 hours; audit log records every PII access |
| **Deployability** | Full platform deploys to GCP or AWS via Helm in under 30 minutes |
| **Extensibility** | New agent type can be added without modifying the orchestrator core |

---

## 8. Out of Scope

- Mobile native app (web only for V1)
- Built-in payment processing beyond Stripe integration
- White-label / rebrandable themes for V1
- SOC2 / ISO certification (roadmap item)

---

## 9. Tech Stack Summary

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
| Infrastructure | GCP (preferred) or AWS |
| API | FastAPI (Python) |
| Audit | Immutable PostgreSQL ledger |
| Secrets | HashiCorp Vault or AWS Secrets Manager |
