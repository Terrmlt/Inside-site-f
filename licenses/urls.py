from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map'),
    path('api/licenses/', views.licenses_json, name='licenses_json'),
    path('api/licenses/all/', views.licenses_all_json, name='licenses_all_json'),
    path('api/licenses/<int:license_id>/', views.license_detail, name='license_detail'),
    path('api/licenses/<int:license_id>/upload/', views.upload_document, name='upload_document'),
    path('api/licenses/export/excel/', views.export_licenses_excel, name='export_licenses_excel'),
    path('api/documents/<int:document_id>/download/', views.download_document, name='download_document'),
    path('upload-geojson/', views.upload_geojson, name='upload_geojson'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
