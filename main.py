import telebot
from telebot.types import ReplyKeyboardMarkup , ReplyKeyboardRemove,InlineKeyboardMarkup,InlineKeyboardButton
from requests_forwarder import setup_proxy
from config_bot import *
from config_db import *
import os
import datetime,time
import random
from Text import *
from DQL import *
from DML import *

setup_proxy(
    proxy_token=proxy_token
)

bot = telebot.TeleBot(telegram_token , threaded= 5)
hide_board = ReplyKeyboardRemove()

#print(f'{os.getcwd()}')

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
CREATE_EXAM_PANEL = 3

user_panel = {} # cid : panel
admin_question = {} # cid : {text : ... , file_id : ... , options : ... , answer_option : ... , answer_text : ...}

# ----- spam
lower_limit = 2     # sec
upper_limit = 15    # sec
max_score = 10
# cid : {last_message_time : ... , score : ...}
spam_data = {}  

teachers = []
admins = []

question_count = 1 # for public quiz

def get_admins():
    global admins
    data = get_users()
    for user in data :
        if user['is_admin'] == 1:
            admins.append(user['telegram_id'])

def get_teachers():
    global teachers
    data = get_users()
    for user in data :
        if user['is_teacher'] == 1:
            teachers.append(user['telegram_id'])

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
    print('teachers : ' , teachers , sep = ' : ')
    data = get_users()
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    name = set_name(first_name , last_name)
    for user in data :
        if user['telegram_id'] == cid:
            edit_user_username(cid , username)
            edit_user_name(cid , name)
            if (user['is_admin'] == 1) and (cid not in admins):
                admins.append(cid)
            elif user['is_admin'] == 0:
                if user['telegram_id'] in admins:
                    admins.remove(user['telegram_id'])
            if (user['is_teacher'] == 1) and (cid not in teachers):
                teachers.append(cid)
            elif user['is_teacher'] == 0:
                print('hello is teacher = 0')
                if user['telegram_id'] in teachers :
                    teachers.remove(user['telegram_id'])
            break
    else :
        add_user(cid , False , False , username , name)
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
        return True
    else :
        return False

def reply_message_type(message):
    try :
        reply_id = message.reply_to_message.forward_origin.type
        print(reply_id)
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
def create_teacher_panel(cid) :
    user_panel[cid] = TEACHER_PANEL
    if (cid not in teachers) and (cid not in admins):
        return False
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Button['generalquizpanel'])
    keyboard.add(Button['exammanagement'])
    keyboard.add(Button['addcategory'])
    keyboard.add(Button['exitteacherpanel'])
    return keyboard

def create_general_quiz_panel(cid):
    user_panel[cid] = GENERAL_QUIZ_PANEL
    if (cid not in teachers) and (cid not in admins):
        return False
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Button['addquestion'])
    keyboard.add(Button['addquestionmul'])
    keyboard.add(Button['exitgeneralquizpanel'])
    return keyboard

def create_exam_management_panel(cid):
    user_panel[cid] = EXAM_PANEL
    if (cid not in teachers) and (cid not in admins):
        return False
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Button['showexams'])
    keyboard.add(Button['createexam'])
    keyboard.add(Button['exitexammanagement'])
    return keyboard

def create_exam_panel(cid):
    user_panel[cid] = CREATE_EXAM_PANEL
    if (cid not in teachers) and (cid not in admins):
        return False
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Button['exitcreateexam'])
    return keyboard

def create_report_panel(cid):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(Button['quizreport']) # inline 
    keyboard.add(Button['examreport']) # inline 
    keyboard.add(Button['exitreportpanel'])
    return keyboard
# ---------------

def create_report_quiz(cid): # working here ...
    pass


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

def create_list_quiz_public(category_id , question_count): # random , output : list of id(s)
    list_of_ids = get_question_id_public(category_id=category_id)
    try :
        list_of_ids = random.sample(list_of_ids , k = question_count)
    except :
        return False
    return list_of_ids

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
    markup.add(Buttons[0] , Buttons[1] , Buttons[2] , Buttons[3])
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

    markup.add(Buttons[0] , Buttons[1] , Buttons[2] , Buttons[3])
    markup.add(Buttons[4])
    return markup

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

def send_question(cid , question_id):
    info = get_question_information(question_id=question_id)
    photo_id = info['photo_id']
    markup = create_inline_for_options(question_id=question_id)
    result = create_text_caption_for_question(question_id=question_id)
    if photo_id is not None : 
        message = bot.send_photo(cid , photo_id , caption=result , reply_markup=markup)
    else :
        message = bot.send_message(cid , result , reply_markup=markup)
    return message

# ----------------------------------

def listener(messages):
    for m in messages:
        #print(m)
        if m.content_type == 'text' :
            print(f'{m.chat.id}  [{m.from_user.username}] : {m.text}')
        elif m.content_type == 'photo' :
            print(f'{m.chat.id}  [{m.from_user.username}] : new photo recieved')
        elif m.content_type == 'document' :
            print(f'{m.chat.id}  [{m.from_user.username}] : new document recieved')

bot.set_update_listener(listener)

@bot.callback_query_handler(func= lambda c : True)
def callback_handler(call):
    cid = call.message.chat.id
    if is_spam(cid) :
        return 
    mid = call.message.message_id
    call_id = call.id
    data = call.data
    if data.startswith('anssupport'):
        _,user_cid,user_mid = data.split('_')
        if get_support_status(user_id = find_user_id(user_cid)['ID'] , user_mid= user_mid)['admin_id'] is None :
            user_step.setdefault(cid , f'adminanswer_{user_cid}_{user_mid}')
            bot.send_message(cid , text['support_message'])
            bot.edit_message_reply_markup(cid , mid , reply_markup=None)
            bot.answer_callback_query(call_id , 'answer')
        else :
            bot.answer_callback_query(call_id , 'answered')
            bot.delete_message(cid , mid)
            bot.send_message(cid , text['support_another_admin'])
            
    elif data.startswith('categorychoice'):
        _,category_id = data.split('_')
        category_id = int(category_id)
        bot.delete_message(cid , mid)
        bot.answer_callback_query(call_id , f'{category_id}')

        bot.send_message(cid , text['add_question_admin_resp'])
        bot.send_message(cid , text['photo_and_text_question'])
        user_step.setdefault(cid , f'addquestion_{category_id}')
        print(user_step)

    # categories
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

    # add teacher process
    
    elif data.startswith('reqteach'):
        _,status,info,inlinestatus = data.split('_')
        user_cid,user_mid = info.split('|')
        if status == 'ans' :
            if get_is_teacher_status(user_cid) == 0:
                if inlinestatus == '11' :
                    new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=True)
                elif inlinestatus == '10' :
                    new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=False)
                bot.send_message(cid , text['support_message'])
                bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
                bot.answer_callback_query(call_id , 'answer')
                user_step.setdefault(cid , '')
                user_step[cid] = f'teachreqans_{user_cid}_{user_mid}'
            elif get_is_teacher_status(user_cid) == 1 :
                new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=False)
                bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
                bot.send_message(cid , text['user_teacher_added'])
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
                bot.send_message(cid , f'{user_cid} added to teachers')
                bot.edit_message_reply_markup(cid , mid , reply_markup= new_markup)
                bot.answer_callback_query(call_id , 'user added to teachers')
            elif get_is_teacher_status(user_cid) == 1 :
                new_markup = create_inlinekeyboard_for_teacher_request(user_cid , user_mid , answer=False , addteacher=False)
                bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
                bot.send_message(cid , text['user_teacher_added'])
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
            bot.send_message(cid , result)
            try :
                bot.edit_message_reply_markup(cid , mid , reply_markup=new_markup)
            except Exception as e:
                pass
                #print(f'{e}')
            bot.answer_callback_query(call_id , 'show information')
    
    elif data.startswith('quizmakingcatchoice'):
        _,category_id = data.split('_')
        category_id = int(category_id)
        list_id = create_list_quiz_public(category_id=category_id , question_count=question_count)
        for i in list_id : 
            send_question(cid , i)
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
        # if find_designer_telegram_id(qid) != cid:
        markup.add(InlineKeyboardButton(text['report_question_designer'], callback_data=f'reportques_{qid}'))
        if answer_text is not None:
            bot.send_message(cid , answer_text , reply_to_message_id=mid , reply_markup=markup)
        else :
            bot.send_photo(cid , answer_photo , reply_to_message_id=mid , reply_markup=markup)
        bot.answer_callback_query(call_id , 'answer')

    elif data.startswith('reportques') : 
        _,qid = data.split('_')
        qid = int(qid)
        designer_cid = find_designer_telegram_id(qid)
        user_step.setdefault(cid , '')
        user_step[cid] = f'reportwrongqa_{qid}_{designer_cid}'
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text['delete_answer_text_photo'] , callback_data='deleteans'))
        bot.edit_message_reply_markup(cid , mid , reply_markup=markup)
        bot.send_message(cid , text['report_wrong_question'])
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

    elif data.startswith('editquestioncateg'): 
        _,category_id,qid = data.split('_')
        category_id = int(category_id)
        qid = int(qid)
        edit_question_category(qid , category_id)
        bot.send_message(cid , text['edited_successfully'])
        bot.delete_message(cid , mid)

    elif data.startswith('editquestion') :
        _,mode,qid = data.split('_')
        if mode == 'category':
            data = get_categories()
            markup = create_inlinekeyboard_for_categoris_editques(data , 0 , qid)
            bot.send_message(cid , text['get_new_category'] , reply_markup=markup)
            bot.answer_callback_query(call_id,'choice category')
        elif mode == 'text':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewtext_{qid}'
            bot.send_message(cid , text['get_new_text'])
            bot.answer_callback_query(call_id , 'get new text')
        elif mode == 'photo':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewphoto_{qid}'
            bot.send_message(cid , text['get_new_photo'])
            bot.answer_callback_query(call_id , 'get new photo')
        elif mode == 'anstext':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewanstext_{qid}'
            bot.send_message(cid , text['get_new_ans_text'])
            bot.answer_callback_query(call_id , 'get new answer')
        elif mode == 'ansop':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewansop_{qid}'
            bot.send_message(cid , text['get_new_ans_option'])
            bot.answer_callback_query(call_id , 'get new answer option')
        elif mode == 'op1':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewop_1_{qid}'
            bot.send_message(cid , text['get_new_option'])
            bot.answer_callback_query(call_id , 'get new option')
        elif mode == 'op2':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewop_2_{qid}'
            bot.send_message(cid , text['get_new_option'])
            bot.answer_callback_query(call_id , 'get new option')       
        elif mode == 'op3':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewop_3_{qid}'
            bot.send_message(cid , text['get_new_option'])
            bot.answer_callback_query(call_id , 'get new option')
        elif mode == 'op4':
            user_step.setdefault(cid , '')
            user_step[cid] = f'getnewop_4_{qid}'
            bot.send_message(cid , text['get_new_option'])
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

    elif data == 'deleteans' : 
        bot.delete_message(cid , mid)
        bot.answer_callback_query(call_id , 'message deleted')

    elif data == 'deletequestion' :
        bot.delete_message(cid , mid)
        bot.answer_callback_query(call_id , 'question deleted')
        
    elif data == 'None' :
        bot.answer_callback_query(call_id , 'None')
    

@bot.message_handler(func=lambda m: m.text in ['/start', Button['start']])
def start_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    print(admins)
    markup = create_start_keyboard(cid)
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['start'] , reply_markup = markup)
    #bot.send_message(cid , show_commands(cid) , parse_mode='MarkdownV2')

@bot.message_handler(func=lambda m: m.text in ['/help', Button['help']]) # Working on this, we have no commands
def start_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    markup = create_start_keyboard(cid)
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup = markup)
    # bot.send_message(cid , show_commands(cid) , parse_mode='MarkdownV2')

@bot.message_handler(func = lambda m: m.text == Button['reportpanel'])
def show_performance_handler(message):
    cid = message.chat.id
    markup = create_report_panel(cid)
    bot.send_message(cid , text['enterreportpanel'] , reply_markup=markup)

@bot.message_handler(func = lambda m : m.text == Button['exitreportpanel'])
def exit_report_panel_handler(message):
    cid = message.chat.id
    markup = create_start_keyboard(cid)
    bot.send_message(cid , text['exitreportpanel'] , reply_markup=markup)    

# ------------------

@bot.message_handler(func = lambda m : m.text == Button['teacherpanel'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) :  
            return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 

    markup = create_teacher_panel(cid)
    bot.send_message(cid , text['enterteacherpanel'] , reply_markup=markup)

@bot.message_handler(func = lambda m : m.text == Button['exitteacherpanel'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
            return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 

    markup = create_start_keyboard(cid)
    bot.send_message(cid , text['exitteacherpanel'] , reply_markup=markup)

# ------------------

@bot.message_handler(func = lambda m : m.text == Button['generalquizpanel'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
            return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 

    markup = create_general_quiz_panel(cid)
    bot.send_message(cid , text['entergeneralquizpanel'] , reply_markup=markup)

@bot.message_handler(func = lambda m : m.text == Button['exitgeneralquizpanel'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
            return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_teacher_panel(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 

    markup = create_teacher_panel(cid)
    bot.send_message(cid , text['exitgeneralquizpanel'] , reply_markup=markup)
# ------------------

@bot.message_handler(func = lambda m : m.text == Button['exammanagement'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
            return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 

    markup = create_exam_management_panel(cid)
    bot.send_message(cid , text['enterexampanel'] , reply_markup=markup)

@bot.message_handler(func = lambda m : m.text == Button['exitexammanagement'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
            return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_teacher_panel(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 

    markup = create_teacher_panel(cid)
    bot.send_message(cid , text['exitexampanel'] , reply_markup=markup)

# ------------------

@bot.message_handler(func = lambda m : m.text == Button['createexam'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
            return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 

    markup = create_exam_panel(cid)
    bot.send_message(cid , text['entercreateexampanel'] , reply_markup=markup)

@bot.message_handler(func = lambda m : m.text == Button['exitcreateexam'])
def teacher_panel_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
            return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup) 

    markup = create_exam_management_panel(cid)
    bot.send_message(cid , text['exitcreateexampanel'] , reply_markup=markup)

# ---------------

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
        bot.send_message(admins[i] , text['buttons_choice'] , reply_markup = markup)
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
    bot.send_message(cid , text['support_answered'])
    user_step.pop(cid)

# ------------------------------------

@bot.message_handler(func=lambda m: m.text in ['/quiz', Button['quiz']])
def quiz_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    data = get_categories()
    markup = create_inlinekeyboard_for_categoris_quizmaking(data , 0)
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['request_for_quiz'] , reply_markup= markup) # Working here ...

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
    bot.send_message(cid, result , parse_mode='MarkdownV2')

# -------------------------------------------- category Teacher

@bot.message_handler(func=lambda m: m.text in ['/addcategory', Button['addcategory']])
def add_category_admin(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup)
        return 
    bot.send_message(cid , text['add_category_admin'])
    user_step[cid] = 'getting_category_name'

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , False) == 'getting_category_name')
def getting_ctgy_name(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    last_id = add_categories(message.text)
    bot.send_message(cid , f'added to \nquiz.categories\nid = {last_id}' , reply_to_message_id=message.message_id)  
    user_step.pop(cid)

# -------------------------------------------- add question Teacher

@bot.message_handler(func=lambda m: m.text in ['/addquestion', Button['addquestion']])
def choice_category_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
        markup = create_start_keyboard(cid)
        bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup)
        return 
    data = get_categories()
    markup = create_inlinekeyboard_for_categoris(data , 0)
    bot.send_message(cid , text['choice_category_admin'] , reply_markup=markup)   

@bot.message_handler(content_types=['text' , 'photo']
                    ,func = lambda m : (user_step.get(m.chat.id , '_')).startswith('addquestion'))
def get_question_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    if message.content_type == 'photo' :
        file_list = message.photo
        photo = file_list[-1]
        file_id = photo.file_id
        #bot.send_photo(cid , file_id , caption=message.caption)
        admin_question.setdefault(cid , dict())
        admin_question[cid].setdefault('file_id' , file_id)
        admin_question[cid].setdefault('text' , message.caption)
        print(admin_question)
        user_step[cid] = f'getoption1_{category_id}'
    elif message.content_type == 'text' : 
        admin_question.setdefault(cid , dict())
        admin_question[cid].setdefault('text' , message.text)
        admin_question[cid].setdefault('file_id' , None)
        print(admin_question)
        user_step[cid] = f'getoption1_{category_id}'
    bot.send_message(cid , text['get_option1'])

@bot.message_handler(func = lambda m : (user_step.get(m.chat.id , '_')).startswith('getoption1'))
def get_option1_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    admin_question[cid].setdefault('option1' , message.text)
    print(admin_question)
    user_step[cid] = f'getoption2_{category_id}'
    bot.send_message(cid , text['get_option2'])

@bot.message_handler(func = lambda m : (user_step.get(m.chat.id , '_')).startswith('getoption2'))
def get_option2_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    admin_question[cid].setdefault('option2' , message.text)
    print(admin_question)
    user_step[cid] = f'getoption3_{category_id}'
    bot.send_message(cid , text['get_option3'])

@bot.message_handler(func = lambda m : (user_step.get(m.chat.id , '_')).startswith('getoption3'))
def get_option1_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    admin_question[cid].setdefault('option3' , message.text)
    print(admin_question)
    user_step[cid] = f'getoption4_{category_id}'
    bot.send_message(cid , text['get_option4'])

@bot.message_handler(func = lambda m : (user_step.get(m.chat.id , '_')).startswith('getoption4'))
def get_option1_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    admin_question[cid].setdefault('option4' , message.text)
    print(admin_question)
    user_step[cid] = f'optionans_{category_id}'
    bot.send_message(cid , text['get_optionanswer'])

@bot.message_handler(func = lambda m : (user_step.get(m.chat.id , '_')).startswith('optionans'))
def get_option1_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    admin_question[cid].setdefault('option_answer' , int(message.text))
    print(admin_question)
    user_step[cid] = f'textans_{category_id}'
    bot.send_message(cid , text['get_textanswer'])

@bot.message_handler(content_types= ['text' , 'photo'],
                     func = lambda m : (user_step.get(m.chat.id , '_')).startswith('textans'))
def get_option1_handler(message):
    print('hello')
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    _,category_id = (user_step[cid]).split('_')
    category_id = int(category_id)
    if message.content_type == 'text' :
        admin_question[cid].setdefault('text_answer' , message.text)
    elif message.content_type == 'photo' :
        file_list = message.photo
        photo = file_list[-1]
        file_id = photo.file_id
        admin_question[cid].setdefault('text_answer' , 'isphoto' + file_id)
    print(admin_question)
    user_id_in_table = find_user_id(cid)
    add_question(   category_id = category_id,
                    designer_id = user_id_in_table['ID'],
                    photo_id    = admin_question[cid]['file_id'],
                    text        = admin_question[cid]['text'],
                    op1         = admin_question[cid]['option1'],
                    op2         = admin_question[cid]['option2'],
                    op3         = admin_question[cid]['option3'],
                    op4         = admin_question[cid]['option4'],
                    ansop       = admin_question[cid]['option_answer'],
                    anstext     = admin_question[cid]['text_answer'] )
    
    bot.send_message(cid , text['questoin_added'])
    admin_question.pop(cid)
    user_step.pop(cid)


# -------------------------------------------- report Question
# f'reportwrongqa_{designer_cid}'
@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_').startswith('reportwrongqa'))
def report_question_handler(message):
    cid = message.chat.id
    step = user_step[cid]
    _,question_id,designer_cid = step.split('_')
    designer_cid = int(designer_cid)
    question_id = int(question_id)
    bot.copy_message(designer_cid , CHANNEL_ID , CHANNEL_MESSAGES['quesiton_report'])
    sent_msg = send_question(designer_cid , question_id)
    sent_msg_id = sent_msg.message_id
    markup = create_inline_for_edit_question(question_id , 0)
    bot.copy_message(designer_cid , cid , message.message_id , reply_to_message_id=sent_msg_id , reply_markup=markup)
    bot.send_message(cid , text['report_wrong_question_sended'])
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
    bot.send_message(cid , text['edited_successfully'])
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
    bot.send_message(cid , text['edited_successfully'])
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
    else :
        edit_question_answer_text(qid , message.text)

    bot.send_message(cid , text['edited_successfully'])
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
    bot.send_message(cid , text['edited_successfully'])
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
    elif op == 2:
        edit_question_option2(qid , message.text)
    elif op == 3:
        edit_question_option3(qid , message.text)
    elif op == 4:
        edit_question_option4(qid , message.text)

    bot.send_message(cid , text['edited_successfully'])
    user_step.pop(cid)

# -------------------------------------------- Support Admin

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , False) == 'support_request')
def support_request_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    mid = message.message_id
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Answer' , callback_data=f'anssupport_{cid}_{mid}'))
    # admin
    for i in range(len(admins)):
        bot.forward_message(admins[i] , cid , mid)
        bot.send_message(admins[i] , text['support_request'] , reply_markup=markup)
    # user
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['sended_support']) #to user who wanted support
    print(message.text)
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
    bot.send_message(cid , text['support_answered'])
    user_step.pop(cid)
    update_support_status(user_id= find_user_id(user_cid)['ID'] , user_mid=user_mid, admin_id=find_user_id(cid)['ID'], admin_text=message.text)

@bot.message_handler(func = lambda m : True)
def every_messages_handler(message):
    cid = message.chat.id
    markup = create_start_keyboard(cid)
    bot.copy_message(cid , CHANNEL_ID , CHANNEL_MESSAGES['help'] , reply_markup=markup)

get_admins()
get_teachers()
print('bot is running !')
#skip_pending=True
bot.infinity_polling()