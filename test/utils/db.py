import sqlite3

def init_db():
    conn = sqlite3.connect("data/Literable.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        school TEXT,
                        student_number TEXT
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS passages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        passage TEXT
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        passage_id INTEGER,
                        question TEXT,
                        model_answer TEXT,
                        question_type INTEGER DEFAULT 1,  -- 1: 사실적, 2: 추론적, 3: 비판적, 4: 창의적
                        FOREIGN KEY (passage_id) REFERENCES passages (id)
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS student_answers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        question_id INTEGER,
                        student_answer TEXT,
                        score INTEGER,
                        feedback TEXT,
                        FOREIGN KEY (student_id) REFERENCES students (id),
                        FOREIGN KEY (question_id) REFERENCES questions (id)
                    )''')
    conn.commit()
    conn.close()

def execute_query(query, params=(), fetch=False):
    conn = sqlite3.connect("data/Literable.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return results
