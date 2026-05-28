from rest_framework import serializers

from .models import ActivityRecord, AuditEvent, Facility, IngestionBatch, SourceSystem, Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "slug"]


class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ["id", "tenant", "code", "name", "country", "grid_region"]


class SourceSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceSystem
        fields = ["id", "tenant", "source_type", "name", "external_owner"]


class IngestionBatchSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)
    source_type = serializers.CharField(source="source.source_type", read_only=True)

    class Meta:
        model = IngestionBatch
        fields = [
            "id",
            "tenant",
            "source",
            "source_name",
            "source_type",
            "filename",
            "status",
            "received_at",
            "imported_by",
            "row_count",
            "error_count",
            "notes",
        ]


class ActivityRecordSerializer(serializers.ModelSerializer):
    facility_code = serializers.CharField(source="facility.code", read_only=True)
    facility_name = serializers.CharField(source="facility.name", read_only=True)
    source_name = serializers.CharField(source="batch.source.name", read_only=True)
    source_type = serializers.CharField(source="batch.source.source_type", read_only=True)

    class Meta:
        model = ActivityRecord
        fields = [
            "id",
            "tenant",
            "batch",
            "facility",
            "facility_code",
            "facility_name",
            "source_name",
            "source_type",
            "source_record_id",
            "scope",
            "activity_type",
            "category",
            "activity_start",
            "activity_end",
            "original_quantity",
            "original_unit",
            "normalized_quantity",
            "normalized_unit",
            "kg_co2e",
            "currency",
            "spend_amount",
            "supplier",
            "suspicious",
            "suspicious_reason",
            "review_status",
            "reviewer_note",
            "source_payload",
            "edited",
            "edited_at",
            "approved_at",
            "locked_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["tenant", "batch", "source_payload", "edited_at", "approved_at", "locked_at", "created_at", "updated_at"]


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = ["id", "tenant", "activity_record", "batch", "actor", "action", "before", "after", "created_at"]
