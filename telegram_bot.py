from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bit.wallet import HDWallet
import random
import requests

TOKEN = "5660902471:AAE-Rcz-OOqfV3rpEPIv4LInrIRmwHDHZxs"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
wallets = {}
keys = {}

def check_transaction(currency, address, comment):
    if currency == 'Bitcoin':
        url = f'https://blockchain.info/rawaddr/{address}'
        response = requests.get(url)
        transactions = response.json()['txs']
        for tx in transactions:
            if comment in tx['out'][0]['addr_tag']:
                return True
    elif currency == 'Ethereum':
        api_key = 'YOUR_API_KEY'
        url = f'https://api.etherscan.io/api?module=account&action=txlist&address={address}&apikey={api_key}'
        response = requests.get(url)
        transactions = response.json()['result']
        for tx in transactions:
            if tx['input'] == comment:
                return True
    return False


keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('Подписка'))

@dp.message_handler(commands=['start'])
async def send_welcome(msg: types.Message):
    await bot.send_message(chat_id=msg.chat.id, text='Здравствуйте, чем я могу вам помочь?.', reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == 'Подписка')
async def handle_button1_click(msg: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Подписаться'), KeyboardButton('Пополнение баланса'), KeyboardButton('Отмена'))
    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
    await bot.send_message(chat_id=msg.chat.id, text='Выберите действие:', reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == 'Пополнение баланса')
async def handle_button4_click(msg: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Bitcoin'), KeyboardButton('Ethereum'), KeyboardButton('Отмена'))
    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
    await bot.send_message(chat_id=msg.chat.id, text='Выберете криптовалюту для пополнения', reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in ['Bitcoin', 'Ethereum'], state=None)
async def handle_currency_selection(msg: types.Message):
    wallet = HDWallet.create('my wallet')
    address = wallet.new_receiving_address()

    code = random.randint(10000, 99999)
    prefix = ''
    if msg.text == 'Bitcoin':
        prefix = 'BTC'
    elif msg.text == 'Ethereum':
        prefix = 'ETH'
        
    comment = f'{prefix}-{code}'
    wallets[msg.chat.id] = {'currency': msg.text, 'address': address, 'comment': comment}

    await bot.send_message(chat_id=msg.chat.id, text=f'Ваш адрес для {msg.text} кошелька: {address}\nКомментарий для пополнения: {comment}')
    keys[msg.chat.id] = 'add_funds'

@dp.message_handler(lambda message: message.text.startswith('BTC-') or message.text.startswith('ETH-'), state=None)
async def handle_deposit(msg: types.Message):
    if msg.chat.id not in wallets:
        await bot.send_message(chat_id=msg.chat.id, text='Сначала нужно выбрать криптовалюту для пополнения.')
    return
    if not msg.text:
        await bot.send_message(chat_id=msg.chat.id, text='Номер кошелька не найден в сообщении.')
    return

    wallet_number = msg.text.split('-')[1]

    try:
        wallet_number = int(wallet_number)
    except ValueError:
        await bot.send_message(chat_id=msg.chat.id, text='Неверный номер кошелька.')
        return

    wallet_data = wallets[msg.chat.id]

    if not wallet_data['currency'].startswith(msg.text.split('-')[0]):
        await bot.send_message(chat_id=msg.chat.id, text='Выбрана неправильная криптовалюта для пополнения.')
        return
    deposit_code = f"{msg.text.split('-')[0]}-{random.randint(10000, 99999)}"
    await bot.send_message(chat_id=msg.chat.id, text=f"Для пополнения вашего кошелька {msg.text}, вам необходимо отправить на него сумму и в качестве комментария использовать код {deposit_code}.")

    keys[msg.chat.id] = 'deposit'

@dp.message_handler(lambda message: message.text == 'Проверить пополнение', state=None)
async def handle_check_deposit(msg: types.Message):
    wallet_data = wallets[msg.chat.id]
    if check_transaction(wallet_data['currency'], wallet_data['address'], wallet_data['comment']):
        del wallets[msg.chat.id]
        await bot.send_message(chat_id=msg.chat.id, text='Успешно пополнено!')
    else:
        await bot.send_message(chat_id=msg.chat.id, text='Пополнение не найдено.')
