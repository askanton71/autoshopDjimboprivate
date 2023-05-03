import aiohttp
import asyncio
import json
from tgbot.data.loader import bot
from tgbot.services.api_sqlite import update_userx, get_refillx, add_refillx, get_userx
from tgbot.utils.const_functions import get_date, get_unix


kassa_login = '(ampaytg)' #логин кассы(вместо нуля)
secret_key = 'ab9b8df0a9cc55fe1eef36d627f7df702e7b4ef7' #секретный ключ кассы (первый)(вместо нуля)

#проверка баланса кассы
async def get_balance(message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.crystalpay.ru/v1/?s={secret_key}&n={kassa_login}&o=balance') as response:
            res = await response.text()
            a = json.loads(res)
            s = ''
            for i in a['balance']:
                s += f'{i} {a["balance"][i]}\n'

            return s

#создание ссылки на оплату и проверка оплаты
async def create_payment(pay_amount, message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.crystalpay.ru/v1/?s={secret_key}&n={kassa_login}&o=invoice-create&amount={pay_amount}&lifetime=10&extra={message.chat.id}&currency=USD') as response:
            res = await response.text()
            g = json.loads(res)

            await bot.send_message(chat_id=message.from_user.id, text=g['url'])

            while True:
                await asyncio.sleep(2)
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'https://api.crystalpay.ru/v1/?s={secret_key}&n={kassa_login}&o=invoice-check&i={g["id"]}') as response:
                        res = await response.text()
                        r = json.loads(res)
                        if r['state'] == 'payed':
                            get_user = get_userx(user_id=r['extra'])

                            add_refillx(get_user['user_id'], get_user['user_login'], get_user['user_name'], 0,
                                            pay_amount, 0, 0, get_date(), get_unix())

                            update_userx(r['extra'],
                                             user_balance=get_user['user_balance'] + pay_amount,
                                             user_refill=get_user['user_refill'] + pay_amount)

                            await bot.send_message(chat_id=message.from_user.id, text=f"<b>💰 Вы пополнили баланс на сумму <code>{pay_amount}$</code>. Удачи ❤\n</b>")

                            break

#проверка на число с плавающей точкой
def is_number(str):
    try:
        float(str)
        return True
    except ValueError:
        return False
