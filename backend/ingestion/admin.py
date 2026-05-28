from django.contrib import admin

from .models import ActivityRecord, AuditEvent, EmissionFactor, Facility, IngestionBatch, RawRecord, SourceSystem, Tenant

admin.site.register(Tenant)
admin.site.register(Facility)
admin.site.register(SourceSystem)
admin.site.register(IngestionBatch)
admin.site.register(RawRecord)
admin.site.register(ActivityRecord)
admin.site.register(AuditEvent)
admin.site.register(EmissionFactor)
