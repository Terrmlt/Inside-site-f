from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.core.files.storage import FileSystemStorage
from .models import License, Document
import json


def map_view(request):
    """
    Главная страница с интерактивной картой
    """
    from django.conf import settings
    return render(request, 'licenses/map.html', {
        'yandex_maps_api_key': settings.YANDEX_MAPS_API_KEY
    })


def licenses_json(request):
    """
    API endpoint для получения списка лицензий в формате JSON
    """
    licenses = License.objects.all()
    data = []
    
    for license in licenses:
        data.append({
            'id': license.id,
            'license_number': license.license_number,
            'license_type': license.license_type,
            'owner': license.owner,
            'latitude': float(license.latitude),
            'longitude': float(license.longitude),
            'region': license.region,
            'area': license.area,
            'issue_date': license.issue_date.strftime('%Y-%m-%d'),
            'expiry_date': license.expiry_date.strftime('%Y-%m-%d') if license.expiry_date else None,
            'mineral_type': license.mineral_type,
            'status': license.status,
            'description': license.description,
        })
    
    return JsonResponse(data, safe=False)


def license_detail(request, license_id):
    """
    Получение детальной информации о лицензии
    """
    license = get_object_or_404(License, id=license_id)
    documents = license.documents.all()
    
    data = {
        'id': license.id,
        'license_number': license.license_number,
        'license_type': license.license_type,
        'owner': license.owner,
        'latitude': float(license.latitude),
        'longitude': float(license.longitude),
        'region': license.region,
        'area': license.area,
        'issue_date': license.issue_date.strftime('%Y-%m-%d'),
        'expiry_date': license.expiry_date.strftime('%Y-%m-%d') if license.expiry_date else None,
        'mineral_type': license.mineral_type,
        'status': license.status,
        'description': license.description,
        'documents': [
            {
                'id': doc.id,
                'title': doc.title,
                'file_type': doc.file_type,
                'file_url': doc.file.url if doc.file else None,
                'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M'),
            }
            for doc in documents
        ]
    }
    
    return JsonResponse(data)


@login_required
def upload_document(request, license_id):
    """
    Загрузка документа для лицензии
    """
    if request.method == 'POST':
        license = get_object_or_404(License, id=license_id)
        
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Файл не найден'}, status=400)
        
        file = request.FILES['file']
        title = request.POST.get('title', file.name)
        file_type = request.POST.get('file_type', 'other')
        
        document = Document.objects.create(
            license=license,
            title=title,
            file=file,
            file_type=file_type,
            uploaded_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'document_id': document.id,
            'message': 'Документ успешно загружен'
        })
    
    return JsonResponse({'error': 'Метод не поддерживается'}, status=405)


def download_document(request, document_id):
    """
    Скачивание документа
    """
    import mimetypes
    import os
    from urllib.parse import quote

    document = get_object_or_404(Document, id=document_id)
    
    if document.file:
        # Получаем оригинальное имя файла
        filename = os.path.basename(document.file.name)
        
        # Определяем MIME-тип по расширению файла
        content_type, _ = mimetypes.guess_type(document.file.name)
        if not content_type:
            content_type = 'application/octet-stream'
        
        response = FileResponse(document.file.open('rb'), content_type=content_type)
        # Кодируем имя файла для поддержки кириллицы и спецсимволов
        encoded_filename = quote(filename)
        response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
        
        return response
    
    return HttpResponse('Файл не найден', status=404)


def login_view(request):
    """
    ЗАГЛУШКА: Форма входа (для будущей LDAP интеграции)
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('map')
        else:
            return render(request, 'licenses/login.html', {
                'error': 'Неверный логин или пароль'
            })
    
    return render(request, 'licenses/login.html')


def logout_view(request):
    """
    Выход из системы
    """
    logout(request)
    return redirect('login')