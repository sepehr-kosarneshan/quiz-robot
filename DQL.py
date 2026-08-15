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

def get_user_information(telegram_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = 'SELECT * FROM USERS WHERE `telegram_id` = %s'
    cur.execute(SQL_QUERY , (telegram_id,))
    result = cur.fetchone()
    cur.close()
    connection.close()
    return result

def get_question_information(question_id) :
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT text,photo_id,answer_text,answer_option,option_1,option_2,option_3,option_4 
        FROM questions
        WHERE id = (%s)
    '''
    cur.execute(SQL_QUERY , (question_id ,))
    result = cur.fetchone()
    cur.close()
    connection.close()
    return result

def get_is_teacher_status(telegram_id) :
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT `is_teacher` FROM USERS WHERE `telegram_id` = (%s)
    '''
    cur.execute(SQL_QUERY , (telegram_id,))
    result = cur.fetchone()
    cur.close()
    connection.close()
    return result['is_teacher']

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

def get_support_status(user_id , user_mid) :
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = 'SELECT `admin_id` FROM user_support_request WHERE `user_id` = (%s) and `message_id` = (%s)'
    cur.execute(SQL_QUERY , (user_id , user_mid))
    result = cur.fetchone()
    cur.close()
    connection.close()
    return result

def get_question_id_public(category_id): # output : list
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = 'SELECT ID FROM questions WHERE `is_public` = 1 and `category_id` = (%s)'
    cur.execute(SQL_QUERY , (category_id , ))
    result = cur.fetchall()
    for i in range(len(result)) : 
        value = result[i]['ID']
        result[i] = value
    cur.close()
    connection.close()
    return result

if __name__ == '__main__':
    print(get_question_information(2))