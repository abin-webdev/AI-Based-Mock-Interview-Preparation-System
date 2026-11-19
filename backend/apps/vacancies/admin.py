from django.contrib import admin
from .models import Vacancy


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('id', 'position', 'company', 'location', 'no_of_vacancy', 'status', 'application_deadline', 'created_at')
    list_filter = ('status', 'location', 'created_at')
    search_fields = ('position', 'company__company_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
