from django.core.management.base import BaseCommand
from django.conf import settings
from pprint import pprint

from telegram import Bot
from telegram import Update
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram.utils.request import Request

from tg_bot.models import *


# Error logs
def log_errors(f):
	def inner(*args, **kwargs):
		try:
			return f(*args, **kwargs)
		except Exception as e:
			error_message = f'Произошла ошибка: {e}'
			print(error_message)
			raise e

	return inner


# Keyboard buttons
btn_new_order = 'Новое задание 📝'
btn_become_freelancer = 'Стать исполнителем'
btn_feedback = 'Обратная связь'
back_button = '← Назад'
btn_send = 'Найти исполнителя 🔎'
btn_cancel = 'Отменить'

# Keyboards
start_keyboard = [[btn_new_order],
				  [btn_become_freelancer, btn_feedback]]

back_keyboard = [[back_button]]

send_keyboard = [[btn_send],
				 [back_button]]

cancel_keyboard = [[btn_cancel]]

# Global vars

stage = ''
subject = ''
deadline = ''
description = ''
photos = []
files = []
order_id = None


@log_errors
def do_start(update: Update, context: CallbackContext):
	global stage
	stage = '1'

	update.message.reply_text(
		text='Отправь мне любое задание, связанное с учёбой. Я пройдусь по сразу нескольким биржам и найду тебе '
			 'исполнителя по самой выгодной цене.',
		reply_markup=ReplyKeyboardMarkup(start_keyboard, True, one_time_keyboard=True),
	)


@log_errors
def new_message(update: Update, context: CallbackContext):
	chat_id = update.message.chat_id
	username = update.message.from_user.username or chat_id
	text = update.message.text

	# Save message
	p, _ = Profile.objects.get_or_create(
		external_id=chat_id,
		defaults={
			'name': username,
		}
	)
	Message.objects.create(profile=p, text=text)

	global stage, subject, deadline, description

	if text == back_button:
		if len(stage) > 1:
			stage = stage[:-1]
		else:
			stage = '1'
		go_to_stage(update, context)
	else:
		if text == btn_new_order:
			stage = '11'
		elif text == btn_become_freelancer:
			stage = '12'
		elif text == btn_feedback:
			stage = '13'
		elif text == btn_send:
			if not subject:
				stage = '11'
			elif not deadline:
				stage = '111'
			elif not description:
				stage = '11112'
			else:
				save_order(update, context, subject, deadline, description)
				return
		elif text == btn_cancel:

			if cancel_order():
				stage = '111112'
			else:
				stage = '111113'

		else:
			if stage == '11':
				subject = text
				stage += '1'
			elif stage == '12':
				save_application(update, context)
				stage += '1'
			elif stage == '111':
				deadline = text
				stage += '1'
			elif stage == '1111':
				description += text + '\n'
				return
			else:
				return
		go_to_stage(update, context)


@log_errors
def go_to_stage(update: Update, context: CallbackContext):
	global stage

	if stage == '1':
		update.message.reply_text(
			text=f'Отправь мне любое задание, связанное с учёбой. Я пройдусь по сразу нескольким биржам и найду тебе '
			 	 f'исполнителя по самой выгодной цене.',
			parse_mode='HTML',
			reply_markup=ReplyKeyboardMarkup(start_keyboard, True),
		)
	elif stage == '11':
		update.message.reply_text(
			text='<b>Какой предмет?</b>\n\nФизика, экология, история...',
			parse_mode='HTML',
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True),
		)
	elif stage == '12':
		update.message.reply_text(
			text='Если ты в чём-то шаришь, то можешь заработать, выполняя задания. Чтобы начать, '
				 'опиши пожалуйста свой опыт и компетенции.',
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True),
		)
	elif stage == '121':
		update.message.reply_text(
			text='Спасибо! Сейчас я работаю с партнёрскими биржами, но также собираю и собственную базу исполнителей. '
				 'Как только система заработает — обязательно сообщу и дам доступ в личный кабинет.',
			reply_markup=ReplyKeyboardMarkup(start_keyboard, True),
		)
		update.message.reply_sticker(
			sticker='CAACAgIAAxkBAAJAlV6PTNF7Qk8-bmzpuKS5ysscaci3AAIOAAPp2BMoE6Y9Q1_4SB8YBA'
		)
		stage = '1'
	elif stage == '13':
		update.message.reply_text(
			text='Возникла проблема?\nЕсть вопрос?\nХочешь предложить идею?\n\nНапиши нам: @feedbackBotanBot',
			reply_markup=ReplyKeyboardMarkup(start_keyboard, True),
		)
		stage = '1'
	elif stage == '111':
		update.message.reply_text(
			text='<b>Какие сроки?</b>\n\nТри дня, 15 марта в 15:20, дедлайн был ещё вчера...',
			parse_mode='HTML',
			reply_markup=ReplyKeyboardMarkup(back_keyboard, True),
		)
	elif stage == '1111':
		update.message.reply_text(
			text=f'<b>Описание</b>\n\nТеперь опиши пожалуйста своё задание поподробнее, чтобы исполнители могли '
				 f'адекватно его оценить. Файлы тоже прикрепляй, если есть.\n\nКогда закончишь, жми "{btn_send}"',
			parse_mode='HTML',
			reply_markup=ReplyKeyboardMarkup(send_keyboard, True),
		)
	elif stage == '11111':
		update.message.reply_text(
			text='Принято. Ищу подходящего исполнителя.',
			reply_markup=ReplyKeyboardMarkup(cancel_keyboard, True),
		)
		update.message.reply_sticker(
			sticker='CAACAgIAAxkBAAJAl16PVi21t0TD0RndGYeQswRQGCTWAAIfAAPp2BMoCBoZcicUneIYBA'
		)
	# chat_message(update, context, 3)
	elif stage == '11112':
		update.message.reply_text(
			text='Заполни пожалуйста описание.',
			reply_markup=ReplyKeyboardMarkup(send_keyboard, True),
		)
		stage = '1111'
	elif stage == '111112':
		update.message.reply_text(
			text='Задание отменено.',
			reply_markup=ReplyKeyboardMarkup(start_keyboard, True),
		)
	elif stage == '111113':
		update.message.reply_text(
			text='Не найдено задания для отмены. Если произошла ошибка, свяжись пожалуйста с технической поддержкой: '
				 '@feedbackBotanBot.',
			reply_markup=ReplyKeyboardMarkup(start_keyboard, True),
		)
		stage = '1'
	elif stage == '11113':
		update.message.reply_text(
			text='На данный момент у тебя 3 задания в процессе выполнения. Больше пока нельзя. Подожди пожалуйста, '
				 'пока какое-то из них не будет выполнено.',
			reply_markup=ReplyKeyboardMarkup(send_keyboard, True),
		)
		stage = '1111'


@log_errors
def new_document(update: Update, context: CallbackContext):
	global files, description

	chat_id = update.message.chat_id
	file_id = update.message.document['file_id']
	caption = update.message.caption

	files.append({'file_id': file_id, 'caption': caption})

	if caption and (not description):
		description += caption

	return


@log_errors
def new_photo(update: Update, context: CallbackContext):
	global files, description

	chat_id = update.message.chat_id
	file_id = update.message.photo[-1]['file_id']
	caption = update.message.caption

	photos.append({'file_id': file_id, 'caption': caption})

	if caption and (not description):
		description += caption

	return


def save_order(update: Update, context: CallbackContext, subject_param, deadline_param, description_param):
	global stage, order_id

	chat_id = update.message.chat_id
	username = update.message.from_user.username or chat_id
	text = update.message.text

	available_chats = {1, 2, 3}

	p, _ = Profile.objects.get_or_create(
		external_id=chat_id,
		name=username,
	)

	active_orders = Order.objects.filter(profile=p).exclude(status='done').exclude(status='canceled')

	for order in active_orders:
		if order.chat in available_chats:
			available_chats.remove(order.chat)

	if available_chats:
		order_chat = next(iter(available_chats))

		new_order = Order.objects.create(profile=p,
										 subject=subject_param,
										 deadline=deadline_param,
										 description=description_param,
										 status='new',
										 chat=order_chat)

		order_id = new_order.id

		global subject, deadline, description

		notification_text = f'NEW ORDER\nOrder ID: {order_id}\n\nChat ID: {chat_id}\nUsername: @{username}\n\n' \
							f' {subject}\n\n{deadline}\n\n{description}'

		send_notification(username, notification_text)
		subject, deadline, description = '', '', ''

		send_files(username)

		stage = '11111'  # waiting for freelancer
	else:
		stage = '11113'  # reached limit of opened orders

	go_to_stage(update, context)


def save_application(update: Update, context: CallbackContext):
	chat_id = update.message.chat_id
	username = update.message.from_user.username or chat_id
	text = update.message.text

	p, _ = Profile.objects.get_or_create(
		external_id=chat_id,
		name=username,
	)

	FreelanceApplication.objects.create(profile=p, description=text)
	send_notification(username, f'FREELANCE APPLICATION\n\n{username}\n\n{text}')


def send_notification(username, text):
	request = Request(
		connect_timeout=10,
		read_timeout=1.0,
	)

	bot = Bot(
		request=request,
		token=settings.TOKEN,
		base_url=getattr(settings, 'PROXY_URL', None),
	)

	bot.sendMessage(chat_id=settings.ADMIN_CHAT_ID, text=text)


def send_files(username):
	request = Request(
		connect_timeout=10,
		read_timeout=1.0,
	)

	bot = Bot(
		request=request,
		token=settings.TOKEN,
		base_url=getattr(settings, 'PROXY_URL', None),
	)

	global photos, files

	for photo in photos:
		bot.sendPhoto(chat_id=settings.ADMIN_CHAT_ID, photo=photo['file_id'], caption=photo['caption'])

	for file in files:
		bot.sendDocument(chat_id=settings.ADMIN_CHAT_ID, document=file['file_id'], caption=file['caption'])

	photos = []
	files = []


def payment_message(price, chat_id, tasks_count, good, bad):
	request = Request(
		connect_timeout=10,
		read_timeout=1.0,
	)

	bot = Bot(
		request=request,
		token=settings.TOKEN,
		base_url=getattr(settings, 'PROXY_URL', None),
	)

	buttons = InlineKeyboardButton(f'Оплатить {price}₽', url=f'https://money.yandex.ru/to/410015462421344/{price}')

	bot.sendMessage(
		chat_id=chat_id,
		text=f'Я нашёл исполнителя!\n\n'
			 f'Цена: {price}₽\n'
			 f'Выполнено заданий: {tasks_count}\n'
			 f'Отзывы: 🙂 {good}  /  ☹️ {bad}\n\n'
			 'Это наименьшая из всех предложенных цен.\n\nВ случае, если исполнитель не справится с заданием, '
			 'деньги будут возвращены.\n\n'
			 'Если не трудно, укажи пожалуйста свой юзернейм или номер телефона в комментарии к переводу. Так мне '
			 'будет легче идентифицировать платёж.',
		reply_markup=InlineKeyboardMarkup([[buttons]])
	)

	global stage
	stage = '111111'


def chat_message(chat_id, chat_number):
	request = Request(
		connect_timeout=10,
		read_timeout=1.0,
	)

	bot = Bot(
		request=request,
		token=settings.TOKEN,
		base_url=getattr(settings, 'PROXY_URL', None),
	)

	bot.sendMessage(
		chat_id=chat_id,
		text=f'Успешная оплата 👌\n\n'
			 f'Связь с исполнителем: @chat{chat_number}BotanBot\n\n'
			 f'По любым проблемам смело обращайся в техническую поддержку: @feedbackBotanBot',
		reply_markup=ReplyKeyboardMarkup(start_keyboard, True),
	)

	global stage
	stage = '1'


@log_errors
def cancel_order():
	global order_id

	if order_id:
		order = Order.objects.get(id=order_id)
	else:
		return False

	if order:
		order.status = 'canceled'
		order.save()
		order_id = None
		return True
	else:
		return False


def find_value(arr, value):
	for index, item in enumerate(arr):
		if item == value:
			return index, item
	return None


class Command(BaseCommand):
	help = 'Telegram Bot'

	def handle(self, *args, **options):
		# 1 -- правильное подключение
		request = Request(
			connect_timeout=5,
			read_timeout=1.0,
		)
		bot = Bot(
			request=request,
			token=settings.TOKEN,
			base_url=getattr(settings, 'PROXY_URL', None),
		)

		# 2 -- обработчики
		updater = Updater(
			bot=bot,
			use_context=True,
		)

		updater.dispatcher.add_handler(CommandHandler('start', do_start))

		message_handler = MessageHandler(Filters.text, new_message)
		updater.dispatcher.add_handler(message_handler)

		updater.dispatcher.add_handler(MessageHandler(Filters.document, new_document))
		updater.dispatcher.add_handler(MessageHandler(Filters.photo, new_photo))

		# 3 -- запустить бесконечную обработку входящих сообщений
		updater.start_polling()
		updater.idle()
