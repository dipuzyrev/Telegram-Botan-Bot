from django.shortcuts import render, redirect
from django.views.generic import View, FormView
from django.contrib.auth import authenticate, login
from django.contrib import messages
import requests

from .models import *
from .forms import *
from .management.commands.bot import payment_message, chat_message


class PaymentRequest(FormView):
	"""
	Send payment request
	"""
	template_name = 'tg_bot/payment_request.html'
	success_url = '/'
	form_class = PaymentRequestForm

	def form_valid(self, form):
		payment_message(form.cleaned_data['price'], form.cleaned_data['chat_id'], form.cleaned_data['tasks_count'],
						form.cleaned_data['good'], form.cleaned_data['bad'])
		return super(PaymentRequest, self).form_valid(form)

	def form_invalid(self, form):
		return super(PaymentRequest, self).form_invalid(form)


class PaymentConfirmation(FormView):
	"""
	Send payment confirmation
	"""
	template_name = 'tg_bot/payment_confirmation.html'
	success_url = '/'
	form_class = PaymentConfirmationForm

	def form_valid(self, form):
		chat_message(form.cleaned_data['chat_id'], form.cleaned_data['chat_number'])
		return super(PaymentConfirmation, self).form_valid(form)

	def form_invalid(self, form):
		return super(PaymentConfirmation, self).form_invalid(form)


class IndexPage(View):
	template = 'tg_bot/index.html'

	def get(self, request):
		URL = "https://money.yandex.ru/api/instance-id"

		# defining a params dict for the parameters to be sent to the API
		data = {'client_id': 'C991DB674E05CAA680300A74455AC1D1A1A702F8522C7F0CDA7972C4D6F1B6F6'}


		# sending get request and saving the response as response object
		r = requests.post(url=URL, data=data)

		# extracting data in json format
		data = r.json()

		return render(request, template_name=self.template, context={'data': data})

