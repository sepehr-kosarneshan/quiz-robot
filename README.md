# Telegram Quiz & Online Exam Bot

A feature-rich Telegram bot designed for interactive public quizzes, secure private exams, bulk question management, and real-time test administration.

---

## 🌟 Key Features

### 1. Exam & Quiz Modes
* **Public Quizzes:** Browse and participate in quizzes filtered by general categories.
* **Private Exams:** Access specific, secure exams using a unique entry code provided by the instructor.

### 2. User Roles & Admin Approval
* **Student/Participant:** Take quizzes, enter private exams, and track personal results.
* **Teacher/Creator Panel:** Regular users can submit a request for instructor privileges. Once approved by an admin, teachers unlock access to:
  * Create and configure new exams.
  * Add and categorize questions.
  * Edit, update, or deactivate existing exams and question sets.

### 3. Flexible Question Management
* **Interactive Step-by-Step Creation:** Add single questions directly in Telegram through guided bot prompts.
* **Bulk Excel Import:** Upload multiple questions simultaneously using Excel (`.xlsx`) files. The bot includes a built-in option to download templates and formatting guides (`openpyxl` & `pandas`).

### 4. Real-Time Exam Administration
* **Automated Timers:** Timers configured by exam creators run seamlessly for all active test-takers.
* **Live Configuration Updates:** If an instructor changes the duration or deactivates an ongoing exam, the system applies the update instantly across all active sessions.

### 5. Performance Reports & Analytics
* View comprehensive report cards and historical performance for both public quizzes and private exams at any time.

### 6. Support & Error Reporting
* **Support Integration:** Access contact support directly from any panel within the bot.
* **Automated Question Flagging:** Report errors or typos in specific questions during a test. Reports are automatically generated and dispatched to the original creator of that question.

---

## 🛠️ Tech Stack & Requirements

* **Language:** Python 3.10+
* **Framework:** `pyTelegramBotAPI` (TeleBot)
* **Database:** MySQL
* **File Handling:** `openpyxl` and `pandas` (Excel import/export)


---

## 🚀 Getting Started

### Prerequisites

* Python 3.10 or higher
* MySQL Database Server
* Telegram Bot Token (obtained via [@BotFather](https://t.me/BotFather))

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/quiz-telegram-bot.git](https://github.com/your-username/quiz-telegram-bot.git)
cd quiz-telegram-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Configuration

Import your database schema into MySQL. Ensure the following core tables are present:
* `categories`           
* `exam`                
* `exam_questions`       
* `questions`            
* `user_answers`         
* `user_support_request` 
* `users`        

### 4. Environment Setup

Create a `.env` file or set environment variables with your configuration:

```bash
proxy_token = ...
telegram_token = ...
host = ...
password = ...
user = ...
database_name = ...
```

---

## 💡 Running the Bot

### Local Execution

```bash
python main.py
```

### Cloud Deployment (e.g., Runflare / Docker / PaaS)

When deploying to PaaS platforms, ensure persistent storage (Volumes/Disks) is attached if storing media, logs, or local SQLite backups. For MySQL setups, ensure database environment variables match your managed database instance credentials.

---

## 📊 Excel Template Structure

For bulk importing questions via Excel (`.xlsx`), structure columns as follows:

| category_id | text | photo_id | answer_text | op1 | op2 | op3 | op4 | ans_option |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | What is 2 + 2? | NULL | this is 4 ! | 2 | 3 | 4 | 5 | 3 |

* `category_id`: Integer corresponding to the database category.
* `answer_text` : A text or add `isphoto` into the begining of your picture id.
* `photo_id`: `NULL` if no image; telegram file ID if image attached.
* `ans_option`: Number matching the correct option index (e.g., `4` for option 4).

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.