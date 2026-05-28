# Decisions

## Source Mechanisms

SAP:

I chose CSV export from SAP S/4HANA purchasing/material data rather than a live OData pull. In real enterprise onboarding, API credentials and SAP network access are often delayed, while business teams can export purchase/fuel rows from MM reports. The parser handles SAP-ish reality: plant codes, purchase order/item IDs, German headers, mixed date formats, and inconsistent unit labels.

Utility:

I chose utility portal CSV exports. Facilities teams commonly download monthly bills or interval/summary usage from utility portals. The prototype models account number, meter number, billing period, tariff/rate plan, usage, unit, amount, and currency. Billing periods are allowed to differ from calendar months.

Corporate travel:

I chose a SAP Concur-like JSON expense export. The shape follows expense entries: expense ID, expense type, transaction date, amount/currency, vendor, and optional itinerary details such as airport codes, distance, and hotel nights.

## Source Subsets

SAP subset:

Handled: fuel purchases and procurement rows from purchase order style exports. Ignored: IDoc processing, purchase order amendments, goods receipt reversals, material master unit conversion tables, and supplier-specific category mapping.

Utility subset:

Handled: summary electricity bill/usage CSV by account, meter, billing period, and tariff. Ignored: PDF OCR, interval data, demand charge calculations, renewable energy certificates, and market/location-based dual Scope 2 accounting.

Travel subset:

Handled: flights, hotels, rail, and ground transport expense entries. Ignored: traveler identity workflows, exchange-rate history, class-of-service radiative forcing, airport distance lookup, and policy exceptions.

## Review Workflow

Rows are imported even when suspicious. This is deliberate: in ESG data operations, the analyst needs visibility into problematic rows instead of silent drops. Rows that cannot parse are saved as `RawRecord` failures at batch level.

Statuses are:

- `pending`
- `approved`
- `rejected`
- `locked`

Only approved rows can be locked. Locked means audit-ready and should not be edited.

## What I Would Ask The PM

- Which emission factor library should be authoritative: EPA, DEFRA, supplier-specific LCA factors, IEA, or a customer-configured set?
- Should Scope 2 be market-based, location-based, or both?
- Which SAP extraction is actually available for this client: S/4HANA OData, ECC report export, IDoc, BW extract, or flat file from a shared folder?
- Does the client have a facility/plant master mapping already?
- Should analysts edit normalized rows directly, or should all edits create correction records?
- What does “auditor locked” mean legally for this product: immutable database rows, append-only ledger, export package, or all of the above?
