from django.contrib import admin
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'company', 'status', 'created_at', 'replied_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'company__company_name', 'complaint_text')
    readonly_fields = ('created_at', 'updated_at')
