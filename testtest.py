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
    st.subheader("📚 지문 및 문제 관리")

    # 세션 상태 초기화
    if 'question_count' not in st.session_state:
        st.session_state['question_count'] = 4
    if 'questions' not in st.session_state:
        st.session_state['questions'] = ["" for _ in range(st.session_state['question_count'])]
    if 'model_answers' not in st.session_state:
        st.session_state['model_answers'] = ["" for _ in range(st.session_state['question_count'])]
    if 'edit_mode' not in st.session_state:
        st.session_state['edit_mode'] = {}
    # 수정 모드에서의 새 문제 추가를 위한 상태
    if 'edit_new_questions' not in st.session_state:
        st.session_state['edit_new_questions'] = {}

    def validate_passage_input(title, passage):
        """지문 입력 검증 함수"""
        errors = []
        if not title:
            errors.append("제목을 입력해주세요.")
        if len(title) > 100:
            errors.append("제목은 100자 이내로 입력해주세요.")
        if not passage:
            errors.append("지문 내용을 입력해주세요.")
        if len(passage) < 10:
            errors.append("지문 내용은 최소 10자 이상이어야 합니다.")
        return errors

    def add_question_session():
        """질문 입력 세션 추가"""
        if st.session_state['question_count'] < 10:
            st.session_state['question_count'] += 1
            st.session_state['questions'].append("")
            st.session_state['model_answers'].append("")
        else:
            st.warning("최대 10개의 질문까지만 추가할 수 있습니다.")

    def delete_question_session():
        """질문 입력 세션 삭제"""
        if st.session_state['question_count'] > 1:
            st.session_state['question_count'] -= 1
            st.session_state['questions'].pop()
            st.session_state['model_answers'].pop()
        else:
            st.warning("질문 입력창이 최소 하나는 있어야 합니다!")

    def add_edit_question_session(passage_id):
        """수정 모드에서 질문 추가"""
        if passage_id not in st.session_state['edit_new_questions']:
            st.session_state['edit_new_questions'][passage_id] = []
        st.session_state['edit_new_questions'][passage_id].append({"question": "", "answer": ""})

    def delete_edit_question_session(passage_id, index):
        """수정 모드에서 새로 추가된 질문 삭제"""
        if passage_id in st.session_state['edit_new_questions']:
            st.session_state['edit_new_questions'][passage_id].pop(index)

    def save_new_questions(passage_id):
        """새로 추가된 질문들 저장"""
        if passage_id in st.session_state['edit_new_questions']:
            for q_data in st.session_state['edit_new_questions'][passage_id]:
                if q_data["question"].strip() and q_data["answer"].strip():
                    add_question(passage_id, q_data["question"], q_data["answer"])
            # 저장 후 초기화
            st.session_state['edit_new_questions'][passage_id] = []

    def confirm_delete_passage(passage_id):
        """지문 삭제 확인 모달"""
        st.warning("🚨 정말로 이 지문을 삭제하시겠습니까?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 예, 삭제합니다", key=f"confirm_delete_{passage_id}"):
                delete_passage(passage_id)
                st.success("🗑️ 지문이 삭제되었습니다.")
                st.session_state["update_key"] = not st.session_state.get("update_key", False)
                st.rerun()
        with col2:
            st.button("❌ 취소", key=f"cancel_delete_{passage_id}")

    def update_question(question_id, question_text, model_answer):
        """질문 업데이트 함수"""
        conn = sqlite3.connect("Literable.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE questions SET question = ?, model_answer = ? WHERE id = ?",
            (question_text, model_answer, question_id)
        )
        conn.commit()
        conn.close()

    def delete_passage(passage_id):
        """지문과 연관된 질문 모두 삭제"""
        conn = sqlite3.connect("Literable.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions WHERE passage_id = ?", (passage_id,))
        cursor.execute("DELETE FROM passages WHERE id = ?", (passage_id,))
        conn.commit()
        conn.close()

    # 메인 섹션 - 새 지문 추가
    with st.expander("📝 새로운 지문 및 문제 추가", expanded=True):
        # 지문 입력
        title = st.text_input("지문 제목", max_chars=100)
        passage = st.text_area("지문 내용", height=200)

        # 동적 질문 및 모범답안 입력
        for i in range(st.session_state['question_count']):
            st.divider()
            col_q, col_a = st.columns(2)
            with col_q:
                st.session_state['questions'][i] = st.text_input(
                    f"질문 {i + 1}",
                    value=st.session_state['questions'][i],
                    key=f"question_{i}"
                )
            with col_a:
                st.session_state['model_answers'][i] = st.text_area(
                    f"모범답안 {i + 1}",
                    value=st.session_state['model_answers'][i],
                    key=f"model_answer_{i}",
                    height=100
                )

        # 질문 추가/삭제 버튼
        col1, col2 = st.columns(2)
        with col1:
            st.button("➕ 질문 추가", on_click=add_question_session)
        with col2:
            st.button("➖ 질문 삭제", on_click=delete_question_session)

        # 저장 버튼
        if st.button("💾 지문 및 문제 저장"):
            # 입력 검증
            input_errors = validate_passage_input(title, passage)

            if not input_errors:
                # 지문 추가
                passage_id = add_passage(title, passage)

                # 질문 추가
                valid_questions = [
                    (q, a) for q, a in zip(st.session_state['questions'], st.session_state['model_answers'])
                    if q.strip() and a.strip()
                ]

                for question, model_answer in valid_questions:
                    add_question(passage_id, question, model_answer)

                st.success("✅ 지문과 질문이 성공적으로 추가되었습니다!")
                st.session_state["update_key"] = not st.session_state.get("update_key", False)
            else:
                for error in input_errors:
                    st.error(error)

    # 등록된 지문 목록
    st.header("📋 등록된 지문 목록")
    search_query = st.text_input("🔍 지문 검색", placeholder="제목 또는 내용으로 검색")
    passages = fetch_passages(search_query)

    if passages:
        for passage in passages:
            with st.expander(f"🗂️ 제목: {passage[1]}", expanded=False):
                if st.session_state['edit_mode'].get(passage[0], False):
                    # 지문 수정 모드
                    st.subheader("📝 지문 수정")
                    updated_title = st.text_input(
                        "지문 제목",
                        value=passage[1],
                        key=f"edit_title_{passage[0]}",
                        max_chars=100
                    )
                    updated_passage = st.text_area(
                        "지문 내용",
                        value=passage[2],
                        key=f"edit_passage_{passage[0]}",
                        height=300
                    )

                    # 기존 문제 표시 및 수정
                    st.subheader("📋 기존 문제 수정")
                    questions = fetch_questions(passage[0])
                    if questions:
                        for question in questions:
                            st.divider()
                            question_edit_key = f"question_edit_{question[0]}"
                            if question_edit_key not in st.session_state:
                                st.session_state[question_edit_key] = False

                            if st.session_state[question_edit_key]:
                                updated_question = st.text_input(
                                    "질문",
                                    value=question[2],
                                    key=f"edit_q_{question[0]}"
                                )
                                updated_answer = st.text_area(
                                    "모범답안",
                                    value=question[3],
                                    key=f"edit_a_{question[0]}"
                                )
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("💾 저장", key=f"save_q_{question[0]}"):
                                        update_question(question[0], updated_question, updated_answer)
                                        st.session_state[question_edit_key] = False
                                        st.success("✅ 문제가 수정되었습니다!")
                                        st.rerun()
                                with col2:
                                    if st.button("❌ 취소", key=f"cancel_q_{question[0]}"):
                                        st.session_state[question_edit_key] = False
                                        st.rerun()
                            else:
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    st.markdown(f"**질문:** {question[2]}")
                                    st.markdown(f"**모범답안:** {question[3]}")
                                with col2:
                                    if st.button("✏️", key=f"edit_q_{question[0]}"):
                                        st.session_state[question_edit_key] = True
                                        st.rerun()
                                with col3:
                                    if st.button("🗑️", key=f"delete_q_{question[0]}"):
                                        delete_question(question[0])
                                        st.success("✅ 문제가 삭제되었습니다!")
                                        st.rerun()

                    # 새 문제 추가 섹션
                    st.subheader("📝 새 문제 추가")
                    if passage[0] not in st.session_state['edit_new_questions']:
                        st.session_state['edit_new_questions'][passage[0]] = []

                    for idx, new_q in enumerate(st.session_state['edit_new_questions'][passage[0]]):
                        st.divider()
                        col_q, col_a = st.columns([1, 1])
                        with col_q:
                            new_q["question"] = st.text_input(
                                "새 질문",
                                value=new_q["question"],
                                key=f"new_q_{passage[0]}_{idx}"
                            )
                        with col_a:
                            new_q["answer"] = st.text_area(
                                "새 모범답안",
                                value=new_q["answer"],
                                key=f"new_a_{passage[0]}_{idx}",
                                height=100
                            )
                        if st.button("❌ 삭제", key=f"delete_new_q_{passage[0]}_{idx}"):
                            delete_edit_question_session(passage[0], idx)
                            st.rerun()

                    if st.button("➕ 새 문제 추가", key=f"add_new_q_{passage[0]}"):
                        add_edit_question_session(passage[0])
                        st.rerun()

                    # 저장 및 취소 버튼
                    st.divider()
                    col_save, col_cancel, col_delete = st.columns(3)
                    with col_save:
                        if st.button("💾 모든 변경사항 저장", key=f"save_all_{passage[0]}"):
                            edit_errors = validate_passage_input(updated_title, updated_passage)
                            if not edit_errors:
                                # 지문 업데이트
                                conn = sqlite3.connect("Literable.db")
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE passages SET title = ?, passage = ? WHERE id = ?",
                                    (updated_title, updated_passage, passage[0]),
                                )
                                conn.commit()
                                conn.close()
                                # 새 문제 저장
                                save_new_questions(passage[0])
                                st.success("✅ 모든 변경사항이 저장되었습니다!")
                                st.session_state['edit_mode'][passage[0]] = False
                                st.rerun()
                            else:
                                for error in edit_errors:
                                    st.error(error)

                    with col_cancel:
                        if st.button("❌ 수정 취소", key=f"cancel_edit_{passage[0]}"):
                            st.session_state['edit_mode'][passage[0]] = False
                            st.session_state['edit_new_questions'][passage[0]] = []
                            st.rerun()

                    with col_delete:
                        if st.button("🗑️ 지문 삭제", key=f"delete_{passage[0]}"):
                            confirm_delete_passage(passage[0])

                else:
                    # 조회 모드
                    st.write(f"**내용:** {passage[2]}")
                    questions = fetch_questions(passage[0])
                    if questions:
                        st.subheader("📋 관련 문제")
                        for question in questions:
                            st.divider()
                            st.markdown(f"**질문:** {question[2]}")
                            st.markdown(f"**모범답안:** {question[3]}")

                    st.divider()
                    if st.button("✏️ 지문 수정", key=f"edit_{passage[0]}"):
                        st.session_state['edit_mode'][passage[0]] = True
                        st.rerun()
    else:
        st.info("📭 등록된 지문이 없습니다.")
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
