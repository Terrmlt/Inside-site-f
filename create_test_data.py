import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mineral_licenses.settings')
django.setup()

from licenses.models import License
from datetime import date, timedelta

def create_test_licenses():
    test_licenses = [
        {
            'license_number': 'МСК-12345-НЕ',
            'license_type': 'Геологическое изучение',
            'owner': 'ООО "ГеоРесурс"',
            'latitude': 55.7558,
            'longitude': 37.6173,
            'region': 'Московская область',
            'area': 'Участок №1, Московская область',
            'issue_date': date(2023, 1, 15),
            'expiry_date': date(2028, 1, 15),
            'mineral_type': 'Нефть',
            'status': 'active',
            'description': 'Лицензия на геологическое изучение с целью поиска и оценки нефти в Московской области.'
        },
        {
            'license_number': 'ТЮМ-67890-ДЭ',
            'license_type': 'Добыча полезных ископаемых',
            'owner': 'ПАО "СибирьНефть"',
            'latitude': 57.1531,
            'longitude': 65.5343,
            'region': 'Тюменская область',
            'area': 'Западно-Сибирский участок',
            'issue_date': date(2020, 5, 10),
            'expiry_date': date(2040, 5, 10),
            'mineral_type': 'Природный газ',
            'status': 'active',
            'description': 'Лицензия на добычу природного газа в Западной Сибири.'
        },
        {
            'license_number': 'КРС-24680-НЕ',
            'license_type': 'Геологическое изучение',
            'owner': 'АО "Красноярскгеология"',
            'latitude': 56.0090,
            'longitude': 92.8725,
            'region': 'Красноярский край',
            'area': 'Енисейский участок',
            'issue_date': date(2022, 3, 20),
            'expiry_date': date(2027, 3, 20),
            'mineral_type': 'Уголь',
            'status': 'active',
            'description': 'Лицензия на геологическое изучение угольных месторождений.'
        },
        {
            'license_number': 'СВР-13579-ДЭ',
            'license_type': 'Добыча полезных ископаемых',
            'owner': 'ООО "Северные минералы"',
            'latitude': 67.5558,
            'longitude': 33.3974,
            'region': 'Мурманская область',
            'area': 'Кольский участок',
            'issue_date': date(2021, 8, 15),
            'expiry_date': date(2031, 8, 15),
            'mineral_type': 'Апатиты',
            'status': 'active',
            'description': 'Лицензия на добычу апатитов на Кольском полуострове.'
        },
        {
            'license_number': 'ЯКУ-98765-НЕ',
            'license_type': 'Геологическое изучение',
            'owner': 'ЗАО "Якутские алмазы"',
            'latitude': 62.0339,
            'longitude': 129.7422,
            'region': 'Республика Саха (Якутия)',
            'area': 'Вилюйский участок',
            'issue_date': date(2019, 11, 1),
            'expiry_date': date(2024, 11, 1),
            'mineral_type': 'Алмазы',
            'status': 'suspended',
            'description': 'Лицензия на геологическое изучение алмазных месторождений (приостановлена).'
        },
        {
            'license_number': 'УРЛ-11223-ДЭ',
            'license_type': 'Добыча полезных ископаемых',
            'owner': 'ПАО "УралРуда"',
            'latitude': 56.8389,
            'longitude': 60.6057,
            'region': 'Свердловская область',
            'area': 'Уральский участок',
            'issue_date': date(2018, 2, 25),
            'expiry_date': date(2023, 2, 25),
            'mineral_type': 'Железная руда',
            'status': 'expired',
            'description': 'Лицензия на добычу железной руды (истекла).'
        },
    ]
    
    for license_data in test_licenses:
        License.objects.get_or_create(
            license_number=license_data['license_number'],
            defaults=license_data
        )
    
    print(f"Создано {len(test_licenses)} тестовых лицензий")

if __name__ == '__main__':
    create_test_licenses()
    print("Тестовые данные успешно созданы!")
