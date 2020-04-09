from django.urls import path, include
from .views import *

urlpatterns = [
	path('', IndexPage.as_view(), name='index_page_url'),
	path('payment_request/', PaymentRequest.as_view(), name='payment_request_url'),
	path('payment_confirmation/', PaymentConfirmation.as_view(), name='payment_confirmation_url'),
]
