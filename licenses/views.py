from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_http_methods
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import License, Document
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from io import BytesIO
from datetime import datetime


def map_view(request):
    """
    Главная страница с интерактивной картой
    """
    from django.conf import settings
    return render(request, 'licenses/map.html', {
        'yandex_maps_api_key': settings.YANDEX_MAPS_API_KEY
    })


def analytics_view(request):
    """
    Страница аналитики с графиками
    """
    return render(request, 'licenses/analytics.html')


def help_page(request):
    """
    Страница документации и помощи для пользователей
    """
    return render(request, 'licenses/help.html')


def licenses_json(request):
    """
    API endpoint для получения списка лицензий в формате JSON с пагинацией
    """
    licenses = License.objects.all()
    
    # Получаем параметры пагинации
    page_number = request.GET.get('page', 1)
    page_size = int(request.GET.get('page_size', 12))
    
    # Создаем пагинатор
    paginator = Paginator(licenses, page_size)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    data = []
    for license in page_obj:
        # Проверяем и обновляем статус, если срок истек
        license.update_status_if_expired()

        data.append({
            'id': license.id,
            'license_number': license.license_number,
            'license_type': license.license_type,
            'owner': license.owner,
            'latitude': float(license.latitude) if license.latitude else None,
            'longitude': float(license.longitude) if license.longitude else None,
            'polygon_data': license.polygon_data,
            'region': license.region,
            'area': license.area,
            'issue_date': license.issue_date.strftime('%Y-%m-%d'),
            'expiry_date': license.expiry_date.strftime('%Y-%m-%d') if license.expiry_date else None,
            'mineral_type': license.mineral_type,
            'status': license.status,
            'description': license.description,
        })
    
    # Возвращаем данные с метаинформацией о пагинации
    return JsonResponse({
        'results': data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }
    })


def licenses_all_json(request):
    """
    API endpoint для получения ВСЕХ лицензий без пагинации (для статистики и графиков)
    """
    licenses = License.objects.all()
    data = []
    
    for license in licenses:
        # Проверяем и обновляем статус, если срок истек
        license.update_status_if_expired()

        data.append({
            'id': license.id,
            'license_number': license.license_number,
            'license_type': license.license_type,
            'owner': license.owner,
            'latitude': float(license.latitude) if license.latitude else None,
            'longitude': float(license.longitude) if license.longitude else None,
            'polygon_data': license.polygon_data,
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
    # Проверяем и обновляем статус, если срок истек
    license.update_status_if_expired()
    documents = license.documents.all()
    
    data = {
        'id': license.id,
        'license_number': license.license_number,
        'license_type': license.license_type,
        'owner': license.owner,
        'latitude': float(license.latitude) if license.latitude else None,
        'longitude': float(license.longitude) if license.longitude else None,
        'polygon_data': license.polygon_data,
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
        content_type, _ = mimetypes.guess_type(filename)  
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Открываем файл в бинарном режиме
        file = document.file.open('rb')
        
        response = FileResponse(file, content_type=content_type)
        
        # Правильное формирование Content-Disposition для поддержки кириллицы
        # Используем только один вариант (filename* для Unicode)
        encoded_filename = quote(filename.encode('utf-8'))
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
        
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


@login_required
def upload_geojson(request):
    """
    Страница для загрузки GeoJSON файлов (только для персонала)
    """
    if not request.user.is_staff:
        return HttpResponse('Доступ запрещён. Только для администраторов.', status=403)
    if request.method == 'POST':
        if 'geojson_file' not in request.FILES:
            return render(request, 'licenses/upload_geojson.html', {
                'error': 'Пожалуйста, выберите GeoJSON файл для загрузки'
            })
        
        geojson_file = request.FILES['geojson_file']
        
        # Проверяем расширение файла
        if not geojson_file.name.endswith('.geojson') and not geojson_file.name.endswith('.json'):
            return render(request, 'licenses/upload_geojson.html', {
                'error': 'Неверный формат файла. Поддерживаются только .geojson и .json файлы'
            })
        
        try:
            # Читаем содержимое файла
            file_content = geojson_file.read().decode('utf-8')
            
            # Импортируем данные
            from .utils import GeoJSONImporter
            importer = GeoJSONImporter()
            result = importer.import_from_file(file_content)
            
            # Формируем сообщение об успехе
            success_message = f"""
                Импорт завершён успешно!
                Создано новых лицензий: {result['imported']}
                Обновлено существующих: {result['updated']}
                Пропущено: {result['skipped']}
                Всего обработано: {result['total']}
            """
            
            return render(request, 'licenses/upload_geojson.html', {
                'success': success_message,
                'result': result
            })
        
        except json.JSONDecodeError:
            return render(request, 'licenses/upload_geojson.html', {
                'error': 'Ошибка: файл не является корректным JSON'
            })
        except Exception as e:
            return render(request, 'licenses/upload_geojson.html', {
                'error': f'Ошибка при обработке файла: {str(e)}'
            })
    
    return render(request, 'licenses/upload_geojson.html')


def export_licenses_excel(request):
    """
    Экспорт лицензий в Excel файл с учетом фильтров
    """
    # Получаем параметры фильтрации из GET параметров
    status_filter = request.GET.get('status', '')
    region_filter = request.GET.get('region', '')
    type_filter = request.GET.get('type', '')
    mineral_filter = request.GET.get('mineral', '')
    search_text = request.GET.get('search', '')
    
    # Начинаем с всех лицензий
    licenses = License.objects.all()
    
    # Применяем фильтры
    if status_filter:
        licenses = licenses.filter(status=status_filter)
    if region_filter:
        licenses = licenses.filter(region=region_filter)
    if type_filter:
        licenses = licenses.filter(license_type=type_filter)
    if mineral_filter:
        licenses = licenses.filter(mineral_type=mineral_filter)
    if search_text:
        from django.db.models import Q
        licenses = licenses.filter(
            Q(license_number__icontains=search_text) | 
            Q(owner__icontains=search_text)
        )
    
    # Создаем Excel файл
    wb = Workbook()
    ws = wb.active
    ws.title = "Лицензии"
    
    # Определяем стили
    header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=12)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    border_style = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    # Заголовки столбцов
    headers = [
        'Номер лицензии', 'Вид пользования', 'Недропользователь', 
        'Регион', 'Участок недр', 'Дата выдачи', 'Дата окончания',
        'Полезное ископаемое', 'Статус', 'Широта', 'Долгота', 'Описание'
    ]
    
    ws.append(headers)
    
    # Применяем стили к заголовкам
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border_style
    
    # Заполняем данные
    for license in licenses:
        # Обновляем статус перед экспортом
        license.update_status_if_expired()
        
        status_text = {
            'active': 'Действующая',
            'expired': 'Истекла',
            'suspended': 'Приостановлена',
            'terminated': 'Прекращена'
        }.get(license.status, license.status)
        
        row_data = [
            license.license_number,
            license.license_type,
            license.owner,
            license.region,
            license.area,
            license.issue_date.strftime('%d.%m.%Y') if license.issue_date else '',
            license.expiry_date.strftime('%d.%m.%Y') if license.expiry_date else '',
            license.mineral_type or '',
            status_text,
            float(license.latitude) if license.latitude else '',
            float(license.longitude) if license.longitude else '',
            license.description or ''
        ]
        
        ws.append(row_data)
    
    # Применяем границы ко всем ячейкам с данными
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(headers)):
        for cell in row:
            cell.border = border_style
            cell.alignment = Alignment(vertical="center", wrap_text=True)
    
    # Автоматически подбираем ширину столбцов
    column_widths = [20, 15, 30, 25, 12, 12, 12, 25, 15, 12, 12, 40]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[chr(64 + i)].width = width
    
    # Фиксируем первую строку
    ws.freeze_panes = 'A2'
    
    # Сохраняем в поток
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Генерируем имя файла с датой и временем
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'licenses_export_{timestamp}.xlsx'
    
    # Возвращаем файл
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


def export_licenses_pdf(request):
    """
    Экспорт лицензий в PDF файл с учетом фильтров
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    
    # Получаем параметры фильтрации из GET параметров
    status_filter = request.GET.get('status', '')
    region_filter = request.GET.get('region', '')
    type_filter = request.GET.get('type', '')
    mineral_filter = request.GET.get('mineral', '')
    search_text = request.GET.get('search', '')
    
    # Начинаем с всех лицензий
    licenses = License.objects.all()
    
    # Применяем фильтры
    if status_filter:
        licenses = licenses.filter(status=status_filter)
    if region_filter:
        licenses = licenses.filter(region=region_filter)
    if type_filter:
        licenses = licenses.filter(license_type=type_filter)
    if mineral_filter:
        licenses = licenses.filter(mineral_type=mineral_filter)
    if search_text:
        from django.db.models import Q
        licenses = licenses.filter(
            Q(license_number__icontains=search_text) | 
            Q(owner__icontains=search_text)
        )
    
    # Создаем PDF файл
    output = BytesIO()
    
    # Используем альбомную ориентацию для широкой таблицы
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=2*cm,
        bottomMargin=1*cm
    )
    
    # Элементы документа
    elements = []
    
    # Стили
    styles = getSampleStyleSheet()
    
    # Заголовок документа
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#3B82F6'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    title = Paragraph('База лицензий на недропользование', title_style)
    elements.append(title)
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6B7280'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    current_date = datetime.now().strftime('%d.%m.%Y %H:%M')
    subtitle = Paragraph(f'Дата формирования: {current_date}', subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.5*cm))
    
    # Данные таблицы
    data = []
    
    # Заголовки
    headers = ['№', 'Номер лицензии', 'Вид', 'Недропользователь', 'Регион', 
               'Дата выдачи', 'Дата окончания', 'Полезное ископаемое', 'Статус']
    data.append(headers)
    
    # Заполняем данные
    for idx, license in enumerate(licenses, 1):
        # Обновляем статус перед экспортом
        license.update_status_if_expired()
        
        status_text = {
            'active': 'Действующая',
            'expired': 'Истекла',
            'suspended': 'Приостановлена',
            'terminated': 'Прекращена'
        }.get(license.status, license.status)
        
        row = [
            str(idx),
            license.license_number or '',
            license.license_type or '',
            (license.owner[:30] + '...') if license.owner and len(license.owner) > 30 else (license.owner or ''),
            license.region or '',
            license.issue_date.strftime('%d.%m.%Y') if license.issue_date else '',
            license.expiry_date.strftime('%d.%m.%Y') if license.expiry_date else '',
            (license.mineral_type[:20] + '...') if license.mineral_type and len(license.mineral_type) > 20 else (license.mineral_type or ''),
            status_text
        ]
        data.append(row)
    
    # Создаем таблицу
    table = Table(data, colWidths=[1*cm, 3.5*cm, 2*cm, 4.5*cm, 3.5*cm, 2.5*cm, 2.5*cm, 3.5*cm, 2.5*cm])
    
    # Стили таблицы
    table_style = TableStyle([
        # Заголовок
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Данные
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Номер по центру
        ('ALIGN', (1, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 1), (-1, -1), 6),
        ('RIGHTPADDING', (0, 1), (-1, -1), 6),
        
        # Сетка
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Чередующиеся строки
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Добавляем информацию о количестве записей
    elements.append(Spacer(1, 0.5*cm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#6B7280'),
        alignment=TA_LEFT
    )
    footer_text = f'Всего записей: {licenses.count()}'
    footer = Paragraph(footer_text, footer_style)
    elements.append(footer)
    
    # Генерируем PDF
    doc.build(elements)
    
    # Получаем данные PDF
    output.seek(0)
    
    # Генерируем имя файла с датой и временем
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'licenses_export_{timestamp}.pdf'
    
    # Возвращаем файл
    response = HttpResponse(output.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response