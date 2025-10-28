from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from .models import License, Document
from .utils import GeoJSONImporter
import json


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
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-geojson/', self.admin_site.admin_view(self.import_geojson_view), name='licenses_import_geojson'),
        ]
        return custom_urls + urls
    
    def import_geojson_view(self, request):
        if request.method == 'POST':
            if 'geojson_file' not in request.FILES:
                messages.error(request, 'Файл не был загружен')
                return redirect('..')
            
            geojson_file = request.FILES['geojson_file']
            
            if not geojson_file.name.endswith('.geojson') and not geojson_file.name.endswith('.json'):
                messages.error(request, 'Неверный формат файла. Поддерживаются только .geojson и .json')
                return redirect('..')
            
            try:
                file_content = geojson_file.read().decode('utf-8')
                importer = GeoJSONImporter()
                result = importer.import_from_file(file_content)
                
                messages.success(
                    request,
                    f'Импорт завершён! Создано: {result["imported"]}, Обновлено: {result["updated"]}, Пропущено: {result["skipped"]}'
                )
                
                if result['errors']:
                    for error in result['errors'][:5]:
                        messages.warning(request, error)
                
                return redirect('..')
            
            except json.JSONDecodeError:
                messages.error(request, 'Файл не является корректным JSON')
                return redirect('..')
            except Exception as e:
                messages.error(request, f'Ошибка при обработке файла: {str(e)}')
                return redirect('..')
        
        context = {
            'title': 'Импорт GeoJSON',
            'site_title': 'Администрирование',
            'has_permission': True,
        }
        return render(request, 'admin/licenses/import_geojson.html', context)


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
