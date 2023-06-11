import mysql.connector

# Establish a connection to the MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Priscilla2058@",
    database="telegram_bot"
)

# Create a cursor object to interact with the database
cursor = db.cursor()

# Create a table for storing user balances
def create_balance_table():
    cursor.execute("CREATE TABLE IF NOT EXISTS balances (user_id INT PRIMARY KEY, balance DECIMAL(10, 2) NOT NULL)")

# Function to get the user's balance from the database
def get_user_balance(user_id):
    cursor.execute("SELECT balance FROM balances WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None

# Function to update the user's balance in the database
def update_user_balance(user_id, new_balance):
    cursor.execute("UPDATE balances SET balance = %s WHERE user_id = %s", (new_balance, user_id))
    db.commit()

# Close the database connection
def close_connection():
    cursor.close()
    db.close()
