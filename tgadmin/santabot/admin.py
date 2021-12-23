from django.contrib import admin

from .models import User
from .models import Event


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'creator',
        'created_at',
        'cost_range',
        'last_register_date',
        'sending_date',
    )
