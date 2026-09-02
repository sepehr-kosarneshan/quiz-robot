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
    cur = connection.cursor()
    SQL_QUERY = '''UPDATE user_support_request
                    SET `admin_id` = (%s) , `admin_text` = (%s)
                    WHERE `user_id` = (%s) AND `message_id` = (%s);
                '''
    cur.execute(SQL_QUERY , (admin_id , admin_text , user_id , user_mid))
    connection.commit()
    cur.close()
    connection.close()
    return True

def add_teacher_with_tel_id(telegram_id) :
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = '''
        UPDATE users SET `is_teacher` = 1 WHERE `telegram_id` = (%s)
    '''
    cur.execute(SQL_QUERY , (telegram_id,))
    connection.commit()
    cur.close()
    connection.close()
    return True

def add_answer_for_question(user_id , question_id , selected_option , exam_id = None):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = '''
        INSERT INTO user_answers (`user_id` , `question_id` , `exam_id` , `selected_option`) 
        VALUES (%s , %s , %s , %s)
    '''
    cur.execute(SQL_QUERY , (user_id , question_id , exam_id , selected_option))
    connection.commit()
    id = cur.lastrowid
    cur.close()
    connection.close()
    return id

def update_option_in_exam(user_id , question_id , new_option , exam_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = '''
        UPDATE user_answers SET `selected_option` = (%s)
        WHERE `user_id` = (%s) AND `question_id` = (%s) AND `exam_id` = (%s)
    '''
    cur.execute(SQL_QUERY , (new_option , user_id , question_id , exam_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

# Edit Question --------------
def edit_question_category(question_id , category_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE questions SET `category_id` = (%s) WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (category_id , question_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def edit_question_text(question_id , new_text):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE questions SET `text` = (%s) WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (new_text , question_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def edit_question_photo_id(question_id , new_photo_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE questions SET `photo_id` = (%s) WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (new_photo_id , question_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def edit_question_answer_text(question_id , new_text):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE questions SET `answer_text` = (%s) WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (new_text , question_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def edit_question_answer_option(question_id , new_answer_option):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE questions SET `answer_option` = (%s) WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (new_answer_option , question_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def edit_question_option1(question_id , new_op1):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE questions SET `option_1` = (%s) WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (new_op1 , question_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def edit_question_option2(question_id , new_op2):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE questions SET `option_2` = (%s) WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (new_op2 , question_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def edit_question_option3(question_id , new_op3):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE questions SET `option_3` = (%s) WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (new_op3 , question_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def edit_question_option4(question_id , new_op4):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE questions SET `option_4` = (%s) WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (new_op4 , question_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

# exam management ---------

def create_exam(name , designer_id , time , code , is_active = 0):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = '''
        INSERT INTO exam (`name` , `special_code` , `designer_id` , `is_active` , `time`)
        VALUES (%s , %s , %s , %s , %s)
    '''
    cur.execute(SQL_QUERY , (name , code , designer_id , is_active , time))
    result = cur.lastrowid
    connection.commit()
    cur.close()
    connection.close()
    return result

def deactive_exam(exam_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE exam SET `is_active` = 0 WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (exam_id ,))
    connection.commit()
    cur.close()
    connection.close()
    return True

def active_exam(exam_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE exam SET `is_active` = 1 WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (exam_id ,))
    connection.commit()
    cur.close()
    connection.close()
    return True

def change_time_exam(exam_id , new_time):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = 'UPDATE exam SET `time` = (%s) WHERE `id` = (%s)'
    cur.execute(SQL_QUERY , (new_time,exam_id))
    connection.commit()
    cur.close()
    connection.close()
    return True

def add_question_to_exam(question_id , exam_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()
    SQL_QUERY = '''
        INSERT INTO exam_questions (`exam_id` , `question_id`) VALUES (%s , %s)
    '''
    cur.execute(SQL_QUERY , (exam_id , question_id))
    result = cur.lastrowid
    connection.commit()
    cur.close()
    connection.close()
    return result

if __name__ == '__main__' :
    print(add_question_to_exam(2 , 1))
    # active_exam(1)
    # edit_question_category(2 , 2)
    # add_answer_for_question(1 , 2 , 2)
    # add_teacher_with_tel_id(1454840970)
    #print(add_categories('structure'))