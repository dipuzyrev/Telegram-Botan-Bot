from django.shortcuts import render, redirect
from django.views.generic import View, FormView
from django.contrib.auth import authenticate, login
from django.contrib import messages
import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from .models import *
from .forms import *
from .management.commands.bot import *


class PaymentRequest(FormView):
	"""
	Send payment request
	"""
	template_name = 'tg_bot/payment_request.html'
	success_url = '/'
	form_class = PaymentRequestForm

	def form_valid(self, form):
		# payment_message(form.cleaned_data['price'], form.cleaned_data['chat_id'], form.cleaned_data['tasks_count'],
		# 				form.cleaned_data['good'], form.cleaned_data['bad'])
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
		# chat_message(form.cleaned_data['chat_id'], form.cleaned_data['chat_number'])
		return super(PaymentConfirmation, self).form_valid(form)

	def form_invalid(self, form):
		return super(PaymentConfirmation, self).form_invalid(form)


class MoneyOutRequestConfirmation(FormView):
	"""
	Send money out request confirmation
	"""
	template_name = 'tg_bot/simple_form.html'
	success_url = '/'
	form_class = MoneyOutRequestConfirmationForm

	def form_valid(self, form):
		id = form.cleaned_data['request_id']
		out_request = MoneyOutRequest.objects.filter(id=id)
		if out_request:
			out_request = out_request[0]
		else:
			return super(MoneyOutRequestConfirmation, self).form_invalid(form)  # TODO: send error message

		chat_id = out_request.profile.external_id
		p = Profile.objects.get(external_id=chat_id)
		p.balance -= out_request.sum
		p.save()

		out_request.status = 'done'
		out_request.save()

		request = Request(
			connect_timeout=5,
			read_timeout=1.0,
		)

		bot = Bot(
			request=request,
			token=settings.TOKEN,
			base_url=getattr(settings, 'PROXY_URL', None),
		)

		notify_user(bot, chat_id, '', 'money_out_success.png', None)
		return super(MoneyOutRequestConfirmation, self).form_valid(form)

	def form_invalid(self, form):
		return super(MoneyOutRequestConfirmation, self).form_invalid(form)


class ApproveOrder(FormView):
	"""
	Notify freelancers about new order by keywords
	"""
	template_name = 'tg_bot/simple_form.html'
	success_url = '/'
	form_class = ApproveOrderForm

	def form_valid(self, form):
		order_id = form.cleaned_data['order_id']

		order = Order.objects.get(id=order_id)
		order.status = 'approved'
		order.save()

		notify_freelancers_by_keywords(order_id)

		return super(ApproveOrder, self).form_valid(form)

	def form_invalid(self, form):
		return super(ApproveOrder, self).form_invalid(form)


class MessageFromSupport(FormView):
	"""
	Send message from support
	"""
	template_name = 'tg_bot/simple_form.html'
	success_url = '/'
	form_class = MessageFromSupportForm

	def form_valid(self, form):
		user_id = form.cleaned_data['user_id']
		text = form.cleaned_data['text']

		user_from = get_profile(settings.ADMIN_CHAT_ID)
		user_to = get_profile(user_id)

		Message.objects.create(
			user_from=user_from,
			user_to=user_to,
			text=text,
			related_to=-1,
		)

		request = Request(
			connect_timeout=5,
			read_timeout=1.0,
		)

		bot = Bot(
			request=request,
			token=settings.TOKEN,
			base_url=getattr(settings, 'PROXY_URL', None),
		)

		notify_user(bot, user_id, '', 'new_support_message.png', None,
					[[InlineKeyboardButton(f'Открыть', callback_data='SUPPORT_CHAT')]])

		return super(MessageFromSupport, self).form_valid(form)

	def form_invalid(self, form):
		return super(MessageFromSupport, self).form_invalid(form)


class LeaveOrderFeedback(FormView):
	"""
	Send order feedback
	"""
	template_name = 'tg_bot/simple_form.html'
	success_url = '/'
	form_class = OrderFeedbackForm

	def form_valid(self, form):
		order_id = form.cleaned_data['order_id']
		price = form.cleaned_data['price']
		comment = form.cleaned_data['comment']

		admin = get_profile(settings.ADMIN_CHAT_ID)

		order = Order.objects.get(id=order_id)
		customer = order.customer

		OrderFeedback.objects.create(
			freelancer=admin,
			comment=comment,
			price=price,
			order=order
		)

		request = Request(
			connect_timeout=5,
			read_timeout=1.0,
		)

		bot = Bot(
			request=request,
			token=settings.TOKEN,
			base_url=getattr(settings, 'PROXY_URL', None),
		)

		notify_user(
			bot,
			customer.external_id,
			'',
			'new_order_feedback.png',
			None,
			[[InlineKeyboardButton(f'Подробнее', callback_data='VIEW_ORDER:' + str(order.id))]]
		)

		return super(LeaveOrderFeedback, self).form_valid(form)

	def form_invalid(self, form):
		return super(LeaveOrderFeedback, self).form_invalid(form)


class PaymentForm(View):
	template = 'tg_bot/payment_form.html'

	def get(self, request, order_id):
		order = Order.objects.get(id=order_id)

		if order.status == 'paid':
			return redirect('https://t.me/yourBotanBot')

		price = order.price
		sum = price / 0.98

		return render(request, template_name=self.template, context={
			'order_id': order.id,
			'sum': sum,
		})


class PaymentSuccess(View):
	def post(self, request):
		amount = request.POST['amount']
		label = request.POST['label']
		notification_type = request.POST['notification_type']
		currency = request.POST['currency']
		datetime = request.POST['datetime']
		sender = request.POST['sender']
		codepro = request.POST['codepro']
		operation_id = request.POST['operation_id']

		notification_secret = '+dLfOJAzqopkYT1+iXeLj3rM'

		str = f'{notification_type}&{operation_id}&{amount}&' \
			  f'{currency}&{datetime}&{sender}&{codepro}&{notification_secret}&{label}'

		h = hashlib.sha1(str.encode('utf-8')).hexdigest()

		if h == request.POST['sha1_hash']:
			order = Order.objects.get(id=int(label))

			request = Request(
				connect_timeout=5,
				read_timeout=1.0,
			)

			bot = Bot(
				request=request,
				token=settings.TOKEN,
				base_url=getattr(settings, 'PROXY_URL', None),
			)

			if order.status == 'approved' and (order.price - 1) <= float(amount):
				order.status = 'paid'
				order.save()

				notify_user(
					bot,
					order.customer.external_id,
					'',
					'order_paid.png',
					None,
					[[InlineKeyboardButton(f'Открыть заказ', callback_data='VIEW_ORDER:' + str(order.id))]]
				)
			else:
				notify_user(
					bot,
					order.customer.external_id,
					'Что-то пошло не так... Но мы уже работаем над этим.',
				)
				notify_admin(
					bot,
					'Что-то пошло не так... Order ID: ' + str(order.id),
				)

			return HttpResponse('', status_code=200)


class IndexPage(View):
	template = 'tg_bot/index.html'

	def get(self, request):
		return render(request, template_name=self.template)

