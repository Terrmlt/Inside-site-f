from django.db import models
from django.contrib.auth.models import User


class License(models.Model):
    """
    Модель для хранения информации о лицензиях на недропользование
    """
    license_number = models.CharField(max_length=100, unique=True, verbose_name="Номер лицензии")
    license_type = models.CharField(max_length=200, verbose_name="Вид пользования недрами")
    owner = models.CharField(max_length=300, verbose_name="Недропользователь")
    
    # Геолокация для отображения на карте
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Широта", null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Долгота", null=True, blank=True)
    
    # Полигон (контур лицензии) в формате GeoJSON
    polygon_data = models.JSONField(verbose_name="Данные полигона (GeoJSON)", null=True, blank=True)
    
    # Информация о территории
    region = models.CharField(max_length=200, verbose_name="Регион")
    area = models.CharField(max_length=300, verbose_name="Участок недр", blank=True)
    
    # Даты
    issue_date = models.DateField(verbose_name="Дата выдачи")
    expiry_date = models.DateField(verbose_name="Дата окончания", null=True, blank=True)
    
    # Дополнительная информация
    mineral_type = models.CharField(max_length=200, verbose_name="Вид полезного ископаемого", blank=True)
    status = models.CharField(
        max_length=50, 
        choices=[
            ('active', 'Действующая'),
            ('expired', 'Истекла'),
            ('suspended', 'Приостановлена'),
            ('terminated', 'Прекращена'),
        ],
        default='active',
        verbose_name="Статус"
    )
    
    
    description = models.TextField(verbose_name="Описание", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления записи")
    
    class Meta:
        verbose_name = "Лицензия"
        verbose_name_plural = "Лицензии"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.license_number} - {self.owner}"

    def update_status_if_expired(self):
        """
        Проверяет и обновляет статус лицензии, если срок действия истек
        """
        from datetime import date
        
        if self.expiry_date and self.expiry_date < date.today():
            if self.status == 'active':
                self.status = 'expired'
                self.save(update_fields=['status'])
        
        return self.status


class Document(models.Model):
    """
    Модель для хранения документов, связанных с лицензиями
    """
    license = models.ForeignKey(
        License, 
        on_delete=models.CASCADE, 
        related_name='documents',
        verbose_name="Лицензия"
    )
    title = models.CharField(max_length=300, verbose_name="Название документа")
    file = models.FileField(upload_to='license_documents/', verbose_name="Файл")
    file_type = models.CharField(
        max_length=50,
        choices=[
            ('license', 'Лицензия'),
            ('report', 'Отчет'),
            ('map', 'Карта'),
            ('other', 'Прочее'),
        ],
        default='other',
        verbose_name="Тип документа"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Загрузил пользователь"
    )
    
    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} ({self.license.license_number})"
