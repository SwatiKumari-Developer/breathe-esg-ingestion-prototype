from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from ingestion.models import EmissionFactor, Facility, SourceSystem, Tenant


class Command(BaseCommand):
    help = "Seed demo tenant, facilities, sources, and emission factors."

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.get_or_create(name="Acme Manufacturing", slug="acme")
        facilities = [
            ("PL01", "Detroit Assembly Plant", "US", "RFCM"),
            ("DE02", "Stuttgart Components", "DE", "DE"),
            ("MX07", "Monterrey Packaging", "MX", "MX"),
        ]
        for code, name, country, region in facilities:
            Facility.objects.get_or_create(
                tenant=tenant,
                code=code,
                defaults={"name": name, "country": country, "grid_region": region},
            )
        sources = [
            ("sap", "SAP S/4HANA MM export", "ERP Integration Team"),
            ("utility", "Facilities utility portal CSV", "Facilities Energy Lead"),
            ("travel", "SAP Concur expense export", "Travel Operations"),
        ]
        for source_type, name, owner in sources:
            SourceSystem.objects.get_or_create(
                tenant=tenant,
                source_type=source_type,
                name=name,
                defaults={"external_owner": owner},
            )
        for scope, activity_type, unit, factor, label in [
            ("scope_1", "diesel", "l", Decimal("2.680"), "Prototype factor set"),
            ("scope_1", "diesel", "gal", Decimal("10.210"), "Prototype factor set"),
            ("scope_2", "electricity", "kwh", Decimal("0.386"), "US average placeholder"),
            ("scope_3", "flight", "km", Decimal("0.158"), "Prototype factor set"),
            ("scope_3", "hotel", "night", Decimal("18.000"), "Prototype factor set"),
            ("scope_3", "rail", "km", Decimal("0.041"), "Prototype factor set"),
            ("scope_3", "ground", "km", Decimal("0.192"), "Prototype factor set"),
        ]:
            EmissionFactor.objects.get_or_create(
                scope=scope,
                activity_type=activity_type,
                unit=unit,
                valid_from=date(2025, 1, 1),
                defaults={"kg_co2e_per_unit": factor, "source_label": label},
            )
        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
