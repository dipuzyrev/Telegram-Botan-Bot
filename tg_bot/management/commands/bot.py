from django.core.management.base import BaseCommand
from django.conf import settings
from enum import Enum
import random
import string
import pytz
from pprint import pprint

from telegram import Bot
from telegram import Update
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import Updater
from telegram.utils.request import Request

from tg_bot.models import *


''' --------------------
	Global variables
-------------------- '''


# Available bot states
class State(Enum):
	START_MENU = 1
	SHOW_STATS = 2
	SETTINGS = 3
	EDIT_KEYWORDS = 4
	BALANCE = 5
	PLUS_MONEY = 6
	MINUS_MONEY = 7
	MINUS_MONEY_SENT = 8
	SUPPORT_CHAT = 9
	NEW_ORDER_STEP1_SUBJECT = 10
	NEW_ORDER_STEP2_TYPE = 11
	NEW_ORDER_STEP3_DEADLINE = 12
	NEW_ORDER_STEP4_PLAGIARISM = 13
	NEW_ORDER_STEP5_DESCRIPTION = 14
	NEW_ORDER_STEP5_DESCRIPTION_EMPTY = 15
	NEW_ORDER_STEP6_SENT = 16
	CURRENT_ORDERS = 17
	ORDER_DETAILS = 18
	ORDER_CANCELED = 19
	ORDER_FEEDBACK_STEP1_PRICE = 20
	ORDER_FEEDBACK_STEP2_COMMENT = 21
	ORDER_FEEDBACK_STEP3_SENT = 22
	ORDER_FEEDBACK_APPROVE = 23
	ORDER_CONFIRM_FINISHING = 24
	ORDER_CLOSE = 25
	ORDER_CHAT = 26


# Keyboard buttons
btn_new_order = '📝 Новый заказ'
btn_current_orders = '⏳️ Текущие'
btn_send_order = '⬆️ Отправить заказ'
btn_balance = '💵 Баланс'
btn_statistics = '🔢 Статистика'
btn_settings = '⚙️ Настройки'
btn_support = '👨‍💻 Поддержка'
btn_back = '← Назад'
btn_edit_keywords = '🔑 Редактировать'
btn_setup_keywords = '🔑 Задать ключевые слова'
btn_remove_keywords = '🧹 Очистить'
btn_balance_minus = '💸 Вывести'
btn_file = '📎 Файл'
btn_show_files = '📎 Показать файлы'
btn_open_order = '📝 Заказ'
btn_cancel_order = '❌ Отменить заказ'
btn_select_freelancer = '👉 Выбрать заявку'
btn_chat_with_freelancer = '💬 Чат с исполнителем'
btn_chat_with_customer = '💬 Чат с заказчиком'
btn_confirm_order_finishing = '✅ Подтвердить выполнение'
btn_send_feedback = '👍 Возьмусь'
btn_balance_management = '💵 Управление балансом'
btn_ok = '👌 ОК'
btn_rating_1 = '🤬 1'
btn_rating_2 = '☹️ 2'
btn_rating_3 = '😏 3'
btn_rating_4 = '🙂 4'
btn_rating_5 = '🤗 5'

# Keyboards
back_keyboard = [[btn_back]]
send_order_keyboard = [[btn_send_order], [btn_back]]


''' -----------------
	Start command
----------------- '''


class Command(BaseCommand):
	help = 'Botan Bot'

	def handle(self, *args, **options):
		request = Request(
			connect_timeout=5,
			read_timeout=1.0,
		)

		bot = Bot(
			request=request,
			token=settings.TOKEN,
			base_url=getattr(settings, 'PROXY_URL', None),
		)

		updater = Updater(
			bot=bot,
			use_context=True,
		)

		updater.dispatcher.add_handler(CommandHandler('start', do_start))
		updater.dispatcher.add_handler(MessageHandler(Filters.text, new_message))
		updater.dispatcher.add_handler(MessageHandler(Filters.document, new_document))
		updater.dispatcher.add_handler(MessageHandler(Filters.photo, new_photo))
		updater.dispatcher.add_handler(CallbackQueryHandler(new_callback_query))

		updater.start_polling()
		updater.idle()


def log_errors(f):
	def inner(*args, **kwargs):
		try:
			return f(*args, **kwargs)
		except Exception as e:
			error_message = f'Error in {f.__name__}(): {e}'
			print(error_message)
			raise e
	return inner


''' ------------
	Handlers
------------ '''


@log_errors
def do_start(update: Updater, context: CallbackContext):
	setup_context(update, context)

	update.message.reply_html(
		text='Коротко про самые основные кнопки:\n\n'
			 '📝 <b>Новый заказ</b> — создаёшь задание и ждёшь заявок от исполнителей. Затем выбираешь нужную, '
			 'оплачиваешь и получаешь результат.\n\n'
			 '⚙️ <b>Настройки</b> — здесь можно задать ключевые слова и начать получать уведомления о новых заказах. '
			 'Естественно, чтобы их выполнять и зарабатывать деньги.'
			 '👨‍💻 <b>Поддержка</b> — смело обращайся к нам с любой проблемой, идеей или предложением!',
		reply_markup=ReplyKeyboardMarkup(build_start_keyboard(context), True, True),
	)


@log_errors
def new_message(update: Updater, context: CallbackContext):

	if not 'chat_id' in context.user_data:
		setup_context(update, context)

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']
	text = update.message.text
	save_state_log = True

	# Admin replies to user's message to support chat
	if update.message.reply_to_message:
		notification_text = update.message.reply_to_message.text or update.message.reply_to_message.caption
		admin_text = update.message.text

		# Parse user's data
		lines = notification_text.split('\n')
		user_chat_id = lines[0][1:].strip()

		send_message_to_chat(context, chat_id, user_chat_id, -1, admin_text)
		return

	# Match user's message with available states
	if text == btn_back:
		go_back(context)
		show_state(update, context)
	else:
		if text == btn_statistics:
			context.user_data['state'] = State.SHOW_STATS

		elif text == btn_settings:
			context.user_data['state'] = State.SETTINGS

		elif text == btn_edit_keywords or text == btn_setup_keywords:
			context.user_data['state'] = State.EDIT_KEYWORDS

		elif text == btn_remove_keywords:
			p = get_profile(context.user_data['chat_id'], context.user_data['username'])
			p.keywords = ''
			p.save()
			save_state_log = False

		elif text == btn_balance:
			context.user_data['state'] = State.BALANCE

		elif text == btn_balance_minus:
			profile = get_profile(context.user_data['chat_id'])
			processing_request = MoneyOutRequest.objects.filter(profile=profile, status='processing')

			if not profile.balance:
				update.message.reply_html(text='Хм, выводить-то пока нечего...')
				return
			elif processing_request:
				update.message.reply_html(text='Уже выводятся, надо только чуть-чуть подождать.')
			else:
				context.user_data['state'] = State.MINUS_MONEY

		elif text == btn_support:
			context.user_data['state'] = State.SUPPORT_CHAT

		elif btn_file in text:
			send_file_from_chat(update, context, text)
			return

		elif text == btn_new_order:
			context.user_data['state'] = State.NEW_ORDER_STEP1_SUBJECT

		elif text == btn_send_order:
			if not context.user_data['forms_data']['new_order_form']['step5']['text']:
				context.user_data['state'] = State.NEW_ORDER_STEP5_DESCRIPTION_EMPTY
			else:
				send_order(context)
				context.user_data['state'] = State.NEW_ORDER_STEP6_SENT

		elif btn_current_orders in text:
			context.user_data['state'] = State.CURRENT_ORDERS

		elif btn_open_order in text:
			order_index = int(text.split('№')[1]) - 1
			if 0 <= order_index < len(context.user_data['orders_list']):
				context.user_data['state'] = State.ORDER_DETAILS
				context.user_data['current_order'] = context.user_data['orders_list'][order_index]

		elif text == btn_cancel_order:
			if context.user_data['current_order']:
				context.user_data['current_order'].status = 'canceled'
				context.user_data['current_order'].save()
				context.user_data['state'] = State.ORDER_CANCELED
			else:
				return

		elif text == btn_send_feedback:
			context.user_data['state'] = State.ORDER_FEEDBACK_STEP1_PRICE

		elif btn_select_freelancer in text:
			feedback_index = int(text.split('№')[1]) - 1
			if 0 <= feedback_index < len(context.user_data['feedback_list']):
				context.user_data['state'] = State.ORDER_FEEDBACK_APPROVE
				context.user_data['current_feedback'] = context.user_data['feedback_list'][feedback_index]
				save_state_log = False

		elif text == btn_ok:
			pay_for_order(context)
			go_back(context)
			save_state_log = False

		elif text == btn_confirm_order_finishing:
			context.user_data['state'] = State.ORDER_CONFIRM_FINISHING

		elif text == btn_rating_1 \
			or text == btn_rating_2 \
			or text == btn_rating_3 \
			or text == btn_rating_4 \
			or text == btn_rating_5:
			context.user_data['order_rating'] = 1
			if text == btn_rating_2:
				context.user_data['order_rating'] = 2
			elif text == btn_rating_3:
				context.user_data['order_rating'] = 3
			elif text == btn_rating_4:
				context.user_data['order_rating'] = 4
			elif text == btn_rating_5:
				context.user_data['order_rating'] = 5

			context.user_data['state'] = State.ORDER_CLOSE

		elif text == btn_show_files:
			send_order_files(update, context)
			return

		elif text == btn_chat_with_freelancer or text == btn_chat_with_customer:
			context.user_data['state'] = State.ORDER_CHAT

		else:
			if context.user_data['state'] == State.EDIT_KEYWORDS:
				save_state_log = False
				save_keywords(context, text)
				go_back(context)

			elif context.user_data['state'] == State.MINUS_MONEY:
				result = add_money_out_request(context, text)
				if result:
					context.user_data['state'] = State.MINUS_MONEY_SENT

			elif context.user_data['state'] == State.SUPPORT_CHAT:
				send_message_to_chat(context, chat_id, settings.ADMIN_CHAT_ID, -1, text, None, None)
				save_state_log = False

			elif context.user_data['state'] == State.ORDER_CHAT:
				order = context.user_data['current_order']
				user_from = order.customer
				user_to = order.freelancer
				if order.freelancer.external_id == chat_id:
					user_from = order.freelancer
					user_to = order.customer
				send_message_to_chat(context, user_from.external_id, user_to.external_id, order.id, text, None, None)
				save_state_log = False

			elif context.user_data['state'] == State.NEW_ORDER_STEP1_SUBJECT:
				context.user_data['forms_data']['new_order_form']['step1'] = text
				context.user_data['state'] = State.NEW_ORDER_STEP2_TYPE

			elif context.user_data['state'] == State.NEW_ORDER_STEP2_TYPE:
				context.user_data['forms_data']['new_order_form']['step2'] = text
				context.user_data['state'] = State.NEW_ORDER_STEP3_DEADLINE

			elif context.user_data['state'] == State.NEW_ORDER_STEP3_DEADLINE:
				context.user_data['forms_data']['new_order_form']['step3'] = text
				context.user_data['state'] = State.NEW_ORDER_STEP4_PLAGIARISM

			elif context.user_data['state'] == State.NEW_ORDER_STEP4_PLAGIARISM:
				context.user_data['forms_data']['new_order_form']['step4'] = text
				context.user_data['state'] = State.NEW_ORDER_STEP5_DESCRIPTION

			elif context.user_data['state'] == State.NEW_ORDER_STEP5_DESCRIPTION:
				if not context.user_data['forms_data']['new_order_form']['step5']['text']:
					context.user_data['forms_data']['new_order_form']['step5']['text'] = text
				else:
					context.user_data['forms_data']['new_order_form']['step5']['text'] += '\n' + text
				return

			elif context.user_data['state'] == State.ORDER_FEEDBACK_STEP1_PRICE:
				price = parse_int_abs(text)
				if price:
					context.user_data['forms_data']['order_feedback_form']['step1'] = price
					context.user_data['state'] = State.ORDER_FEEDBACK_STEP2_COMMENT
				else:
					update.message.reply_html(text='Введи пожалуйста только число, никаких лишних знаков.')
					return

			elif context.user_data['state'] == State.ORDER_FEEDBACK_STEP2_COMMENT:
				context.user_data['forms_data']['order_feedback_form']['step2'] = text
				send_order_feedback(context)
				context.user_data['state'] = State.ORDER_FEEDBACK_STEP3_SENT

			else:
				go_to_start(update, context)
				return

		show_state(update, context, save_state_log)


@log_errors
def new_document(update: Update, context: CallbackContext):

	if not 'chat_id' in context.user_data:
		setup_context(update, context)

	file_id = update.message.document['file_id']
	caption = update.message.caption
	chat_id = context.user_data['chat_id']

	if context.user_data['state'] == State.SUPPORT_CHAT:
		send_message_to_chat(context, context.user_data['chat_id'], settings.ADMIN_CHAT_ID, -1, caption, file_id, None)
		show_state(update, context)

	elif context.user_data['state'] == State.ORDER_CHAT:
		order = context.user_data['current_order']
		user_from = order.customer
		user_to = order.freelancer
		if order.freelancer.external_id == chat_id:
			user_from = order.freelancer
			user_to = order.customer

		send_message_to_chat(context, user_from.external_id, user_to.external_id, order.id, caption, file_id, None)
		show_state(update, context)

	elif context.user_data['state'] == State.NEW_ORDER_STEP5_DESCRIPTION:
		text = caption if caption else ''

		files_count = len(context.user_data['forms_data']['new_order_form']['step5']['files'].split(',,'))

		if context.user_data['forms_data']['new_order_form']['step5']['text']:
			context.user_data['forms_data']['new_order_form']['step5']['text'] += '\n' + text if text else '\n'
		else:
			context.user_data['forms_data']['new_order_form']['step5']['text'] = text

		context.user_data['forms_data']['new_order_form']['step5']['text'] += f' [Файл {files_count}]'
		context.user_data['forms_data']['new_order_form']['step5']['files'] += 'document,' + file_id + ',,'

	return


@log_errors
def new_photo(update: Update, context: CallbackContext):

	if not 'chat_id' in context.user_data:
		setup_context(update, context)

	photo_id = update.message.photo[-1]['file_id']
	caption = update.message.caption
	chat_id = context.user_data['chat_id']

	if context.user_data['state'] == State.SUPPORT_CHAT:
		send_message_to_chat(context, context.user_data['chat_id'], settings.ADMIN_CHAT_ID, -1, caption, None, photo_id)
		show_state(update, context)

	elif context.user_data['state'] == State.ORDER_CHAT:
		order = context.user_data['current_order']
		user_from = order.customer
		user_to = order.freelancer
		if order.freelancer.external_id == chat_id:
			user_from = order.freelancer
			user_to = order.customer

		send_message_to_chat(context, user_from.external_id, user_to.external_id, order.id, caption, None, photo_id)
		show_state(update, context)

	elif context.user_data['state'] == State.NEW_ORDER_STEP5_DESCRIPTION:
		text = caption if caption else ''

		files_count = len(context.user_data['forms_data']['new_order_form']['step5']['files'].split(',,'))

		if context.user_data['forms_data']['new_order_form']['step5']['text']:
			context.user_data['forms_data']['new_order_form']['step5']['text'] += '\n' + text if text else '\n'
		else:
			context.user_data['forms_data']['new_order_form']['step5']['text'] = text

		context.user_data['forms_data']['new_order_form']['step5']['text'] += f' [Файл {files_count}]'
		context.user_data['forms_data']['new_order_form']['step5']['files'] += 'photo,' + photo_id + ',,'

	return


@log_errors
def new_callback_query(update: Updater, context: CallbackContext):

	if not 'chat_id' in context.user_data:
		setup_context(update.callback_query, context)

	data = update.callback_query.data

	if data == 'SUPPORT_CHAT':
		if context.user_data['state'] != State.SUPPORT_CHAT:
			context.user_data['state'] = State.SUPPORT_CHAT
			context.user_data['states_log'].append(context.user_data['state'])

		update.callback_query.message.delete()

		update.callback_query.message.reply_text(
			text=get_support_chat_state_text(context),
			parse_mode='HTML',
			reply_markup=ReplyKeyboardMarkup(build_chat_keyboard(context), True),
		)

	elif 'ORDER_CHAT' in data:
		order_id = data.split(':')[1]
		context.user_data['current_order'] = Order.objects.get(id=order_id)

		if context.user_data['state'] != State.ORDER_CHAT:
			context.user_data['state'] = State.ORDER_CHAT
			context.user_data['states_log'].append(context.user_data['state'])

		update.callback_query.message.delete()

		update.callback_query.message.reply_html(
			text=get_order_chat_state_text(context),
			reply_markup=ReplyKeyboardMarkup(build_chat_keyboard(context), True),
		)

	elif 'VIEW_ORDER' in data:
		id = int(data.split(':')[1])
		order = Order.objects.get(id=id)
		if order:
			update.callback_query.message.delete()

			context.user_data['current_order'] = order
			context.user_data['state'] = State.ORDER_DETAILS
			show_state(update.callback_query, context)
		else:
			update.callback_query.answer('Что-то пошло не так...')
			return

	elif data == 'BALANCE':
		context.user_data['state'] = State.BALANCE
		show_state(update.callback_query, context)

	update.callback_query.answer()


''' ------------------
	Help functions
------------------ '''


@log_errors
def setup_context(update, context):
	context.user_data['chat_id'] = update.message.chat_id
	context.user_data['username'] = update.message.from_user.username or update.message.from_user.id
	context.user_data['state'] = State.START_MENU
	context.user_data['states_log'] = []
	context.user_data['current_order'] = None
	context.user_data['current_feedback'] = None
	context.user_data['current_files'] = []
	context.user_data['orders_list'] = []
	context.user_data['feedback_list'] = []

	context.bot_data['forms'] = {
		'new_order_form': {
			'step1': '<b>📚 Какой предмет?</b>\n\n<b>Например:</b>\n• История\n• Физика\n• Экология',
			'step2': '<b>📃 Тип работы?</b>\n\n<b>Например:</b>\n• Реферат\n• Презентация\n• Диплом',
			'step3': '<b>🕑 Какой срок?</b>\n\n<b>Например:</b>\n• 6 апреля в 15:20\n• Неделя\n• Дедлайн сегодня',
			'step4': '<b>🔎 Нужен ли антиплагиат?</b>\n\n<b>Например:</b>\n• Да, от 75% в antiplagiat.ru\n• Не нужен',
			'step5': '<b>✍️ Описание</b>\n\n<b>Например:</b>\n'
					 'Тема реферата: «Внешняя политика Ивана Грозного». Минимум 15 страниц формата А4. Шрифт 14, '
					 'Times New Roman. Обязательно сослаться на 3 исторических документа.\n\n'
					 '<i>Это финальный шаг. Опиши пожалуйста заказ как можно подробнее, чтобы исполнители могли '
					 'адекватно его оценить. Файлы тоже прикрепляй, если есть. Как закончишь, жми кнопку отправки.</i>'
		},
		'order_feedback_form': {
			'step1': '<b>💵 Стоимость выполнения?</b>\n\n<b>Например:</b>\n• 500\n\n'
					 '<i>Комиссия сервиса – 10%. Например, если укажешь 500₽, заработаешь 450₽.</i>',
			'step2': '<b>✍️ Комментарий к заявке</b>\n\n<b>Например:</b>\nДобрый день! Я преподаватель истории, '
					 'профессионально выполню задание в соответствии со всеми требованиями.'
		}
	}

	context.user_data['forms_data'] = {
		'new_order_form': {
			'step1': '',
			'step2': '',
			'step3': '',
			'step4': '',
			'step5': {
				'text': '',
				'files': '',
			}
		},
		'order_feedback_form': {
			'step1': '',
			'step2': ''
		}
	}


@log_errors
def show_state(update, context, add_to_log=True):
	"""
	Shows specified bot's state
	:param update: update
	:param context: callback context
	:param add_to_log: add state to log or not
	:return:
	"""

	state_to_show = context.user_data['state']

	if add_to_log:
		if len(context.user_data['states_log']) > 0:
			if state_to_show != context.user_data['states_log'][len(context.user_data['states_log']) - 1]:
				context.user_data['states_log'].append(state_to_show)
		else:
			context.user_data['states_log'].append(state_to_show)

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']

	if state_to_show == State.START_MENU:
		update.message.reply_html(
			text=f'🎛 Главное меню',
			reply_markup=ReplyKeyboardMarkup(build_start_keyboard(context), True, True),
		)

	elif state_to_show == State.SHOW_STATS:
		update.message.reply_html(
			text=get_statistics_state_text(context),
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True),
		)

	elif state_to_show == State.SETTINGS:
		update.message.reply_html(
			text=get_settings_state_text(context),
			reply_markup=ReplyKeyboardMarkup(build_settings_keyboard(context), True),
		)

	elif state_to_show == State.EDIT_KEYWORDS:
		p = get_profile(chat_id, username)

		update.message.reply_html(
			text='🔑 <b>Ключевые слова через запятую</b>\n\n'
				 '<b>Например:</b>\n• Информатика, программирование\n'
				 '• Презентация, реферат, доклад',
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True),
		)

	elif state_to_show == State.BALANCE:
		update.message.reply_html(
			text=get_balance_state_text(context),
			reply_markup=ReplyKeyboardMarkup(build_balance_keyboard(context), True),
		)

	elif state_to_show == State.MINUS_MONEY:
		update.message.reply_html(
			text='💸 <b>Куда выводим?</b>\n\n<b>Например:</b>\n'
				 '• Сбербанк – 1234567891011121\n'
				 '• Яндекс Деньги – 123456789101112',
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True),
		)

	elif state_to_show == State.MINUS_MONEY_SENT:
		go_back(context)
		go_back(context)
		show_state(update, context)

	elif state_to_show == State.SUPPORT_CHAT:
		update.message.reply_html(
			text=get_support_chat_state_text(context),
			reply_markup=ReplyKeyboardMarkup(build_chat_keyboard(context), True)
		)

	elif state_to_show == State.NEW_ORDER_STEP1_SUBJECT:
		update.message.reply_html(
			text=context.bot_data['forms']['new_order_form']['step1'],
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True)
		)

	elif state_to_show == State.NEW_ORDER_STEP2_TYPE:
		update.message.reply_html(
			text=context.bot_data['forms']['new_order_form']['step2'],
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True)
		)

	elif state_to_show == State.NEW_ORDER_STEP3_DEADLINE:
		update.message.reply_html(
			text=context.bot_data['forms']['new_order_form']['step3'],
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True)
		)

	elif state_to_show == State.NEW_ORDER_STEP4_PLAGIARISM:
		update.message.reply_html(
			text=context.bot_data['forms']['new_order_form']['step4'],
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True)
		)

	elif state_to_show == State.NEW_ORDER_STEP5_DESCRIPTION:
		update.message.reply_html(
			text=context.bot_data['forms']['new_order_form']['step5'],
			reply_markup=ReplyKeyboardMarkup(send_order_keyboard, True)
		)

	elif state_to_show == State.NEW_ORDER_STEP5_DESCRIPTION_EMPTY:
		update.message.reply_html(
			text="Подожди-ка, а где описание?",
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True)
		)
		go_back(context)
		show_state(update, context)

	elif state_to_show == State.NEW_ORDER_STEP6_SENT:
		update.message.reply_html(
			text="Заказ принят, скоро начнут поступать заявки от исполнителей.",
			reply_markup=ReplyKeyboardMarkup(build_start_keyboard(context), True, True)
		)
		context.user_data['state'] = State.START_MENU

	elif state_to_show == State.CURRENT_ORDERS:
		update.message.reply_html(
			text=get_current_orders_state_text(context),
			reply_markup=ReplyKeyboardMarkup(build_current_orders_keyboard(context), True)
		)

	elif state_to_show == State.ORDER_DETAILS:
		details = get_order_details_state(context)

		for text in details:
			if text:
				update.message.reply_html(
					text=text,
					reply_markup=ReplyKeyboardMarkup(build_order_details_keyboard(context), True)
				)

	elif state_to_show == State.ORDER_CANCELED:
		update.message.reply_html(
			text='Ок, заказ отменён.',
			reply_markup=ReplyKeyboardMarkup(build_start_keyboard(context), True, True)
		)

	elif state_to_show == State.ORDER_FEEDBACK_STEP1_PRICE:
		update.message.reply_html(
			text=context.bot_data['forms']['order_feedback_form']['step1'],
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True)
		)

	elif state_to_show == State.ORDER_FEEDBACK_STEP2_COMMENT:
		update.message.reply_html(
			text=context.bot_data['forms']['order_feedback_form']['step2'],
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True)
		)

	elif state_to_show == State.ORDER_FEEDBACK_STEP3_SENT:
		update.message.reply_html(
			text='Отлично, заявка отправлена.',
			reply_markup=ReplyKeyboardMarkup(build_start_keyboard(context), True, True)
		)
		context.user_data['state'] = State.START_MENU

	elif state_to_show == State.ORDER_FEEDBACK_APPROVE:
		price = context.user_data['current_feedback'].price
		order_id = context.user_data['current_order'].id

		context.user_data['current_order'].price = price
		context.user_data['current_order'].freelancer = context.user_data['current_feedback'].freelancer
		context.user_data['current_order'].save()

		update.message.reply_html(
			text='Отлично! Осталось оплатить заказ и исполнитель начнёт работу.',
			reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
				f'Оплатить {price}₽', url=f'https://yourbotan.ru/pay/{order_id}'
			)]])
		)

	elif state_to_show == State.ORDER_CONFIRM_FINISHING:
		update.message.reply_html(
			text='На сколько ты оценишь исполнителя?',
			reply_markup=ReplyKeyboardMarkup(
				[[btn_rating_1, btn_rating_2, btn_rating_3, btn_rating_4, btn_rating_5], [btn_back]],
				True)
		)

	elif state_to_show == State.ORDER_CLOSE:
		update.message.reply_html(text='Спасибо за оценку!')
		confirm_order_finishing(context)
		go_to_start(update, context)

	elif state_to_show == State.ORDER_CHAT:
		update.message.reply_html(
			text=get_order_chat_state_text(context),
			reply_markup=ReplyKeyboardMarkup(build_chat_keyboard(context), True)
		)


@log_errors
def notify_admin(bot, text, photo=None, document=None, inline_buttons=None):
	"""
	Notifies admin about client's actions
	:param text: notification text
	:return:
	"""

	user_chat_id = settings.ADMIN_CHAT_ID
	notify_user(bot, user_chat_id, text, photo, document, inline_buttons)


@log_errors
def notify_user(bot, user_chat_id, text, photo=None, document=None, inline_buttons=None):
	"""
	Notifies user about something
	:param context: callback context
	:param user_chat_id: user's chat id to notify
	:param text: notification text
	:param inline_buttons: callback buttons if needed
	:return:
	"""

	if inline_buttons:
		if photo:
			bot.send_photo(
				chat_id=user_chat_id,
				caption=text,
				photo=open(settings.BASE_DIR + '/static/img/' + photo, 'rb'),
				parse_mode='HTML',
				reply_markup=InlineKeyboardMarkup(inline_buttons)
			)
		elif document:
			bot.send_document(
				chat_id=user_chat_id,
				caption=text,
				document=open(settings.BASE_DIR + '/static/img/' + document, 'rb'),
				parse_mode='HTML',
				reply_markup=InlineKeyboardMarkup(inline_buttons)
			)
		else:
			bot.send_message(
				chat_id=user_chat_id,
				text=text,
				parse_mode='HTML',
				reply_markup=InlineKeyboardMarkup(inline_buttons)
			)
	else:
		if photo:
			bot.send_photo(
				chat_id=user_chat_id,
				caption=text,
				photo=open(settings.BASE_DIR + '/static/img/' + photo, 'rb'),
				parse_mode='HTML',
			)
		elif document:
			bot.send_document(
				chat_id=user_chat_id,
				caption=text,
				document=open(settings.BASE_DIR + '/static/img/' + document, 'rb'),
				parse_mode='HTML',
			)
		else:
			bot.send_message(
				chat_id=user_chat_id,
				text=text,
				parse_mode='HTML',
			)


@log_errors
def notify_freelancers_by_keywords(order_id):
	freelancers = Profile.objects.all().exclude(keywords='')
	order = Order.objects.get(id=order_id)

	request = Request(
		connect_timeout=5,
		read_timeout=1.0,
	)

	bot = Bot(
		request=request,
		token=settings.TOKEN,
		base_url=getattr(settings, 'PROXY_URL', None),
	)

	for freelancer in freelancers:
		keywords = freelancer.keywords.split(',')

		for keyword in keywords:
			if keyword.strip().lower() in (order.subject + order.type + order.description).lower():
				notify_user(
					bot,
					freelancer.external_id,
					f'📚 <b>{order.subject}, {order.type.lower()}</b>\n\n'
					f'{order.description}',
					'new_order_by_keywords.png',
					None,
					[[InlineKeyboardButton(f'Подробнее', callback_data='VIEW_ORDER:'+str(order.id))]]
				)
				break


@log_errors
def send_file_from_chat(update, context, button):
	"""
	Sends file to user after clicking btn_file
	:param update: update
	:param context: callback context
	:param button: btn_file + 'file number'
	:return:
	"""

	file_number = int(button[len(btn_file):].strip())
	file_index = file_number - 1

	if 0 <= file_index < len(context.user_data['current_files']):
		file = context.user_data['current_files'][file_index]

		if file[1] == 'photo':
			update.message.reply_photo(photo=file[0])
		else:
			update.message.reply_document(document=file[0])


@log_errors
def send_order_files(update, context):
	"""
	Sends files to freelancer
	:param update: update
	:param context: callback context
	:return:
	"""

	files = context.user_data['current_files']

	for file in files:
		if file[1] == 'photo':
			update.message.reply_photo(photo=file[0])
		else:
			update.message.reply_document(document=file[0])


@log_errors
def get_profile(profile_chat_id, profile_username=None):
	"""
	Gets profile from database or creates new
	:param profile_chat_id: chat id
	:param profile_username: username
	:return:
	"""

	if not profile_username:
		profile_username = profile_chat_id

	profile, _ = Profile.objects.get_or_create(
		external_id=profile_chat_id,
		defaults={
			'name': profile_username,
			'promo_code': generate_promo_code(),
		}
	)

	return profile


@log_errors
def generate_promo_code():
	"""
	Generates unique promo code
	:return: promo code like 'AB1234'
	"""

	letters = string.ascii_uppercase
	numbers = '123456789'

	while True:
		code = ''.join(random.choice(letters) for _ in range(2))
		code += ''.join(random.choice(numbers) for _ in range(4))

		duplicates = Profile.objects.filter(promo_code=code)
		if not duplicates:
			return code


@log_errors
def save_bank_card_number(context, card_number):
	"""
	Saves card number
	:param context: callback context
	:param card_number: number of bank card
	:return:
	"""

	profile = get_profile(context.user_data['chat_id'])
	profile.card_number = card_number
	profile.save()


@log_errors
def save_keywords(context, keywords):
	"""
	Saves keywords
	:param context: callback context
	:param keywords: words, separated by comma
	:return:
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']
	profile = get_profile(chat_id, username)

	words = keywords.split(',')
	unique_words = []
	for word in words:
		word = word.strip().lower()
		if not word in unique_words:
			unique_words.append(word)

	profile.keywords = ','.join(unique_words)
	profile.save()


@log_errors
def add_money_out_request(context, requisites):
	"""
	Adds request to database and notifies admin
	:param context: callback context
	:param requisites: requisites
	:return: True if success and False if there already processing requests in database from this user
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']
	profile = get_profile(chat_id, username)

	processing = MoneyOutRequest.objects.filter(profile=profile, status='processing')

	if not processing:
		request = MoneyOutRequest.objects.create(profile=profile, sum=profile.balance, requisites=requisites)

		# TODO: create tg:// link if no username
		notify_admin(
			context.bot,
			f'<a href="{settings.ADMIN_DOMAIN}/admin/tg_bot/moneyoutrequest/{request.id}/change/">'
			f'Новая заявка</a> на вывод {profile.balance}₽ от @{username}.'
		)
		return True

	return False


@log_errors
def delete_money_out_request(context):
	"""
	Removes request from database
	:param context: callback context
	:return: True if removed or False if not found
	"""

	profile = get_profile(context.user_data['chat_id'], context.user_data['username'])
	processing = MoneyOutRequest.objects.get(profile=profile, status='processing')

	if processing:
		processing.delete()
		return True

	return False


@log_errors
def go_back(context):
	"""
	Go back to previous state
	:param context: callback context
	:return:
	"""

	if len(context.user_data['states_log']) > 0:
		context.user_data['states_log'] = context.user_data['states_log'][:-1]

	if len(context.user_data['states_log']) > 0:
		context.user_data['state'] = context.user_data['states_log'][len(context.user_data['states_log']) - 1]
	else:
		context.user_data['state'] = State.START_MENU


@log_errors
def go_to_start(update, context):
	"""
	Go back to previous state
	:param update: update
	:param context: callback context
	:return:
	"""

	context.user_data['state'] = State.START_MENU
	context.user_data['state_log'] = []
	show_state(update, context, False)


@log_errors
def send_message_to_chat(context, from_chat_id, to_chat_id, related_to, text, document_id=None, photo_id=None):
	"""
	Saves message to database and notifies receiver
	:param context: callback context
	:param from_chat_id: sender
	:param to_chat_id: receiver
	:param related_to: order_id or -1 if support chat (current case)
	:param text: message text
	:param document_id: document id if file sent
	:param photo_id: photo id if photo send
	:return:
	"""

	bot = context.bot
	chat_id = context.user_data['chat_id']
	username = context.user_data['username']

	user_from = get_profile(from_chat_id)
	user_to = get_profile(to_chat_id)

	Message.objects.create(
		user_from=user_from,
		user_to=user_to,
		text=text,
		related_to=related_to,
		file_id=document_id,
		photo_id=photo_id
	)

	if related_to == -1:
		if str(from_chat_id) == settings.ADMIN_CHAT_ID:
			# Send notification to user
			notify_user(context.bot, to_chat_id, '', 'message_from_support.png', None,
						[[InlineKeyboardButton(f'Открыть', callback_data='SUPPORT_CHAT')]])
		else:
			# Send notification to admin
			message_text = '#' + str(chat_id) + '\n@' + str(username) + '\n\n' + str(text or '')

			if document_id:
				bot.send_document(chat_id=settings.ADMIN_CHAT_ID, document=document_id, caption=message_text)
			elif photo_id:
				bot.send_photo(chat_id=settings.ADMIN_CHAT_ID, photo=photo_id, caption=message_text)
			else:
				bot.send_message(
					chat_id=settings.ADMIN_CHAT_ID,
					text=message_text,
					parse_mode='HTML')
	else:
		order = Order.objects.get(id=related_to)
		img = 'message_from_customer.png' if user_to == order.freelancer else 'message_from_freelancer.png'

		notify_user(context.bot, to_chat_id, '', img, None,
					[[InlineKeyboardButton(f'Открыть', callback_data='ORDER_CHAT:' + str(related_to))]])


@log_errors
def send_order(context):
	"""
	Saves order to database and notifies freelancers
	:param context: callback context
	:return:
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']

	profile = get_profile(chat_id, username)
	new_order_form = context.user_data['forms_data']['new_order_form']

	subject = new_order_form['step1']
	new_order_form['step1'] = ''

	type = new_order_form['step2']
	new_order_form['step2'] = ''

	deadline = new_order_form['step3']
	new_order_form['step3'] = ''

	plagiarism = new_order_form['step4']
	new_order_form['step4'] = ''

	description = new_order_form['step5']['text']
	new_order_form['step5']['text'] = ''

	files = new_order_form['step5']['files'] or None
	new_order_form['step5']['files'] = ''

	order = Order.objects.create(
		customer=profile,
		subject=subject,
		type=type,
		deadline=deadline,
		description=description,
		plagiarism=plagiarism,
		files=files,
		status='new',
	)



	# TODO: create tg:// link for username
	notify_admin(
		context.bot,
		f'<a href="{settings.ADMIN_DOMAIN}/admin/tg_bot/order/{order.id}/change/">Новый заказ</a> от @{username}.\n\n'
		f'📚 <b>{order.subject}, '
		f'{order.type.lower()}</b>\n\n'
		f'{order.description}',
		None,
		None,
		[[InlineKeyboardButton(f'Подробнее', callback_data='VIEW_ORDER:' + str(order.id))]]
	)


@log_errors
def send_order_feedback(context):
	"""
	Saves feedback to database and notifies customer
	:param context: callback context
	:return:
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']

	freelancer = get_profile(chat_id, username)
	order_feedback_form = context.user_data['forms_data']['order_feedback_form']

	price = order_feedback_form['step1']
	order_feedback_form['step1'] = ''

	comment = order_feedback_form['step2']
	order_feedback_form['step2'] = ''

	order = context.user_data['current_order']

	OrderFeedback.objects.create(
		freelancer=freelancer,
		comment=comment,
		price=price,
		order=order
	)

	notify_user(
		context.bot,
		order.customer.external_id,
		'', 'new_feedback.png', None,
		[[InlineKeyboardButton(f'Подробнее', callback_data='VIEW_ORDER:' + str(order.id))]]
	)


@log_errors
def pay_for_order(order_id):
	"""
	Makes payment and updates database
	:param order_id: order id
	:return:
	"""

	order = Order.objects.get(id=order_id)
	order.status = 'paid'


@log_errors
def confirm_order_finishing(context):
	"""
	Makes payment and updates database
	:param context: callback context
	:return:
	"""

	order = context.user_data['current_order']
	freelancer = order.freelancer

	freelancer.balance += round(order.price * 0.9)
	freelancer.save()

	order.status = 'done'
	order.rate = context.user_data['order_rating']
	order.save()

	notify_user(
		context.bot,
		freelancer.external_id,
		'',
		'order_completed.png',
		None,
		[[InlineKeyboardButton(f'Открыть баланс', callback_data='BALANCE')]]
	)

	context.user_data['order_rating'] = None


''' -------------------------
	State text generators
------------------------- '''


@log_errors
def get_statistics_state_text(context):
	"""
	Creates text for statistics state
	:param context: callback context
	:return: created text
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']

	p = get_profile(chat_id, username)
	orders_as_customer = Order.objects.filter(customer=p, status='done')
	orders_as_freelancer = Order.objects.filter(freelancer=p, status='done')

	as_customer_count = orders_as_customer.count()
	as_customer_sum = 0
	for order in orders_as_customer:
		if order.price:
			as_customer_sum += order.price

	as_freelancer_count = orders_as_freelancer.count()
	as_freelancer_sum = 0
	as_freelancer_rating = 0
	for order in orders_as_freelancer:
		if order.price:
			as_freelancer_sum += order.price
		if order.rate:
			as_freelancer_rating += order.rate
	as_freelancer_rating = 0 if not as_freelancer_count else (as_freelancer_rating / as_freelancer_count)

	rating = round(as_freelancer_rating, 1)

	stars = ''
	for _ in range(round(rating)):
		stars += '★'

	for _ in range(5-round(rating)):
		stars += '☆'

	as_freelancer_sum = round(as_freelancer_sum * 0.9)


	text = '🔢🔢🔢\n\n' \
			f'<b>Исполнитель:</b>\n' \
			f'{stars} <b>({rating})</b>\n' \
			f'• {get_right_number_label(as_freelancer_count, ["Выполнено", "Выполнен", "Выполнено"])} ' \
		    f'{as_freelancer_count} ' \
		   	f'{get_right_number_label(as_freelancer_count, ["заказов", "заказ", "заказа"])}\n' \
		    f'• {get_right_number_label(as_freelancer_sum, ["Заработано", "Заработан", "Заработано"])} ' \
		    f'{as_freelancer_sum}₽\n' \
			f'• Средний чек – ' \
		    f'{0 if not as_freelancer_count else round(as_freelancer_sum / as_freelancer_count)}₽\n\n' \
			f'<b>Заказчик:</b>\n' \
			f'• {get_right_number_label(as_customer_count, ["Размещено", "Размещён", "Размещено"])} ' \
		    f'{as_customer_count} ' \
		   	f'{get_right_number_label(as_customer_count, ["заказов", "заказ", "заказа"])}\n' \
		    f'• {get_right_number_label(as_customer_sum, ["Выплачено", "Выплачен", "Выплачено"])} ' \
		    f'{as_customer_sum}₽\n' \
			f'• Средний чек – {0 if not as_customer_count else round(as_customer_sum / as_customer_count)}₽'

	return text


@log_errors
def get_settings_state_text(context):
	"""
	Creates text for settings state
	:param context: callback context
	:return: created text
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']

	p = get_profile(chat_id, username)
	# card_number = '<b>' + str(p.card_number) + '</b>\n' if p.card_number else '<b><i>Не задано</i></b>\n'

	keywords = ''

	text = '⚙️⚙️⚙️\n\nКлючевые слова:\n'

	if p.keywords:
		for word in p.keywords.split(','):
			keywords += f'<b>• {word.strip().capitalize()}</b>\n'
	else:
		keywords = '<b>• Не настроены</b>\n'

	return text + keywords + '\nЕсли хочешь зарабатывать на выполнении заказов – задай ключевые слова. Например, это ' \
							 'могут быть определённые предметы или типы заданий. Как только они встретятся в новом ' \
							 'заказе, тебе придёт уведомление.'


@log_errors
def get_balance_state_text(context):
	"""
	Creates text for balance state
	:param context: callback context
	:return: created text
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']

	p = get_profile(chat_id, username)

	word = get_right_number_label(p.balance, ['рублей', 'рубль', 'рубля'])

	text = '💵💵💵\n\n'
	text += f'<b>Баланс: {p.balance}₽</b>\n\n'

	text += 'Сюда падает твой заработок с выполнения заказов. Для вывода просто нажми кнопку и укажи реквизиты.'

	# if not p.balance:
	# 	text += ' Как только тут будет не ноль, появится кнопка для вывода.'

	money_out_request = MoneyOutRequest.objects.filter(profile=p, status='processing')
	if money_out_request:
		money_out_request = money_out_request[0]
		word = get_right_number_label(money_out_request.sum, ['рублей', 'рубля', 'рублей'])
		text += f'\n\n<i>Заявка на вывод {money_out_request.sum}₽ будет обработана в течение суток.</i>'

	# if p.promo_code:
	# 	orders = Order.objects.filter(promo_code=p.promo_code, status='done')
	# 	count = orders.count()
	# 	sum = 0
	#
	# 	for order in orders:
	# 		if order.price:
	# 			sum += order.price
	#
	# 	sum = round(sum * 0.1)
	#
	# 	word = get_right_number_label(sum, ['раз', 'раз', 'раза'])
	#
	# 	text += f'Промокод: <b>{p.promo_code}</b>\n'
	# 	text += f'Использован {count} {word}\n'
	# 	text += f'Начислено {sum}₽\n\n'
	# 	text += 'Промокодом <s>можно</s> нужно делиться с друзьями. Друг получит 10% скидку, а ты — 5% на свой счёт.'

	return text


@log_errors
def get_current_orders_state_text(context):
	"""
	Creates text for current orders state
	:param context: callback context
	:return: created text
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']

	profile = get_profile(chat_id, username)

	customer_orders = list(Order.objects.filter(customer=profile).exclude(status='done').exclude(status='canceled'))
	freelancer_orders = list(Order.objects.filter(freelancer=profile, status='paid'))

	context.user_data['orders_list'] = customer_orders + freelancer_orders
	orders_list = context.user_data['orders_list']

	if customer_orders and freelancer_orders:
		text = '<b>Ты – заказчик:</b>'
	else:
		text = ''

	order_counter = 0
	for order in customer_orders:
		order_counter += 1
		text += f'\n\n📝 <b>Заказ №{order_counter}</b>\n'
		text += f'📚 {order.subject}, {order.type.lower()}\n'
		text += '⚡️ '

		if order.status == 'new':
			text += 'На модерации'
		elif order.status == 'approved':
			text += 'Поиск исполнителя'
		elif order.status == 'paid':
			text += 'Выполняется'
		else:
			text += 'Неизвестно'

	if customer_orders and freelancer_orders:
		text += '\n\n——\n\n<b>Ты – исполнитель:</b>'

	for order in freelancer_orders:
		order_counter += 1
		text += f'\n\n📝 <b>Заказ №{order_counter}</b>\n'
		text += f'📚 {order.subject}, {order.type.lower()}\n'
		text += '⚡️ '

		if order.status == 'new':
			text += 'На модерации'
		elif order.status == 'approved':
			text += 'Поиск исполнителя'
		elif order.status == 'paid':
			text += 'Выполняется'
		else:
			text += 'Неизвестно'

		# feedbacks = OrderFeedback.objects.filter(order=orders_list[i]).count()
		# word = get_right_number_label(feedbacks, ['заявок', 'заявка', 'заявки'])
		#
		# if orders_list[i].status == 'approved':
		# 	text += f' ({feedbacks})'

	if not text:
		text = '\n\nЗдесь пока пусто...'

	return text


@log_errors
def get_support_chat_state_text(context):
	"""
	Creates text for support chat state
	:param context: callback context
	:return: created text
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']
	context.user_data['current_files'] = []

	profile = get_profile(chat_id, username)
	admin_p = get_profile(settings.ADMIN_CHAT_ID, settings.ADMIN_USERNAME)

	m_from = list(Message.objects.filter(
		related_to=-1, user_from=profile, user_to=admin_p).order_by('-created_at'))

	m_to = list(Message.objects.filter(
		related_to=-1, user_from=admin_p, user_to=profile).order_by('-created_at'))

	messages = m_from + m_to
	messages.sort(key=lambda x: x.created_at, reverse=False)

	end_caption = '<i>Чтобы написать в чат, просто отправь сообщение или файл.</i>'

	chat = []
	chat_len = 0
	is_all = True

	for i in range(len(messages) - 1, -1, -1):
		message = messages[i]
		if message.user_from == profile:
			message_title = f'💬 <b>Ты {get_rus_date(message.created_at)}</b>'
			message_text = message.text if message.text else ''
		else:
			message_title = f'👨‍💻 <b>Тебе {get_rus_date(message.created_at)}</b>'
			message_text = message.text if message.text else ''

		message_file = ''
		if message.file_id or message.photo_id:
			if message.file_id:
				context.user_data['current_files'].append([message.file_id, 'document'])
			else:
				context.user_data['current_files'].append([message.photo_id, 'photo'])
			message_file = '[Файл '

		chat_len += len(message_title) + len(message_text) + len(message_file)

		if (chat_len + len(end_caption)) <= settings.TEXT_LIMIT:
			chat.append({'title': message_title, 'text': message_text, 'file': message_file})
		else:
			is_all = False
			break

	chat.reverse()
	context.user_data['current_files'].reverse()
	file_counter = 0

	chat_text = '<b>Чат с технической поддержкой</b>\n\n'
	chat_text += '' if is_all else '...\n\n'

	for msg in chat:
		chat_text += msg['title'] + '\n' + msg['text']
		if msg['file']:
			file_counter += 1
			chat_text += ' ' + msg['file'] + str(file_counter) + ']'
		chat_text += '\n\n'

	if not chat:
		chat_text += 'Здесь пока тихо...\n\n'

	chat_text += end_caption

	return chat_text


@log_errors
def get_order_chat_state_text(context):
	"""
	Creates text for order chat state
	:param context: callback context
	:return: created text
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']
	order = context.user_data['current_order']
	context.user_data['current_files'] = []

	# if customer
	profile_from = order.customer
	profile_to = order.freelancer

	# freelancer
	if order.freelancer.external_id == chat_id:
		profile_from = order.freelancer
		profile_to = order.customer

	m_from = list(Message.objects.filter(
		related_to=order.id, user_from=profile_from, user_to=profile_to).order_by('-created_at'))

	m_to = list(Message.objects.filter(
		related_to=order.id, user_from=profile_to, user_to=profile_from).order_by('-created_at'))

	messages = m_from + m_to
	messages.sort(key=lambda x: x.created_at, reverse=False)

	end_caption = '<i>Чтобы написать в чат, просто отправь сообщение или файл.</i>'

	chat = []
	chat_len = 0
	is_all = True

	for i in range(len(messages) - 1, -1, -1):
		message = messages[i]
		if message.user_from == profile_from:
			message_title = f'💬 <b>Ты {get_rus_date(message.created_at)}</b>'
			message_text = message.text if message.text else ''
		else:
			message_title = f'👨‍💻 <b>Тебе {get_rus_date(message.created_at)}</b>'
			message_text = message.text if message.text else ''

		message_file = ''
		if message.file_id or message.photo_id:
			if message.file_id:
				context.user_data['current_files'].append([message.file_id, 'document'])
			else:
				context.user_data['current_files'].append([message.photo_id, 'photo'])
			message_file = '[Файл '

		chat_len += len(message_title) + len(message_text) + len(message_file)

		if (chat_len + len(end_caption)) <= settings.TEXT_LIMIT:
			chat.append({'title': message_title, 'text': message_text, 'file': message_file})
		else:
			is_all = False
			break

	chat.reverse()
	context.user_data['current_files'].reverse()
	file_counter = 0

	chat_text = f'<b>Чат с {"заказчиком" if order.freelancer.external_id == chat_id else "исполнителем"}</b>\n\n'
	chat_text += '' if is_all else '...\n\n'

	for msg in chat:
		chat_text += msg['title'] + '\n' + msg['text']
		if msg['file']:
			file_counter += 1
			chat_text += ' ' + msg['file'] + str(file_counter) + ']'
		chat_text += '\n\n'

	if not chat:
		chat_text += 'Здесь пока тихо...\n\n'

	chat_text += end_caption

	return chat_text


@log_errors
def get_order_details_state(context):
	"""
	Creates text for order details state
	:param context: callback context
	:return: created text or False if order not specified
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']
	current_order = context.user_data['current_order']

	if not current_order:
		return False

	date = get_rus_date(current_order.date)
	subject = current_order.subject
	type = current_order.type
	deadline = current_order.deadline
	plagiarism = current_order.plagiarism
	description = current_order.description
	status = 'На модерации'

	if current_order.status == 'approved':
		status = 'Поиск исполнителя'
	elif current_order.status == 'paid':
		status = 'Выполняется'

	text1 = '<b>🗓 Дата размещения</b>\n'
	text1 += date + '\n\n'

	text1 += '<b>📚 Предмет</b>\n'
	text1 += subject + '\n\n'

	text1 += '<b>📃 Тип работы</b>\n'
	text1 += type + '\n\n'

	text1 += '<b>🕑 Срок</b>\n'
	text1 += deadline + '\n\n'

	text1 += '<b>🔎 Антиплагиат</b>\n'
	text1 += plagiarism + '\n\n'

	text1 += '<b>✍️ Описание</b>\n'
	text1 += description + '\n\n'

	text1 += '<b>⚡️ Статус</b>\n'
	text1 += status

	text2 = ''

	current_user = get_profile(chat_id, username)
	if current_user == current_order.customer and current_order.status == 'approved':
		feedbacks = OrderFeedback.objects.filter(order=current_order)

		if feedbacks:
			context.user_data['feedback_list'] = feedbacks
			text2 += '<b>Заявки на выполнение:</b>'

		counter = 0
		for feedback in feedbacks:
			comment = feedback.comment
			price = feedback.price
			counter += 1

			text2 += f'\n\n<b>Заявка №{counter}</b>\n'
			text2 += f'💵 <b>{price}₽</b>\n'
			text2 += f'✍️ {comment}'

	if current_order.files:
		context.user_data['current_files'] = []

		files = current_order.files.split(',,')

		for file in files:
			if file:
				type = file.split(',')[0]
				file_id = file.split(',')[1]
				context.user_data['current_files'].append([file_id, type])

	return [text1, text2]


''' -----------------
	Menu builders
----------------- '''


@log_errors
def build_chat_keyboard(context):
	"""
	Builds menu for chat (adds btn_file buttons if there attachments in messages)
	:param context: callback context
	:return: keyboard - array of array of buttons
	"""

	keyboard = []
	current_files = context.user_data['current_files']

	for i in range(len(current_files)):
		keyboard.append([btn_file + ' ' + str(i + 1)])


	# files_buttons = []
	#
	# in_row = 4
	# for i in range(len(current_files) // in_row):
	# 	row = []
	# 	for j in range(in_row):
	# 		row.append(btn_file + str(i * in_row + j + 1))
	# 	files_buttons.append(row)
	#
	# last_row = []
	# for i in range(len(current_files) % in_row):
	# 	last_row.append(btn_file + str(in_row * (len(current_files) // in_row) + i + 1))
	#
	# files_buttons.append(last_row)
	#
	# if files_buttons:
	# 	keyboard = files_buttons

	keyboard.append([btn_back])

	return keyboard


@log_errors
def build_settings_keyboard(context):
	"""
	Builds menu for settings
	:param context: callback context
	:return: keyboard - array of array of buttons
	"""

	keyboard = [[btn_setup_keywords]]

	keywords = get_profile(context.user_data['chat_id'], context.user_data['username']).keywords
	if keywords:
		keyboard = [[btn_edit_keywords, btn_remove_keywords]]

	keyboard.append([btn_back])

	return keyboard


@log_errors
def build_balance_keyboard(context):
	"""
	Builds balance for settings
	:param context: callback context
	:return: keyboard - array of array of buttons
	"""

	profile = get_profile(context.user_data['chat_id'], context.user_data['username'])
	out_requests = MoneyOutRequest.objects.filter(profile=profile, status='processing').count()

	# if profile.balance and not out_requests:
	return [[btn_back, btn_balance_minus]]


@log_errors
def build_current_orders_keyboard(context):
	"""
	Builds menu for current orders (adds btn_open_order to each order)
	:param context: callback context
	:return: keyboard - array of array of buttons
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']

	keyboard = []

	profile = get_profile(chat_id, username)
	customer_orders = Order.objects.filter(customer=profile).exclude(status='done').exclude(status='canceled').count()
	freelancer_orders = Order.objects.filter(freelancer=profile, status='paid').count()

	for i in range(customer_orders + freelancer_orders):
		keyboard.append([btn_open_order + ' №' + str(i + 1)])

	keyboard.append([btn_back])
	return keyboard


@log_errors
def build_order_details_keyboard(context):
	"""
	Builds menu for order details
	:param context: callback context
	:return: keyboard - array of array of buttons (or False if order not specified)
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']
	current_order = context.user_data['current_order']

	if not current_order:
		return [[btn_back]]

	profile = get_profile(chat_id, username)
	keyboard = []

	# user is customer
	if profile == current_order.customer:
		# new
		if current_order.status == 'new':
			if current_order.files:
				keyboard.append([btn_show_files])
			keyboard.append([btn_cancel_order])
			keyboard.append([btn_back])

		# approved
		elif current_order.status == 'approved':
			for i in range(len(context.user_data['feedback_list'])):
				keyboard.append([btn_select_freelancer + ' №' + str(i + 1)])
			# if current_order.files:
			# 	keyboard.append([btn_show_files])
			keyboard.append([btn_cancel_order])
			keyboard.append([btn_back])

		# paid
		elif current_order.status == 'paid':
			keyboard.append([btn_chat_with_freelancer])
			# if current_order.files:
			# 	keyboard.append([btn_show_files])
			keyboard.append([btn_confirm_order_finishing])
			keyboard.append([btn_back])

	# user is freelancer
	else:
		# approved
		if current_order.status == 'approved':
			keyboard.append([btn_send_feedback])

		# paid
		elif current_order.status == 'paid':
			keyboard.append([btn_chat_with_customer])

		if current_order.files:
			keyboard.append([btn_show_files])

		keyboard.append([btn_back])

	return keyboard


@log_errors
def build_start_keyboard(context):
	"""
	Builds main menu (adds btn_current_orders if there orders in database)
	:param context: callback context
	:return: keyboard
	"""

	chat_id = context.user_data['chat_id']
	username = context.user_data['username']

	profile = get_profile(chat_id, username)
	orders_as_customer = Order.objects.filter(customer=profile).exclude(status='done').exclude(status='canceled').count()
	orders_as_freelancer = Order.objects.filter(freelancer=profile, status='paid').count()
	orders_count = orders_as_customer + orders_as_freelancer

	top_row = [btn_new_order]
	if orders_count:
		top_row = [btn_new_order, btn_current_orders + f' ({orders_count})']

	return [top_row, [btn_balance, btn_statistics], [btn_settings, btn_support]]


''' --------------------------
	Small language helpers
-------------------------- '''


@log_errors
def find_value(arr, value):
	"""
	Finds list in array
	:param arr: list
	:param value: value to find
	:return:
	"""

	for index, item in enumerate(arr):
		if item == value:
			return index, item
	return None


@log_errors
def parse_int_abs(text):
	"""
	Parses positive integer number from string
	:param text: string to parse
	:return:
	"""

	try:
		return abs(int(text))
	except ValueError:
		try:
			return abs(round(float(text)))
		except ValueError:
			return False


@log_errors
def get_rus_date(date):
	"""
	Generates good russian date
	:param date: datetime
	:return: normal date as string
	"""

	tz = pytz.timezone('Europe/Moscow')
	dd = date.astimezone(tz)

	month = dd.strftime('%m')
	day = dd.strftime('%d')
	time = dd.strftime('%H:%M')

	months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября',
			  'ноября', 'декабря']
	month = months[int(month) - 1]

	return day + ' ' + month + ' в ' + time


@log_errors
def get_right_number_label(number, options):
	"""
	Gets right label for russian language

	:param number: integers number
	:param options: ['for 0', 'for 1', 'for 2']
	:return:
	"""
	if (number % 10 == 1) and (number != 11):
		return options[1]
	elif (2 <= number % 10 <= 4) and ((number <= 12) or (number >= 14)):
		return options[2]
	else:
		return options[0]
