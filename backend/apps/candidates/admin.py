from django.contrib import admin
from .models import CandidateProfile


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'city', 'state', 'experience_years', 'created_at')
    search_fields = ('full_name', 'user__email', 'phone', 'city')
    list_filter = ('gender', 'state', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
