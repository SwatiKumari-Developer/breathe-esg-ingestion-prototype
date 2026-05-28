from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivityRecordViewSet,
    AuditEventViewSet,
    FacilityViewSet,
    IngestionBatchViewSet,
    SourceSystemViewSet,
    TenantViewSet,
    dashboard,
    upload_ingestion,
)

router = DefaultRouter()
router.register("tenants", TenantViewSet)
router.register("facilities", FacilityViewSet)
router.register("sources", SourceSystemViewSet)
router.register("batches", IngestionBatchViewSet)
router.register("records", ActivityRecordViewSet)
router.register("audit-events", AuditEventViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", dashboard),
    path("upload/", upload_ingestion),
]
