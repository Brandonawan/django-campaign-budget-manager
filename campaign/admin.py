# campaign/admin.py
from django.contrib import admin
from .models import Brand, Campaign, SpendLog

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'daily_budget', 'monthly_budget', 'current_daily_spend', 'current_monthly_spend')
    search_fields = ('name',)

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'is_active', 'total_spend_today', 'total_spend_month', 'allowed_start_hour', 'allowed_end_hour')
    list_filter = ('is_active', 'brand')
    search_fields = ('name',)

@admin.register(SpendLog)
class SpendLogAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'amount', 'timestamp')
    list_filter = ('campaign__brand', 'timestamp')
    search_fields = ('campaign__name',)
