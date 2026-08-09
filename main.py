import telebot
from telebot.types import ReplyKeyboardMarkup , ReplyKeyboardRemove,InlineKeyboardMarkup,InlineKeyboardButton
from requests_forwarder import setup_proxy
from config_bot import *
from config_db import *
import os
import datetime,time
from Text import *
from DQL import *
from DML import *

setup_proxy(
    proxy_token=proxy_token
)

bot = telebot.TeleBot(telegram_token , threaded= 5)
hide_board = ReplyKeyboardRemove()
#print(f'{os.getcwd()}')

channel_id = -1004392460681 #messages

command = {
    '/start'            : text['start_command'],
    '/help'             : text['help_command'],
    '/support'          : text['support_command'],
    '/quiz'             : text['quiz_creating_command'],
    '/showcategory'     : text['show_categories'],
    '/reqteach'   : text['request_teacher'],
}
teacher_commands = {
    '/addquestion' : text['add_question_teacher'],
    '/addcategory' : text['add_category_command'],
}

admin_commands = {
}

channel_messages = {
    'start'             : 2,
    'help'              : 4,
    'req_support'       : 6,
    'sended_support'    : 8,
    'teacher_request'   : 10,
    'you_added_teacher' : 12,
}

user_step = {}
admin_question = {} # cid : {text : ... , file_id : ... , options : ... , answer_option : ... , answer_text : ...}

# ----- spam
lower_limit = 2     # sec
upper_limit = 15    # sec
max_score = 10
# cid : {last_message_time : ... , score : ...}
spam_data = {}  

teachers = []
admins = []

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
            if user['is_admin'] == 0:
                if user['telegram_id'] in admins:
                    admins.remove(user['telegram_id'])
            if (user['is_teacher'] == 1) and (cid not in teachers):
                teachers.append(cid)
            if user['is_teacher'] == 0:
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

def show_commands(cid , command):
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
        markup.add(InlineKeyboardButton('◀️' , callback_data=f'changepage_{page - 1}') , \
                   InlineKeyboardButton('▶️' , callback_data=f'changepage_{page + 1}'))
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
    elif data.startswith('changepage'):
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
    #reqteach_ans_{cid}|{mid}

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
                bot.copy_message(user_cid , channel_id , channel_messages['you_added_teacher'] , reply_to_message_id=user_mid)
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

@bot.message_handler(commands=['start'])
def start_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    print(admins)
    bot.copy_message(cid , channel_id , channel_messages['start'])
    bot.send_message(cid , show_commands(cid, command) , parse_mode='MarkdownV2')
    # admins

@bot.message_handler(commands=['help'])
def start_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    bot.copy_message(cid , channel_id , channel_messages['help'])
    bot.send_message(cid , show_commands(cid, command) , parse_mode='MarkdownV2')

# Teacher Request ------------------------------------
    
@bot.message_handler(commands=['reqteach'])
def request_teacher_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) :
        return 
    manage_user(message , cid)
    bot.copy_message(cid , channel_id , channel_messages['teacher_request'])
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
    bot.copy_message(cid , channel_id , channel_messages['sended_support'])
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

@bot.message_handler(commands=['quiz'])
def quiz_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    bot.send_message(cid , 'request for quiz')
    # ........ data base 
    # Working here ...

@bot.message_handler(commands=['support']) 
def support_command_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    bot.copy_message(cid , channel_id , channel_messages['req_support'])
    user_step.setdefault(cid , '')
    user_step[cid] = 'support_request'

@bot.message_handler(commands=['showcategory'])
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

@bot.message_handler(commands=['addcategory'])
def add_category_admin(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return 
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
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

@bot.message_handler(commands=['addquestion'])
def choice_category_handler(message):
    cid = message.chat.id
    if is_spam(cid) : 
        return
    manage_user(message , cid)
    if (cid not in teachers) and (cid not in admins):
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
        admin_question[cid].serdefault('text_answer' , file_id)
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
                    anstext     = admin_question[cid]['text_answer'])
    
    bot.send_message(cid , text['questoin_added'])
    admin_question.pop(cid)
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
    bot.copy_message(cid , channel_id , channel_messages['sended_support']) #to user who wanted support
    print(message.text)
    add_support_request(user_id = find_user_id(cid)['ID'] , message_id = mid , text = message.text)
    user_step.pop(cid)

@bot.message_handler(func = lambda m : user_step.get(m.chat.id , '_').startswith('adminanswer')) # inline pressed
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
    
get_admins()
get_teachers()
print('bot is running !')
bot.infinity_polling(skip_pending=True)