from django.db import models

class User(models.Model):
    external_id = models.PositiveIntegerField(
        verbose_name='ID',
    )
    name = models.TextField(
        verbose_name='TG Nickname',
    )

    def __str__(self):
        return f'#{self.external_id} - {self.name}'

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователя'


class Event(models.Model):
    name = models.CharField(
        max_length=39,
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
    cost_range = models.CharField(
        max_length=30,
        verbose_name='Ценовой диапозон',
        blank=True,
    )
    last_register_date = models.DateTimeField(
        verbose_name='Последний день регистрации',
    )
    sending_date = models.DateTimeField(
        verbose_name='Дата отправки подарка',
    )

    def __str__(self):
        return f'Игра {self.name}, созданная пользователем {self.creator}'

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'


class Interests(models.Model):
    interest = models.CharField(
        max_length=30,
        verbose_name='Интерес',
        unique=True,
    )

    def __str__(self):
        return f'{self.interest}'

    class Meta:
        verbose_name = 'Интерес'
        verbose_name_plural = 'Интересы'


class Participant(models.Model):
    event = models.ForeignKey(
        to='santabot.Event',
        verbose_name='Игра',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        to='santabot.User',
        verbose_name='Имя участника',
        on_delete=models.CASCADE,
    )
    phone_number = models.CharField(
        max_length=30,
        verbose_name='Номер телефона'
    )
    letter_for_santa = models.TextField(
        verbose_name='Письмо Санте',
        blank=True,
    )
    interests = models.ManyToManyField(
        Interests,
        verbose_name='Интересы',
    )

    def __str__(self):
        return f'{self.user} - игра {self.event}'

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'
