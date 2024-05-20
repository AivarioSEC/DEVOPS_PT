import logging
import re

import psycopg2
from psycopg2 import Error

from telegram import Update, ForceReply
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters, ConversationHandler
import paramiko
import dotenv
import os
dotenv.load_dotenv()


TOKEN = os.getenv('TOKEN')
host = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')

DB_username=os.getenv('DB_USER')
DB_password=os.getenv('DB_PASSWORD')
DB_host=os.getenv('DB_HOST')
DB_port=os.getenv('DB_PORT')
DB_database=os.getenv('DB_DATABASE')
connection = None

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет, {user.full_name}!')

def helpCommand(update: Update, context):
    update.message.reply_text('Help!')

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'

def findEmailsCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска почты: ')

    return 'findEmails'

def aptListCommand(update: Update, context):
    update.message.reply_text('Введите название пакета или all:')

    return 'aptList'

def validPassCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')
    return 'validPass'

def writePhoneNumbers(update: Update, context: CallbackContext):
    user_input=update.message.text
    if user_input.lower()=='да':
        phoneNumberList = context.user_data.get('phoneNumberList', [])
        if phoneNumberList:
            connection = None
            try:
                connection = psycopg2.connect(user=DB_username,
                                password=DB_password,
                                host=DB_host,
                                port=DB_port, 
                                database=DB_database)

                cursor = connection.cursor()
                for number in phoneNumberList:
                    cursor.execute("INSERT INTO phones (phnumber) VALUES (%s);", (number,))
                    connection.commit()
                logging.info("Команда успешно выполнена")
                update.message.reply_text('Номера телефонов успешно сохранены в базе данных.')
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
            finally:
                if connection is not None:
                    cursor.close()
                    connection.close()
                    return ConversationHandler.END
    else:
        update.message.reply_text('Номера телефонов не сохранены.')
        return ConversationHandler.END

def writeEmails(update: Update, context: CallbackContext):
    user_input=update.message.text
    if user_input.lower()=='да':
        emailList = context.user_data.get('emailList', [])
        if emailList:
            connection = None
            try:
                connection = psycopg2.connect(user=DB_username,
                                password=DB_password,
                                host=DB_host,
                                port=DB_port, 
                                database=DB_database)

                cursor = connection.cursor()
                for email in emailList:
                    cursor.execute("INSERT INTO emails (email) VALUES (%s);", (email,))
                    connection.commit()
                logging.info("Команда успешно выполнена")
                update.message.reply_text('Email адреса успешно сохранены в базе данных.')
            except (Exception, Error) as error:
                logging.error("Ошибка при работе с PostgreSQL: %s", error)
            finally:
                if connection is not None:
                    cursor.close()
                    connection.close()
                    return ConversationHandler.END
    else:
        update.message.reply_text('Email адреса не сохранены.')
        return ConversationHandler.END



def validPass(update: Update, context: CallbackContext):
    user_input = update.message.text

    # Определение регулярных выражений для проверки критериев сложности пароля
    has_upper = re.search(r'[A-Z]', user_input)
    has_lower = re.search(r'[a-z]', user_input)
    has_digit = re.search(r'[0-9]', user_input)
    has_special = re.search(r'[@#$%^&*()]', user_input)
    is_long_enough = len(user_input) >= 8

    # Проверка всех условий для определения сложности пароля
    if has_upper and has_lower and has_digit and has_special and is_long_enough:
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')

    return ConversationHandler.END



def findEmails(update: Update, context):
    user_input = update.message.text

    # Регулярное выражение для поиска email адресов
    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    # Поиск всех совпадений в тексте
    email_list = email_regex.findall(user_input)

    # Проверка на наличие найденных email адресов
    if not email_list:
        update.message.reply_text('Email адреса не найдены')
        return ConversationHandler.END

    # Создание строки с перечнем найденных email адресов
    emails = '\n'.join(f'{i + 1}. {email}' for i, email in enumerate(email_list))
    
    # Отправка результатов пользователю
    update.message.reply_text(emails)
    update.message.reply_text('Сохранить найденные данные? Да/Нет')

    # Сохранение списка найденных email адресов в контексте пользователя
    context.user_data['emailList'] = email_list

    return 'writeEmails'

def findPhoneNumbers(update: Update, context: CallbackContext):
    user_input = update.message.text  
    phone_regex = re.compile(
        r'(?:\+7|8)(?: \(\d{3}\) \d{3}-\d{2}-\d{2}|\d{10}|\(\d{3}\)\d{7}| \d{3} \d{3} \d{2} \d{2}| \(\d{3}\) \d{3} \d{2} \d{2}|-\d{3}-\d{3}-\d{2}-\d{2})'
    )
    # Ищем номера телефонов
    phone_number_list = phone_regex.findall(user_input)
    
    if not phone_number_list:
        update.message.reply_text('Телефонные номера не найдены.')
        return ConversationHandler.END  
    
    phone_numbers = '\n'.join(f'{i + 1}. {number}' for i, number in enumerate(phone_number_list))
    
    # Отправляем найденные номера пользователю
    update.message.reply_text(phone_numbers)
    update.message.reply_text('Сохранить найденные данные? Да/Нет')

    # Сохраняем список найденных номеров во временное хранилище для возможности последующего сохранения в базу
    context.user_data['phoneNumberList'] = phone_number_list

    return 'writePhoneNumbers'  # Переходим к следующему шагу в обработчике

#def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def ssh_execute(host, username, password, port, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    return data.decode('utf-8')


def clean_ssh_output(data):
    # Убирает лишние символы из вывода SSH и форматирует его для показа в сообщении
    return data.replace('\\n', '\n').replace('\\t', '\t')[2:-1]

# /get_release
def get_release(update: Update, context):
    data = ssh_execute(host, username, password, port, 'cat /etc/*-release')
    update.message.reply_text(clean_ssh_output(data))
# /get_uname
def get_uname(update: Update, context):
    data = ssh_execute(host, username, password, port, 'uname -a')
    update.message.reply_text(clean_ssh_output(data))
# /get_uptime
def get_uptime(update: Update, context):
    data = ssh_execute(host, username, password, port, 'uptime')
    update.message.reply_text(clean_ssh_output(data))
# /get_df
def get_df(update: Update, context):
    data = ssh_execute(host, username, password, port, 'df')
    update.message.reply_text(clean_ssh_output(data))
# /get_free
def get_free(update: Update, context):
    data = ssh_execute(host, username, password, port, 'free -h')
    update.message.reply_text(clean_ssh_output(data))
# /get_mpstat
def get_mpstat(update: Update, context):
    data = ssh_execute(host, username, password, port, 'mpstat')
    update.message.reply_text(clean_ssh_output(data))
# /get_w
def get_w(update: Update, context):
    data = ssh_execute(host, username, password, port, 'w')
    update.message.reply_text(clean_ssh_output(data))
# /get_auths
def get_auths(update: Update, context):
    command = 'last -10'
    data = ssh_execute(host, username, password, port, command)  
    update.message.reply_text(clean_ssh_output(data))

# /get_critical
def get_critical(update: Update, context):
    command = 'journalctl -p 2 -n 5'
    data = ssh_execute(host, username, password, port, command)
    update.message.reply_text(clean_ssh_output(data))
# /get_ps
def get_ps(update: Update, context):
    command = 'ps'
    data = ssh_execute(host, username, password, port, command)
    update.message.reply_text(clean_ssh_output(data))
# /get_ss
def get_ss(update: Update, context):
    command = 'ss | head -n 20'
    data = ssh_execute(host, username, password, port, command)
    update.message.reply_text(clean_ssh_output(data))
# /get_apt_list
def get_apt_list(update: Update, context):
    user_input = update.message.text  
    command = 'apt list --installed'
    if user_input.lower() != 'all':
        command += ' ' + user_input  
    command += ' | head -n 50'     
    
    data = ssh_execute(host, username, password, port, command)
    update.message.reply_text(clean_ssh_output(data))
    return ConversationHandler.END
# /get_services
def get_services(update: Update, context):
    command = 'systemctl list-units --type=service | head -n 20' 
    data = ssh_execute(host, username, password, port, command)  
    update.message.reply_text(clean_ssh_output(data))

# /get_repl_logs
def get_repl_logs(update: Update, context):
    # Команда для получения последних 25 записей логов репликации из Docker контейнера
    command = 'cat /var/log/postgresql/postgresql-14-main.log | grep replica | tail -n 25'
    
    data = ssh_execute(host, username, password, port, command)   
    update.message.reply_text(clean_ssh_output(data))



def getEmailsBD(update: Update, context):
    try:
        connection = psycopg2.connect(user=DB_username,
                                password=DB_password,
                                host=DB_host,
                                port=DB_port, 
                                database=DB_database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emails;")
        data = cursor.fetchall()
        emailRegex = re.compile(r'[\w\.-]+@[\w\.-]+(?:\.[\w]+)+')
        emailList = emailRegex.findall(str(data)) 
        emails = '' 
        for i in range(len(emailList)):
            emails += f'{i+1}. {emailList[i]}\n' 
        update.message.reply_text(emails)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def getPhonesBD(update: Update, context):
    try:
        connection = psycopg2.connect(user=DB_username,
                                password=DB_password,
                                host=DB_host,
                                port=DB_port, 
                                database=DB_database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phones;")
        data = cursor.fetchall()
        phoneNumRegex = re.compile(r'(?:\+7|8)(?: \(\d{3}\) \d{3}-\d{2}-\d{2}|\d{10}|\(\d{3}\)\d{7}| \d{3} \d{3} \d{2} \d{2}| \(\d{3}\) \d{3} \d{2} \d{2}|-\d{3}-\d{3}-\d{2}-\d{2})')
        phoneNumberList = phoneNumRegex.findall(str(data))
        phoneNumbers = ''
        for i in range(len(phoneNumberList)):
            phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n'
        update.message.reply_text(phoneNumbers)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'writePhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, writePhoneNumbers)]
        },
        fallbacks=[]
    )

    convHandlerValidPass = ConversationHandler(
        entry_points=[CommandHandler('verify_password', validPassCommand)],
        states={
            'validPass': [MessageHandler(Filters.text & ~Filters.command, validPass)],
        },
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            'findEmails': [MessageHandler(Filters.text & ~Filters.command, findEmails)],
            'writeEmails': [MessageHandler(Filters.text & ~Filters.command, writeEmails)]
        },
        fallbacks=[]
    )

    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', aptListCommand)],
        states={
            'aptList': [MessageHandler(Filters.text & ~Filters.command, get_apt_list)],
        },
        fallbacks=[]
    )
		
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerValidPass)
    dp.add_handler(convHandlerGetAptList)
	
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))

    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", getEmailsBD))
    dp.add_handler(CommandHandler("get_phone_numbers", getPhonesBD))
	# Регистрируем обработчик текстовых сообщений
    #dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
