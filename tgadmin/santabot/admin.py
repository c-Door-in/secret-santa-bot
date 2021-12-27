from django.contrib import admin
from django.db.models import fields

from .models import User, Event, Participant, Interests, Pairs


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
    fields = (
        'user',
        'name',
        'event',
        'phone_number',
        'letter_for_santa',
        'interests',
    )


@admin.register(Interests)
class InterestsAdmin(admin.ModelAdmin):
    list_display = ('id', 'interest')


@admin.register(Pairs)
class PairsAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'donor', 'receiver')
