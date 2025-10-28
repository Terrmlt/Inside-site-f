import json
from django.core.management.base import BaseCommand
from licenses.utils import GeoJSONImporter


class Command(BaseCommand):
    help = 'Импорт лицензий из GeoJSON файла'

    def add_arguments(self, parser):
        parser.add_argument('geojson_file', type=str, help='Путь к GeoJSON файлу')

    def handle(self, *args, **options):
        geojson_file = options['geojson_file']
        
        self.stdout.write(self.style.SUCCESS(f'Загрузка данных из {geojson_file}...'))
        
        try:
            with open(geojson_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            features = data.get('features', [])
            self.stdout.write(f'Найдено объектов: {len(features)}')
            
            importer = GeoJSONImporter()
            result = importer.import_from_file(data)
            
            self.stdout.write(self.style.SUCCESS(f'\n=== Итоги импорта ==='))
            self.stdout.write(self.style.SUCCESS(f'Создано новых: {result["imported"]}'))
            self.stdout.write(self.style.SUCCESS(f'Обновлено: {result["updated"]}'))
            self.stdout.write(self.style.WARNING(f'Пропущено: {result["skipped"]}'))
            self.stdout.write(self.style.SUCCESS(f'Всего обработано: {result["total"]}'))
            
            if result['errors']:
                self.stdout.write(self.style.WARNING(f'\nВозникли предупреждения:'))
                for error in result['errors']:
                    self.stdout.write(self.style.WARNING(f'  - {error}'))
                    
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл не найден: {geojson_file}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Файл не является корректным JSON'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при обработке файла: {str(e)}'))
