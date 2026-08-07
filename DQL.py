import mysql.connector
from config_db import *

def find_user_id(telegram_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = 'SELECT `ID` FROM USERS WHERE `telegram_id` = %s'
    cur.execute(SQL_QUERY , (telegram_id,))
    result = cur.fetchone()
    cur.close()
    connection.close()
    return result

def get_users():
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT id,telegram_id,username,name,is_admin,is_teacher FROM users
    '''
    cur.execute(SQL_QUERY)
    result = cur.fetchall()
    cur.close()
    connection.close()
    return result

def get_categories():
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = 'SELECT ID,NAME FROM categories'
    cur.execute(SQL_QUERY)
    result = cur.fetchall()
    cur.close()
    connection.close()
    return result

if __name__ == '__main__':
    print(get_users())