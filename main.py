import telebot
from telebot.types import ReplyKeyboardMarkup , ReplyKeyboardRemove,InlineKeyboardMarkup,InlineKeyboardButton
from config_bot import *
from config_db import *
import os
import time
import random
from Text import *
from DQL import *
from DML import *
from read_excel_file import *
import secrets
import threading
import logging
import openpyxl

os.makedirs('Data' , exist_ok=True)
logging.basicConfig(filename = os.path.join('Data','project.log') 
                    , level = logging.INFO
                    , format = '%(asctime)s-%(levelname)s : %(message)s'
                    , encoding = 'utf-8') 

logging.info('Data folder created')

# from requests_forwarder import setup_proxy
# setup_proxy(proxy_token=proxy_token)

bot = telebot.TeleBot(telegram_token , threaded= 5)
hide_board = ReplyKeyboardRemove()

os.makedirs(os.path.join('excel_files' , 'data') , exist_ok=True)
logging.info('excel_files/data created')

CHANNEL_ID = -1004392460681 #messages

command = {
    '/start'            : text['start_command'],
    '/help'             : text['help_command'],
    '/support'          : text['support_command'],
    '/quiz'             : text['quiz_creating_command'],
    '/showcategory'     : text['show_categories'],
    '/reqteach'         : text['request_teacher'],
}

teacher_commands = {
    '/addquestion' : text['add_question_teacher'],
    '/addcategory' : text['add_category_command'],
}

admin_commands = {
}

CHANNEL_MESSAGES = {
    'start'             : 2,
    'help'              : 4,
    'req_support'       : 6,
    'sended_support'    : 8,
    'teacher_request'   : 10,
    'you_added_teacher' : 12,
    'request_for_quiz'  : 14,
    'quesiton_report'   : 16,
    'guideforexcelQ'    : 18,
    'showexamsandmanage': 20,
    'guideformanageexam': 22,
    'guideforenterexam' : 24,
    'examended'         : 26,
    'showreportforexam' : 28,
    'helpteachers'      : 30,
}

EDIT_QUESTION_PAGES = [
    #page 0
    [{'button_text' : text['edit_question_categoty'] , 'data' : 'editquestion_category_'},\
    {'button_text' : text['edit_question_text'] , 'data' : 'editquestion_text_'},\
    {'button_text' : text['edit_question_photo_id'] , 'data' : 'editquestion_photo_'},\
    {'button_text' : text['edit_question_anstext'] , 'data' : 'editquestion_anstext_'},\
    {'button_text' : text['edit_question_ansop'] , 'data' : 'editquestion_ansop_'}],
    #page 1
    [{'button_text' : text['edit_question_op1'] , 'data' : 'editquestion_op1_'},\
    {'button_text' : text['edit_question_op2'] , 'data' : 'editquestion_op2_'},\
    {'button_text' : text['edit_question_op3'] , 'data' : 'editquestion_op3_'},\
    {'button_text' : text['edit_question_op4'] , 'data' : 'editquestion_op4_'},\
    {'button_text' : text['end_edit_question'] , 'data' : 'editquestion_end_'}]
]

user_step = {}

TEACHER_PANEL = 0
GENERAL_QUIZ_PANEL = 1
EXAM_PANEL = 2
ADDAQUESTIONEXAM = 3

user_panel = {} # cid : panel
admin_question = {} # cid : {text : ... , file_id : ... , options : ... , answer_option : ... , answer_text : ...}
teacher_exam = {} # cid : {name : ... , time : ...}
exam_cid_time = {} # {... , exam_id : {cid : start_time , ... } , ...}
delete_messages_dict = {} # {(mid , cid) : time to delete , ...}

# ----- spam
lower_limit = 2     # sec
upper_limit = 15    # sec
max_score = 10
# cid : {last_message_time : ... , score : ...}
spam_data = {}  

teachers = []
admins = []

question_count = 1 # for public quiz

def send_message(*args, **kwars):
    try:
        return bot.send_message(*args, **kwars)
    except Exception as e:
        logging.error(f'{e} occured in sending')

def send_photo(*args, **kwars):
    try:
        return bot.send_photo(*args, **kwars)
    except Exception as e:
        logging.error(f'{e} occured in sending photo')

def send_document(*args, **kwars):
    try:
        return bot.send_document(*args, **kwars)
    except Exception as e:
        logging.error(f'{e} occured in sending document')

def generate_exam_special_code(length = 7):
    characters = "ABCDEFGHJKMNPQRSTUVWXYZ23456789!*&%$#"
    return "".join(secrets.choice(characters) for _ in range(length))

def get_admins():
    global admins
    data = get_admins_db()
    for user in data :
        admins.append(user['telegram_id'])
        logging.info(f'{user['telegram_id']} is admin')
    # print(admins)

def get_teachers():
    global teachers
    data = get_teachers_db()
    for user in data :
        teachers.append(user['telegram_id'])
        logging.info(f'{user['telegram_id']} is teacher')
    # print(teachers)

def set_name(first_name , last_name) :
    if first_name is not None :
        if last_name is not None :
            name = first_name + ' ' + last_name
        else :
            name = first_name
    else :
        if last_name is not None :
            name = last_name
        else :
            name = None
    return name

def manage_user(message , cid): 
    global admins
    global teachers
    # print('teachers : ' , teachers , sep = ' : ')
    data = get_user_data_from_cid(cid)
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    name = set_name(first_name , last_name)     
    if data is not None:
        edit_user_username(cid , username)
        edit_user_name(cid , name)
        if (data['is_admin'] == 1) and (cid not in admins):
            admins.append(cid)
        elif data['is_admin'] == 0:
            if cid in admins:
                admins.remove(cid)
        if (data['is_teacher'] == 1) and (cid not in teachers):
            teachers.append(cid)
        elif data['is_teacher'] == 0:
            if cid in teachers :
                teachers.remove(cid)
    else :
        add_user(cid , False , False , username , name)
        print(f'new user with cid = {cid} added to database')
        logging.info(f'new user with cid = {cid} added to database')
    return True

def is_spam(cid):
    if spam_data.get(cid , False) :
        t = time.time()
        dt = t - spam_data[cid]['last_message_time']
        if dt >= upper_limit:
            n = int(dt / upper_limit)
            spam_data[cid]['score'] = max(0 , spam_data[cid]['score'] - n)
        elif dt <= lower_limit:
            spam_data[cid]['score'] += 1
        spam_data[cid]['last_message_time'] = t
    else : 
        spam_data.setdefault(cid,{'last_message_time' : time.time() , 'score' : 0})
        return False
    
    if spam_data[cid]['score'] >= max_score:
        logging.info(f'{cid} is in the spam list')
        return True
    else :
        return False

def reply_message_type(message):
    try :
        reply_id = message.reply_to_message.forward_origin.type
        # print(reply_id)
    except :
        reply_id = False
    return reply_id

def show_commands(cid):
    result = ''
    for key , value in command.items():
        result += f'✅ {key} : _{value}_\n'
    if (cid in teachers) and (len(teacher_commands) > 0):
        result += '\n*TEACHER COMMANDS*\n\n'
        for key , value in teacher_commands.items():
            result += f'✅ {key} : _{value}_\n'
    if (cid in admins) and (len(admin_commands) > 0): 
        result += '\n*ADMIN COMMANDS*\n\n'
        for key , value in admin_commands.items():
            result += f'✅ {key} : _{value}_\n'
    return result

def create_start_keyboard(cid) :
    try :
        user_panel.pop(cid)
    except :
        pass
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Button['start'] , Button['help'],Button['support'])
    keyboard.add(Button['showcategory'])
    keyboard.add(Button['quiz'],Button['exam'])
    keyboard.add(Button['reportpanel'])
    if  (cid not in teachers) and (cid not in admins):
        keyboard.add(Button['req_teacher'])
    else:
        # keyboard.add(Button['addquestion'],Button['addcategory'])
        keyboard.add(Button['teacherpanel'])
        
    return keyboard
# ---------------

def generate_sample_excel(file_path=os.path.join('excel_files' , 'sample.xlsx')):
    if os.path.exists(file_path):
        return file_path
    
    wb = openpyxl.Workbook()
    ws = wb.active

    headers = ["category_id", "text", "photo_id", "answer_text", "op1", "op2", "op3", "op4", "ans_option"]
    ws.append(headers)

    row_2 = ["", "", "NULL", '"isphoto" + photo_id if you have a picture', "", "", "", "", ""]
    ws.append(row_2)

    wb.save(file_path)
    return file_path

generate_sample_excel()
logging.info('sample.xlsx created')

# ---------------
def create_teacher_panel(cid) :
    user_panel[cid] = TEACHER_PANEL
    if (cid not in teachers) and (cid not in admins):
        return False
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Button['generalquizpanel'] , Button['exammanagement'])
    keyboard.add(Button['addcategory'])
    keyboard.add(Button['exitteacherpanel'],Button['support'])
    return keyboard

def create_general_quiz_panel(cid):
    user_panel[cid] = GENERAL_QUIZ_PANEL
    if (cid not in teachers) and (cid not in admins):
        return False
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Button['addquestion'],Button['addquestionmul'])
    # keyboard.add(Button['addquestionmul'])
    keyboard.add(Button['showphotoid'])
    keyboard.add(Button['guideformultipleques'])
    keyboard.add(Button['exitgeneralquizpanel'],Button['support'])
    return keyboard

def create_exam_management_panel(cid):
    user_panel[cid] = EXAM_PANEL
    if (cid not in teachers) and (cid not in admins):
        return False
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Button['showexams'] , Button['createexam'])
    keyboard.add(Button['showphotoid'])
    keyboard.add(Button['guideformultipleques'])
    keyboard.add(Button['exitexammanagement'],Button['support'])
    return keyboard

def create_report_panel(cid):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Button['quizreport']) 
    keyboard.add(Button['examreport'])  
    keyboard.add(Button['exitreportpanel'],Button['support'])
    return keyboard
# ---------------

def create_category_excel(data): # data : DQL.get_categories() in excel_files folder on category.xlsx
    with open(os.path.join('excel_files' , 'category.csv') , 'w' , encoding="utf-8-sig") as f:
        result = 'name,id\n'
        for item in data:
            result += f'{item['NAME']},{item['ID']}\n'
        f.write(result)
        logging.info('ctegory.csv created')
    return True

# report ------------------

def create_report_quiz(cid): # working here ... 
    db_data = get_report_quiz_from_telegram_id(cid)
    report_dict = {} # 'category_name' : {true : ... , false : ...}
    for item in db_data:
        category_name = item['category_name']
        report_dict.setdefault(category_name , {'true' : 0 , 'false' : 0})
        if item['answer_option'] == item['selected_option']:
            report_dict[category_name]['true'] += 1
        else :
            report_dict[category_name]['false'] += 1
    
    result_text = text['reporttextquiz'] + '\n\n'
    # print(report_dict)
    for key in report_dict.keys():
        value = report_dict[key]
        percent = (100 * value['true'])/(value['true'] + value['false'])
        result_text += f'__{key}__\n'
        result_text += text['correct'] + '\n'
        result_text += str(value['true']) + '\n'
        result_text += text['false'] + '\n'
        result_text += str(value['false']) + '\n'
        result_text += text['percent'] + '\n'
        result_text += f'*{clean_text_for_markdown(str(round(percent , 3)))}%*\n\n'
        result_text += clean_text_for_markdown('---------------------------------\n')
    logging.info(f'quiz report created for {cid}')
    return result_text.strip(clean_text_for_markdown('---------------------------------'))
                

def create_report_exam(cid , exam_id): 
    db_data = get_report_exam_from_telegram_id(cid , exam_id)
    total_questions = len(get_list_of_question_in_exam(exam_id))
    name = get_exam_data_id(exam_id)['name']
    report_dict = {} # 'category_name' : {true : ... , false : ...}
    for item in db_data:
        category_name = item['category_name']
        report_dict.setdefault(category_name , {'true' : 0 , 'false' : 0})
        if item['answer_option'] == item['selected_option']:
            report_dict[category_name]['true'] += 1
        else :
            report_dict[category_name]['false'] += 1
    result_text = text['reportexamuser'] + '\n'
    result_text += name + '\n\n'
    # print(report_dict)
    for key in report_dict.keys():
        value = report_dict[key]
        percent = (100 * value['true'])/(total_questions)
        result_text += f'__{key}__\n'
        result_text += text['correct'] + '\n'
        result_text += str(value['true']) + '\n'
        result_text += text['false'] + '\n'
        result_text += str(value['false']) + '\n'
        result_text += text['empty'] + '\n'
        result_text += str(total_questions - value['true'] - value['false']) + '\n'
        result_text += text['percent'] + '\n'
        result_text += f'*{clean_text_for_markdown(str(round(percent , 3)))}%*\n\n'
        result_text += clean_text_for_markdown('---------------------------------\n')
    logging.info(f'exam report created for {cid} in exam No.{exam_id}')
    return result_text.strip(clean_text_for_markdown('---------------------------------'))

# ---------------------

def category_pages(clist) : # clist : DQL.get_categories()
    result = []
    row = []
    for i in range(len(clist)):
        row.append(clist[i])
        if len(row) >= 3:
            result.append(row)
            row = [] 
    if len(row) > 0:
        result.append(row)
    return result

# ----------------------------------- Inline Keyboards

def create_inlinekeyboard_for_categoris(clist , page) : # clist : DQL.get_categories() and page starts from 0
    category_pages_list = category_pages(clist)
    if 0<= page <= len(category_pages_list) - 1 :
        categories = category_pages_list[page]
        markup = InlineKeyboardMarkup()
        for i in range(len(categories)):
            markup.add(InlineKeyboardButton(f'{categories[i]['NAME']}' , callback_data=f'categorychoice_{categories[i]['ID']}'))
        left_button = InlineKeyboardButton('◀️' , callback_data=f'changepageshowcat_{page - 1}')
        right_button = InlineKeyboardButton('▶️' , callback_data=f'changepageshowcat_{page + 1}')
        if page == len(category_pages_list) - 1:
            markup.add(left_button)
        elif page == 0 : 
            markup.add(right_button)
        else :
            markup.add(left_button , right_button)
        return markup
    else :
        return False

def create_inlinekeyboard_for_categoris_quizmaking(clist , page) : # clist : DQL.get_categories() and page starts from 0
    category_pages_list = category_pages(clist)
    if 0<= page <= len(category_pages_list) - 1 :
        categories = category_pages_list[page]
        markup = InlineKeyboardMarkup()
        for i in range(len(categories)):
            markup.add(InlineKeyboardButton(f'{categories[i]['NAME']}' , callback_data=f'quizmakingcatchoice_{categories[i]['ID']}'))
        left_button = InlineKeyboardButton('◀️' , callback_data=f'chpagequiz_{page - 1}')
        right_button = InlineKeyboardButton('▶️' , callback_data=f'chpagequiz_{page + 1}')
        if page == len(category_pages_list) - 1:
            markup.add(left_button)
        elif page == 0 : 
            markup.add(right_button)
        else :
            markup.add(left_button , right_button)
        return markup
    else :
        return False

def create_inlinekeyboard_for_categoris_editques(clist , page , qid) : # clist : DQL.get_categories() and page starts from 0
    category_pages_list = category_pages(clist)
    if 0<= page <= len(category_pages_list) - 1 :
        categories = category_pages_list[page]
        markup = InlineKeyboardMarkup()
        for i in range(len(categories)):
            markup.add(InlineKeyboardButton(f'{categories[i]['NAME']}' , callback_data=f'editquestioncateg_{categories[i]['ID']}_{qid}'))
        left_button = InlineKeyboardButton('◀️' , callback_data=f'chpageeditques_{page - 1}_{qid}')
        right_button = InlineKeyboardButton('▶️' , callback_data=f'chpageeditques_{page + 1}_{qid}')
        if page == len(category_pages_list) - 1:
            markup.add(left_button)
        elif page == 0 : 
            markup.add(right_button)
        else :
            markup.add(left_button , right_button)
        return markup
    else :
        return False

def create_inlinekeyboard_for_teacher_request(cid , mid , answer = True , addteacher = True):
    markup = InlineKeyboardMarkup()
    if answer :
        status = '1'
        if addteacher :
            status += '1'
        else :
            status += '0'
        button1 = InlineKeyboardButton('Answer' , callback_data= f'reqteach_ans_{cid}|{mid}_{status}')
        markup.add(button1)
    if addteacher :
        status = ''
        if answer :
            status = '11'
        else :
            status = '01'
        button2 = InlineKeyboardButton('Add Teacher' , callback_data= f'reqteach_add_{cid}|{mid}_{status}')
        markup.add(button2)
    else :
        status = '00'
    button3 = InlineKeyboardButton('Show Information' , callback_data= f'reqteach_si_{cid}|{mid}_{status}')
    markup.add(button3)
    return markup

# ---------------

def create_list_question_exam(cid , exam_id):
    data = get_list_of_question_in_exam(exam_id)
    question_list = []
    for item in data:
        question_list.append(item['qid'])
    random.seed(cid)
    random.shuffle(question_list)
    return question_list

def create_list_quiz_public(category_id , question_count): # working here ...
    list_of_ids = get_question_id_public(category_id=category_id)
    try :
        list_of_ids = random.sample(list_of_ids , k = question_count)
    except :
        return False
    return list_of_ids

def create_text_caption_for_question(question_id):
    info = get_question_information(question_id=question_id)
    question_text = info['text']
    option_1 = info['option_1']
    option_2 = info['option_2']
    option_3 = info['option_3']
    option_4 = info['option_4']
    result = question_text + '\n\n'
    result += '✅' + text['options'] + '✅' + '\n\n'
    result += f'{option_sticker['1']} : {option_1}\n\n'
    result += f'{option_sticker['2']} : {option_2}\n\n'
    result += f'{option_sticker['3']} : {option_3}\n\n'
    result += f'{option_sticker['4']} : {option_4}\n'
    return result

# enter exam -------------------------------------------

def create_inline_for_exam(exam_id , question_index , cid , next = True):
    '''
        question_index : index of id in create_list_question_exam(exam_id , cid)
        0 =< question_index  < len(create_list_question_exam(exam_id , cid)) and starts at zero
    '''
    next_var = 1
    if next == False:
        next_var = 0
    data = create_list_question_exam(cid , exam_id)
    if len(data) == 0:
        return False
    markup = InlineKeyboardMarkup()
    Buttons = [InlineKeyboardButton(option_sticker['1'] , callback_data = f'examop_1_{question_index}_{exam_id}_{next_var}') ,\
               InlineKeyboardButton(option_sticker['2'] , callback_data = f'examop_2_{question_index}_{exam_id}_{next_var}') ,\
               InlineKeyboardButton(option_sticker['3'] , callback_data = f'examop_3_{question_index}_{exam_id}_{next_var}'),\
               InlineKeyboardButton(option_sticker['4'] , callback_data = f'examop_4_{question_index}_{exam_id}_{next_var}')]
    
    markup.add(Buttons[0] , Buttons[1])
    markup.add(Buttons[2] , Buttons[3])
    if next_var == 1:        
        right_button = InlineKeyboardButton(text['nextquestionexam'] , callback_data=f'examquestionselect_{question_index + 1}_{exam_id}')
        if question_index != len(data) - 1:
            markup.add(right_button)
    markup.add(InlineKeyboardButton(text['get_answer_for_question'] , callback_data=f'examgetanswer_{data[question_index]}_{exam_id}' , style='primary'))
    markup.add(InlineKeyboardButton(text['endexamtime'] , callback_data = f'endtimeexam_{exam_id}'))

    print(f'this inline created for question with id = {data[question_index]}')

    return markup

def create_inline_for_answered_in_exam(user_choice , exam_id , question_index , cid , next = True):
    data = create_list_question_exam(cid , exam_id)
    qid = data[question_index]
    next_var = 1
    if next == False:
        next_var = 0
    else :
        if question_index == len(data) - 1:
            next_var = 0
    markup = InlineKeyboardMarkup()
    options = ['1' , '2' , '3' , '4']
    for i in range(len(options)):
        if str(user_choice) == options[i]:
            options[i] += 'u'
    Buttons = []
    for i in range(len(options)):
        calldata = f'examop_{options[i][0]}_{question_index}_{exam_id}_{next_var}'
        # print(data)
        text_option = option_sticker[str(options[i][0])]
        if 'u' in options[i]:
            Buttons.append(InlineKeyboardButton(text_option , callback_data = calldata , style='primary'))
        else :
            Buttons.append(InlineKeyboardButton(text_option , callback_data = calldata))
    markup.add(Buttons[0] , Buttons[1])
    markup.add(Buttons[2] , Buttons[3])

    if next_var == 1:
        right_button = InlineKeyboardButton(text['nextquestionexam'] , callback_data=f'examquestionselect_{question_index + 1}_{exam_id}')
        if question_index != len(data) - 1:
            markup.add(right_button)
    markup.add(InlineKeyboardButton(text['get_answer_for_question'] , callback_data=f'examgetanswer_{qid}_{exam_id}' , style='primary'))
    markup.add(InlineKeyboardButton(text['endexamtime'] , callback_data = f'endtimeexam_{exam_id}'))

    print(f'this answered inline created for question with id = {data[question_index]} with user choice {user_choice}')

    return markup

def send_question_exam(cid , question_index , exam_id , markup):
    data = create_list_question_exam(cid , exam_id)
    if len(data) == 0:
        return False
    info = get_question_information(question_id = data[question_index])
    photo_id = info['photo_id']
    result = create_text_caption_for_question(data[question_index])
    if photo_id is not None : 
        message = send_photo(cid , photo_id , caption=result , reply_markup=markup)
    else :
        message = send_message(cid , result , reply_markup=markup)
    logging.info(f'question No.{data[question_index]} sended to {cid} in exam No.{exam_id}')
    return message 

# ------------------------

def create_inline_for_answered_option(user_choice ,correct_option , question_id , mid):
    markup = InlineKeyboardMarkup()
    options = ['1' , '2' , '3' , '4']
    for i in range(len(options)):
        if options[i] == str(user_choice) and options[i] == str(correct_option):
            options[i] += 'uc'
        elif options[i] == str(correct_option) :
            options[i] += 'c'
        elif options[i] == str(user_choice) :
            options[i] += 'u'
    Buttons = []
    for i in range(len(options)):
        if 'uc' in options[i]:
            text_option = option_sticker[str(options[i][0])]
            Buttons.append(InlineKeyboardButton(text_option , callback_data='None' , style='success'))
        elif 'u' in options[i]:
            text_option = option_sticker[str(options[i][0])]
            Buttons.append(InlineKeyboardButton(text_option , callback_data='None' , style= 'danger'))
        elif 'c' in options[i] :
            text_option = option_sticker[str(options[i][0])]
            Buttons.append(InlineKeyboardButton(text_option , callback_data='None' , style= 'success'))
        else :
            text_option = option_sticker[str(options[i][0])]
            Buttons.append(InlineKeyboardButton(text_option , callback_data='None'))
    markup.add(Buttons[0] , Buttons[1])
    markup.add(Buttons[2] , Buttons[3])
    markup.add(InlineKeyboardButton(text['get_answer_for_question'] , callback_data=f'getanswer_{mid}_{question_id}' , style='primary'))
    markup.add(InlineKeyboardButton(text['delete_question'] , callback_data=f'deletequestion'))
    return markup

def create_inline_for_options(question_id):
    markup = InlineKeyboardMarkup()
    Buttons = [InlineKeyboardButton(option_sticker['1'] , callback_data = f'option_1_{question_id}') ,\
            InlineKeyboardButton(option_sticker['2'] , callback_data = f'option_2_{question_id}') ,\
            InlineKeyboardButton(option_sticker['3'] , callback_data = f'option_3_{question_id}'),\
            InlineKeyboardButton(option_sticker['4'] , callback_data = f'option_4_{question_id}'),\
            InlineKeyboardButton(text['delete_question'] , callback_data=f'deletequestion')]

    markup.add(Buttons[0] , Buttons[1])
    markup.add(Buttons[2] , Buttons[3])
    markup.add(Buttons[4])
    return markup

def create_inline_for_edit_question(question_id , page): # page 0 or 1
    markup = InlineKeyboardMarkup()
    # markup.add(InlineKeyboardButton(text['edit_question_categoty']  , callback_data=f'editquestion_category_{question_id}'))
    list_of_buttons = EDIT_QUESTION_PAGES[page]
    for i in range(len(list_of_buttons)):
        markup.add(InlineKeyboardButton(list_of_buttons[i]['button_text'] , callback_data = list_of_buttons[i]['data'] + f'{question_id}'))
    if page == 0 :
        markup.add(InlineKeyboardButton( '▶️', callback_data = f'editqpage_1_{question_id}'))
    elif page == 1:
        markup.add(InlineKeyboardButton( '◀️', callback_data = f'editqpage_0_{question_id}'))
    else :
        return False
    return markup

def send_question_quiz(cid , question_id):
    info = get_question_information(question_id=question_id)
    photo_id = info['photo_id']
    markup = create_inline_for_options(question_id=question_id)
    result = create_text_caption_for_question(question_id=question_id)
    if photo_id is not None : 
        message = send_photo(cid , photo_id , caption=result , reply_markup=markup)
    else :
        message = send_message(cid , result , reply_markup=markup)
    logging.info(f'question No.{question_id} sended for {cid} in general quiz')
    return message
# ----------------------------------
def create_text_for_exam_data(id):
    data = get_exam_data_id(id)
    active = 'Yes' if data['is_active'] == 1 else 'No'
    result = f'ℹ️ Information ℹ️\n✅ID : {data['id']}\n✅Name : {data['name']}\n✅Special Code : {data['special_code']}\n✅Active : {active}\n✅Time : {data['time']} minutes'
    return result 

def clean_text_for_markdown(text_):
    result = ''
    for char in text_ :
        if char in r'_*[]()~`>#+-=|{}.!\'\\':
            result += fr'\{char}'
        else :
            result += char
    return result

def create_text_for_starting_exam(exam_id):
    info = get_exam_data_id(exam_id)
    total_question = get_question_count_for_exam(exam_id)
    result = f' نام آزمون : {info['name']}\n\nتعداد سوال : {total_question}\n\nمدت زمان پاسخ دهی : {info['time']} دقیقه'
    return result

def create_text_for_exam_code(code , exam_name):
    clean_code = clean_text_for_markdown(code)
    clean_exam_name = clean_text_for_markdown(exam_name)
    clean_guide_text = clean_text_for_markdown(text['examcodecopy'])
    result = text['createtextforcode']
    result += f'\n__{clean_exam_name}__'
    result += f'\n\n`{clean_code}`\n\n'
    result += f'_{clean_guide_text}_'
    return result

def create_inline_manage_exam(id):
    '''
        id --> exam id
    '''
    markup = InlineKeyboardMarkup()
    data = get_exam_data_id(id)
    if data['is_active'] == 1:
        markup.add(InlineKeyboardButton(text['deactivate'] , callback_data=f'examdeactive_{id}' , style='danger') \
                  ,InlineKeyboardButton(text['timechange'] , callback_data=f'examtimechange_{id}'))
    else :
        markup.add(InlineKeyboardButton(text['activate'] , callback_data=f'examactive_{id}' , style='success') \
                  ,InlineKeyboardButton(text['timechange'] , callback_data=f'examtimechange_{id}'))
    markup.add(InlineKeyboardButton(text['examaddonequestion'] , callback_data=f'examaddone_{id}'))
    markup.add(InlineKeyboardButton(text['examaddmulquestion'] , callback_data=f'examaddmul_{id}'))
    markup.add(InlineKeyboardButton(text['questioncount'] , callback_data=f'getcountquestion_{id}' , style='primary'),\
               InlineKeyboardButton(text['specialcodeget'] , callback_data=f'getspecialcode_{id}' , style = 'primary'))        
    markup.add(InlineKeyboardButton('🗑️' , callback_data = 'deletemessage'))
    return markup

def create_page_list_for_exams(data):
    '''
        data = get_exams_from_user_id(user_id)
    '''
    result = []
    row = []
    for i in range(len(data)):
        row.append(data[i])
        if len(row) >= 4:
            result.append(row)
            row = [] 
    if len(row) > 0:
        result.append(row)
    return result

def create_inline_for_show_exams(data , page = 0): 
    '''
        data = get_exams_from_user_id(user_id)
    '''
    exam_pages = create_page_list_for_exams(data)
    if 0<= page <= len(exam_pages) - 1 :
        exam = exam_pages[page]
        markup = InlineKeyboardMarkup()
        for i in range(len(exam)):
            markup.add(InlineKeyboardButton(f'{exam[i]['name']}' , callback_data= f'examshowdata_{exam[i]['id']}'))
        left_button = InlineKeyboardButton('◀️' , callback_data=f'examshowchpage_{page - 1}')
        right_button = InlineKeyboardButton('▶️' , callback_data=f'examshowchpage_{page + 1}')
        if len(exam_pages) != 1:
            if page == len(exam_pages) - 1:
                markup.add(left_button)
            elif page == 0 : 
                markup.add(right_button)
            else :
                markup.add(left_button , right_button)
        return markup
    else :
        return False

def create_inline_for_show_exams_for_report(data , page = 0): 
    '''
        data = get_exam_participation_cid(cid)
    '''
    exam_pages = create_page_list_for_exams(data)
    if 0<= page <= len(exam_pages) - 1 :
        exam = exam_pages[page]
        markup = InlineKeyboardMarkup()
        for i in range(len(exam)):
            markup.add(InlineKeyboardButton(f'{exam[i]['name']}' , callback_data= f'examshowreport_{exam[i]['exam_id']}'))
        left_button = InlineKeyboardButton('◀️' , callback_data=f'examshowreportchpage_{page - 1}')
        right_button = InlineKeyboardButton('▶️' , callback_data=f'examshowreportchpage_{page + 1}')
        if len(exam_pages) != 1:
            if page == len(exam_pages) - 1:
                markup.add(left_button)
            elif page == 0 : 
                markup.add(right_button)
            else :
                markup.add(left_button , right_button)
        return markup
    else :
        return False

# --------------------- worker

def check_exam_time():
    global exam_cid_time
    delete_id = []
    for exam_id in exam_cid_time:
        value = exam_cid_time[exam_id]
        dt = get_exam_data_id(exam_id)['time'] * 60 # second
        for cid in value:
            if value[cid] is not None:
                now = time.time()
                if now - value[cid] >= dt:
                    value[cid] = None
                    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['examended'])
                    logging.info(f'Exam time is over for {cid} in exam No.{exam_id}')
        for cid in value:
            if value[cid] is not None:
                break
        else :
            delete_id.append(exam_id)

    for id in delete_id:
        logging.info(f'Exam No.{exam_id} becomes Deacive because all of the students finished')
        deactive_exam(id)
        exam_cid_time.pop(id)

def check_cid_in_exam(cid , exam_id):
    data = exam_cid_time.get(exam_id , False)
    if data != False:
        data = data.get(cid , False)
        if data != False:
            if data is None :
                return False
            else :
                return True
        else :
            return False
    else :
        return False

def check_delete_messages_list():
    # (mid , cid) : time to delete , ...}
    global delete_messages_dict
    pop_list = [] # mid
    for cmid in delete_messages_dict:
        mid,cid = cmid
        time_to_delete = delete_messages_dict[cmid]
        now = time.time()
        if now >= time_to_delete:
            try : 
                bot.delete_message(cid , mid)
            except :
                pass
            pop_list.append(cmid)
    for item in pop_list:
        mid,cid = item
        logging.info(f'message with id {mid} in chat {cid} deleted after its time interval')
        delete_messages_dict.pop(item)

def worker(deltatime):
    while True:
        try :
            if len(teachers) == 0 and len(admins) == 0:
                get_admins()
                get_teachers()
                logging.info(f'Bot Started and We have Teachers and Admins')
            check_delete_messages_list()
            check_exam_time()
            # print(delete_messages_dict)
            # print(exam_cid_time)
            time.sleep(deltatime)
        except :
            pass
    
thread = threading.Thread(
    target=worker, 
    args=(5,), 
    daemon=True
)

# ---------------------

def listener(messages):
    for m in messages:
        if m.content_type == 'text' :
            print(f'{m.chat.id}  [{m.from_user.username}] : {m.text}')
            logging.critical(f'{m.chat.id}  [{m.from_user.username}] : {m.text}')
        else :
            print(f'{m.chat.id}  [{m.from_user.username}] : new {m.content_type} recieved')
            logging.critical(f'{m.chat.id}  [{m.from_user.username}] : new {m.content_type} recieved')

bot.set_update_listener(listener)

@bot.callback_query_handler(func= lambda c : True)
def callback_handler(call):
    cid = call.message.chat.id
    if is_spam(cid) :
        return 
    mid = call.message.message_id
    call_id = call.id
    data = call.data
    logging.info(f'in message with id {mid} in {cid} call with id {call_id} with data = {data} received')

    # Suuport And Admin Answer --------------
    if data.startswith('anssupport'):
        _,user_cid,user_mid = data.split('_')
        if get_support_status(user_id = find_user_id(user_cid)['ID'] , user_mid= user_mid)['admin_id'] is None :
            user_step.setdefault(cid , f'adminanswer_{user_cid}_{user_mid}')
            send_message(cid , text['support_message'])
            bot.edit_message_reply_markup(cid , mid , reply_markup=None)
            bot.answer_callback_query(call_id , 'answer')
        else :
            bot.answer_callback_query(call_id , 'answered')
            bot.delete_message(cid , mid)
            send_message(cid , text['support_another_admin'])

    # Category choice for add one question in exam and quiz --------------
    elif data.startswith('categorychoice'):
        _,category_id = data.split('_')
        category_id = int(category_id)
        bot.delete_message(cid , mid)
        bot.answer_callback_query(call_id , f'{category_id}')

        send_message(cid , text['add_question_admin_resp'])
        send_message(cid , text['photo_and_text_question'])
        if str(user_panel[cid]).startswith('ADDAQUESTIONEXAM') :
            status = user_panel[cid]
            _,exam_id = status.split('_')
            user_step.setdefault(cid , '')
            user_step[cid] = f'addquestion_{category_id}_{exam_id}'
            user_panel[cid] = ADDAQUESTIONEXAM
        else :
            user_step.setdefault(cid , '')
            user_step[cid] = f'addquestion_{category_id}'

    elif data.startswith('changepageshowcat'):
        _,new_page = data.split('_')
        new_page = int(new_page)
        clist = get_categories()
        markup = create_inlinekeyboard_for_categoris(clist , new_page)
        if markup :
            bot.edit_message_reply_markup(cid , mid , reply_markup=markup)    
            bot.answer_callback_query(call_id , f'new page : {new_page}') 
        else :
            bot.answer_callback_query(call_id , f'wrong button')

    # Add teacher process --------------
    elif data.startswith('reqteach'):
        _,status,info,inlinestatus = data.split('_')
        user_cid,user_mid = info.split('|')
        if status == 'ans' :
            if get_is_teacher_status(user_cid) == 0:
                if inlinestatus == '11' :
                    new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=True)
                elif inlinestatus == '10' :
                    new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=False)
                send_message(cid , text['support_message'])
                bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
                bot.answer_callback_query(call_id , 'answer')
                user_step.setdefault(cid , '')
                user_step[cid] = f'teachreqans_{user_cid}_{user_mid}'
            elif get_is_teacher_status(user_cid) == 1 :
                new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=False)
                bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
                send_message(cid , text['user_teacher_added'])
                bot.answer_callback_query(call_id , 'not allowed')
        elif status == 'add' :
            if get_is_teacher_status(user_cid) == 0:
                if inlinestatus == '01':
                    new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=False)
                elif inlinestatus == '11' :
                    new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=True , addteacher=False)
                add_teacher_with_tel_id(user_cid)
                teachers.append(user_cid)
                keyboard = create_start_keyboard(user_cid)
                bot.copy_message(user_cid , CHANNEL_ID , CHANNEL_MESSAGES['you_added_teacher'] , reply_to_message_id=user_mid , reply_markup=keyboard)
                send_message(cid , f'{user_cid} added to teachers')
                bot.edit_message_reply_markup(cid , mid , reply_markup= new_markup)
                bot.answer_callback_query(call_id , 'user added to teachers')
                logging.info(f'admin {cid} added {user_cid} to teachers')
            elif get_is_teacher_status(user_cid) == 1 :
                new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=False)
                bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
                send_message(cid , text['user_teacher_added'])
                bot.answer_callback_query(call_id , 'not allowed')
        elif status == 'si' :
            if inlinestatus == '10' :
                new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=True , addteacher=False)
            elif inlinestatus == '01':
                new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=True)
            elif inlinestatus == '00' :
                new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=False)
            information = get_user_information(user_cid)
            result = ''
            for key,value in information.items():
                result += f'ℹ️ {key} : {value} \n'
            send_message(cid , result)

            try :
                bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
            except Exception as e:
                logging.error(f'Error {e} occured')

            bot.answer_callback_query(call_id , 'show information')

    # Send and make quiz question after choosing category --------------
    elif data.startswith('quizmakingcatchoice'):
        _,category_id = data.split('_')
        category_id = int(category_id)
        list_id = create_list_quiz_public(category_id=category_id , question_count=question_count)
        for i in list_id : 
            send_question_quiz(cid , i)
        bot.answer_callback_query(call_id , text['category_choice_callanswe'])

    elif data.startswith('chpagequiz'):
        _,page = data.split('_')
        page = int(page)
        data = get_categories()
        new_markup = create_inlinekeyboard_for_categoris_quizmaking(data , page)
        if new_markup : 
            bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
            bot.answer_callback_query(call_id , f'page {page+1}')
        else :
            bot.answer_callback_query(call_id , 'wrong buuton')

    elif data.startswith('option'):
        _,user_option,question_id = data.split('_')
        user_option = int(user_option)
        question_id = int(question_id)
        info = get_question_information(question_id=question_id)
        correct_option = info['answer_option']
        user_id_dict = find_user_id(cid)
        user_id = user_id_dict['ID']
        if is_answered_this_question(user_id=user_id , question_id=question_id) is None:
            add_answer_for_question(user_id=user_id , question_id = question_id , selected_option=user_option)

        new_markup = create_inline_for_answered_option(user_option , correct_option , question_id , mid)
        bot.edit_message_reply_markup(cid , mid , reply_markup = new_markup)

    elif data.startswith('getanswer'):
        _,mid,qid = data.split('_')
        mid = int(mid)
        qid = int(qid)
        info = get_question_information(question_id=qid)
        answer_photo = None
        answer_text = None
        if info['answer_text'].startswith('isphoto'):
            photo_id = info['answer_text'][7:]
            answer_photo =  photo_id
        else :
            answer_text = info['answer_text'] 
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text['delete_answer_text_photo'], callback_data='deleteans'))
        if find_designer_telegram_id(qid) != cid:
            markup.add(InlineKeyboardButton(text['report_question_designer'], callback_data=f'reportques_{qid}'))
        if answer_text is not None:
            send_message(cid , answer_text , reply_to_message_id=mid , reply_markup=markup)
        else :
            send_photo(cid , answer_photo , reply_to_message_id=mid , reply_markup=markup)
        bot.answer_callback_query(call_id , 'answer')

    # Report question in quiz and exam process --------------
    elif data.startswith('reportques') : 
        _,qid = data.split('_')
        qid = int(qid)
        designer_cid = find_designer_telegram_id(qid)
        user_step.setdefault(cid , '')
        user_step[cid] = f'reportwrongqa_{qid}_{designer_cid}'
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text['delete_answer_text_photo'] , callback_data='deleteans'))
        bot.edit_message_reply_markup(cid , mid , reply_markup=markup)
        send_message(cid , text['report_wrong_question'])
        bot.answer_callback_query(call_id , 'report question')

    elif data.startswith('chpageeditques'):
        _,new_page,qid = data.split('_')
        new_page = int(new_page)
        qid = int(qid)
        data = get_categories()
        new_markup = create_inlinekeyboard_for_categoris_editques(data , new_page , qid)
        if new_markup : 
            bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
            bot.answer_callback_query(call_id , f'page changed')
        else :
            bot.answer_callback_query(call_id , 'wrong buuton')

    # Edit question by designer --------------
    elif data.startswith('editquestioncateg'): 
        _,category_id,qid = data.split('_')
        category_id = int(category_id)
        qid = int(qid)
        edit_question_category(qid , category_id)
        send_message(cid , text['edited_successfully'])
        bot.delete_message(cid , mid)

    elif data.startswith('editquestion') :
        _,mode,qid = data.split('_')
        if mode == 'category':
            data = get_categories()
            markup = create_inlinekeyboard_for_categoris_editques(data , 0 , qid)
            send_message(cid , text['get_new_category'] , reply_markup=markup)
            bot.answer_callback_query(call_id,'choice category')
        elif mode == 'text':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewtext_{qid}'
            send_message(cid , text['get_new_text'])
            bot.answer_callback_query(call_id , 'get new text')
        elif mode == 'photo':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewphoto_{qid}'
            send_message(cid , text['get_new_photo'])
            bot.answer_callback_query(call_id , 'get new photo')
        elif mode == 'anstext':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewanstext_{qid}'
            send_message(cid , text['get_new_ans_text'])
            bot.answer_callback_query(call_id , 'get new answer')
        elif mode == 'ansop':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewansop_{qid}'
            send_message(cid , text['get_new_ans_option'])
            bot.answer_callback_query(call_id , 'get new answer option')
        elif mode == 'op1':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewop_1_{qid}'
            send_message(cid , text['get_new_option'])
            bot.answer_callback_query(call_id , 'get new option')
        elif mode == 'op2':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewop_2_{qid}'
            send_message(cid , text['get_new_option'])
            bot.answer_callback_query(call_id , 'get new option')       
        elif mode == 'op3':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewop_3_{qid}'
            send_message(cid , text['get_new_option'])
            bot.answer_callback_query(call_id , 'get new option')
        elif mode == 'op4':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewop_4_{qid}'
            send_message(cid , text['get_new_option'])
            bot.answer_callback_query(call_id , 'get new option')
        elif mode == 'end' :
            bot.delete_message(cid , mid)
            bot.answer_callback_query(call_id , 'message deleted')

    elif data.startswith('editqpage'):
        _,new_page,qid = data.split('_')
        new_page = int(new_page)
        qid = int(qid)
        new_markup = create_inline_for_edit_question(qid , new_page)
        bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
        bot.answer_callback_query(call_id , 'page changed')

    # Exam management items --------------
    elif data.startswith('examshowreportchpage'):
        _,new_page = data.split('_')
        new_page = int(new_page)
        data = get_exam_participation_cid(cid)
        new_markup = create_inline_for_show_exams_for_report(data , new_page)
        bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
    
    elif data.startswith('examshowreport'):
        _,exam_id = data.split('_')
        exam_id = int(exam_id)
        report = create_report_exam(cid , exam_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text['deletemessage'] , callback_data='deletemessage'))
        send_message(cid , report , reply_markup = markup , parse_mode='MarkdownV2')
        bot.answer_callback_query(call_id , 'report created')
        logging.info(f'exam report for exam No.{exam_id} sended to {cid}')

    elif data.startswith('getspecialcode'):
        _,exam_id = data.split('_')
        exam_id = int(exam_id)
        data = get_exam_data_id(exam_id)
        code = data['special_code']
        name = data['name']
        send_message(cid , create_text_for_exam_code(code , name) , parse_mode='MarkdownV2' , reply_to_message_id=mid)
        bot.answer_callback_query(call_id , 'exam code')
    
    elif data.startswith('getcountquestion'):
        _,exam_id = data.split('_')
        exam_id = int(exam_id)
        count = get_question_count_for_exam(exam_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text['deletemessage'] , callback_data='deletemessage'))
        send_message(cid , count , reply_to_message_id = mid ,reply_markup=markup)
        bot.answer_callback_query(call_id , f'count : {count}')

    elif data.startswith('examdeactive'):
        _,exam_id = data.split('_')
        exam_id = int(exam_id)
        deactive_exam(exam_id=exam_id)
        new_text = create_text_for_exam_data(exam_id)
        new_markup = create_inline_manage_exam(exam_id)
        new_text = create_text_for_exam_data(exam_id)
        bot.edit_message_text(new_text , cid , mid)
        bot.edit_message_reply_markup(cid , mid , reply_markup = new_markup)
        bot.answer_callback_query(call_id , 'deactive')
        data = exam_cid_time.get(exam_id , False)
        if data != False :
            for cid in data:
                if data[cid] is not None:
                    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['examended'])
        try :
            exam_cid_time.pop(exam_id)
        except :
            pass

    elif data.startswith('examactive'):
        _,exam_id = data.split('_')
        active_exam(exam_id=exam_id)
        new_text = create_text_for_exam_data(exam_id)
        new_markup = create_inline_manage_exam(exam_id)
        new_text = create_text_for_exam_data(exam_id)
        bot.edit_message_text(new_text , cid , mid)
        bot.edit_message_reply_markup(cid , mid , reply_markup = new_markup)
        bot.answer_callback_query(call_id , 'deactive')

    elif data.startswith('examtimechange'):
        _,exam_id = data.split('_')
        user_step.setdefault(cid , '')
        user_step[cid] = f'examtimechange_{exam_id}_{mid}'
        send_message(cid , text['examtimechanging'])
        bot.answer_callback_query(call_id , 'time change')

    # Exam add one question --------------
    elif data.startswith('examaddone'):
        _,exam_id = data.split('_')
        data = get_categories()
        markup = create_inlinekeyboard_for_categoris(data , 0)
        send_message(cid , text['choice_category_admin'] , reply_markup=markup)
        user_panel.setdefault(cid , '')
        user_panel[cid] = f'ADDAQUESTIONEXAM_{exam_id}'
        bot.answer_callback_query(call_id , 'add one question')

    # Exam add multiple question --------------
    elif data.startswith('examaddmul'):
        _,exam_id = data.split('_')
        user_step.setdefault(cid , '')
        user_step[cid] = f'addmulquestionexam_{exam_id}'
        send_message(cid , text['getfileforquestions'])
        bot.answer_callback_query(call_id , 'add questions')

    # Show exams to designer --------------
    elif data.startswith('examshowchpage'):
        _,new_page = data.split('_')
        data = get_exams_from_user_id(find_user_id(cid)['ID'])
        new_markup = create_inline_for_show_exams(data = data , page = new_page)
        bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
        bot.answer_callback_query(call_id , 'page changed')

    elif data.startswith('examshowdata'):
        _,exam_id = data.split('_')
        exam_id = int(exam_id)
        data = get_exam_data_id(exam_id)
        result = create_text_for_exam_data(exam_id)
        markup = create_inline_manage_exam(exam_id)
        send_message(cid , result , reply_markup=markup)
        bot.answer_callback_query(call_id , 'show data')

    # Enter exam callback handlers --------------
    elif data.startswith('examstart'):
        _,exam_id = data.split('_')
        now = time.time()
        exam_id = int(exam_id)
        exam_cid_time.setdefault(exam_id , {})
        exam_cid_time[exam_id].setdefault(cid , now)
        markup = create_inline_for_exam(exam_id , 0 , cid)
        starttext = create_text_for_starting_exam(exam_id)
        send_message(cid , starttext)
        send_question_exam(cid , 0 , exam_id , markup)
        bot.edit_message_reply_markup(cid , mid , reply_markup=None)
        bot.answer_callback_query(call_id , 'exam started')

    elif data.startswith('examtanswer'):
        _,question_id,exam_id = data.split('_')
        question_id = int(question_id)
        exam_id = int(exam_id)
        cid_status = check_cid_in_exam(cid , exam_id)
        if cid_status == False:
            info = get_question_information(question_id)
            answer_photo = None
            answer_text = None
            if info['answer_text'].startswith('isphoto'):
                photo_id = info['answer_text'][7:]
                answer_photo =  photo_id
            else :
                answer_text = info['answer_text'] 
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(text['delete_answer_text_photo'], callback_data='deleteans'))
            if find_designer_telegram_id(qid) != cid:
                markup.add(InlineKeyboardButton(text['report_question_designer'], callback_data=f'reportques_{question_id}'))
            if answer_text is not None:
                send_message(cid , answer_text , reply_to_message_id=mid , reply_markup=markup)
            else :
                send_photo(cid , answer_photo , reply_to_message_id=mid , reply_markup=markup)
            bot.answer_callback_query(call_id , 'answer')
        else :
            msgid = send_message(cid , text['youcannotseeanswer'])
            msgid = msgid.message_id
            time_to_delete = time.time() + 4
            delete_messages_dict.setdefault((msgid , cid) , time_to_delete)
            bot.answer_callback_query(call_id , 'None')

    # Options in exams --------------
    elif data.startswith('examop'):
        _,selected_option,qindex,exam_id,next_var = data.split('_')
        cid_status = check_cid_in_exam(cid , int(exam_id))
        if cid_status == True:        
            qindex = int(qindex)
            info_data = create_list_question_exam(cid , exam_id)
            qid = info_data[qindex]
            selected_option = int(selected_option)
            exam_id = int(exam_id)
            next_var = int(next_var)
            user_id = find_user_id(cid)['ID']
            # ---------------
            if is_answered_in_exam(user_id , exam_id ,qid):
                if selected_option != what_option_answered_in_exam(user_id , qid , exam_id):
                    update_option_in_exam(user_id , qid , selected_option , exam_id)
            else :
                add_answer_for_question(user_id , qid , selected_option , exam_id)  
            # ---------------
            if next_var == 1:
                new_markup = create_inline_for_answered_in_exam(selected_option , exam_id , qindex , cid)
            else :
                new_markup = create_inline_for_answered_in_exam(selected_option , exam_id , qindex , cid , next=False)
            try :
                bot.edit_message_reply_markup(cid , mid , reply_markup = new_markup)
            except :
                pass
            bot.answer_callback_query(call_id , 'question answered')

        else :
            msgid = send_message(cid , text['examtimeover'])
            msgid = msgid.message_id
            time_to_delete = time.time() + 3
            delete_messages_dict.setdefault((msgid , cid) , time_to_delete)
            bot.answer_callback_query(call_id , 'None')

    # Next question item in exam questions
    elif data.startswith('examquestionselect'):
        # working here ... 
        _,new_index,exam_id = data.split('_')
        cid_status = check_cid_in_exam(cid , int(exam_id))
        if cid_status == True:   
            new_index = int(new_index)
            exam_id = int(exam_id)
            info_data = create_list_question_exam(cid , exam_id)
            question_id = info_data[new_index-1]
            user_id = find_user_id(cid)['ID']
            new_markup = create_inline_for_exam(exam_id , new_index , cid)
            if is_answered_in_exam(user_id , exam_id , question_id):
                option = what_option_answered_in_exam(find_user_id(cid)['ID'] , question_id , exam_id)
                old_markup = create_inline_for_answered_in_exam(option , exam_id , new_index-1 , cid , next = False)
            else :
                old_markup = create_inline_for_exam(exam_id , new_index-1 , cid , next=False)

            bot.edit_message_reply_markup(cid , mid , reply_markup=old_markup)
            send_question_exam(cid , new_index , exam_id , new_markup)
            bot.answer_callback_query(call_id , 'question changed')
        else :
            msgid = send_message(cid , text['examtimeover'])
            msgid = msgid.message_id
            time_to_delete = time.time() + 3
            delete_messages_dict.setdefault((msgid , cid) , time_to_delete)
            bot.answer_callback_query(call_id , 'None')

    # finish exam time by user 
    elif data.startswith('endtimeexam'):
        _,exam_id = data.split('_')
        exam_id = int(exam_id)
        logging.info(f'Exam No.{exam_id} finished by {cid}')
        status = check_cid_in_exam(cid , exam_id)
        if status == True:
            exam_cid_time[exam_id][cid] = None
            bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['examended'])
            bot.answer_callback_query(call_id , 'finish')
        else :
            msgid = send_message(cid , text['examtimeover'])
            msgid = msgid.message_id
            time_to_delete = time.time() + 3
            delete_messages_dict.setdefault((msgid , cid) , time_to_delete)
            bot.answer_callback_query(call_id , 'None')
    # Delete message button
    elif data == 'deleteans' or data == 'deletemessage' : 
        logging.info(f'message No.{mid} deleted')
        bot.delete_message(cid , mid)
        bot.answer_callback_query(call_id , 'message deleted')

    elif data == 'deletequestion' :
        bot.delete_message(cid , mid)
        bot.answer_callback_query(call_id , 'question deleted')
        
    elif data == 'None' :
        bot.answer_callback_query(call_id , 'None')

# _______________________________ MESSAGE HADLERS _______________________________ #

@bot.message_handler(func=lambda m: m.text in ['/start', Button['start']])
def start_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    markup = create_start_keyboard(cid)
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['start'] , reply_markup = markup)
    #send_message(cid , show_commands(cid) , parse_mode='MarkdownV2')

@bot.message_handler(func=lambda m: m.text in ['/help', Button['help']]) # working on this ...
def start_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    markup = create_start_keyboard(cid)
    if (cid in admins) or (cid in teachers):
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['helpteachers'] , reply_markup= markup)
    else :
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup = markup)
    # send_message(cid , show_commands(cid) , parse_mode='MarkdownV2')

# Enter exam handlers -----------

@bot.message_handler(func = lambda m : m.text == Button['exam'])
def enter_exam_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    user_step.setdefault(cid , '')
    user_step[cid] = 'enterexamcode'
    send_message(cid , text['enterexam'])

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_') == 'enterexamcode')
def enter_exam_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    code = message.text.strip()
    exam_info = get_info_from_special_code(special_code=code)
    if exam_info is None :
        send_message(cid , text['examnotfound'])
        user_step.pop(cid)
    else :
        exam_id = exam_info['id']
        active = exam_info['is_active']
        if participation_in_exam(cid , exam_id) == False:
            if active == 0:
                send_message(cid , text['examisnotactive'])
            else :
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton(Button['examstart'] , callback_data=f'examstart_{exam_id}'))
                bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['guideforenterexam'] , reply_markup=markup)
        else :
            send_message(cid , text['youwasinthisexam'])
    try :
        user_step.pop(cid)
    except :
        pass

# Panels ------------------

@bot.message_handler(func = lambda m: m.text == Button['reportpanel'])
def show_performance_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    markup = create_report_panel(cid)
    send_message(cid , text['enterreportpanel'] , reply_markup=markup)
    logging.info(f'{cid} enters report panel ')

@bot.message_handler(func = lambda m : m.text == Button['exitreportpanel'])
def exit_report_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    markup = create_start_keyboard(cid)
    send_message(cid , text['exitreportpanel'] , reply_markup=markup)
    logging.info(f'{cid} exit report panel')
    try :
        user_step.pop(cid) 
    except :
        pass 

@bot.message_handler(func = lambda m : m.text == Button['teacherpanel'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) :  
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to enter teacher panel')
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup)
        return  

    markup = create_teacher_panel(cid)
    send_message(cid , text['enterteacherpanel'] , reply_markup=markup)
    logging.info(f'{cid} enters teacher panel')

@bot.message_handler(func = lambda m : m.text == Button['exitteacherpanel'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to exit teacher panel')
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return

    markup = create_start_keyboard(cid)
    send_message(cid , text['exitteacherpanel'] , reply_markup=markup)
    logging.info(f'{cid} exits teacher panel')
    try :
        user_step.pop(cid) 
    except :
        pass 

# ------------------

@bot.message_handler(func = lambda m : m.text == Button['generalquizpanel'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to enter general quiz panel')
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return

    markup = create_general_quiz_panel(cid)
    send_message(cid , text['entergeneralquizpanel'] , reply_markup=markup)
    logging.info(f'{cid} enters general quiz panel')

@bot.message_handler(func = lambda m : m.text == Button['exitgeneralquizpanel'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to exit general quiz panel')
        markup = create_teacher_panel(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return

    markup = create_teacher_panel(cid)
    send_message(cid , text['exitgeneralquizpanel'] , reply_markup=markup)
    logging.info(f'{cid} exits general quiz panel')
    try :
        user_step.pop(cid) 
    except :
        pass 
    
# ------------------

@bot.message_handler(func = lambda m : m.text == Button['exammanagement'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to enter exam manage panel')
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return

    markup = create_exam_management_panel(cid)
    send_message(cid , text['enterexampanel'] , reply_markup=markup)
    logging.info(f'{cid} enters exam manage panel')

@bot.message_handler(func = lambda m : m.text == Button['exitexammanagement'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to exit exam manage panel')
        markup = create_teacher_panel(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return

    markup = create_teacher_panel(cid)
    send_message(cid , text['exitexampanel'] , reply_markup=markup)
    logging.info(f'{cid} exits exam manage panel')
    try :
        user_step.pop(cid) 
    except :
        pass 

# Create exam --------------

@bot.message_handler(func = lambda m : m.text == Button['createexam'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to create exam')
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return

    send_message(cid , text['enterexamname'])
    user_step.setdefault(cid , '')
    user_step[cid] = 'getexamname'

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_') == 'getexamname')
def get_exam_name_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    name = message.text
    name = name.strip()
    teacher_exam.setdefault(cid , {})
    teacher_exam[cid].setdefault('name' , name)
    user_step[cid] = 'getexamtime'
    send_message(cid , text['getexamtime'])

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_') == 'getexamtime')
def get_exam_name_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    exam_time = message.text
    exam_time = int(exam_time.strip())
    designer_id = find_user_id(cid)['ID']
    special_code = generate_exam_special_code()
    while is_special_code_exist(special_code):
        special_code = generate_exam_special_code()

    last_id = create_exam(name = teacher_exam[cid]['name'] ,
                designer_id = designer_id , 
                time = exam_time , 
                code = special_code)

    logging.info(f'{cid} creates exam No.{last_id}')
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['guideformanageexam'])
    teacher_exam.pop(cid)
    user_step.pop(cid)

@bot.message_handler(func = lambda m : m.text == Button['exitcreateexam'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return 

    markup = create_exam_management_panel(cid)
    send_message(cid , text['exitcreateexampanel'] , reply_markup=markup)
    try :
        user_step.pop(cid) 
    except :
        pass 

@bot.message_handler(func = lambda m : m.text == Button['showexams'])
def show_exams_handler(message):
    cid = message.chat.id
    if is_spam(cid):
        return
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to get exam data')
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return

    data = get_exams_from_user_id(find_user_id(cid)['ID'])
    if len(data) == 0:
        send_message(cid , text['noexamhere'])
    else :
        markup = create_inline_for_show_exams(data)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['showexamsandmanage'] , reply_markup=markup)
        logging.info(f'{cid} gets its exam names')

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_').startswith('examtimechange'))
def time_changing_handler(message):
    cid = message.chat.id
    status = user_step[cid]
    _,exam_id,mid = status.split('_')
    exam_id = int(exam_id)
    mid = int(mid)
    try :
        change_time_exam(exam_id , int(message.text))
        logging.info(f'{cid} changes tiem exam with id = {exam_id}')
        new_text = create_text_for_exam_data(exam_id)
        new_markup = create_inline_manage_exam(exam_id)
        try :
            bot.edit_message_text(new_text , cid , mid)
            bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
        except :
            pass
        send_message(cid , text['success'])
    except :
        send_message(cid , text['wrongvaluefortime'])

# Add multiple question ---------------

@bot.message_handler(func = lambda m : (m.text == Button['addquestionmul']))
def add_multiple_question_for_quiz_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to add multiple question in exam')
        markup = create_teacher_panel(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return 
    
    user_step.setdefault(cid , '')
    user_step[cid] = 'get_question_document'
    send_message(cid , text['getfileforquestions'])

@bot.message_handler(content_types=['document'] , func = lambda m : user_step.get(m.chat.id , '_').startswith('addmulquestionexam'))
def add_multiple_question_for_exam_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    name = message.document.file_name
    step = user_step[cid]
    _,exam_id = step.split('_')
    exam_id = int(exam_id)
    if check_excel_file(name):
        
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = f'{cid}-{str(time.time()).replace('.' , '')}.xlsx'
        saved_file_directory = os.path.join('excel_files' , 'data' , file_name)

        with open(saved_file_directory , 'wb') as f:
            f.write(downloaded_file)
            logging.info(f'{cid} file saved as {saved_file_directory}')

        user_id = find_user_id(cid)['ID']
        status = get_data_from_excel_exam(saved_file_directory , user_id , exam_id)
        if  status == True:
            send_message(cid , text['questionsaddedexam'])
            logging.info(f'{cid} questions successfully added to database for exam No.{exam_id}')
        elif status.startswith('ERROR'): # should be tested 
            _,error_type = status.split('-')
            logging.info(f'{error_type} occured in adding questions in exam No.{exam_id} by {cid}')
            if error_type == 'readexcel':
                send_message(cid , text['errorinreadingfile'])
            else :
                line = error_type[4:]
                if line != '1':
                    send_message(cid , text['errorinlineexam'] + '\n' + f'line : {line}' + '\n\n' + text['correctedfile'])
                else :
                    send_message(cid , text['firstlineerror'])
    else :
        send_message(cid , text['wrongfile'])
        logging.info(f'{cid} sends wrong file format for exam No.{exam_id}')

@bot.message_handler(content_types=['document'] , func = lambda m : user_step.get(m.chat.id , '') == 'get_question_document')
def add_multiple_question_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    name = message.document.file_name
    if check_excel_file(name):

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = f'{cid}-{str(time.time()).replace('.' , '')}.xlsx'
        saved_file_directory = os.path.join('excel_files' , 'data' , file_name)
        
        with open(saved_file_directory , 'wb') as f:
            f.write(downloaded_file)
            logging.info(f'{cid} file saved at {saved_file_directory}')
        user_id = find_user_id(cid)['ID']
        status = get_data_from_excel_quiz(saved_file_directory , user_id)
        if  status == True:
            logging.info(f'{cid} added successfully multiple questions')
            send_message(cid , text['questionsadded'])
        elif status.startswith('ERROR'): # should be tested 
            _,error_type = status.split('-')
            if error_type == 'readexcel':
                send_message(cid , text['errorinreadingfile'])
            else :
                line = error_type[4:]
                if line != '1':
                    send_message(cid , text['errorinline'] + '\n' + f'line : {line}' + '\n\n' + text['correctedfile'])
                else :
                    send_message(cid , text['firstlineerror'])
    else :
        send_message(cid , text['wrongfile'])
        logging.info(f'{cid} sends wrong file format for quiz')

# ---------------

@bot.message_handler(func = lambda m : m.text == Button['guideformultipleques'])
def send_guide_handler(message):
    cid = message.chat.id
    if is_spam(cid) :
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to get guide text and files for adding multiple questions')
        markup = create_teacher_panel(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return 
    
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['guideforexcelQ'])
    with open(os.path.join('excel_files' , 'sample.xlsx') , 'rb') as f:
        send_document(cid , f)
        logging.info(f'sample.xlsx successfully sended for {cid}')
    data = get_categories()
    if create_category_excel(data):
        with open(os.path.join('excel_files' , 'category.csv') , 'rb') as f:
            send_document(cid , f)
            logging.info(f'category.csv successfully sended for {cid}')

@bot.message_handler(func = lambda m : m.text == Button['showphotoid'])
def show_photo_id_handler(message):
    cid = message.chat.id
    if is_spam(cid) :
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to get photo id')
        markup = create_teacher_panel(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return 
    
    send_message(cid , text['getimage'])
    user_step.setdefault(cid , '')
    user_step[cid] = 'get_image_id'

@bot.message_handler(content_types=['photo' , 'document' , 'text']\
                     ,func = lambda m : user_step.get(m.chat.id , '_') == 'get_image_id')
def send_photo_id(message):
    cid = message.chat.id
    if is_spam(cid) :
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to get photo id')
        markup = create_teacher_panel(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 
        return 
    
    if message.content_type == 'photo':
        file_list = message.photo
        photo = file_list[-1]
        file_id = photo.file_id
        send_message(cid , 'Photo ID :' + '\n\n' + file_id)
        logging.info(f'{file_id} sended to {cid} successfully')
    else :
        logging.info(f'{cid} sends wrong file for getting photo id')
        send_message(cid , text['wrongfile'])

# Report ------------
@bot.message_handler(func = lambda m : m.text == Button['examreport'])
def quiz_report_handler(message):
    cid = message.chat.id
    if is_spam(cid) :
        return 
    manage_user(message , cid)
    total_exams = get_exam_participation_cid(cid)
    if len(total_exams) > 0:
        data = get_exam_participation_cid(cid)
        markup = create_inline_for_show_exams_for_report(data , 0)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['showreportforexam'] , reply_markup= markup)
    else :
        send_message(cid , text['youdonthaveanyexam'])

@bot.message_handler(func = lambda m : m.text == Button['quizreport'])
def quiz_report_handler(message):
    cid = message.chat.id
    if is_spam(cid) :
        return 
    manage_user(message , cid)
    result_text = create_report_quiz(cid)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text['deletemessage'] , callback_data='deletemessage'))
    send_message(cid , result_text , parse_mode='MarkdownV2',reply_markup=markup)
    logging.info(f'Quiz reports sended for {cid}')

# Teacher Request ------------------------------------

@bot.message_handler(func=lambda m: m.text in ['/reqteach', Button['req_teacher']])
def request_teacher_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) :
        return 
    manage_user(message , cid)
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['teacher_request'])
    user_step.setdefault(cid , '')
    user_step[cid] = 'teacher_request_info'

@bot.message_handler(content_types=['text' , 'photo'] , func = lambda m : user_step.get(m.chat.id , False) == 'teacher_request_info')
def information_receive_handler(message):
    cid = message.chat.id
    mid  = message.message_id
    if is_spam(cid) :
        return 
    manage_user(message , cid)
    markup = create_inlinekeyboard_for_teacher_request(cid , mid)
    for i in range(len(admins)):
        bot.forward_message(admins[i] , cid , mid)
        send_message(admins[i] , text['buttons_choice'] , reply_markup = markup)
        logging.info(f'Teacher request for cid {cid} sended to admins')
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['sended_support'])
    user_step.pop(cid)

@bot.message_handler(content_types=['text' , 'photo'] , func = lambda m : user_step.get(m.chat.id , '_').startswith('teachreqans'))
def teach_request_answer_handler(message) :
    cid = message.chat.id
    if is_spam(cid) :
        return 
    manage_user(message , cid)
    #teachreqans_{user_cid}_{user_mid}
    step = user_step.get(cid , False)
    _,user_cid,user_mid = step.split('_')
    user_cid = int(user_cid)
    user_mid = int(user_mid)
    bot.copy_message(user_cid , cid , message.message_id , reply_to_message_id=user_mid)
    send_message(cid , text['support_answered'])
    user_step.pop(cid)
    logging.info(f'admin {cid} answers to {user_cid} for Teacher request')

# ------------------------------------

@bot.message_handler(func=lambda m: m.text in ['/quiz', Button['quiz']])
def quiz_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    data = get_categories()
    markup = create_inlinekeyboard_for_categoris_quizmaking(data , 0)
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['request_for_quiz'] , reply_markup= markup)

@bot.message_handler(func=lambda m: m.text in ['/support', Button['support']]) 
def support_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['req_support'])
    user_step.setdefault(cid , '')
    user_step[cid] = 'support_request'

@bot.message_handler(func=lambda m: m.text in ['/showcategory', Button['showcategory']])
def showcategory_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    data = get_categories()
    result = ''
    for item in data :
        value = item['NAME']
        result += f'🔴 *{value}*\n'
    send_message(cid, result , parse_mode='MarkdownV2')

@bot.message_handler(func=lambda m: m.text in ['/addcategory', Button['addcategory']])
def add_category_admin(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to add category')
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup)
        return 
    
    send_message(cid , text['add_category_admin'])
    user_step[cid] = 'getting_category_name'

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , False) == 'getting_category_name')
def getting_ctgy_name(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    last_id = add_categories(message.text)
    logging.info(f'{cid} added category with id {last_id} to database')
    send_message(cid , f'added to \nquiz.categories\nid = {last_id}' , reply_to_message_id=message.message_id)  
    user_step.pop(cid)

# Add one question Teacher (quiz and exam) --------------
@bot.message_handler(func=lambda m: m.text in ['/addquestion', Button['addquestion']])
def choice_category_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        logging.info(f'{cid} is not teacher or admin but wants to add one question at quiz questions database')
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup)
        return 
    
    data = get_categories()
    markup = create_inlinekeyboard_for_categoris(data , 0)
    send_message(cid , text['choice_category_admin'] , reply_markup=markup)   

@bot.message_handler(content_types=['text' , 'photo']
                    ,func = lambda m : (user_step.get(m.chat.id , '_')).startswith('addquestion'))
def get_question_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        _,category_id,exam_id = (user_step[cid]).split('_')
    else :
        _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    if message.content_type == 'photo' :
        file_list = message.photo
        photo = file_list[-1]
        file_id = photo.file_id
        #send_photo(cid , file_id , caption=message.caption)
        admin_question.setdefault(cid , dict())
        admin_question[cid].setdefault('file_id' , file_id)
        admin_question[cid].setdefault('text' , message.caption)
        # print(admin_question)

        if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
            user_step[cid] = f'getoption1_{category_id}_{exam_id}'
        else :
            user_step[cid] = f'getoption1_{category_id}'

    elif message.content_type == 'text' : 
        admin_question.setdefault(cid , dict())
        admin_question[cid].setdefault('text' , message.text)
        admin_question[cid].setdefault('file_id' , None)
        # print(admin_question)

        if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
            user_step[cid] = f'getoption1_{category_id}_{exam_id}'
        else : 
            user_step[cid] = f'getoption1_{category_id}'

        send_message(cid , text['get_option1'])

@bot.message_handler(func = lambda m : (user_step.get(m.chat.id , '_')).startswith('getoption1'))
def get_option1_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        _,category_id,exam_id = (user_step[cid]).split('_')
    else :
        _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    admin_question[cid].setdefault('option1' , message.text)
    # print(admin_question)

    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        user_step[cid] = f'getoption2_{category_id}_{exam_id}'
    else : 
        user_step[cid] = f'getoption2_{category_id}'

    send_message(cid , text['get_option2'])

@bot.message_handler(func = lambda m : (user_step.get(m.chat.id , '_')).startswith('getoption2'))
def get_option2_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
            _,category_id,exam_id = (user_step[cid]).split('_')
    else :
        _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    admin_question[cid].setdefault('option2' , message.text)
    # print(admin_question)

    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        user_step[cid] = f'getoption3_{category_id}_{exam_id}'
    else : 
        user_step[cid] = f'getoption3_{category_id}'

    send_message(cid , text['get_option3'])

@bot.message_handler(func = lambda m : (user_step.get(m.chat.id , '_')).startswith('getoption3'))
def get_option1_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
                _,category_id,exam_id = (user_step[cid]).split('_')
    else :
        _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    admin_question[cid].setdefault('option3' , message.text)
    # print(admin_question)

    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        user_step[cid] = f'getoption4_{category_id}_{exam_id}'
    else : 
        user_step[cid] = f'getoption4_{category_id}'

    send_message(cid , text['get_option4'])

@bot.message_handler(func = lambda m : (user_step.get(m.chat.id , '_')).startswith('getoption4'))
def get_option1_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        _,category_id,exam_id = (user_step[cid]).split('_')
    else :
        _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    admin_question[cid].setdefault('option4' , message.text)
    # print(admin_question)

    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        user_step[cid] = f'optionans_{category_id}_{exam_id}'
    else : 
        user_step[cid] = f'optionans_{category_id}'

    send_message(cid , text['get_optionanswer'])

@bot.message_handler(func = lambda m : (user_step.get(m.chat.id , '_')).startswith('optionans'))
def get_option1_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        _,category_id,exam_id = (user_step[cid]).split('_')
    else :
        _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    admin_question[cid].setdefault('option_answer' , int(message.text))
    # print(admin_question)

    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        user_step[cid] = f'textans_{category_id}_{exam_id}'
    else : 
        user_step[cid] = f'textans_{category_id}'

    send_message(cid , text['get_textanswer'])

@bot.message_handler(content_types = ['text' , 'photo'],
                     func = lambda m : (user_step.get(m.chat.id , '_')).startswith('textans'))
def get_option1_handler(message):
    # print('hello')
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        _,category_id,exam_id = (user_step[cid]).split('_')
        category_id = int(category_id)
        exam_id = int(exam_id)
    else :
        _,category_id = (user_step[cid]).split('_')
        category_id = int(category_id)

    if message.content_type == 'text' :
        admin_question[cid].setdefault('text_answer' , message.text)
    elif message.content_type == 'photo' :
        file_list = message.photo
        photo = file_list[-1]
        file_id = photo.file_id
        admin_question[cid].setdefault('text_answer' , 'isphoto' + file_id)
    # print(admin_question)
    user_id_in_table = find_user_id(cid)

    if user_panel.get(cid , '_') == ADDAQUESTIONEXAM:
        last_row_id = add_question(   category_id = category_id,
                        designer_id = user_id_in_table['ID'],
                        photo_id    = admin_question[cid]['file_id'],
                        text        = admin_question[cid]['text'],
                        op1         = admin_question[cid]['option1'],
                        op2         = admin_question[cid]['option2'],
                        op3         = admin_question[cid]['option3'],
                        op4         = admin_question[cid]['option4'],
                        ansop       = admin_question[cid]['option_answer'],
                        anstext     = admin_question[cid]['text_answer'],
                        is_public   = False)
        add_question_to_exam(question_id=last_row_id , exam_id=exam_id)
        send_message(cid , text['questoin_added_to_exam'])
        admin_question.pop(cid)
        user_step.pop(cid)
        user_panel[cid] = EXAM_PANEL
        logging.info(f'{cid} added question with id {last_row_id} in exam with id {exam_id}')
    else :
        last_row_id = add_question(   category_id = category_id,
                        designer_id = user_id_in_table['ID'],
                        photo_id    = admin_question[cid]['file_id'],
                        text        = admin_question[cid]['text'],
                        op1         = admin_question[cid]['option1'],
                        op2         = admin_question[cid]['option2'],
                        op3         = admin_question[cid]['option3'],
                        op4         = admin_question[cid]['option4'],
                        ansop       = admin_question[cid]['option_answer'],
                        anstext     = admin_question[cid]['text_answer'] )
        send_message(cid , text['questoin_added'])
        admin_question.pop(cid)
        user_step.pop(cid)
        logging.info(f'{cid} added question with id {last_row_id} in quiz questions')

@bot.message_handler(content_types=['document'] \
                     , func = lambda m : user_panel.get(m.chat.id , False) == GENERAL_QUIZ_PANEL)
def add_multiple_question_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    file_name = message.document.file_name
    if check_excel_file(file_name):
        pass
    else :
        send_message(cid , text['wrongfile'])

# Report question proccess in quiz and exam --------------
@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_').startswith('reportwrongqa'))
def report_question_handler(message):
    cid = message.chat.id
    step = user_step[cid]
    _,question_id,designer_cid = step.split('_')
    designer_cid = int(designer_cid)
    question_id = int(question_id)
    bot.copy_message(designer_cid , CHANNEL_ID , CHANNEL_MESSAGES['quesiton_report'])
    sent_msg = send_question_quiz(designer_cid , question_id)
    sent_msg_id = sent_msg.message_id
    markup = create_inline_for_edit_question(question_id , 0)
    bot.copy_message(designer_cid , cid , message.message_id , reply_to_message_id=sent_msg_id , reply_markup=markup)
    send_message(cid , text['report_wrong_question_sended'])
    logging.info(f'{cid} sended report for question with id {question_id} to designer {designer_cid}')
    user_step.pop(cid)

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_').startswith('getnewtext'))
def get_new_text_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    step = user_step[cid]
    _,qid = step.splut('_')
    qid = int(qid)
    edit_question_text(qid , message.text)
    logging.info(f'{cid} changes text for question with id {qid}')
    send_message(cid , text['edited_successfully'])
    user_step.pop(cid)

@bot.message_handler(content_types=['photo'], func = lambda m : user_step.get(m.chat.id , '_').startswith('getnewphoto'))
def get_new_text_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    step = user_step[cid]
    _,qid = step.split('_')
    qid = int(qid)
    file_list = message.photo
    photo = file_list[-1]
    file_id = photo.file_id
    edit_question_photo_id(question_id=qid , new_photo_id=file_id)
    logging.info(f'{cid} changes photo for question with id {qid}')
    send_message(cid , text['edited_successfully'])
    user_step.pop(cid)

# getnewanstext
@bot.message_handler(content_types=['text','photo'], func = lambda m : user_step.get(m.chat.id , '_').startswith('getnewanstext'))
def get_new_text_handler(message):
    cid = message.chat.id
    if is_spam(cid) :
        return
    manage_user(message , cid)
    step = user_step[cid]
    _,qid = step.split('_')
    qid = int(qid)
    if message.content_type == 'photo':
        file_list = message.photo
        photo = file_list[-1]
        file_id = photo.file_id
        edit_question_answer_text(qid , 'isphoto' + file_id)
        logging.info(f'{cid} sets photo for answer in question No.{qid}')
    else :
        edit_question_answer_text(qid , message.text)
        logging.info(f'{cid} sets text for answer in question No.{qid}')

    send_message(cid , text['edited_successfully'])
    user_step.pop(cid)

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_').startswith('getnewansop'))
def get_new_text_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    step = user_step[cid]
    _,qid = step.split('_')
    qid = int(qid)
    edit_question_answer_option(qid , int(message.text))
    logging.info(f'{cid} changes correct option for question No.{qid} to {message.text}')
    send_message(cid , text['edited_successfully'])
    user_step.pop(cid)

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_').startswith('getnewop'))
def get_new_text_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    step = user_step[cid]
    _,op,qid = step.split('_')
    qid = int(qid)
    op = int(op)

    if op == 1:
        edit_question_option1(qid , message.text)
        logging.info(f'{cid} changed option 1 in question No.{qid}')

    elif op == 2:
        edit_question_option2(qid , message.text)
        logging.info(f'{cid} changed option 2 in question No.{qid}')

    elif op == 3:
        edit_question_option3(qid , message.text)
        logging.info(f'{cid} changed option 3 in question No.{qid}')

    elif op == 4:
        edit_question_option4(qid , message.text)
        logging.info(f'{cid} changed option 4 in question No.{qid}')

    send_message(cid , text['edited_successfully'])
    user_step.pop(cid)

# Support ----------------
@bot.message_handler(func = lambda m : user_step.get(m.chat.id , False) == 'support_request')
def support_request_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    mid = message.message_id
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Answer' , callback_data=f'anssupport_{cid}_{mid}'))
    # send to admins
    for i in range(len(admins)):
        bot.forward_message(admins[i] , cid , mid)
        send_message(admins[i] , text['support_request'] , reply_markup=markup)
        logging.info(f'support request from {cid} sends to admins')
    # user
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['sended_support']) #to user who wanted support
    # print(message.text)
    add_support_request(user_id = find_user_id(cid)['ID'] , message_id = mid , text = message.text)
    user_step.pop(cid)

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_').startswith('adminanswer')) # inline pressed by admin
def admin_answer_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    _,user_cid,user_mid = user_step.get(cid).split('_')
    user_cid = int(user_cid)
    user_mid = int(user_mid)
    bot.copy_message(user_cid,cid, message.message_id , reply_to_message_id=user_mid)
    send_message(cid , text['support_answered'])
    user_step.pop(cid)
    update_support_status(user_id= find_user_id(user_cid)['ID'] , user_mid=user_mid, admin_id=find_user_id(cid)['ID'], admin_text=message.text)
    logging.info(f'admin {cid} answers to {user_cid} for support request')

@bot.message_handler(func = lambda m : True)
def every_messages_handler(message):
    cid = message.chat.id
    markup = create_start_keyboard(cid)
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup)

print('bot is running !' , os.getcwd() , sep = ' ---> ')
logging.info('bot started')

#skip_pending=True
thread.start()
bot.infinity_polling()