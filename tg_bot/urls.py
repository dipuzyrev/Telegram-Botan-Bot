from django.urls import path, include
from .views import *

urlpatterns = [
	path('', IndexPage.as_view(), name='index_page_url'),
	path('payment_request/', PaymentRequest.as_view(), name='payment_request_url'),
	path('payment_confirmation/', PaymentConfirmation.as_view(), name='payment_confirmation_url'),
	path('money_out_request_confirmation/', MoneyOutRequestConfirmation.as_view(),
			name='money_out_request_confirmation_url'),
	path('approve_order/', ApproveOrder.as_view(), name='approve_order_url'),
	path('message_from_support/', MessageFromSupport.as_view(), name='message_from_support_url'),
	path('order_feedback/', LeaveOrderFeedback.as_view(), name='order_feedback_url'),
	path('pay/<int:order_id>', PaymentForm.as_view(), name='payment_form_url'),
	path('payment_success/', PaymentSuccess.as_view(), name='payment_success_url'),
]
