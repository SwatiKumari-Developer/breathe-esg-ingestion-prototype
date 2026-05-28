from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import ActivityRecord, AuditEvent, Facility, IngestionBatch, SourceSystem, Tenant
from .normalizers import ingest_file
from .serializers import (
    ActivityRecordSerializer,
    AuditEventSerializer,
    FacilitySerializer,
    IngestionBatchSerializer,
    SourceSystemSerializer,
    TenantSerializer,
)


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tenant.objects.all().order_by("name")
    serializer_class = TenantSerializer


class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.select_related("tenant").all().order_by("code")
    serializer_class = FacilitySerializer


class SourceSystemViewSet(viewsets.ModelViewSet):
    queryset = SourceSystem.objects.select_related("tenant").all().order_by("source_type", "name")
    serializer_class = SourceSystemSerializer


class IngestionBatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IngestionBatch.objects.select_related("tenant", "source").all().order_by("-received_at")
    serializer_class = IngestionBatchSerializer


class ActivityRecordViewSet(viewsets.ModelViewSet):
    queryset = ActivityRecord.objects.select_related("tenant", "facility", "batch__source").all().order_by("-created_at")
    serializer_class = ActivityRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        source_type = self.request.query_params.get("source_type")
        suspicious = self.request.query_params.get("suspicious")
        if status_filter:
            qs = qs.filter(review_status=status_filter)
        if source_type:
            qs = qs.filter(batch__source__source_type=source_type)
        if suspicious in {"true", "false"}:
            qs = qs.filter(suspicious=suspicious == "true")
        return qs

    def perform_update(self, serializer):
        record = self.get_object()
        if record.review_status == ActivityRecord.LOCKED:
            raise ValueError("Locked records cannot be edited")
        before = ActivityRecordSerializer(record).data
        updated = serializer.save(edited=True, edited_at=timezone.now())
        AuditEvent.objects.create(
            tenant=updated.tenant,
            activity_record=updated,
            action="record_edited",
            before=before,
            after=ActivityRecordSerializer(updated).data,
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        record = self.get_object()
        record.review_status = ActivityRecord.APPROVED
        record.reviewer_note = request.data.get("note", record.reviewer_note)
        record.approved_at = timezone.now()
        record.save()
        AuditEvent.objects.create(tenant=record.tenant, activity_record=record, action="record_approved", after={"note": record.reviewer_note})
        return Response(ActivityRecordSerializer(record).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        record = self.get_object()
        record.review_status = ActivityRecord.REJECTED
        record.reviewer_note = request.data.get("note", record.reviewer_note)
        record.save()
        AuditEvent.objects.create(tenant=record.tenant, activity_record=record, action="record_rejected", after={"note": record.reviewer_note})
        return Response(ActivityRecordSerializer(record).data)

    @action(detail=True, methods=["post"])
    def lock(self, request, pk=None):
        record = self.get_object()
        if record.review_status != ActivityRecord.APPROVED:
            return Response({"detail": "Only approved records can be locked."}, status=status.HTTP_400_BAD_REQUEST)
        record.review_status = ActivityRecord.LOCKED
        record.locked_at = timezone.now()
        record.save()
        AuditEvent.objects.create(tenant=record.tenant, activity_record=record, action="record_locked")
        return Response(ActivityRecordSerializer(record).data)


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.select_related("tenant", "activity_record", "batch").all()
    serializer_class = AuditEventSerializer


@api_view(["POST"])
def upload_ingestion(request):
    source_id = request.data.get("source")
    file_obj = request.FILES.get("file")
    if not source_id or not file_obj:
        return Response({"detail": "source and file are required"}, status=status.HTTP_400_BAD_REQUEST)
    source = SourceSystem.objects.select_related("tenant").get(id=source_id)
    batch = IngestionBatch.objects.create(
        tenant=source.tenant,
        source=source,
        filename=file_obj.name,
        imported_by=request.data.get("imported_by", "analyst@demo.local"),
    )
    try:
        ingest_file(batch, file_obj)
    except Exception as exc:
        batch.status = IngestionBatch.FAILED
        batch.notes = str(exc)
        batch.save()
        return Response({"detail": str(exc), "batch": IngestionBatchSerializer(batch).data}, status=status.HTTP_400_BAD_REQUEST)
    return Response(IngestionBatchSerializer(batch).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def dashboard(request):
    total = ActivityRecord.objects.count()
    by_status = ActivityRecord.objects.values("review_status").annotate(count=Count("id")).order_by("review_status")
    by_scope = ActivityRecord.objects.values("scope").annotate(count=Count("id"), kg_co2e=Sum("kg_co2e")).order_by("scope")
    by_source = ActivityRecord.objects.values("batch__source__source_type").annotate(count=Count("id")).order_by("batch__source__source_type")
    recent_batches = IngestionBatch.objects.select_related("source", "tenant").order_by("-received_at")[:6]
    return Response(
        {
            "total_records": total,
            "suspicious_records": ActivityRecord.objects.filter(suspicious=True).count(),
            "pending_records": ActivityRecord.objects.filter(review_status=ActivityRecord.PENDING).count(),
            "locked_records": ActivityRecord.objects.filter(review_status=ActivityRecord.LOCKED).count(),
            "by_status": list(by_status),
            "by_scope": list(by_scope),
            "by_source": list(by_source),
            "recent_batches": IngestionBatchSerializer(recent_batches, many=True).data,
        }
    )
