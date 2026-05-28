# Data Model

The prototype uses one normalized review table, `ActivityRecord`, backed by raw source evidence and audit events.

## Core Entities

- `Tenant`: company boundary for multi-tenancy. Every operational table carries `tenant_id`.
- `Facility`: tenant-specific plant/site lookup. SAP plant codes and utility facility codes resolve here.
- `SourceSystem`: configured source of truth, such as SAP S/4HANA, a utility portal export, or SAP Concur.
- `IngestionBatch`: one uploaded file/API pull, with row counts, errors, received time, owner, and status.
- `RawRecord`: immutable-ish source payload per row. Failed rows are still stored with error messages.
- `ActivityRecord`: normalized ESG activity row used by analysts.
- `AuditEvent`: append-only log for batch imports, edits, approvals, rejections, and locks.
- `EmissionFactor`: factor metadata shape. The current calculator uses constants in code for prototype speed, but the table is present for production migration.

## Why One Normalized Activity Table

SAP purchase rows, utility bills, and travel expense rows have very different source schemas, but analysts need to review the same questions:

- What source produced this row?
- What scope/category does it belong to?
- What quantity did we receive and what unit was it normalized to?
- What calculated CO2e will go downstream?
- Is the row suspicious?
- Has an analyst approved or locked it?

`ActivityRecord` gives that common surface while preserving the raw source payload through `RawRecord` and `source_payload`.

## Required Assignment Concerns

Multi-tenancy:

Every source, facility, batch, raw row, activity row, and audit event is tied to `Tenant`. Production would enforce tenant scoping through authentication middleware and row-level query filters. The prototype keeps the data model ready for that but does not build login.

Scope 1/2/3 categorization:

- SAP diesel/natural gas rows map to Scope 1.
- Utility electricity maps to Scope 2.
- Procurement and travel map to Scope 3.

Source-of-truth tracking:

`SourceSystem` identifies the upstream system. `IngestionBatch` records when data arrived and who imported it. `RawRecord` stores the original payload. `ActivityRecord.source_record_id` links normalized records to source IDs such as purchase order/item, meter/account/period, or Concur expense ID.

Edited tracking:

`ActivityRecord.edited`, `edited_at`, and `AuditEvent` preserve review changes. Locked records are intended to be immutable after audit signoff.

Unit normalization:

The normalizer stores both original and normalized values:

- `original_quantity`, `original_unit`
- `normalized_quantity`, `normalized_unit`

Examples: MWh becomes kWh; SAP liter aliases become `l`; travel nights and kilometers are standardized.

Audit trail:

`AuditEvent` captures batch ingestion, record edits, approvals, rejections, and locks with before/after JSON where useful.

## Suspicion Flags

Suspicious rows remain importable but are highlighted:

- Utility billing periods outside 20-45 days.
- Travel distance missing for flight/rail/ground records.
- Procurement spend rows that need category-specific emission factor mapping.
- Non-positive quantities.

This matches the assignment goal: analysts should see what came in, what failed, what looks suspicious, and approve rows before audit.
