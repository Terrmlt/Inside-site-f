import json
import re
from datetime import date
from licenses.models import License


class GeoJSONImporter:
    """
    Утилита для импорта лицензий из GeoJSON файлов
    """
    
    def __init__(self):
        self.imported_count = 0
        self.skipped_count = 0
        self.updated_count = 0
        self.errors = []
    
    def import_from_file(self, file_content):
        """
        Импортирует лицензии из GeoJSON файла
        
        Args:
            file_content: содержимое GeoJSON файла (строка или dict)
        
        Returns:
            dict с результатами импорта
        """
        # Парсим JSON, если передана строка
        if isinstance(file_content, str):
            data = json.loads(file_content)
        else:
            data = file_content
        
        features = data.get('features', [])
        
        for feature in features:
            try:
                self._process_feature(feature)
            except Exception as e:
                self.errors.append(f'Ошибка обработки объекта: {str(e)}')
                self.skipped_count += 1
        
        return {
            'imported': self.imported_count,
            'updated': self.updated_count,
            'skipped': self.skipped_count,
            'total': self.imported_count + self.updated_count + self.skipped_count,
            'errors': self.errors
        }
    
    def _process_feature(self, feature):
        """Обрабатывает один объект из GeoJSON"""
        geometry = feature['geometry']
        properties = feature.get('properties', {})
        description = properties.get('description', '')
        fill_color = properties.get('fill', '')
        
        # Парсим описание
        parsed = self.parse_description(description)
        
        if not parsed['license_number']:
            self.errors.append(f'Пропуск: не найден номер лицензии в "{description[:100]}"')
            self.skipped_count += 1
            return
        
        # Определяем статус по цвету
        status = self.get_status_from_color(fill_color, description)
        
        # Вычисляем центр полигона
        center = self.calculate_polygon_center(geometry['coordinates'], geometry.get('type', 'Polygon'))
        
        # Определяем регион по префиксу номера лицензии
        region = self.extract_region(parsed['license_number'])
        
        # Создаем или обновляем лицензию
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
            self.imported_count += 1
        else:
            self.updated_count += 1
    
    def parse_description(self, description):
        """Парсит описание лицензии"""
        text = description.replace('<br/>', ' | ').strip()
        
        result = {
            'license_number': '',
            'license_type': '',
            'area_name': '',
            'owner': '',
            'area_size': ''
        }
        
        parts = [p.strip() for p in text.split('|')]
        
        if len(parts) > 0:
            first_part = parts[0]
            
            # Извлекаем номер лицензии с видом (например, "МАГ 12345 БЭ")
            license_match = re.search(r'([А-ЯЁ]{3}\s+\d{5,6}\s+[А-ЯЁ]{2})', first_part)
            if license_match:
                result['license_number'] = license_match.group(1)
                
                remainder = first_part[license_match.end():].strip()
                
                # Извлекаем вид лицензии из номера
                license_parts = result['license_number'].split()
                if len(license_parts) >= 3:
                    license_type_code = license_parts[-1]  # БЭ, БП, БР и т.д.
                    
                    # Вид пользования - только двухбуквенный код
                    result['license_type'] = license_type_code
                    
                    # Название участка - в поле area_name
                    result['area_name'] = remainder if remainder else ''
                else:
                    result['license_type'] = remainder
                    result['area_name'] = remainder
            else:
                # Если не нашли с видом, пробуем без вида (старый формат)
                license_match = re.search(r'([А-ЯЁ]{3}\s+\d{5,6})', first_part)
                if license_match:
                    result['license_number'] = license_match.group(1)
                    remainder = first_part[license_match.end():].strip()
                    result['license_type'] = remainder
                    result['area_name'] = remainder
        
        # Площадь
        if len(parts) > 1:
            area_match = re.search(r'Площадь:\s*([\d,]+)\s*кв\.км', parts[1])
            if area_match:
                result['area_size'] = area_match.group(1)
        
        # Владелец
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
        """Вычисляет центр полигона"""
        if not coordinates or len(coordinates) == 0:
            return None
        
        if geom_type == 'MultiPolygon':
            if not coordinates[0] or len(coordinates[0]) == 0:
                return None
            outer_ring = coordinates[0][0]
        else:
            outer_ring = coordinates[0]
        
        if not outer_ring or len(outer_ring) == 0:
            return None
        
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
