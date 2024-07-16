import sqlite3

# Создание и подключение к базе данных
conn = sqlite3.connect('chatbot.db')
cursor = conn.cursor()

# Создание таблицы для хранения контекста диалога
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_context (
    user_id INTEGER PRIMARY KEY,
    context TEXT
)
''')

conn.commit()
conn.close()