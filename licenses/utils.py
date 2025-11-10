import json
import re
from datetime import date, datetime
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
            'total':
            self.imported_count + self.updated_count + self.skipped_count,
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
            self.errors.append(
                f'Пропуск: не найден номер лицензии в "{description[:100]}"')
            self.skipped_count += 1
            return

        # Определяем статус по цвету
        status = self.get_status_from_color(fill_color, description)

        # Вычисляем центр полигона
        center = self.calculate_polygon_center(geometry['coordinates'],
                                               geometry.get('type', 'Polygon'))

        # Определяем регион по префиксу номера лицензии
        region = self.extract_region(parsed['license_number'])

        # Проверяем, существует ли лицензия
        try:
            license_obj = License.objects.get(license_number=parsed['license_number'])
            # Лицензия существует - объединяем полигоны
            merged_geometry = self.merge_polygons(license_obj.polygon_data, geometry)
            license_obj.polygon_data = merged_geometry
            
            # Пересчитываем центр для нового объединённого полигона
            new_center = self.calculate_polygon_center(
                merged_geometry['coordinates'],
                merged_geometry.get('type', 'Polygon')
            )
            if new_center:
                license_obj.latitude = new_center[1]
                license_obj.longitude = new_center[0]
            
            license_obj.save()
            self.updated_count += 1
        except License.DoesNotExist:
            # Парсим даты из строк в date объекты
            issue_date_obj = date.today()  # По умолчанию - сегодня
            if parsed['issue_date']:
                try:
                    issue_date_obj = datetime.strptime(parsed['issue_date'], '%d.%m.%Y').date()
                except ValueError:
                    pass  # Оставляем значение по умолчанию

            expiry_date_obj = None
            if parsed['expiry_date']:
                try:
                    expiry_date_obj = datetime.strptime(parsed['expiry_date'], '%d.%m.%Y').date()
                except ValueError:
                    pass

            # Вид полезного ископаемого - используем из описания или значение по умолчанию
            mineral_type_str = parsed['mineral_type'] if parsed['mineral_type'] else 'Не указано'

            # Создаём новую лицензию
            license_obj = License.objects.create(
                license_number=parsed['license_number'],
                license_type=parsed['license_type'],
                owner=parsed['owner'],
                latitude=center[1] if center else None,
                longitude=center[0] if center else None,
                polygon_data=geometry,
                region=region,
                area=parsed['area_name'],
                issue_date=issue_date_obj,
                expiry_date=expiry_date_obj,
                mineral_type=mineral_type_str,
                status=status,
                description=description.replace('<br/>', '\n'),
            )
            self.imported_count += 1

    def parse_description(self, description):
        """Парсит описание лицензии"""
        text = description.replace('<br/>', ' | ').strip()

        result = {
            'license_number': '',
            'license_type': '',
            'area_name': '',
            'owner': '',
            'area_size': '',
            'issue_date': None,
            'expiry_date': None,
            'mineral_type': ''
        }

        parts = [p.strip() for p in text.split('|')]

        if len(parts) > 0:
            first_part = parts[0]

            # Извлекаем номер лицензии с видом (например, "МАГ 12345 БЭ")
            license_match = re.search(r'([А-ЯЁ]{3}\s+\d{5,6}\s+[А-ЯЁ]{2})',
                                      first_part)
            if license_match:
                result['license_number'] = license_match.group(1)

                remainder = first_part[license_match.end():].strip()

                # Извлекаем вид лицензии из номера
                license_parts = result['license_number'].split()
                if len(license_parts) >= 3:
                    license_type_code = license_parts[-1]  # БЭ, БП, БР и т.д.

                    # Вид пользования - только двухбуквенный код
                    result['license_type'] = license_type_code

                    # Название участка - очищаем от организаций и лишних данных
                    area_name = remainder if remainder else ''
                    # Убираем упоминания организаций (ООО, АО и т.д.)
                    area_name = re.sub(
                        r'(ООО|АО|ПАО|ЗАО|ОАО|ИП|ГУП|МУП|ФГУП)\s+[«"]?[^|»"]+[»"]?',
                        '',
                        area_name,
                        flags=re.IGNORECASE)
                    # Убираем площадь, если она попала
                    area_name = re.sub(r'Площадь:?\s*[\d,]+\s*кв\.км',
                                       '',
                                       area_name,
                                       flags=re.IGNORECASE)
                    # Убираем лишние пробелы и символы
                    area_name = area_name.strip(' |,-')

                    result['area_name'] = area_name
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

        # Владелец - ищем организацию во всех частях описания
        owner_found = False
        for part in parts:
            # Ищем организации: ООО, АО, ПАО, ЗАО, ИП и т.д.
            # Сначала пробуем найти с кавычками
            owner_match = re.search(
                r'(ООО|АО|ПАО|ЗАО|ОАО|ИП|ГУП|МУП|ФГУП)\s+([«"][^»"]+[»"])',
                part, re.IGNORECASE)
            if owner_match:
                # Извлекаем полное название организации с кавычками
                org_type = owner_match.group(1)
                org_name = owner_match.group(2).strip()
                # Убираем внешние кавычки, оставляя внутренние
                org_name = org_name.strip('«»""')
                result['owner'] = f'{org_type} {org_name}'
                owner_found = True
                break

            # Если не нашли с кавычками, ищем без них
            owner_match = re.search(
                r'(ООО|АО|ПАО|ЗАО|ОАО|ИП|ГУП|МУП|ФГУП)\s+([^\|,\n]+?)(?=\s*(?:Площадь|кв\.км|\||$))',
                part, re.IGNORECASE)
            if owner_match:
                # Извлекаем название организации без кавычек
                org_type = owner_match.group(1)
                org_name = owner_match.group(2).strip()
                result['owner'] = f'{org_type} {org_name}'
                owner_found = True
                break

        if not owner_found:
            # Если не нашли по паттерну, пробуем взять из второй или третьей части
            if len(parts) > 2:
                result['owner'] = parts[2].strip()
            elif len(parts) > 1 and 'Площадь' not in parts[1]:
                result['owner'] = parts[1].strip()
            else:
                result['owner'] = 'Не указан'

        # Даты - ищем во всех частях описания
        for part in parts:
            # Дата выдачи (форматы: "Дата выдачи: 01.01.2020" или "Выдана: 01.01.2020")
            if not result['issue_date']:
                date_match = re.search(r'(?:Дата\s+выдачи|Выдана|Дата\s+оформления):\s*(\d{2}\.\d{2}\.\d{4})', part, re.IGNORECASE)
                if date_match:
                    result['issue_date'] = date_match.group(1)
            
            # Дата окончания (форматы: "Дата окончания: 01.01.2025" или "Действует до: 01.01.2025")
            if not result['expiry_date']:
                expiry_match = re.search(r'(?:Дата\s+окончания|Действует\s+до|До):\s*(\d{2}\.\d{2}\.\d{4})', part, re.IGNORECASE)
                if expiry_match:
                    result['expiry_date'] = expiry_match.group(1)
            
            # Вид полезного ископаемого (форматы: "Полезное ископаемое: Золото" или "Ископаемое: Золото")
            if not result['mineral_type']:
                mineral_match = re.search(r'(?:Полезное\s+ископаемое|Ископаемое|Вид\s+ископаемого):\s*([А-Яа-яёЁ\s\-]+?)(?:\||$)', part, re.IGNORECASE)
                if mineral_match:
                    result['mineral_type'] = mineral_match.group(1).strip()

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
        """
        Вычисляет центр полигона или мультиполигона
        Для MultiPolygon учитывает все полигоны
        """
        if not coordinates or len(coordinates) == 0:
            return None

        all_points = []
        
        if geom_type == 'MultiPolygon':
            # Для MultiPolygon собираем точки из всех полигонов
            for polygon_coords in coordinates:
                if polygon_coords and len(polygon_coords) > 0:
                    # Берём внешний контур каждого полигона
                    outer_ring = polygon_coords[0]
                    if outer_ring and len(outer_ring) > 0:
                        all_points.extend(outer_ring)
        else:
            # Для Polygon берём внешний контур
            outer_ring = coordinates[0]
            if outer_ring and len(outer_ring) > 0:
                all_points.extend(outer_ring)

        if not all_points:
            return None

        lon_sum = sum(coord[0] for coord in all_points)
        lat_sum = sum(coord[1] for coord in all_points)
        count = len(all_points)

        return [lon_sum / count, lat_sum / count]

    def merge_polygons(self, existing_geometry, new_geometry):
        """
        Объединяет два полигона в MultiPolygon
        
        Args:
            existing_geometry: существующая геометрия (Polygon или MultiPolygon)
            new_geometry: новая геометрия для добавления (Polygon или MultiPolygon)
        
        Returns:
            объединённая геометрия типа MultiPolygon (всегда)
        """
        # Список всех полигонов
        all_polygons = []
        
        # Добавляем существующие полигоны (если есть)
        if existing_geometry and existing_geometry.get('coordinates'):
            existing_type = existing_geometry.get('type', 'Polygon')
            if existing_type == 'MultiPolygon':
                all_polygons.extend(existing_geometry['coordinates'])
            elif existing_type == 'Polygon':
                all_polygons.append(existing_geometry['coordinates'])
        
        # Добавляем новые полигоны
        if new_geometry and new_geometry.get('coordinates'):
            new_type = new_geometry.get('type', 'Polygon')
            if new_type == 'MultiPolygon':
                all_polygons.extend(new_geometry['coordinates'])
            elif new_type == 'Polygon':
                all_polygons.append(new_geometry['coordinates'])
        
        # Всегда возвращаем как MultiPolygon
        return {
            'type': 'MultiPolygon',
            'coordinates': all_polygons
        }
    
    def extract_region(self, license_number):
        """Извлекает название региона из префикса номера лицензии"""
        regions = {
            'МАГ': 'Магаданская область',
            'КЕМ': 'Кемеровская область',
            'ПЕМ': 'Пермский край',
            'ЧИТ': 'Забайкальский край',
            'ЮСХ': 'Сахалинская область',
            'ИРК': 'Иркутская область',
            'БЛГ': 'Амурская область',
            'ХАБ': 'Хабаровский край',
            'КРР': 'Красноярский край',
            'УДЭ': 'Республика Бурятия',
            'ЯКУ': 'Республика Саха (Якутия)',
            'ТЮМ': 'Тюменская область',
            'ВЛВ': 'Приморский край',
            'АБН': 'Республика Хакасия'
        }

        prefix = license_number[:3]
        return regions.get(prefix, 'Регион не определён')
