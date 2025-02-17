import streamlit as st
import sqlite3
import requests

# GPT-4o API 설정
FN_CALL_KEY = "5acf6c1d1aed44eaa670dd059c8c84ce"
FN_CALL_ENDPOINT = "https://apscus-prd-aabc2-openai.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"

headers_fn_call = {
    "Content-Type": "application/json",
    "api-key": FN_CALL_KEY
}

def call_llm(system_prompt, user_prompt):
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1500
    }

    response = requests.post(FN_CALL_ENDPOINT, headers=headers_fn_call, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        st.error(f"Failed to get response from LLM: {response.status_code}")
        return None

# Database initialization
def init_db():
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()

    # 학생 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT
                    )''')

    # 지문 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS passages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        passage TEXT
                    )''')

    # 문제 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        passage_id INTEGER,
                        question TEXT,
                        model_answer TEXT,
                        FOREIGN KEY (passage_id) REFERENCES passages (id)
                    )''')

    # 학생 답안 테이블
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

# Initialize database
init_db()

# Database functions
def fetch_table_data(table_name):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    conn.close()
    return data

def add_student(name):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def fetch_students():
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()
    return students

# Streamlit app
st.title("AI 논술 첨삭 서비스")

menu = st.sidebar.radio("메뉴", ["학생 관리", "지문 검색 및 문제 보기", "학생 답안 입력", "첨삭 보고서 생성", "데이터 추가"])

# 학생 관리
if menu == "학생 관리":
    st.header("학생 관리")
    new_student_name = st.text_input("학생 이름")
    if st.button("학생 추가"):
        if new_student_name:
            add_student(new_student_name)
            st.success(f"학생 '{new_student_name}'이(가) 추가되었습니다.")
        else:
            st.error("학생 이름을 입력하세요.")

    st.subheader("등록된 학생 목록")
    students = fetch_students()
    for student in students:
        st.text(f"ID: {student[0]}, 이름: {student[1]}")

# 지문 검색 및 문제 보기
if menu == "지문 검색 및 문제 보기":
    st.header("지문 검색 및 문제 보기")
    passages = fetch_table_data("passages")
    if passages:
        selected_passage = st.selectbox("지문 선택", passages, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        if selected_passage:
            st.text_area("지문 내용", selected_passage[2], height=200, disabled=True, key=f"passage_{selected_passage[0]}")
            questions = fetch_table_data("questions")
            related_questions = [q for q in questions if q[1] == selected_passage[0]]
            for idx, question in enumerate(related_questions):
                st.text_area(f"문제: {question[2]}", height=100, disabled=True, key=f"question_{question[0]}")
                st.text_area(f"모범 답안: {question[3]}", height=100, disabled=True, key=f"model_answer_{question[0]}")
    else:
        st.warning("저장된 지문이 없습니다.")

# 학생 답안 입력
if menu == "학생 답안 입력":
    st.header("학생 답안 입력")
    students = fetch_students()
    if students:
        selected_student = st.selectbox("학생 선택", students, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        passages = fetch_table_data("passages")
        if passages:
            selected_passage = st.selectbox("지문 선택", passages, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
            questions = fetch_table_data("questions")
            related_questions = [q for q in questions if q[1] == selected_passage[0]]
            answers = {}
            for idx, question in enumerate(related_questions):
                st.text_area(f"문제: {question[2]}", height=100, disabled=True, key=f"student_question_{question[0]}")
                answers[question[0]] = st.text_area(f"학생 답안 (문제 ID: {question[0]})", height=100, key=f"student_answer_{question[0]}")
            if st.button("답안 저장"):
                conn = sqlite3.connect("Literable.db")
                cursor = conn.cursor()
                for question_id, answer in answers.items():
                    cursor.execute("INSERT INTO student_answers (student_id, question_id, student_answer) VALUES (?, ?, ?)",
                                   (selected_student[0], question_id, answer))
                conn.commit()
                conn.close()
                st.success("답안이 저장되었습니다.")
        else:
            st.warning("저장된 지문이 없습니다.")
    else:
        st.warning("학생 데이터를 추가하세요.")

# 첨삭 보고서 생성
if menu == "첨삭 보고서 생성":
    st.header("첨삭 보고서 생성")
    students = fetch_students()
    if students:
        selected_student = st.selectbox("학생 선택", students, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        passages = fetch_table_data("passages")
        if passages:
            selected_passage = st.selectbox("지문 선택", passages, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
            questions_data = fetch_table_data("questions")
            student_answers_data = fetch_table_data("student_answers")

            # 관련 질문, 모범 답안, 학생 답안 필터링
            questions = [q for q in questions_data if q[1] == selected_passage[0]]
            student_answers = [a for a in student_answers_data if a[1] == selected_student[0]]

            if questions and student_answers:
                for idx, question in enumerate(questions):
                    question_text = question[2]
                    model_answer = question[3]
                    student_answer = next((a[3] for a in student_answers if a[2] == question[0]), None)
                    if not student_answer:
                        continue

                    system_prompt = "You are an AI trained to evaluate essay responses."
                    user_prompt = f"""
문제: {question_text}
모범 답안: {model_answer}
학생 답안: {student_answer}

위의 학생 답안을 평가하고 점수(0-100)를 매기세요. 또한, 학생 답안에 대한 피드백을 제공하세요.
결과는 아래 형식으로 반환하세요:
점수: <점수>
피드백: <피드백>
"""

                    evaluation = call_llm(system_prompt, user_prompt)
                    st.subheader(f"문제: {question_text}")
                    st.text_area("학생 답안", student_answer, height=100, disabled=True, key=f"eval_student_answer_{idx}")
                    st.text_area("LLM 평가 결과", evaluation, height=150, disabled=True, key=f"eval_result_{idx}")

    else:
        st.warning("학생 데이터를 추가하세요.")

# 데이터 추가
if menu == "데이터 추가":
    st.header("데이터 추가")
    title = st.text_input("지문 제목")
    passage = st.text_area("지문 텍스트", height=200, key="new_passage")
    questions = []
    model_answers = []
    for i in range(1, 5):
        questions.append(st.text_area(f"문제 {i}", height=100, key=f"new_question_{i}"))
        model_answers.append(st.text_area(f"문제 {i} 모범 답안", height=100, key=f"new_model_answer_{i}"))
    if st.button("지문 및 문제 저장"):
        if title and passage and all(questions) and all(model_answers):
            conn = sqlite3.connect("Literable.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO passages (title, passage) VALUES (?, ?)", (title, passage))
            passage_id = cursor.lastrowid
            for i in range(4):
                cursor.execute("INSERT INTO questions (passage_id, question, model_answer) VALUES (?, ?, ?)",
                               (passage_id, questions[i], model_answers[i]))
            conn.commit()
            conn.close()
            st.success("지문과 문제 및 모범 답안이 저장되었습니다.")
        else:
            st.error("모든 필드를 입력해주세요.")
