# Generated for the Breathe ESG prototype.
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=180, unique=True)),
                ("slug", models.SlugField(unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="EmissionFactor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope", models.CharField(max_length=16)),
                ("activity_type", models.CharField(max_length=64)),
                ("unit", models.CharField(max_length=32)),
                ("kg_co2e_per_unit", models.DecimalField(decimal_places=6, max_digits=14)),
                ("source_label", models.CharField(max_length=180)),
                ("valid_from", models.DateField()),
                ("valid_to", models.DateField(blank=True, null=True)),
            ],
            options={"unique_together": {("scope", "activity_type", "unit", "valid_from")}},
        ),
        migrations.CreateModel(
            name="Facility",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=32)),
                ("name", models.CharField(max_length=180)),
                ("country", models.CharField(default="US", max_length=2)),
                ("grid_region", models.CharField(blank=True, max_length=64)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="facilities", to="ingestion.tenant")),
            ],
            options={"unique_together": {("tenant", "code")}},
        ),
        migrations.CreateModel(
            name="SourceSystem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(choices=[("sap", "SAP"), ("utility", "Utility"), ("travel", "Corporate travel")], max_length=24)),
                ("name", models.CharField(max_length=180)),
                ("external_owner", models.CharField(blank=True, max_length=180)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sources", to="ingestion.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="IngestionBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("filename", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("completed", "Completed"), ("completed_with_errors", "Completed with errors"), ("failed", "Failed")], default="pending", max_length=32)),
                ("received_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("imported_by", models.CharField(default="analyst@demo.local", max_length=180)),
                ("row_count", models.PositiveIntegerField(default=0)),
                ("error_count", models.PositiveIntegerField(default=0)),
                ("notes", models.TextField(blank=True)),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="batches", to="ingestion.sourcesystem")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batches", to="ingestion.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="RawRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("row_number", models.PositiveIntegerField()),
                ("payload", models.JSONField()),
                ("parsed_ok", models.BooleanField(default=False)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="raw_records", to="ingestion.ingestionbatch")),
            ],
        ),
        migrations.CreateModel(
            name="ActivityRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_record_id", models.CharField(max_length=180)),
                ("scope", models.CharField(choices=[("scope_1", "Scope 1"), ("scope_2", "Scope 2"), ("scope_3", "Scope 3")], max_length=16)),
                ("activity_type", models.CharField(max_length=64)),
                ("category", models.CharField(max_length=100)),
                ("activity_start", models.DateField()),
                ("activity_end", models.DateField()),
                ("original_quantity", models.DecimalField(decimal_places=4, max_digits=16)),
                ("original_unit", models.CharField(max_length=32)),
                ("normalized_quantity", models.DecimalField(decimal_places=4, max_digits=16)),
                ("normalized_unit", models.CharField(max_length=32)),
                ("kg_co2e", models.DecimalField(decimal_places=4, max_digits=16)),
                ("currency", models.CharField(blank=True, max_length=3)),
                ("spend_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ("supplier", models.CharField(blank=True, max_length=180)),
                ("suspicious", models.BooleanField(default=False)),
                ("suspicious_reason", models.TextField(blank=True)),
                ("review_status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"), ("locked", "Locked")], default="pending", max_length=24)),
                ("reviewer_note", models.TextField(blank=True)),
                ("source_payload", models.JSONField()),
                ("edited", models.BooleanField(default=False)),
                ("edited_at", models.DateTimeField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("locked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="activity_records", to="ingestion.ingestionbatch")),
                ("facility", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="ingestion.facility")),
                ("raw_record", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="activity_record", to="ingestion.rawrecord")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activity_records", to="ingestion.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("actor", models.CharField(default="analyst@demo.local", max_length=180)),
                ("action", models.CharField(max_length=64)),
                ("before", models.JSONField(blank=True, null=True)),
                ("after", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("activity_record", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="ingestion.activityrecord")),
                ("batch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="ingestion.ingestionbatch")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="ingestion.tenant")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="activityrecord",
            index=models.Index(fields=["tenant", "review_status"], name="ingestion_a_tenant__613d8e_idx"),
        ),
        migrations.AddIndex(
            model_name="activityrecord",
            index=models.Index(fields=["tenant", "scope", "activity_type"], name="ingestion_a_tenant__a09a9d_idx"),
        ),
        migrations.AddIndex(
            model_name="activityrecord",
            index=models.Index(fields=["source_record_id"], name="ingestion_a_source__74d07e_idx"),
        ),
    ]
