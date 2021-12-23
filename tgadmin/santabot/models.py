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
