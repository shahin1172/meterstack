from django.contrib import admin
from django.contrib import admin
from .models import Endpoint, UsageRecord, UsageSummary

@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'tenant', 'is_active', 'price_per_call')
    list_filter = ('tenant', 'is_active')
    search_fields = ('name', 'path')

@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'user', 'endpoint', 'timestamp', 'calls', 'cost')
    list_filter = ('tenant', 'endpoint', 'timestamp')
    search_fields = ('user__email',)
    date_hierarchy = 'timestamp'
    raw_id_fields = ('user',)   # for large datasets

@admin.register(UsageSummary)
class UsageSummaryAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'endpoint', 'period', 'total_calls', 'total_cost')
    list_filter = ('tenant', 'period')
    search_fields = ('endpoint__name',)

# Register your models here.
