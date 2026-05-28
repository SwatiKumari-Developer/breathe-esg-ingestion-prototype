from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    name = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Facility(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="facilities")
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=180)
    country = models.CharField(max_length=2, default="US")
    grid_region = models.CharField(max_length=64, blank=True)

    class Meta:
        unique_together = ("tenant", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class SourceSystem(models.Model):
    SAP = "sap"
    UTILITY = "utility"
    TRAVEL = "travel"
    SOURCE_CHOICES = [
        (SAP, "SAP"),
        (UTILITY, "Utility"),
        (TRAVEL, "Corporate travel"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="sources")
    source_type = models.CharField(max_length=24, choices=SOURCE_CHOICES)
    name = models.CharField(max_length=180)
    external_owner = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class IngestionBatch(models.Model):
    PENDING = "pending"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (COMPLETED, "Completed"),
        (COMPLETED_WITH_ERRORS, "Completed with errors"),
        (FAILED, "Failed"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="batches")
    source = models.ForeignKey(SourceSystem, on_delete=models.PROTECT, related_name="batches")
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=PENDING)
    received_at = models.DateTimeField(default=timezone.now)
    imported_by = models.CharField(max_length=180, default="analyst@demo.local")
    row_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.source.name} {self.received_at:%Y-%m-%d %H:%M}"


class RawRecord(models.Model):
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name="raw_records")
    row_number = models.PositiveIntegerField()
    payload = models.JSONField()
    parsed_ok = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class EmissionFactor(models.Model):
    scope = models.CharField(max_length=16)
    activity_type = models.CharField(max_length=64)
    unit = models.CharField(max_length=32)
    kg_co2e_per_unit = models.DecimalField(max_digits=14, decimal_places=6)
    source_label = models.CharField(max_length=180)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("scope", "activity_type", "unit", "valid_from")


class ActivityRecord(models.Model):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    LOCKED = "locked"
    REVIEW_CHOICES = [
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
        (LOCKED, "Locked"),
    ]

    SCOPE_CHOICES = [("scope_1", "Scope 1"), ("scope_2", "Scope 2"), ("scope_3", "Scope 3")]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="activity_records")
    batch = models.ForeignKey(IngestionBatch, on_delete=models.PROTECT, related_name="activity_records")
    raw_record = models.OneToOneField(RawRecord, on_delete=models.PROTECT, related_name="activity_record")
    facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
    source_record_id = models.CharField(max_length=180)
    scope = models.CharField(max_length=16, choices=SCOPE_CHOICES)
    activity_type = models.CharField(max_length=64)
    category = models.CharField(max_length=100)
    activity_start = models.DateField()
    activity_end = models.DateField()
    original_quantity = models.DecimalField(max_digits=16, decimal_places=4)
    original_unit = models.CharField(max_length=32)
    normalized_quantity = models.DecimalField(max_digits=16, decimal_places=4)
    normalized_unit = models.CharField(max_length=32)
    kg_co2e = models.DecimalField(max_digits=16, decimal_places=4)
    currency = models.CharField(max_length=3, blank=True)
    spend_amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    supplier = models.CharField(max_length=180, blank=True)
    suspicious = models.BooleanField(default=False)
    suspicious_reason = models.TextField(blank=True)
    review_status = models.CharField(max_length=24, choices=REVIEW_CHOICES, default=PENDING)
    reviewer_note = models.TextField(blank=True)
    source_payload = models.JSONField()
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "review_status"]),
            models.Index(fields=["tenant", "scope", "activity_type"]),
            models.Index(fields=["source_record_id"]),
        ]

    def __str__(self):
        return f"{self.source_record_id} {self.activity_type}"


class AuditEvent(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="audit_events")
    activity_record = models.ForeignKey(ActivityRecord, on_delete=models.CASCADE, related_name="audit_events", null=True, blank=True)
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name="audit_events", null=True, blank=True)
    actor = models.CharField(max_length=180, default="analyst@demo.local")
    action = models.CharField(max_length=64)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
