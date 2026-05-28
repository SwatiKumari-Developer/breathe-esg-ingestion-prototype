# Sources Researched

## SAP Fuel And Procurement

Researched format:

- SAP S/4HANA purchase order item API/CDS style fields, including purchase order, item, material group, plant, document currency, and purchase order quantity unit.
- SAP plant/order-unit concepts, where plant (`WERKS`) and purchase order unit of measure are common keys in procurement data.

What I learned:

SAP exports are usually not analyst-friendly. Purchase data tends to carry purchase order/item IDs, plant codes, material groups, supplier/vendor IDs, document currency, and quantity units. Implementations may expose English labels, SAP technical names, or localized labels.

Sample data:

`samples/sap_fuel_procurement.csv` uses German headers (`Bestellung`, `Werk`, `Buchungsdatum`, `Menge`, `MEINS`) mixed with fuel/procurement rows. Dates intentionally vary between `DD.MM.YYYY`, `YYYYMMDD`, and slash formats.

What would break in production:

Material master unit conversions, canceled/reversed documents, supplier-specific material naming, and procurement categories without emission factors.

References:

- SAP Help Portal, Purchase Order Item CDS view: https://help.sap.com/docs/SAP_S4HANA_CLOUD/c0c54048d35849128be8e872df5bea6d/33192c1211354eed9e40fac66e55fcc1.html
- SAP A067 table fields including plant and purchase order unit: https://saplearners.com/sap-tables/a067/

## Utility Electricity

Researched format:

- Electricity bills and portal exports typically include account/meter identifiers, billing period, kWh consumption, tariffs/rate plans, charges, and sometimes demand charges.

What I learned:

Utility data is period-based. Billing periods often do not align to calendar months, and analysts need both meter/account identity and the service dates to avoid duplicate or shifted reporting.

Sample data:

`samples/utility_electricity.csv` includes account number, meter number, facility code, utility, billing start/end, usage, unit, tariff, bill amount, and currency. One row is a short billing period so it is flagged as suspicious.

What would break in production:

PDF bills, estimated reads, interval data, multiple meters on one bill, net metering, demand charges, taxes, RECs, and market-vs-location Scope 2 reporting.

References:

- Nevada Public Utilities Commission sample electric bill with billing period/kWh concepts: https://puc.nv.gov/uploadedFiles/pucnvgov/Content/Utilities/MHP/SampleElectricBill.pdf

## Corporate Travel

Researched format:

- SAP Concur expense entries and itinerary reports expose report/expense IDs, expense types, amounts/currency, vendors, and travel-related fields such as airlines, hotels, airports, and itinerary source.

What I learned:

Travel emissions are category-dependent. Flights, hotels, rail, and ground transport need different factors. Distance is not guaranteed; sometimes airport codes or itinerary segments are available instead.

Sample data:

`samples/concur_travel.json` mimics expense entries with `expenseId`, `expenseType`, dates, amount/currency, vendor, airport codes, distance, and hotel nights. One ground transport row has missing distance so analysts see it as suspicious.

What would break in production:

Missing airport distance lookup, cabin class, multi-leg itineraries, traveler home office allocation, exchange rates, personal travel exclusions, and receipt-only entries without itinerary data.

References:

- SAP Concur expense entry example fields: https://docs.blinkops.com/docs/integrations/sap-concur/actions/get-expenses-entries-by-report-id
- SAP Help Portal itinerary details report fields: https://help.sap.com/docs/SAP_CONCUR/92814b27ae9c4b298c6e80d2a3241445/1c431f2e700b1014a46a108435d32877.html
