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

if __name__ == '__main__' :
    edit_user_username(1,None)
    #print(add_categories('structure'))

