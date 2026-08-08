import mysql.connector
from config_db import *

def create_database():
    connection = mysql.connector.connect(**config)
    cur = connection.cursor()
    cur.execute(f'DROP DATABASE IF EXISTS {database_name};')
    cur.execute(f'CREATE DATABASE IF NOT EXISTS {database_name};')
    print(f'data base {database_name} created')
    cur.close()
    connection.close()

def create_table_users():
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()

    cur.execute('''
        CREATE TABLE users (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNSIGNED UNIQUE,
            username VARCHAR(255),
            name VARCHAR(255),
            is_admin BOOLEAN DEFAULT 0,
            is_teacher BOOLEAN DEFAULT 0,
            register_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );''')
    
    connection.commit()
    print(f'table users created')
    cur.close()
    connection.close()

def create_table_categories():
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()

    cur.execute('''
        CREATE TABLE categories (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            register_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );''')
    
    connection.commit()
    print(f'table categories created')
    cur.close()
    connection.close()

def create_table_questions():
    connenction = mysql.connector.connect(**config , database = database_name)
    cur = connenction.cursor()

    cur.execute('''
        CREATE TABLE questions (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            category_id INT UNSIGNED,
            designer_id INT UNSIGNED,
            text TEXT NOT NULL,
            photo_id VARCHAR(255),
            answer_text TEXT NOT NULL,
            answer_option TINYINT UNSIGNED,
            option_1 VARCHAR(255) NOT NULL,
            option_2 VARCHAR(255) NOT NULL,
            option_3 VARCHAR(255) NOT NULL,
            option_4 VARCHAR(255) NOT NULL,
            is_public BOOLEAN DEFAULT 1,
            register_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
            FOREIGN KEY (designer_id) REFERENCES users(id) ON DELETE SET NULL
        );''')
    connenction.commit()
    print('table questions created')
    cur.close()
    connenction.close()

def create_table_exam():
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()

    cur.execute('''
        CREATE TABLE exam (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            special_code VARCHAR(100) NOT NULL UNIQUE,
            designer_id INT UNSIGNED,
            start_time DATETIME NOT NULL,    
            end_time DATETIME NOT NULL,   
            register_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (designer_id) REFERENCES users(id) ON DELETE CASCADE
        );''')
    
    connection.commit()
    print('table exam created')
    cur.close()
    connection.close()

def create_table_exam_questions():
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()

    cur.execute('''
        CREATE TABLE exam_questions (
            exam_id INT UNSIGNED,
            question_id INT UNSIGNED,
            time_to_answer INT UNSIGNED NOT NULL DEFAULT 60,
            PRIMARY KEY (exam_id, question_id),
            FOREIGN KEY (exam_id) REFERENCES exam(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );''')
    
    connection.commit()
    print('table exam_questions created')
    cur.close()
    connection.close()

def create_user_answer_table():
    connection = mysql.connector.connect(**config , database = database_name)
    cur = connection.cursor()

    cur.execute('''
        CREATE TABLE user_answers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT UNSIGNED NOT NULL,           
            question_id INT UNSIGNED NOT NULL,
            exam_id INT UNSIGNED DEFAULT NULL,          
            selected_option TINYINT NOT NULL,  
            register_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
            FOREIGN KEY (exam_id) REFERENCES exam(id) ON DELETE CASCADE
        );''')
    connection.commit()
    print('table user_answer created')
    cur.close()
    connection.close()

if __name__ == '__main__':
    create_database()
    create_table_users()
    create_table_categories()
    create_table_questions()
    create_table_exam()
    create_table_exam_questions()
    create_user_answer_table()


