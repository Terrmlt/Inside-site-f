import json
import re
from datetime import date, datetime
from django.core.management.base import BaseCommand
from licenses.models import License


class Command(BaseCommand):
    help = 'Импорт лицензий из GeoJSON файла'

    def add_arguments(self, parser):
        parser.add_argument('geojson_file', type=str, help='Путь к GeoJSON файлу')

    def handle(self, *args, **options):
        geojson_file = options['geojson_file']
        
        self.stdout.write(self.style.SUCCESS(f'Загрузка данных из {geojson_file}...'))
        
        with open(geojson_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        features = data.get('features', [])
        self.stdout.write(f'Найдено объектов: {len(features)}')
        
        imported_count = 0
        skipped_count = 0
        updated_count = 0
        
        for feature in features:
            try:
                # Извлекаем данные
                geometry = feature['geometry']
                properties = feature['properties']
                description = properties.get('description', '')
                fill_color = properties.get('fill', '')
                
                # Парсим описание
                parsed = self.parse_description(description)
                
                if not parsed['license_number']:
                    self.stdout.write(self.style.WARNING(f'Пропуск: не найден номер лицензии в "{description[:100]}"'))
                    skipped_count += 1
                    continue
                
                # Определяем статус по цвету
                status = self.get_status_from_color(fill_color, description)
                
                # Вычисляем центр полигона
                center = self.calculate_polygon_center(geometry['coordinates'], geometry.get('type', 'Polygon'))
                
                # Определяем регион по префиксу номера лицензии
                region = self.extract_region(parsed['license_number'])
                
                # Проверяем, существует ли лицензия
                license_obj, created = License.objects.update_or_create(
                    license_number=parsed['license_number'],
                    defaults={
                        'license_type': parsed['license_type'],
                        'owner': parsed['owner'],
                        'latitude': center[1] if center else None,
                        'longitude': center[0] if center else None,
                        'polygon_data': geometry,
                        'region': region,
                        'area': parsed['area_name'],
                        'issue_date': date.today(),
                        'mineral_type': 'Золото',
                        'status': status,
                        'description': description.replace('<br/>', '\n'),
                    }
                )
                
                if created:
                    imported_count += 1
                    self.stdout.write(f'✓ Создана: {parsed["license_number"]}')
                else:
                    updated_count += 1
                    self.stdout.write(f'↻ Обновлена: {parsed["license_number"]}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка обработки объекта: {str(e)}'))
                skipped_count += 1
                continue
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Итоги импорта ==='))
        self.stdout.write(self.style.SUCCESS(f'Создано новых: {imported_count}'))
        self.stdout.write(self.style.SUCCESS(f'Обновлено: {updated_count}'))
        self.stdout.write(self.style.WARNING(f'Пропущено: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'Всего обработано: {imported_count + updated_count + skipped_count}'))

    def parse_description(self, description):
        """Парсит описание лицензии"""
        # Удаляем HTML теги
        text = description.replace('<br/>', ' | ').strip()
        
        result = {
            'license_number': '',
            'license_type': '',
            'area_name': '',
            'owner': '',
            'area_size': ''
        }
        
        # Разбиваем по разделителю |
        parts = [p.strip() for p in text.split('|')]
        
        if len(parts) > 0:
            # Первая часть обычно содержит номер, тип и название
            first_part = parts[0]
            
            # Пытаемся извлечь номер лицензии (формат: ЧИТ 011511, МАГ 04663, и т.д.)
            license_match = re.search(r'([А-ЯЁ]{3}\s+\d{5,6})', first_part)
            if license_match:
                result['license_number'] = license_match.group(1)
                
                # Всё после номера - это тип и название
                remainder = first_part[license_match.end():].strip()
                
                # Тип обычно идёт сразу после номера (БЭ, БП, БР и т.д.)
                type_match = re.match(r'(БЭ|БП|БР|ГРР)\s+(.*)', remainder)
                if type_match:
                    result['license_type'] = f"{type_match.group(1)} - {type_match.group(2)}"
                    result['area_name'] = type_match.group(2)
                else:
                    result['license_type'] = remainder
                    result['area_name'] = remainder
        
        # Площадь
        if len(parts) > 1:
            area_match = re.search(r'Площадь:\s*([\d,]+)\s*кв\.км', parts[1])
            if area_match:
                result['area_size'] = area_match.group(1)
        
        # Владелец - обычно последняя часть
        if len(parts) > 2:
            result['owner'] = parts[2].strip()
        elif len(parts) > 1 and 'Площадь' not in parts[1]:
            result['owner'] = parts[1].strip()
        else:
            result['owner'] = 'Не указан'
            
        return result

    def get_status_from_color(self, color, description):
        """Определяет статус лицензии по цвету"""
        color = color.lower()
        
        if color == '#1bad03':
            return 'terminated'
        elif color == '#ed4543':
            return 'active'
        elif color in ['#0e4779', '#006edb']:
            return 'active'
        elif 'purple' in color or 'violet' in color or '#9b30ff' in color:
            return 'suspended'
        else:
            return 'active'

    def calculate_polygon_center(self, coordinates, geom_type='Polygon'):
        """Вычисляет центр полигона (поддерживает Polygon и MultiPolygon)"""
        if not coordinates or len(coordinates) == 0:
            return None
        
        if geom_type == 'MultiPolygon':
            # Для MultiPolygon берём первый полигон
            if not coordinates[0] or len(coordinates[0]) == 0:
                return None
            outer_ring = coordinates[0][0]
        else:
            # Для обычного Polygon берём внешний контур (первый массив)
            outer_ring = coordinates[0]
        
        if not outer_ring or len(outer_ring) == 0:
            return None
        
        # Вычисляем среднее арифметическое координат
        lon_sum = sum(coord[0] for coord in outer_ring)
        lat_sum = sum(coord[1] for coord in outer_ring)
        count = len(outer_ring)
        
        return [lon_sum / count, lat_sum / count]

    def extract_region(self, license_number):
        """Извлекает название региона из префикса номера лицензии"""
        regions = {
            'МАГ': 'Магаданская область',
            'КЕМ': 'Кемеровская область',
            'ПЕМ': 'Пермский край',
            'ЧИТ': 'Забайкальский край',
            'САХ': 'Сахалинская область',
            'ИРК': 'Иркутская область',
            'АМУ': 'Амурская область',
            'ХАБ': 'Хабаровский край',
            'КРА': 'Красноярский край',
            'БУР': 'Республика Бурятия',
            'ЯКУ': 'Республика Саха (Якутия)',
            'ТЮМ': 'Тюменская область',
        }
        
        prefix = license_number[:3]
        return regions.get(prefix, 'Регион не определён')
