import streamlit as st
import sqlite3
import pandas as pd
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt

# GPT-4o API 설정
FN_CALL_KEY = "5acf6c1d1aed44eaa670dd059c8c84ce"
FN_CALL_ENDPOINT = "https://apscus-prd-aabc2-openai.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"

headers_fn_call = {
    "Content-Type": "application/json",
    "api-key": FN_CALL_KEY
}

# LLM 호출 함수
def call_llm(system_prompt, user_prompt):
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1500
    }
    try:
        response = requests.post(FN_CALL_ENDPOINT, headers=headers_fn_call, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        st.error(f"LLM 호출 실패: {e}")
        return None

# Database 초기화 함수
def init_db():
    conn = sqlite3.connect("Literable.db")
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

init_db()

# 데이터 관리 및 답안 작성 기능
# 데이터베이스 관련 함수
def fetch_students():
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()
    return students

def add_student(name, school, student_number):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name, school, student_number) VALUES (?, ?, ?)", (name, school, student_number))
    conn.commit()
    conn.close()

def update_student(student_id, name, school, student_number):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET name = ?, school = ?, student_number = ? WHERE id = ?", (name, school, student_number, student_id))
    conn.commit()
    conn.close()

def delete_student(student_id):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

def fetch_table_data(table_name):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    conn.close()
    return data

def manage_students():
    st.subheader("학생 관리")
    new_student_name = st.text_input("학생 이름")
    new_student_school = st.text_input("학교명")
    new_student_number = st.text_input("학번")

    if st.button("학생 추가"):
        if new_student_name and new_student_school and new_student_number:
            add_student(new_student_name, new_student_school, new_student_number)
            st.success(f"학생 '{new_student_name}'이 추가되었습니다.")
        else:
            st.error("모든 정보를 입력하세요.")

    search_name = st.text_input("학생 이름 검색", placeholder="학생 이름 입력")
    students = fetch_students()

    if students:
        student_df = pd.DataFrame(students, columns=["ID", "이름", "학교", "학번"])

        if search_name:
            filtered_students = student_df[student_df["이름"].str.contains(search_name, case=False, na=False)]
        else:
            filtered_students = student_df

        st.dataframe(filtered_students)

        selected_student_id = st.selectbox(
            "수정 또는 삭제할 학생 선택 (ID)",
            filtered_students["ID"]
        )

        if selected_student_id:
            selected_student = student_df[student_df["ID"] == selected_student_id].iloc[0]

            st.text_input("학생 이름", value=selected_student["이름"], key="edit_name")
            st.text_input("학교명", value=selected_student["학교"], key="edit_school")
            st.text_input("학번", value=selected_student["학번"], key="edit_number")

            if st.button("학생 정보 수정"):
                update_student(selected_student_id, new_student_name, new_student_school, new_student_number)
                st.success("학생 정보가 수정되었습니다.")

            if st.button("학생 삭제"):
                delete_student(selected_student_id)
                st.success("학생 정보가 삭제되었습니다.")
    else:
        st.info("등록된 학생이 없습니다.")

def add_passage(title, passage):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO passages (title, passage) VALUES (?, ?)", (title, passage))
    passage_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return passage_id

def add_question(passage_id, question, model_answer):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO questions (passage_id, question, model_answer) VALUES (?, ?, ?)", (passage_id, question, model_answer))
    conn.commit()
    conn.close()

def add_student_answer(student_id, question_id, student_answer):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO student_answers (student_id, question_id, student_answer) VALUES (?, ?, ?)", (student_id, question_id, student_answer))
    conn.commit()
    conn.close()

def update_student_answer(answer_id, student_answer):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE student_answers SET student_answer = ? WHERE id = ?", (student_answer, answer_id))
    conn.commit()
    conn.close()

def delete_student_answer(answer_id):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM student_answers WHERE id = ?", (answer_id,))
    conn.commit()
    conn.close()

# PDF 생성 함수
def generate_pdf(student_name, passage_title, evaluation_results):
    pdfmetrics.registerFont(TTFont("NanumGothic", "NanumGothic.ttf"))
    pdf_file = f"{student_name}_{passage_title}_첨삭결과.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter

    c.setFont("NanumGothic-Bold", 16)
    c.drawString(50, height - 50, f"첨삭 결과 - {student_name}")
    c.setFont("NanumGothic", 12)
    c.drawString(50, height - 80, f"지문 제목: {passage_title}")

    y = height - 120
    for idx, result in enumerate(evaluation_results):
        question, model_answer, student_answer, score, feedback = result

        c.setFont("NanumGothic-Bold", 12)
        c.drawString(50, y, f"문제 {idx + 1}")
        y -= 20

        c.setFont("NanumGothic", 10)
        c.drawString(50, y, f"문제: {question}")
        y -= 40
        c.drawString(50, y, f"모범 답안: {model_answer}")
        y -= 40
        c.drawString(50, y, f"학생 답안: {student_answer}")
        y -= 40
        c.drawString(50, y, f"점수: {score}")
        y -= 20
        c.drawString(50, y, f"피드백: {feedback}")
        y -= 40

        if y < 100:
            c.showPage()
            y = height - 50

    c.save()
    return pdf_file

def manage_report():

def manage_QA():


# 점수 시각화 함수
def plot_scores(evaluation_results):
    questions = [f"문제 {i+1}" for i in range(len(evaluation_results))]
    scores = [result[3] for result in evaluation_results]

    fig, ax = plt.subplots()
    ax.bar(questions, scores)
    ax.set_title("학생 답안 점수")
    ax.set_xlabel("문제")
    ax.set_ylabel("점수")
    st.pyplot(fig)

# 첨삭 결과 및 보고서 생성
def generate_feedback(selected_student, selected_passage):
    questions = fetch_table_data("questions")
    student_answers = fetch_table_data("student_answers")

    relevant_questions = [q for q in questions if q[1] == selected_passage[0]]
    relevant_answers = [a for a in student_answers if a[1] == selected_student[0]]

    evaluation_results = []

    for question in relevant_questions:
        student_answer = next((a[3] for a in relevant_answers if a[2] == question[0]), None)
        if student_answer:
            user_prompt = "질문: {question}\n모범 답안: {model_answer}\n학생 답안: {student_answer}".format(
                question=question[2],
                model_answer=question[3],
                student_answer=student_answer
            )
            feedback = call_llm("Evaluate the essay:", user_prompt)
            if feedback:
                score = int(feedback.split("점수:")[1].split("\n")[0].strip())
                comments = feedback.split("피드백:")[1].strip()
                evaluation_results.append((question[2], question[3], student_answer, score, comments))

    return evaluation_results

# Streamlit 메인
menu = st.sidebar.radio("메뉴", ["데이터 관리 및 답안 작성", "첨삭 결과 및 보고서 생성"])

if menu == "데이터 관리 및 답안 작성":
    st.header("데이터 관리 및 답안 작성")
    tab1, tab2, tab3 = st.tabs(["학생 관리", "지문 및 문제 관리", "답안 작성"])

    with tab1:
        manage_students()
    with tab2:
        manage_QA()
    with tab3:
        manage_report()
elif menu == "첨삭 결과 및 보고서 생성":
    st.header("첨삭 결과 및 보고서 생성")
    students = fetch_students()
    passages = fetch_table_data("passages")

    if students and passages:
        selected_student = st.selectbox("학생 선택", students, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        selected_passage = st.selectbox("지문 선택", passages, format_func=lambda x: f"{x[1]} (ID: {x[0]})")

        if st.button("첨삭 시작"):
            with st.spinner("AI 모델이 답안을 평가 중입니다..."):
                evaluation_results = generate_feedback(selected_student, selected_passage)

            if evaluation_results:
                plot_scores(evaluation_results)
                pdf_file = generate_pdf(selected_student[1], selected_passage[1], evaluation_results)
                with open(pdf_file, "rb") as file:
                    st.download_button(
                        label="PDF 다운로드",
                        data=file,
                        file_name=pdf_file,
                        mime="application/pdf"
                    )
    else:
        st.warning("학생 또는 지문 데이터가 부족합니다.")
