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
                        FOREIGN KEY (passage_id) REFERENCES passages ()
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

def fetch_passages(search_query=""):
    conn = sqlite3.connect("Literable.db")
    try:
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM passages WHERE title LIKE ?", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT * FROM passages")
        passages = cursor.fetchall()
        return passages
    finally:
        conn.close()
def fetch_questions(passage_id):
    conn = sqlite3.connect("Literable.db")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE passage_id = ?", (passage_id,))
        questions = cursor.fetchall()
        return questions
    finally:
        conn.close()

def add_passage(title, passage):
    conn = sqlite3.connect("Literable.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO passages (title, passage) VALUES (?, ?)", (title, passage))
        passage_id = cursor.lastrowid
        conn.commit()
        return passage_id
    finally:
        conn.close()

def add_question(passage_id, question, model_answer):
    conn = sqlite3.connect("Literable.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO questions (passage_id, question, model_answer) VALUES (?, ?, ?)",
                       (passage_id, question, model_answer))
        conn.commit()
    finally:
        conn.close()

def delete_passage(passage_id):
    conn = sqlite3.connect("Literable.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM passages WHERE id = ?", (passage_id,))
        conn.commit()
    finally:
        conn.close()

def delete_question(question_id):
    conn = sqlite3.connect("Literable.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
    finally:
        conn.close()

def manage_students():
    st.subheader("학생 관리")

    # 학생 추가
    with st.form("add_student"):
        name = st.text_input("학생 이름")
        school = st.text_input("학교")
        student_number = st.text_input("학번")
        submitted = st.form_submit_button("학생 추가")
        if submitted:
            if name and school and student_number:
                add_student(name, school, student_number)
                st.success("학생이 성공적으로 추가되었습니다!")
            else:
                st.error("모든 필드를 입력해주세요.")

    # 학생 검색
    st.write("### 학생 검색")
    search_query = st.text_input("학생 이름 검색")
    students = fetch_students(search_query)

    # 검색 결과 표시
    st.write("### 등록된 학생 목록")
    if students:
        for student in students:
            with st.expander(f"{student[1]} ({student[2]}) - 학번: {student[3]}"):
                # 수정 및 삭제
                with st.form(f"edit_student_{student[0]}"):
                    updated_name = st.text_input("학생 이름", value=student[1])
                    updated_school = st.text_input("학교", value=student[2])
                    updated_student_number = st.text_input("학번", value=student[3])
                    col1, col2 = st.columns([1, 8])
                    with col1:
                        update_submitted = st.form_submit_button("수정")
                    with col2:
                        delete_submitted = st.form_submit_button("삭제")
                    if update_submitted:
                        if updated_name and updated_school and updated_student_number:
                            update_student(student[0], updated_name, updated_school, updated_student_number)
                            st.success("학생 정보가 수정되었습니다!")
                        else:
                            st.error("모든 필드를 입력해주세요.")
                    if delete_submitted:
                        delete_student(student[0])
                        st.warning("학생이 삭제되었습니다.")
    else:
        st.info("검색된 학생이 없습니다.")

def manage_QA():

    st.subheader("지문 및 문제 관리")

    # 세션 상태 초기화
    if 'question_count' not in st.session_state:
        st.session_state['question_count'] = 4
    if 'questions' not in st.session_state:
        st.session_state['questions'] = ["" for _ in range(st.session_state['question_count'])]
    if 'model_answers' not in st.session_state:
        st.session_state['model_answers'] = ["" for _ in range(st.session_state['question_count'])]

    # 질문 추가 및 삭제 버튼 동작
    def add_question_session():
        st.session_state['question_count'] += 1
        st.session_state['questions'].append("")
        st.session_state['model_answers'].append("")

    def delete_question_session():
        if st.session_state['question_count'] > 1:
            st.session_state['question_count'] -= 1
            st.session_state['questions'].pop()
            st.session_state['model_answers'].pop()
        else:
            st.warning("질문 입력창이 최소 하나는 있어야 합니다!")

    with st.expander("질문 및 모범답안 관리", expanded=True):
        title = st.text_input("지문 제목")
        passage = st.text_area("지문 내용")

        for i in range(st.session_state['question_count']):
            st.text_input(f"질문 {i + 1}", value=st.session_state['questions'][i], key=f"question_{i}")
            st.text_area(f"모범답안 {i + 1}", value=st.session_state['model_answers'][i], key=f"model_answer_{i}")

        # 질문 추가/삭제 버튼 아래로 이동
        st.write("\n")  # Add spacing for clarity
        col1, col2 = st.columns([1, 1])
        with col1:
            st.button("질문 추가", on_click=add_question_session)
        with col2:
            st.button("질문 삭제", on_click=delete_question_session)

        if st.button("저장"):
            if title and passage:
                passage_id = add_passage(title, passage)
                for question, model_answer in zip(st.session_state['questions'], st.session_state['model_answers']):
                    if question and model_answer:
                        add_question(passage_id, question, model_answer)
                st.success("지문과 질문이 성공적으로 추가되었습니다!")
            else:
                st.error("지문 제목과 내용을 입력해주세요.")

    st.write("### 등록된 지문 목록")
    search_query = st.text_input("지문 제목 검색")
    passages = fetch_passages(search_query)

    if passages:
        for passage in passages:
            with st.expander(f"제목: {passage[1]}"):
                st.write(f"내용: {passage[2]}")
                questions = fetch_questions(passage[0])
                for question in questions:
                    st.write(f"질문: {question[2]} | 모범답안: {question[3]}")
                    if st.button("질문 삭제", key=f"delete_question_{question[0]}"):
                        delete_question(question[0])
                        st.experimental_rerun()

                if st.button("지문 삭제", key=f"delete_passage_{passage[0]}"):
                    delete_passage(passage[0])
                    st.experimental_rerun()
    else:
        st.info("등록된 지문이 없습니다.")


def manage_report():
    st.subheader("답안 작성")
    st.write("학생 답안을 입력하고 조회/수정/삭제할 수 있습니다.")

    # 학생 선택
    student_name = st.selectbox("학생 선택", ["홍길동", "김철수"])

    # 질문 선택 및 답안 작성
    question_list = ["질문 1: 환경 문제란 무엇인가?", "질문 2: 환경 문제의 원인은?"]
    selected_question = st.selectbox("질문 선택", question_list)

    # 답안 입력 및 제출
    with st.form("submit_answer"):
        st.text_area("학생 답안", key="student_answer")
        st.slider("점수 입력", min_value=0, max_value=100, key="score")
        st.text_area("피드백 입력", key="feedback")
        submitted = st.form_submit_button("답안 제출")
        if submitted:
            st.success(f"{student_name} 학생의 답안이 성공적으로 저장되었습니다!")

    # 기존 답안 조회 및 수정/삭제
    st.write("### 기존 답안 목록")
    existing_answers = [
        {"question": "질문 1: 환경 문제란 무엇인가?", "answer": "환경 문제는 ...", "score": 90, "feedback": "좋은 답변입니다."},
        {"question": "질문 2: 환경 문제의 원인은?", "answer": "환경 문제의 원인은 ...", "score": 85, "feedback": "구체적인 답변이 필요합니다."},
    ]
    for answer in existing_answers:
        st.write(f"질문: {answer['question']}")
        st.write(f"답안: {answer['answer']}")
        st.write(f"점수: {answer['score']}")
        st.write(f"피드백: {answer['feedback']}")
        st.button(f"수정 ({answer['question']})", key=f"edit_{answer['question']}")
        st.button(f"삭제 ({answer['question']})", key=f"delete_{answer['question']}")

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
