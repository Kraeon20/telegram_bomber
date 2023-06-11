import telebot
import mysql.connector
import requests

# MySQL database configuration
database_config = {
    'user': 'root',
    'password': 'Priscilla2058@',
    'host': 'localhost',
    'database': 'telegram_bot'
}

# Create the user_data table
def create_table():
    connection = mysql.connector.connect(**database_config)
    cursor = connection.cursor()

    # SQL query to create the table
    query = """
    CREATE TABLE IF NOT EXISTS user_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        chat_id VARCHAR(255),
        ip_address VARCHAR(255)
    )
    """

    # Execute the query
    cursor.execute(query)

    # Commit the changes and close the connection
    connection.commit()
    cursor.close()
    connection.close()

# Get user's IP address
def get_user_ip():
    try:
        # Make a request to IPify API
        response = requests.get('https://api.ipify.org?format=json')
        data = response.json()

        # Extract the IP address from the response
        ip_address = data['ip']

        return ip_address
    except requests.RequestException:
        return None

# Initialize the Telebot API token
bot = telebot.TeleBot('6138199032:AAED2by4VqEeLHWoEnoXsyWQuM7-W1YAD1M')

# Handle /start command
@bot.message_handler(commands=['start'])
def handle_start(message):
    # Get the user's name
    user_name = message.from_user.first_name

    # Get the user's IP address
    ip_address = get_user_ip()

    if ip_address is not None:
        # Get the chat ID
        chat_id = message.chat.id

        # Save the data in the MySQL database
        save_data(user_name, chat_id, ip_address)

        # Send a response to the user
        bot.reply_to(message, f"Hello {user_name}!\n\nYour address has been sent to Kraeon!(@kraeon).")
    else:
        # Send an error message if the IP address couldn't be retrieved
        bot.reply_to(message, "Sorry, I couldn't retrieve your IP address.")

# Save data in MySQL database
def save_data(user_name, chat_id, ip_address):
    connection = mysql.connector.connect(**database_config)
    cursor = connection.cursor()

    # Insert the data into the table
    query = "INSERT INTO user_data (name, chat_id, ip_address) VALUES (%s, %s, %s)"
    values = (user_name, chat_id, ip_address)
    cursor.execute(query, values)

    # Commit the changes and close the connection
    connection.commit()
    cursor.close()
    connection.close()

# Create the user_data table
create_table()

# Start the bot
bot.polling()
