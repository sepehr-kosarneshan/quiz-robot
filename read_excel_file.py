import pandas as pd
import openpyxl
import os
from DML import *

def check_excel_file(name):
    _,file_type = name.split('.')
    return file_type == 'xlsx'

def get_data_from_excel_exam(excel_file_path , user_id , exam_id):
    try :
        dataframe = pd.read_excel(excel_file_path)
    except :
        return 'ERROR-readexcel'
    print(dataframe)
    for i in range(len(dataframe)):
        try :
            categoryid = int(str(dataframe.category_id[i]).strip())
            questiontext = str(dataframe.text[i]).strip()
            photoid = str(dataframe.photo_id[i]).strip()
            answertext = str(dataframe.answer_text[i]).strip()
            option1 = str(dataframe.op1[i]).strip()
            option2 = str(dataframe.op2[i]).strip()
            option3 = str(dataframe.op3[i]).strip()
            option4 = str(dataframe.op4[i]).strip()
            ansoption = int(str(dataframe.ans_option[i]).strip())
            if photoid.strip() == 'nan':
                photoid = None
            last_row_id = add_question(designer_id = user_id,
                        category_id = categoryid , 
                        text = questiontext , 
                        photo_id = photoid , 
                        anstext = answertext , 
                        op1 = option1 ,
                        op2 = option2 , 
                        op3 = option3 , 
                        op4 = option4 , 
                        ansop = ansoption , 
                        is_public = False)
            add_question_to_exam(last_row_id , exam_id)
        except :
            return f'ERROR-line{i+1}'
    else :
        return True

def get_data_from_excel_quiz(excel_file_path , user_id):
    try :
        dataframe = pd.read_excel(excel_file_path)
    except :
        return 'ERROR-readexcel'
    print(dataframe)
    for i in range(len(dataframe)):
        try :
            categoryid = int(str(dataframe.category_id[i]).strip())
            questiontext = str(dataframe.text[i]).strip()
            photoid = str(dataframe.photo_id[i]).strip()
            answertext = str(dataframe.answer_text[i]).strip()
            option1 = str(dataframe.op1[i]).strip()
            option2 = str(dataframe.op2[i]).strip()
            option3 = str(dataframe.op3[i]).strip()
            option4 = str(dataframe.op4[i]).strip()
            ansoption = int(str(dataframe.ans_option[i]).strip())
            if photoid.strip() == 'nan':
                photoid = None
            add_question(designer_id = user_id,
                        category_id = categoryid , 
                        text = questiontext , 
                        photo_id = photoid , 
                        anstext = answertext , 
                        op1 = option1 ,
                        op2 = option2 , 
                        op3 = option3 , 
                        op4 = option4 , 
                        ansop = ansoption)
        except :
            return f'ERROR-line{i+1}'
    else :
        return True

if __name__ == '__main__':
    path = r'C:\Users\user\Desktop\quizbot\excel_files\data\1454840970-1787933438803456.xlsx'
    print(get_data_from_excel_quiz(path , 1))