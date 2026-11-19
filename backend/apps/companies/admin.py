from django.contrib import admin
from .models import CompanyProfile


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'email', 'phone', 'verification_status', 'is_verified', 'created_at')
    list_filter = ('verification_status', 'created_at')
    search_fields = ('company_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'verified_at')
    actions = ['approve_companies', 'reject_companies', 'suspend_companies']

    @admin.action(description='Approve selected companies')
    def approve_companies(self, request, queryset):
        queryset.update(verification_status='APPROVED')

    @admin.action(description='Reject selected companies')
    def reject_companies(self, request, queryset):
        queryset.update(verification_status='REJECTED')

    @admin.action(description='Suspend selected companies')
    def suspend_companies(self, request, queryset):
        queryset.update(verification_status='SUSPENDED')
