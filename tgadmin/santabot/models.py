from django.db import models

class User(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name='User ID',
    )
    name = models.TextField(
        verbose_name='User name',
    )

    def __str__(self):
        return f'#{self.external_id} - {self.name}'

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователя'


class Event(models.Model):
    name = models.TextField(
        verbose_name='Название игры',
    )
    creator = models.ForeignKey(
        to='santabot.User',
        verbose_name='Создатель',
        on_delete=models.PROTECT,
    )
    created_at = models.DateTimeField(
        verbose_name='Время создания',
        auto_now_add=True,
    )
    cost_range = models.TextField(
        verbose_name='Ценовой диапозон',
        blank=True,
    )
    last_register_date = models.TextField(
        verbose_name='Последний день регистрации',
    )
    sending_date = models.TextField(
        verbose_name='Дата отправки подарка',
    )

    def __str__(self):
        return f'Игра {self.name}, созданная пользователем {self.creator}'

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'
