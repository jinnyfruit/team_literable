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

# 초기화 호출
init_db()

# Database 관련 함수
def fetch_students(search_query=None):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()

    if search_query:  # 검색 조건이 있는 경우
        cursor.execute("SELECT * FROM students WHERE name LIKE ?", ('%' + search_query + '%',))
    else:  # 검색 조건이 없는 경우 (모든 학생 데이터 반환)
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

def fetch_passages(search_query=""):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    if search_query:
        cursor.execute("SELECT * FROM passages WHERE title LIKE ?", (f"%{search_query}%",))
    else:
        cursor.execute("SELECT * FROM passages")
    passages = cursor.fetchall()
    conn.close()
    return passages

# 질문 조회 함수
def fetch_questions(passage_id):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''SELECT * FROM questions WHERE passage_id = ?''', (passage_id,))
        questions = cursor.fetchall()
        print(f"질문 조회 성공: passage_id={passage_id}, questions={questions}")
        return questions
    except Exception as e:
        print(f"질문 조회 오류: {e}")
        return []
    finally:
        conn.close()


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
    try:
        cursor.execute('''INSERT INTO questions (passage_id, question, model_answer)
                          VALUES (?, ?, ?)''', (passage_id, question, model_answer))
        conn.commit()
        print(f"질문 저장 성공: passage_id={passage_id}, question={question}, model_answer={model_answer}")
    except Exception as e:
        print(f"질문 저장 오류: {e}")
    finally:
        conn.close()


def delete_passage(passage_id):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM passages WHERE id = ?", (passage_id,))
    conn.commit()
    conn.close()

def delete_question(question_id):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()

def fetch_table_data(table_name):
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    conn.close()
    return data

# PDF 생성 함수
def generate_pdf(student_name, passage_title, evaluation_results):
    pdfmetrics.registerFont(TTFont("NanumGothic", "NanumGothic.ttf"))
    pdf_file = f"{student_name}_{passage_title}_첨삭결과.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter

    c.setFont("NanumGothic", 16)
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

# 학생 관리 함수
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

# 지문 및 문제 관리 함수
def manage_passages_and_questions():
    st.subheader("지문 및 문제 관리")

    # 세션 상태 초기화
    if 'question_count' not in st.session_state:
        st.session_state['question_count'] = 4
    if 'questions' not in st.session_state:
        st.session_state['questions'] = ["" for _ in range(st.session_state['question_count'])]
    if 'model_answers' not in st.session_state:
        st.session_state['model_answers'] = ["" for _ in range(st.session_state['question_count'])]

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
            st.session_state['questions'][i] = st.text_input(
                f"질문 {i + 1}", value=st.session_state['questions'][i], key=f"question_{i}"
            )
            st.session_state['model_answers'][i] = st.text_area(
                f"모범답안 {i + 1}", value=st.session_state['model_answers'][i], key=f"model_answer_{i}"
            )

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
                st.session_state["update_key"] = not st.session_state.get("update_key", False)
            else:
                st.error("지문 제목과 내용을 입력해주세요.")

    st.write("### 등록된 지문 목록")
    search_query = st.text_input("지문 제목 검색")
    passages = fetch_passages(search_query)

    # Streamlit 상태 초기화
    if 'edit_mode' not in st.session_state:
        st.session_state['edit_mode'] = {}

    if passages:
        for passage in passages:
            # 상태 초기화
            if passage[0] not in st.session_state['edit_mode']:
                st.session_state['edit_mode'][passage[0]] = False

            with st.expander(f"제목: {passage[1]}"):
                if st.session_state['edit_mode'][passage[0]]:
                    # 수정 모드: 제목과 지문 내용 수정
                    st.write("### 지문 수정")
                    updated_title = st.text_input("지문 제목", value=passage[1], key=f"edit_title_{passage[0]}")
                    updated_passage = st.text_area("지문 내용", value=passage[2], key=f"edit_passage_{passage[0]}")

                    if st.button("수정 저장", key=f"save_passage_{passage[0]}"):
                        if updated_title and updated_passage:
                            conn = sqlite3.connect("Literable.db")
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE passages SET title = ?, passage = ? WHERE id = ?",
                                (updated_title, updated_passage, passage[0]),
                            )
                            conn.commit()
                            conn.close()
                            st.success("지문이 성공적으로 수정되었습니다!")
                            st.session_state['edit_mode'][passage[0]] = False  # 수정 모드 종료
                            st.session_state["update_key"] = not st.session_state.get("update_key", False)
                        else:
                            st.error("제목과 내용을 모두 입력해야 합니다.")

                    if st.button("수정 취소", key=f"cancel_edit_passage_{passage[0]}"):
                        st.session_state['edit_mode'][passage[0]] = False  # 수정 모드 종료
                else:
                    # 조회 모드
                    st.write(f"**내용:** {passage[2]}")
                    questions = fetch_questions(passage[0])
                    for question in questions:
                        st.write(f"**질문:** {question[2]} | **모범답안:** {question[3]}")

                    # 수정 버튼
                    if st.button("수정", key=f"edit_passage_{passage[0]}"):
                        st.session_state['edit_mode'][passage[0]] = True  # 수정 모드 활성화

                # 지문 삭제 버튼
                if st.button("지문 삭제", key=f"delete_passage_{passage[0]}"):
                    delete_passage(passage[0])
                    st.success("지문이 삭제되었습니다.")
                    st.session_state["update_key"] = not st.session_state.get("update_key", False)
    else:
        st.info("등록된 지문이 없습니다.")


def manage_students_answer():
    print()

# Streamlit 메인
menu = st.sidebar.radio("메뉴", ["데이터 관리 및 답안 작성", "첨삭 결과 및 보고서 생성"])

if menu == "데이터 관리 및 답안 작성":
    st.header("데이터 관리 및 답안 작성")
    tab1, tab2, tab3 = st.tabs(["학생 관리", "지문 및 문제 관리","답안 작성"])

    with tab1:
        manage_students()
    with tab2:
        manage_passages_and_questions()
    with tab3:
        manage_students_answer()

elif menu == "첨삭 결과 및 보고서 생성":
    st.header("첨삭 결과 및 보고서 생성")
    students = fetch_students()
    passages = fetch_passages()

    if students and passages:
        selected_student = st.selectbox("학생 선택", students, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        selected_passage = st.selectbox("지문 선택", passages, format_func=lambda x: f"{x[1]} (ID: {x[0]})")

        if st.button("첨삭 시작"):
            st.spinner("AI 평가 진행 중...")
            # 평가 결과 생성 로직 추가 가능
