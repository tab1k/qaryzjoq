from django.db import models


class Lead(models.Model):
    """Заявка на бесплатную консультацию с лендинга."""

    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_WORK = 'in_work', 'В работе'
        DONE = 'done', 'Обработана'

    name = models.CharField('Имя', max_length=120)
    phone = models.CharField('Телефон', max_length=32)
    debt = models.CharField('Сумма долга', max_length=64, blank=True)
    message = models.TextField('Сообщение', blank=True)
    status = models.CharField('Статус', max_length=16, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField('Создана', auto_now_add=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.name} — {self.phone}'
