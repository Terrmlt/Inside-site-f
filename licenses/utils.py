
import json
from datetime import datetime
from .models import License


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
            'total': len(features),
            'errors': self.errors
        }

    def _process_feature(self, feature):
        """
        Обрабатывает один объект GeoJSON и создает/обновляет лицензию
        """
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})

        # Извлекаем номер лицензии
        license_number = properties.get('Номер лицензии') or properties.get('license_number')
        
        if not license_number:
            self.errors.append('Пропущен объект без номера лицензии')
            self.skipped_count += 1
            return

        # Извлекаем координаты центра полигона
        coordinates = self._extract_center_coordinates(geometry)

        # Проверяем, существует ли лицензия
        license_obj, created = License.objects.update_or_create(
            license_number=license_number,
            defaults={
                'license_type': properties.get('Вид пользования недрами') or properties.get('license_type', ''),
                'owner': properties.get('Недропользователь') or properties.get('owner', ''),
                'region': properties.get('Регион') or properties.get('region', ''),
                'area': properties.get('Участок недр') or properties.get('area', ''),
                'mineral_type': properties.get('Полезное ископаемое') or properties.get('mineral_type', ''),
                'status': properties.get('status', 'active'),
                'description': properties.get('Описание') or properties.get('description', ''),
                'latitude': coordinates.get('latitude'),
                'longitude': coordinates.get('longitude'),
                'polygon_data': geometry,  # Сохраняем весь полигон
                'issue_date': self._parse_date(properties.get('Дата выдачи') or properties.get('issue_date')),
                'expiry_date': self._parse_date(properties.get('Дата окончания') or properties.get('expiry_date')),
            }
        )

        if created:
            self.imported_count += 1
        else:
            self.updated_count += 1

    def _extract_center_coordinates(self, geometry):
        """
        Извлекает координаты центра из геометрии полигона
        """
        if not geometry or geometry.get('type') != 'Polygon':
            return {'latitude': None, 'longitude': None}

        coordinates = geometry.get('coordinates', [[]])[0]
        
        if not coordinates:
            return {'latitude': None, 'longitude': None}

        # Вычисляем центр полигона
        lats = [coord[1] for coord in coordinates if len(coord) >= 2]
        lons = [coord[0] for coord in coordinates if len(coord) >= 2]

        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            return {'latitude': center_lat, 'longitude': center_lon}

        return {'latitude': None, 'longitude': None}

    def _parse_date(self, date_str):
        """
        Парсит дату из строки в разных форматах
        """
        if not date_str:
            return None

        # Пытаемся распарсить разные форматы дат
        date_formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']
        
        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except (ValueError, TypeError):
                continue

        return None
