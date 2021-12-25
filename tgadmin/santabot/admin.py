from django.contrib import admin

from .models import User
from .models import Event
from .models import Participant
from .models import Interests


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


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'event',
        'user',
        'phone_number',
        'letter_for_santa',
    )


@admin.register(Interests)
class InterestsAdmin(admin.ModelAdmin):
    list_display = ('id', 'participant', 'interest')
