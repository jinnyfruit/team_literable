import streamlit as st
import sqlite3
import pandas as pd
import requests
import json
import functools
import time
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu

# API 설정
FN_CALL_KEY = "your-api-key"
FN_CALL_ENDPOINT = "your-endpoint"

headers_fn_call = {
    "Content-Type": "application/json",
    "api-key": FN_CALL_KEY
}

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        school TEXT,
        student_number TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS passages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        passage TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        passage_id INTEGER,
        question TEXT,
        model_answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (passage_id) REFERENCES passages (id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS student_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        question_id INTEGER,
        student_answer TEXT,
        score INTEGER,
        feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (question_id) REFERENCES questions (id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS statistics_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cache_key TEXT UNIQUE,
        cache_value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    )''')

    conn.commit()
    conn.close()

# 데이터베이스 유틸리티 함수들
@safe_db_query
def fetch_students(cursor, search_query=None):
    if search_query:
        cursor.execute("""
            SELECT * FROM students 
            WHERE name LIKE ? OR student_number LIKE ?
            ORDER BY created_at DESC
        """, (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM students ORDER BY created_at DESC")
    return cursor.fetchall()

@safe_db_query
def add_student(cursor, name, school, student_number):
    cursor.execute(
        "INSERT INTO students (name, school, student_number) VALUES (?, ?, ?)",
        (name, school, student_number)
    )

@safe_db_query
def update_student(cursor, student_id, name, school, student_number):
    cursor.execute(
        "UPDATE students SET name = ?, school = ?, student_number = ? WHERE id = ?",
        (name, school, student_number, student_id)
    )

@safe_db_query
def delete_student(cursor, student_id):
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))

@safe_db_query
def fetch_passages(cursor, search_query=None):
    if search_query:
        cursor.execute("""
            SELECT * FROM passages 
            WHERE title LIKE ? OR passage LIKE ?
            ORDER BY created_at DESC
        """, (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM passages ORDER BY created_at DESC")
    return cursor.fetchall()

@safe_db_query
def add_passage(cursor, title, passage):
    cursor.execute(
        "INSERT INTO passages (title, passage) VALUES (?, ?)",
        (title, passage)
    )
    return cursor.lastrowid

@safe_db_query
def add_question(cursor, passage_id, question, model_answer):
    cursor.execute(
        "INSERT INTO questions (passage_id, question, model_answer) VALUES (?, ?, ?)",
        (passage_id, question, model_answer)
    )

@safe_db_query
def fetch_questions(cursor, passage_id):
    cursor.execute(
        "SELECT * FROM questions WHERE passage_id = ? ORDER BY id",
        (passage_id,)
    )
    return cursor.fetchall()

# LLM 함수
def call_llm(system_prompt, user_prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 1500
            }
            response = requests.post(
                FN_CALL_ENDPOINT,
                headers=headers_fn_call,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                st.error(f"LLM 호출 실패: {e}")
                return None
            time.sleep(1)

# 캐시 관리 함수들
def get_cached_statistics(cache_key):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT cache_value, expires_at 
            FROM statistics_cache 
            WHERE cache_key = ? AND expires_at > datetime('now')
        """, (cache_key,))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None
    finally:
        conn.close()

def set_cached_statistics(cache_key, value, expires_in_minutes=15):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO statistics_cache 
            (cache_key, cache_value, expires_at) 
            VALUES (?, ?, datetime('now', ?))
        """, (cache_key, json.dumps(value), f'+{expires_in_minutes} minutes'))
        conn.commit()
    finally:
        conn.close()

# PDF 생성 함수
def generate_pdf(student_name, passage_title, evaluation_results):
    pdf_file = f"{student_name}_{passage_title}_첨삭결과.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter

    # PDF 폰트 설정
    pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))
    c.setFont('NanumGothic', 16)

    # 헤더 정보
    c.drawString(50, height - 50, f"첨삭 결과 - {student_name}")
    c.setFont('NanumGothic', 12)
    c.drawString(50, height - 80, f"지문 제목: {passage_title}")
    c.drawString(50, height - 100, f"분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 결과 출력
    y = height - 140
    for idx, (question, model_answer, student_answer, score, feedback) in enumerate(evaluation_results, 1):
        if y < 100:  # 페이지 넘김
            c.showPage()
            y = height - 50
            c.setFont('NanumGothic', 12)

        c.setFont('NanumGothic', 11)
        c.drawString(50, y, f"문제 {idx}")
        y -= 20

        c.setFont('NanumGothic', 10)
        # 문제 텍스트 줄바꿈 처리
        lines = textwrap.wrap(question, width=80)
        for line in lines:
            c.drawString(50, y, line)
            y -= 15

        y -= 10
        c.drawString(50, y, "모범 답안:")
        y -= 15
        lines = textwrap.wrap(model_answer, width=80)
        for line in lines:
            c.drawString(70, y, line)
            y -= 15

        y -= 10
        c.drawString(50, y, "학생 답안:")
        y -= 15
        lines = textwrap.wrap(student_answer, width=80)
        for line in lines:
            c.drawString(70, y, line)
            y -= 15

        y -= 10
        c.drawString(50, y, f"점수: {score}점")
        y -= 20

        c.drawString(50, y, "피드백:")
        y -= 15
        lines = textwrap.wrap(feedback, width=80)
        for line in lines:
            c.drawString(70, y, line)
            y -= 15

        y -= 30

    c.save()
    return pdf_file

# 데코레이터: 데이터베이스 연결 및 에러 처리
def safe_db_query(query_func):
    @functools.wraps(query_func)
    def wrapper(*args, **kwargs):
        try:
            conn = sqlite3.connect("Literable.db")
            cursor = conn.cursor()
            result = query_func(cursor, *args, **kwargs)
            conn.commit()
            return result
        except sqlite3.Error as e:
            st.error(f"데이터베이스 오류: {str(e)}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    return wrapper

