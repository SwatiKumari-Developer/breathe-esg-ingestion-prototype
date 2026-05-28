# Tradeoffs

## 1. No Authentication Or Role-Based Access

The data model is multi-tenant, but the prototype does not implement login, tenant-scoped auth middleware, or analyst/auditor roles. I left this out because the assignment emphasizes ingestion judgment and model quality. In production, tenant isolation must be enforced before customers use it.

## 2. No Real External API Pulls

The app ingests uploaded files rather than pulling directly from SAP, utility providers, or Concur. This makes the prototype deployable and reviewable without secret credentials. Production would add source connectors, token storage, retry queues, and scheduled syncs.

## 3. Simplified Emission Factor Engine

The prototype computes CO2e with a small fixed factor map. That is enough to demonstrate normalization and review UX, but not enough for real reporting. A production engine needs versioned factor libraries, geography, vehicle/fuel subtypes, hotel country factors, flight cabin class, and factor provenance.
