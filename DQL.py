import mysql.connector
from config_db import *

def find_user_id(telegram_id):
    '''
        user_id = find_user_id(cid)['ID']
    '''
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

def is_answered_this_question(user_id , question_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = 'SELECT `id` FROM user_answers WHERE `user_id` = (%s) AND `question_id` = (%s)'
    cur.execute(SQL_QUERY , (user_id , question_id))
    result = cur.fetchone()
    cur.close()
    connection.close()
    return result

def find_designer_telegram_id(question_id): # who added this question (question_id) ??
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT Q.ID AS `question_id`,U.telegram_id FROM questions AS Q INNER JOIN users AS U ON Q.designer_id = U.id WHERE Q.ID = (%s);
    ''' 
    cur.execute(SQL_QUERY , (question_id , ))
    result = cur.fetchone()
    cur.close()
    connection.close()
    return result['telegram_id']

def get_report_quiz_from_telegram_id(cid):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        select u.telegram_id , q.id as question_id ,  us.selected_option , q.answer_option , c.name as category_name
        
        from quiz.user_answers as us 

        inner join quiz.users as u 
        on us.user_id = u.id 
        inner join quiz.questions as q
        on q.id = us.question_id
        inner join quiz.categories as c
        on q.category_id = c.id

        where telegram_id = (%s) and us.exam_id is null
    '''
    cur.execute(SQL_QUERY , (cid,))
    result = cur.fetchall()
    cur.close()
    connection.close()
    return result

# exam section

def what_option_answered_in_exam(user_id , question_id , exam_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT selected_option FROM user_answers WHERE user_id = (%s) AND exam_id = (%s) AND question_id = (%s) 
    '''
    cur.execute(SQL_QUERY , (user_id , exam_id , question_id))
    result = cur.fetchone()
    cur.close()
    connection.close()
    return result['selected_option']

def is_answered_in_exam(user_id , exam_id , question_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT id FROM user_answers WHERE user_id = (%s) AND exam_id = (%s) AND question_id = (%s) 
    '''
    cur.execute(SQL_QUERY , (user_id , exam_id , question_id))
    result = cur.fetchall()
    cur.close()
    connection.close()
    return len(result) > 0
    
def get_list_of_question_in_exam(exam_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT question_id AS qid FROM exam_questions WHERE exam_id = (%s) ORDER BY question_id DESC; 
    '''
    cur.execute(SQL_QUERY , (exam_id , ))
    result = cur.fetchall()
    cur.close()
    connection.close()
    return result    

def get_exams_from_user_id(user_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT id,name FROM exam WHERE designer_id = (%s)
    '''
    cur.execute(SQL_QUERY , (user_id , ))
    result = cur.fetchall()
    cur.close()
    connection.close()
    return result

def get_exam_data_id(id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT id,name,special_code,is_active,time FROM exam WHERE id = (%s)
    '''
    cur.execute(SQL_QUERY , (id , ))
    result = cur.fetchone()
    cur.close()
    connection.close()
    return result

def is_special_code_exist(special_code):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT name FROM exam WHERE `special_code` = (%s)
    '''
    cur.execute(SQL_QUERY , (special_code , ))
    result = cur.fetchall()
    cur.close()
    connection.close()
    return len(result) != 0

def get_question_count_for_exam(exam_id):
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor(dictionary=True)
    SQL_QUERY = '''
        SELECT id FROM exam_questions WHERE `exam_id` = (%s)
    '''
    cur.execute(SQL_QUERY , (exam_id , ))
    result = cur.fetchall()
    cur.close()
    connection.close()
    return len(result)

if __name__ == '__main__':
    print(what_option_answered_in_exam(7 , 6 , 1))
    # print(get_report_quiz_from_telegram_id(1454840970)[2])
    # print(find_user_id(1454840970)['ID'])
    # print(find_designer_telegram_id(2))
    # print(is_answered_this_question(2 , 2))
    # print(get_question_information(2))