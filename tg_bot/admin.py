from django.contrib import admin

from .forms import ProfileForm
from .models import *


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'external_id', 'name', 'balance', 'promo_code')
    form = ProfileForm


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_from', 'user_to', 'text', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'date', 'deadline', 'status')


@admin.register(OrderFeedback)
class OrderFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'freelancer', 'date', 'price')


# @admin.register(FreelanceApplication)
# class FreelanceApplicationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'profile', 'date')


@admin.register(MoneyOutRequest)
class MoneyOutRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'date', 'sum', 'status')


@admin.register(MoneyInRequest)
class MoneyInRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'date', 'sum', 'status')
