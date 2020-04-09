from django.contrib import admin

from .forms import ProfileForm
from .models import *


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name')
    form = ProfileForm


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'text', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'date', 'deadline', 'status', 'chat')


@admin.register(FreelanceApplication)
class FreelanceApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'date')
