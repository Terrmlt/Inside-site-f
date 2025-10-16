from django.contrib import admin
from .models import License, Document


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ['license_number', 'owner', 'license_type', 'region', 'status', 'issue_date']
    list_filter = ['status', 'region', 'license_type']
    search_fields = ['license_number', 'owner', 'region', 'mineral_type']
    date_hierarchy = 'issue_date'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('license_number', 'license_type', 'owner', 'status')
        }),
        ('Территория', {
            'fields': ('region', 'area', 'latitude', 'longitude')
        }),
        ('Даты', {
            'fields': ('issue_date', 'expiry_date')
        }),
        ('Дополнительная информация', {
            'fields': ('mineral_type', 'description')
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'license', 'file_type', 'uploaded_at', 'uploaded_by']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['title', 'license__license_number']
    date_hierarchy = 'uploaded_at'
    ordering = ['-uploaded_at']
    
    fieldsets = (
        ('Информация о документе', {
            'fields': ('license', 'title', 'file_type')
        }),
        ('Файл', {
            'fields': ('file',)
        }),
        ('Метаданные', {
            'fields': ('uploaded_by',),
            'classes': ('collapse',)
        }),
    )
