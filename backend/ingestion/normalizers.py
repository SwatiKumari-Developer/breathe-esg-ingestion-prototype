import csv
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import ActivityRecord, AuditEvent, Facility, IngestionBatch, RawRecord


EMISSION_FACTORS = {
    ("scope_1", "diesel", "l"): Decimal("2.680"),
    ("scope_1", "diesel", "gal"): Decimal("10.210"),
    ("scope_1", "natural_gas", "therm"): Decimal("5.300"),
    ("scope_2", "electricity", "kwh"): Decimal("0.386"),
    ("scope_3", "flight", "km"): Decimal("0.158"),
    ("scope_3", "hotel", "night"): Decimal("18.000"),
    ("scope_3", "rail", "km"): Decimal("0.041"),
    ("scope_3", "ground", "km"): Decimal("0.192"),
}

UNIT_ALIASES = {
    "liter": "l",
    "litre": "l",
    "l": "l",
    "ltr": "l",
    "gal": "gal",
    "gallon": "gal",
    "gallons": "gal",
    "kwh": "kwh",
    "mwh": "mwh",
    "km": "km",
    "kilometer": "km",
    "kilometers": "km",
    "night": "night",
    "nights": "night",
}

SAP_HEADERS = {
    "document": ["PurchaseOrder", "Bestellung", "PO Number", "Einkaufsbeleg"],
    "item": ["PurchaseOrderItem", "Position", "PO Item"],
    "plant": ["Plant", "Werk", "WERKS"],
    "posting_date": ["PostingDate", "Buchungsdatum", "DocumentDate"],
    "material_group": ["MaterialGroup", "Warengruppe"],
    "description": ["ShortText", "Kurztext", "PurchaseOrderItemText"],
    "quantity": ["Quantity", "Menge", "OrderQuantity"],
    "unit": ["Unit", "MEINS", "PurchaseOrderQuantityUnit"],
    "supplier": ["Supplier", "Lieferant", "Vendor"],
    "amount": ["NetAmount", "Betrag", "Amount"],
    "currency": ["Currency", "Waehrung", "DocumentCurrency"],
}


def _pick(row, names, default=""):
    normalized = {key.strip().lower(): value for key, value in row.items()}
    for name in names:
        if name.lower() in normalized:
            return normalized[name.lower()]
    return default


def _decimal(value, fallback=None):
    if value is None or value == "":
        if fallback is not None:
            return fallback
        raise ValueError("missing numeric value")
    try:
        return Decimal(str(value).replace(",", "").strip())
    except InvalidOperation as exc:
        raise ValueError(f"invalid numeric value: {value}") from exc


def _date(value):
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unsupported date format: {value}")


def _unit(value):
    key = str(value).strip().lower()
    return UNIT_ALIASES.get(key, key)


def _activity_from_text(text):
    lowered = text.lower()
    if "diesel" in lowered or "fuel" in lowered or "kraftstoff" in lowered:
        return "diesel", "Fuel"
    if "gas" in lowered:
        return "natural_gas", "Fuel"
    return "procurement", "Purchased goods"


def _normalize_quantity(activity_type, quantity, unit):
    if unit == "mwh":
        return quantity * Decimal("1000"), "kwh"
    if activity_type == "diesel" and unit in {"l", "gal"}:
        return quantity, unit
    return quantity, unit


def _co2e(scope, activity_type, quantity, unit):
    factor = EMISSION_FACTORS.get((scope, activity_type, unit))
    if factor is None:
        return Decimal("0")
    return (quantity * factor).quantize(Decimal("0.0001"))


def _facility(tenant, code):
    if not code:
        return None
    facility, _ = Facility.objects.get_or_create(
        tenant=tenant,
        code=str(code).strip(),
        defaults={"name": f"Unknown facility {code}", "country": "US"},
    )
    return facility


def ingest_file(batch, uploaded_file):
    content = uploaded_file.read().decode("utf-8-sig")
    source_type = batch.source.source_type
    if source_type == "sap":
        rows = list(csv.DictReader(content.splitlines()))
        return _ingest_rows(batch, rows, normalize_sap_row)
    if source_type == "utility":
        rows = list(csv.DictReader(content.splitlines()))
        return _ingest_rows(batch, rows, normalize_utility_row)
    if source_type == "travel":
        payload = json.loads(content)
        rows = payload.get("expenses", payload if isinstance(payload, list) else [])
        return _ingest_rows(batch, rows, normalize_travel_row)
    raise ValueError(f"unsupported source type {source_type}")


@transaction.atomic
def _ingest_rows(batch, rows, normalizer):
    imported = 0
    errors = 0
    for index, row in enumerate(rows, start=1):
        raw = RawRecord.objects.create(batch=batch, row_number=index, payload=row)
        try:
            attrs = normalizer(batch.tenant, row)
            ActivityRecord.objects.create(batch=batch, raw_record=raw, tenant=batch.tenant, source_payload=row, **attrs)
            raw.parsed_ok = True
            imported += 1
        except Exception as exc:
            raw.error_message = str(exc)
            errors += 1
        raw.save()
    batch.row_count = len(rows)
    batch.error_count = errors
    batch.status = IngestionBatch.COMPLETED if errors == 0 else IngestionBatch.COMPLETED_WITH_ERRORS
    batch.save()
    AuditEvent.objects.create(
        tenant=batch.tenant,
        batch=batch,
        action="batch_ingested",
        after={"rows": len(rows), "imported": imported, "errors": errors},
    )
    return batch


def normalize_sap_row(tenant, row):
    document = _pick(row, SAP_HEADERS["document"])
    item = _pick(row, SAP_HEADERS["item"], "00010")
    plant = _pick(row, SAP_HEADERS["plant"])
    description = _pick(row, SAP_HEADERS["description"])
    material_group = _pick(row, SAP_HEADERS["material_group"])
    quantity = _decimal(_pick(row, SAP_HEADERS["quantity"]))
    original_unit = _unit(_pick(row, SAP_HEADERS["unit"]))
    activity_type, category = _activity_from_text(f"{description} {material_group}")
    scope = "scope_1" if activity_type in {"diesel", "natural_gas"} else "scope_3"
    normalized_quantity, normalized_unit = _normalize_quantity(activity_type, quantity, original_unit)
    activity_date = _date(_pick(row, SAP_HEADERS["posting_date"]))
    suspicious = normalized_quantity <= 0 or activity_type == "procurement"
    reason = "Procurement spend requires category-specific factor mapping" if activity_type == "procurement" else ""
    return {
        "facility": _facility(tenant, plant),
        "source_record_id": f"SAP-{document}-{item}",
        "scope": scope,
        "activity_type": activity_type,
        "category": category,
        "activity_start": activity_date,
        "activity_end": activity_date,
        "original_quantity": quantity,
        "original_unit": original_unit,
        "normalized_quantity": normalized_quantity,
        "normalized_unit": normalized_unit,
        "kg_co2e": _co2e(scope, activity_type, normalized_quantity, normalized_unit),
        "currency": _pick(row, SAP_HEADERS["currency"]),
        "spend_amount": _decimal(_pick(row, SAP_HEADERS["amount"], ""), Decimal("0")),
        "supplier": _pick(row, SAP_HEADERS["supplier"]),
        "suspicious": suspicious,
        "suspicious_reason": reason,
    }


def normalize_utility_row(tenant, row):
    start = _date(_pick(row, ["BillingStart", "Start Date", "Service From"]))
    end = _date(_pick(row, ["BillingEnd", "End Date", "Service To"]))
    quantity = _decimal(_pick(row, ["Usage", "kWh", "Consumption"]))
    original_unit = _unit(_pick(row, ["Unit", "Usage Unit"], "kwh"))
    normalized_quantity, normalized_unit = _normalize_quantity("electricity", quantity, original_unit)
    days = (end - start).days + 1
    suspicious = days < 20 or days > 45 or normalized_quantity <= 0
    reason = "Billing period is outside expected 20-45 day range" if suspicious else ""
    return {
        "facility": _facility(tenant, _pick(row, ["FacilityCode", "Plant", "Site"])),
        "source_record_id": f"UTIL-{_pick(row, ['AccountNumber', 'Utility Account'])}-{_pick(row, ['MeterNumber', 'Meter'])}-{start}",
        "scope": "scope_2",
        "activity_type": "electricity",
        "category": _pick(row, ["Tariff", "Rate Plan"], "Electricity"),
        "activity_start": start,
        "activity_end": end,
        "original_quantity": quantity,
        "original_unit": original_unit,
        "normalized_quantity": normalized_quantity,
        "normalized_unit": normalized_unit,
        "kg_co2e": _co2e("scope_2", "electricity", normalized_quantity, normalized_unit),
        "currency": _pick(row, ["Currency"], "USD"),
        "spend_amount": _decimal(_pick(row, ["BillAmount", "Total Charges"], ""), Decimal("0")),
        "supplier": _pick(row, ["Utility", "Supplier"], "Utility provider"),
        "suspicious": suspicious,
        "suspicious_reason": reason,
    }


def normalize_travel_row(tenant, row):
    category = str(row.get("expenseType") or row.get("category") or "").lower()
    if "air" in category or "flight" in category:
        activity_type = "flight"
        unit = "km"
        quantity = _decimal(row.get("distanceKm"), Decimal("0"))
        suspicious = quantity == 0
        reason = "Flight distance missing; airport-code distance lookup needed"
    elif "hotel" in category:
        activity_type = "hotel"
        unit = "night"
        quantity = _decimal(row.get("nights"), Decimal("1"))
        suspicious = quantity <= 0
        reason = "Hotel night count missing or invalid" if suspicious else ""
    elif "rail" in category or "train" in category:
        activity_type = "rail"
        unit = "km"
        quantity = _decimal(row.get("distanceKm"), Decimal("0"))
        suspicious = quantity == 0
        reason = "Rail distance missing" if suspicious else ""
    else:
        activity_type = "ground"
        unit = "km"
        quantity = _decimal(row.get("distanceKm"), Decimal("0"))
        suspicious = quantity == 0
        reason = "Ground transport distance missing" if suspicious else ""
    start = _date(row.get("transactionDate") or row.get("startDate"))
    return {
        "facility": None,
        "source_record_id": f"TRAVEL-{row.get('expenseId')}",
        "scope": "scope_3",
        "activity_type": activity_type,
        "category": str(row.get("expenseType") or row.get("category")),
        "activity_start": start,
        "activity_end": _date(row.get("endDate") or row.get("transactionDate") or row.get("startDate")),
        "original_quantity": quantity,
        "original_unit": unit,
        "normalized_quantity": quantity,
        "normalized_unit": unit,
        "kg_co2e": _co2e("scope_3", activity_type, quantity, unit),
        "currency": row.get("currency", "USD"),
        "spend_amount": _decimal(row.get("amount"), Decimal("0")),
        "supplier": row.get("vendor", ""),
        "suspicious": suspicious,
        "suspicious_reason": reason,
    }
