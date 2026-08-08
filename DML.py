import mysql.connector
from config_db import *

def add_user(telegram_id,is_admin = False , is_teacher = False ,username = None,name = None):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = '''
        INSERT INTO users (`telegram_id`,`username`,`name`,`is_admin`,`is_teacher`) 
        VALUES (%s,%s,%s,%s,%s)
    '''
    cur.execute(SQL_QUERY , (telegram_id,username,name,is_admin,is_teacher))
    result = cur.lastrowid
    connection.commit()
    cur.close()
    connection.close()
    return result

def edit_user_name(telegram_id,name):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = '''
        UPDATE users SET `name` = (%s) WHERE `telegram_id` = (%s)
    '''
    cur.execute(SQL_QUERY , (name , telegram_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def edit_user_username(telegram_id,username):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = '''
        UPDATE users SET `username` = (%s) WHERE `telegram_id` = (%s)
    '''
    cur.execute(SQL_QUERY , (username , telegram_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def add_categories(name):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'INSERT INTO categories (`NAME`) VALUES (%s)'
    cur.execute(SQL_QUERY , (name,))
    result = cur.lastrowid
    connection.commit()
    cur.close()
    connection.close()
    return result

def add_question(category_id , designer_id , text , op1 , op2 , op3 , op4 ,ansop ,anstext, is_public = True , photo_id = None):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = '''
        INSERT INTO questions (`category_id`,`designer_id`,`text`,`photo_id`,`answer_text`,`answer_option`,`option_1`,`option_2`,`option_3`,`option_4`,`is_public`)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    '''
    cur.execute(SQL_QUERY , (category_id , designer_id , text , photo_id , anstext, ansop , op1 , op2 , op3 , op4 , is_public))
    result = cur.lastrowid
    connection.commit()
    cur.close()
    connection.close()
    return result

def add_support_request(user_id , message_id , text):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = '''
        INSERT INTO user_support_request (`user_id`,`message_id`,`text`)
        VALUES (%s , %s , %s)
    '''
    cur.execute(SQL_QUERY , (user_id , message_id , text))
    result = cur.lastrowid
    connection.commit()
    cur.close()
    connection.close()
    return result

def update_support_status(user_id , user_mid , admin_id , admin_text) :
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''update user_support_request
                    SET `admin_id` = (%s) , `admin_text` = (%s)
                    WHERE `user_id` = (%s) AND `message_id` = (%s);
                '''
    cur.execute(SQL_QUERY , (admin_id , admin_text , user_id , user_mid))
    connection.commit()
    cur.close()
    connection.close()
    return True

if __name__ == '__main__' :
    update_support_status(1 , 1 , 1 , 'alieke salam')
    #print(add_categories('structure'))

