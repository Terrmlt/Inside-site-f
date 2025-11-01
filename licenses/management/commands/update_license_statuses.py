from django.core.management.base import BaseCommand
from licenses.models import License
from datetime import date


class Command(BaseCommand):
    help = 'Обновляет статусы всех лицензий, у которых истек срок действия'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Показать детальную информацию по каждой обновленной лицензии',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write(self.style.WARNING('Начало проверки статусов лицензий...'))
        
        # Получаем все активные лицензии
        active_licenses = License.objects.filter(status='active')
        total_active = active_licenses.count()
        
        self.stdout.write(f'Найдено активных лицензий: {total_active}')
        
        # Счетчики
        updated_count = 0
        today = date.today()
        
        # Проходим по всем активным лицензиям
        for license in active_licenses:
            if license.expiry_date and license.expiry_date < today:
                license.status = 'expired'
                license.save(update_fields=['status'])
                updated_count += 1
                
                if verbose:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Обновлена лицензия {license.license_number} '
                            f'(срок истек {license.expiry_date})'
                        )
                    )
        
        # Итоговая статистика
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Обновление завершено!'))
        self.stdout.write(f'Всего проверено лицензий: {total_active}')
        self.stdout.write(
            self.style.WARNING(f'Обновлено статусов: {updated_count}')
            if updated_count > 0
            else self.style.SUCCESS('Обновлено статусов: 0 (все лицензии актуальны)')
        )
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Дополнительная статистика по всем лицензиям
        all_licenses = License.objects.all()
        stats = {
            'active': all_licenses.filter(status='active').count(),
            'expired': all_licenses.filter(status='expired').count(),
            'suspended': all_licenses.filter(status='suspended').count(),
            'terminated': all_licenses.filter(status='terminated').count(),
        }
        
        self.stdout.write('\nТекущая статистика:')
        self.stdout.write(f'  Действующие: {stats["active"]}')
        self.stdout.write(f'  Истекшие: {stats["expired"]}')
        self.stdout.write(f'  Приостановленные: {stats["suspended"]}')
        self.stdout.write(f'  Прекращенные: {stats["terminated"]}')
        self.stdout.write(f'  Всего: {all_licenses.count()}')
