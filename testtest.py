
from reportlab.pdfgen import canvas
import streamlit as st
import sqlite3
import pandas as pd
import requests
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.lib import colors

# 폰트 설정 (한글 지원을 위해)
try:
    pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))
    BASE_FONT = 'NanumGothic'
except:
    BASE_FONT = 'Helvetica'
    st.warning("한글 폰트가 설치되어 있지 않아 기본 폰트로 대체됩니다.")

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

    def add_question_session():
        if st.session_state['question_count'] < 10:
            st.session_state['question_count'] += 1
            st.session_state['questions'].append("")
            st.session_state['model_answers'].append("")
        else:
            st.warning("최대 10개의 질문까지만 추가할 수 있습니다.")

    def delete_question_session():
        if st.session_state['question_count'] > 1:
            st.session_state['question_count'] -= 1
            st.session_state['questions'].pop()
            st.session_state['model_answers'].pop()
        else:
            st.warning("질문 입력창이 최소 하나는 있어야 합니다!")

    # 새 지문 추가 섹션
    with st.expander("📝 새로운 지문 및 문제 추가", expanded=True):
        title = st.text_input("지문 제목", max_chars=100)
        passage = st.text_area("지문 내용", height=200)

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

        col1, col2 = st.columns(2)
        with col1:
            st.button("➕ 질문 추가", on_click=add_question_session)
        with col2:
            st.button("➖ 질문 삭제", on_click=delete_question_session)

        if st.button("💾 지문 및 문제 저장"):
            if title and passage:
                passage_id = add_passage(title, passage)
                valid_questions = [
                    (q, a) for q, a in zip(st.session_state['questions'], st.session_state['model_answers'])
                    if q.strip() and a.strip()
                ]
                for question, model_answer in valid_questions:
                    add_question(passage_id, question, model_answer)
                st.success("✅ 지문과 질문이 성공적으로 추가되었습니다!")
                st.session_state['questions'] = ["" for _ in range(st.session_state['question_count'])]
                st.session_state['model_answers'] = ["" for _ in range(st.session_state['question_count'])]
                st.rerun()
            else:
                st.error("제목과 내용을 모두 입력해주세요.")

    # 지문 목록 섹션
    st.header("📋 등록된 지문 목록")
    search_query = st.text_input("🔍 지문 검색", placeholder="제목 또는 내용으로 검색")

    passages = fetch_passages(search_query)
    if not passages:
        st.info("📭 등록된 지문이 없습니다.")
        return

    for passage in passages:
        with st.expander(f"🗂️ 제목: {passage[1]}", expanded=False):
            delete_key = f"delete_state_{passage[0]}"
            if delete_key not in st.session_state:
                st.session_state[delete_key] = False

            # 지문 내용 표시
            st.write(f"**내용:** {passage[2]}")

            # 지문 수정 UI
            if st.session_state['edit_mode'].get(passage[0], False):
                st.subheader("📝 지문 수정")
                updated_title = st.text_input(
                    "지문 제목",
                    value=passage[1],
                    key=f"edit_title_input_{passage[0]}",
                    max_chars=100
                )
                updated_passage = st.text_area(
                    "지문 내용",
                    value=passage[2],
                    key=f"edit_passage_input_{passage[0]}",
                    height=300
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 수정 저장", key=f"save_edit_{passage[0]}"):
                        if updated_title and updated_passage:
                            conn = sqlite3.connect("Literable.db")
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE passages SET title = ?, passage = ? WHERE id = ?",
                                (updated_title, updated_passage, passage[0])
                            )
                            conn.commit()
                            conn.close()
                            st.success("✅ 지문이 수정되었습니다!")
                            st.session_state['edit_mode'][passage[0]] = False
                            st.rerun()
                with col2:
                    if st.button("❌ 취소", key=f"cancel_edit_mode_{passage[0]}"):
                        st.session_state['edit_mode'][passage[0]] = False
                        st.rerun()

            # 질문 관리 섹션
            questions = fetch_questions(passage[0])
            if questions:
                st.subheader("📋 등록된 문제")
                for question in questions:
                    question_edit_key = f"question_edit_state_{question[0]}"  # Modified key
                    if question_edit_key not in st.session_state:
                        st.session_state[question_edit_key] = False

                    st.divider()
                    if st.session_state[question_edit_key]:
                        # 질문 수정 모드
                        updated_question = st.text_input(
                            "질문",
                            value=question[2],
                            key=f"edit_question_input_{question[0]}"  # Modified key
                        )
                        updated_answer = st.text_area(
                            "모범답안",
                            value=question[3],
                            key=f"edit_answer_input_{question[0]}"  # Modified key
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 저장", key=f"save_question_{question[0]}"):  # Modified key
                                conn = sqlite3.connect("Literable.db")
                                cursor = conn.cursor()
                                try:
                                    cursor.execute(
                                        "UPDATE questions SET question = ?, model_answer = ? WHERE id = ?",
                                        (updated_question, updated_answer, question[0])
                                    )
                                    conn.commit()
                                    st.success("✅ 문제가 수정되었습니다!")
                                    st.session_state[question_edit_key] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"수정 중 오류가 발생했습니다: {str(e)}")
                                finally:
                                    conn.close()
                        with col2:
                            if st.button("❌ 취소", key=f"cancel_question_{question[0]}"):  # Modified key
                                st.session_state[question_edit_key] = False
                                st.rerun()
                    else:
                        # 질문 표시 모드
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"**질문:** {question[2]}")
                            st.markdown(f"**모범답안:** {question[3]}")
                        with col2:
                            if st.button("✏️", key=f"edit_question_button_{question[0]}"):  # Modified key
                                st.session_state[question_edit_key] = True
                                st.rerun()
                        with col3:
                            if st.button("🗑️", key=f"delete_question_{question[0]}"):  # Modified key
                                conn = sqlite3.connect("Literable.db")
                                cursor = conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM questions WHERE id = ?", (question[0],))
                                    conn.commit()
                                    st.success("✅ 문제가 삭제되었습니다!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"삭제 중 오류가 발생했습니다: {str(e)}")
                                finally:
                                    conn.close()

            # 새 질문 추가 섹션
            st.divider()
            st.subheader("➕ 새 질문 추가")
            col_q, col_a = st.columns(2)
            with col_q:
                new_question = st.text_input("새 질문", key=f"new_question_{passage[0]}")  # Modified key
            with col_a:
                new_answer = st.text_area("새 모범답안", key=f"new_answer_{passage[0]}")  # Modified key

            if st.button("💾 질문 추가", key=f"add_question_{passage[0]}"):  # Modified key
                if new_question.strip() and new_answer.strip():
                    conn = sqlite3.connect("Literable.db")
                    cursor = conn.cursor()
                    try:
                        add_question(passage[0], new_question, new_answer)
                        st.success("✅ 새로운 문제가 추가되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"추가 중 오류가 발생했습니다: {str(e)}")
                    finally:
                        conn.close()
                else:
                    st.error("질문과 모범답안을 모두 입력해주세요.")

            # 삭제 확인 UI
            if st.session_state[delete_key]:
                st.warning("🚨 정말로 이 지문을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 예, 삭제합니다", key=f"confirm_delete_{passage[0]}"):  # Modified key
                        conn = sqlite3.connect("Literable.db")
                        cursor = conn.cursor()
                        try:
                            cursor.execute("""
                                    DELETE FROM student_answers 
                                    WHERE question_id IN (
                                        SELECT id FROM questions WHERE passage_id = ?
                                    )
                                """, (passage[0],))
                            cursor.execute("DELETE FROM questions WHERE passage_id = ?", (passage[0],))
                            cursor.execute("DELETE FROM passages WHERE id = ?", (passage[0],))
                            conn.commit()
                            st.success("✅ 지문이 성공적으로 삭제되었습니다!")
                            st.session_state[delete_key] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 중 오류가 발생했습니다: {str(e)}")
                        finally:
                            conn.close()
                with col2:
                    if st.button("❌ 취소", key=f"cancel_delete_{passage[0]}"):  # Modified key
                        st.session_state[delete_key] = False
                        st.rerun()

            # 지문 수정/삭제 버튼
            st.divider()
            col1, col2, col3 = st.columns([2, 2, 8])
            with col1:
                if st.button("✏️ 지문 수정", key=f"edit_mode_toggle_{passage[0]}"):  # Modified key
                    st.session_state['edit_mode'][passage[0]] = True
                    st.rerun()
            with col2:
                if st.button("🗑️ 지문 삭제", key=f"delete_init_button_{passage[0]}"):  # Modified key
                    st.session_state[delete_key] = True
                    st.rerun()


def manage_report():
    st.subheader("답안 관리")

    # 학생 검색 및 선택
    st.write("### 학생 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색")

    # 학생 검색 쿼리
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    if search_student:
        cursor.execute("""
            SELECT * FROM students 
            WHERE name LIKE ? OR student_number LIKE ?
        """, (f"%{search_student}%", f"%{search_student}%"))
    else:
        cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()

    if not students:
        st.warning("검색된 학생이 없습니다.")
        return

    with col2:
        selected_student = st.selectbox(
            "학생 선택",
            students,
            format_func=lambda x: f"{x[1]} ({x[2]} - {x[3]})",  # 이름 (학교 - 학번)
            key="student_select"
        )

    # 지문 검색 및 선택
    st.write("### 지문 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_passage = st.text_input("지문 제목 검색")

    # 지문 검색 쿼리
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    if search_passage:
        cursor.execute("""
            SELECT * FROM passages 
            WHERE title LIKE ?
        """, (f"%{search_passage}%",))
    else:
        cursor.execute("SELECT * FROM passages")
    passages = cursor.fetchall()
    conn.close()

    if not passages:
        st.warning("검색된 지문이 없습니다.")
        return

    with col2:
        selected_passage = st.selectbox(
            "지문 선택",
            passages,
            format_func=lambda x: x[1],  # 지문 제목만 표시
            key="passage_select"
        )

    # 선택된 지문 내용 표시
    with st.expander("지문 내용 보기", expanded=False):
        st.write(selected_passage[2])

    # 선택된 지문의 문제들 가져오기
    questions = fetch_questions(selected_passage[0])
    if not questions:
        st.warning("선택된 지문에 등록된 문제가 없습니다.")
        return

    # 선택된 학생의 답안들 가져오기
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sa.*, q.question, q.model_answer 
        FROM student_answers sa 
        JOIN questions q ON sa.question_id = q.id 
        WHERE sa.student_id = ? AND q.passage_id = ?
    """, (selected_student[0], selected_passage[0]))
    existing_answers = {answer[2]: answer for answer in cursor.fetchall()}  # question_id를 키로 사용
    conn.close()

    # 답안 관리 섹션
    st.write("### 답안 입력 및 수정")

    # 전체 답안 상태 표시
    total_questions = len(questions)
    answered_questions = len(existing_answers)
    st.write(f"답안 작성 현황: {answered_questions}/{total_questions} 문제 완료")
    progress = answered_questions / total_questions if total_questions > 0 else 0
    st.progress(progress)

    for question in questions:
        with st.expander(f"문제: {question[2]}", expanded=True):
            # 기존 답안이 있는 경우
            existing_answer = existing_answers.get(question[0])

            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("**모범답안:**")
                st.info(question[3])

            with col2:
                if existing_answer:
                    st.write("**현재 점수:**")
                    st.info(f"{existing_answer[4]}점")

            # 답안 입력/수정 폼
            with st.form(key=f"answer_form_{question[0]}"):
                student_answer = st.text_area(
                    "학생 답안",
                    value=existing_answer[3] if existing_answer else "",
                    height=150
                )

                col1, col2 = st.columns([2, 2])
                with col1:
                    score = st.number_input(
                        "점수",
                        min_value=0,
                        max_value=100,
                        value=existing_answer[4] if existing_answer else 0
                    )
                with col2:
                    feedback = st.text_area(
                        "피드백",
                        value=existing_answer[5] if existing_answer else "",
                        height=100
                    )

                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    submit = st.form_submit_button("저장")
                with col2:
                    if existing_answer:
                        delete = st.form_submit_button("삭제", type="secondary")

                if submit and student_answer:
                    conn = sqlite3.connect("Literable.db")
                    cursor = conn.cursor()

                    if existing_answer:
                        # 기존 답안 수정
                        cursor.execute("""
                            UPDATE student_answers 
                            SET student_answer = ?, score = ?, feedback = ? 
                            WHERE id = ?
                        """, (student_answer, score, feedback, existing_answer[0]))
                        st.success("답안이 성공적으로 수정되었습니다!")
                    else:
                        # 새로운 답안 추가
                        cursor.execute("""
                            INSERT INTO student_answers 
                            (student_id, question_id, student_answer, score, feedback) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (selected_student[0], question[0], student_answer, score, feedback))
                        st.success("답안이 성공적으로 저장되었습니다!")

                    conn.commit()
                    conn.close()
                    st.rerun()  # experimental_rerun() 대신 rerun() 사용

                elif submit and not student_answer:
                    st.error("답안을 입력해주세요.")

                if existing_answer and delete:
                    conn = sqlite3.connect("Literable.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM student_answers WHERE id = ?", (existing_answer[0],))
                    conn.commit()
                    conn.close()
                    st.warning("답안이 삭제되었습니다.")
                    st.rerun()  # experimental_rerun() 대신 rerun() 사용


def load_prompt(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        st.error(f"프롬프트 파일을 찾을 수 없습니다: {filename}")
        return None
    except Exception as e:
        st.error(f"프롬프트 파일 읽기 오류: {str(e)}")
        return None


def analyze_feedback():
    st.subheader("AI 첨삭")

    # 학생 검색 및 선택
    st.write("### 학생 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색")

    # 학생 검색 쿼리
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    if search_student:
        cursor.execute("""
            SELECT * FROM students 
            WHERE name LIKE ? OR student_number LIKE ?
        """, (f"%{search_student}%", f"%{search_student}%"))
    else:
        cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()

    if not students:
        st.warning("검색된 학생이 없습니다.")
        return

    with col2:
        selected_student = st.selectbox(
            "학생 선택",
            students,
            format_func=lambda x: f"{x[1]} ({x[2]} - {x[3]})"
        )

    # 지문 검색 및 선택
    st.write("### 지문 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_passage = st.text_input("지문 제목 검색")

    # 지문 검색 쿼리
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    if search_passage:
        cursor.execute("""
            SELECT * FROM passages 
            WHERE title LIKE ?
        """, (f"%{search_passage}%",))
    else:
        cursor.execute("SELECT * FROM passages")
    passages = cursor.fetchall()
    conn.close()

    if not passages:
        st.warning("검색된 지문이 없습니다.")
        return

    with col2:
        selected_passage = st.selectbox(
            "지문 선택",
            passages,
            format_func=lambda x: x[1]
        )

    if selected_student and selected_passage:
        # 저장된 답안 확인
        conn = sqlite3.connect("Literable.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.id, q.question, q.model_answer, sa.student_answer, sa.score, sa.feedback
            FROM questions q
            LEFT JOIN student_answers sa ON q.id = sa.question_id 
                AND sa.student_id = ?
            WHERE q.passage_id = ?
            ORDER BY q.id
        """, (selected_student[0], selected_passage[0]))
        answers = cursor.fetchall()
        conn.close()

        if not any(answer[3] for answer in answers):
            st.warning("저장된 답안이 없습니다. 답안 관리 탭에서 먼저 답안을 입력해주세요.")
            return

        # 답안 표시 및 분석
        answers_to_analyze = {}
        questions_order = []  # 문제 순서 유지를 위한 리스트

        for i, answer in enumerate(answers, 1):
            if answer[3]:  # 답안이 있는 경우만 처리
                with st.expander(f"{answer[1]}", expanded=True):
                    st.write("**모범답안:**")
                    st.info(answer[2])

                    st.write("**학생답안:**")
                    st.info(answer[3])

                    if answer[4] is not None:
                        st.write("**현재 점수:**", f"{answer[4]}점")
                        st.write("**피드백:**", answer[5] if answer[5] else "")

                answers_to_analyze[i] = {
                    'question_id': answer[0],
                    'question_text': answer[1],
                    'model_answer': answer[2],
                    'student_answer': answer[3]
                }
                questions_order.append(i)

        if answers_to_analyze:
            if st.button("📝 AI 첨삭 분석 시작", type="primary"):
                system_prompt = load_prompt("prompt.txt")
                if system_prompt is None:
                    return

                with st.spinner("AI가 답안을 분석중입니다..."):
                    analysis_results = []
                    progress_bar = st.progress(0)

                    for i, q_num in enumerate(questions_order):
                        data = answers_to_analyze[q_num]
                        progress_text = st.empty()
                        progress_text.text(f"분석 진행중... ({i + 1}/{len(questions_order)})")
                        progress_bar.progress((i + 1) / len(questions_order))

                        user_prompt = f"""
                        문제: {data['question_text']}
                        모범답안: {data['model_answer']}
                        학생답안: {data['student_answer']}
                        """

                        result = call_llm(system_prompt, user_prompt)
                        if result:
                            try:
                                score_text = result.split('점수:')[1].split('\n')[0]
                                score = int(score_text.replace('점', '').strip())
                                feedback = result.split('피드백:')[1].split('개선사항:')[0].strip()

                                analysis_results.append({
                                    'question_id': data['question_id'],
                                    'question_text': data['question_text'],
                                    'student_answer': data['student_answer'],
                                    'score': score,
                                    'feedback': feedback
                                })
                            except Exception as e:
                                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")

                    progress_text.empty()
                    progress_bar.empty()

                    if analysis_results:
                        # 결과 저장
                        conn = sqlite3.connect("Literable.db")
                        cursor = conn.cursor()
                        try:
                            for result in analysis_results:
                                cursor.execute("""
                                    UPDATE student_answers 
                                    SET score = ?, feedback = ?
                                    WHERE student_id = ? AND question_id = ?
                                """, (result['score'], result['feedback'],
                                      selected_student[0], result['question_id']))
                            conn.commit()
                            st.success("첨삭 보고서가 저장되었습니다. 분석 결과 탭에서 확인할 수 있습니다.")

                        except Exception as e:
                            st.error(f"결과 저장 중 오류가 발생했습니다: {str(e)}")
                        finally:
                            conn.close()
                            st.rerun()

def main():
    # 사이드바 스타일링 및 구성
    with st.sidebar:
        st.image("Logo.png", width=50)
        st.title("Literable")

        # 구분선 추가
        st.markdown("---")

        # 메뉴 선택
        selected = option_menu(
            menu_title=None,
            options=["데이터 관리", "AI 첨삭 분석", "통계 대시보드"],
            icons=["gear", "robot", "graph-up"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important"},
                "icon": {"font-size": "1rem"},
                "nav-link": {
                    "font-size": "0.9rem",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
            },
        )

        # 사이드바 하단 정보
        st.markdown("---")
        st.caption("© 2024 Literable")

    # 메인 컨텐츠
    if selected == "데이터 관리":
        st.title("데이터 관리")
        tabs = st.tabs(["👥 학생 관리", "📚 지문/문제 관리", "📝 답안 작성"])

        with tabs[0]:
            manage_students()
        with tabs[1]:
            manage_passages_and_questions()
        with tabs[2]:
            manage_report()

    elif selected == "AI 첨삭 분석":
        st.title("AI 첨삭 분석")
        tabs = st.tabs(["🤖 AI 첨삭", "📊 분석 결과"])

        with tabs[0]:
            analyze_feedback()
        with tabs[1]:
            show_detailed_analysis()

    else:  # 통계 대시보드
        st.title("통계 대시보드")
        tabs = st.tabs(["📈 종합 통계", "👥 학생별 분석", "📚 지문별 분석"])

        with tabs[0]:
            show_overall_statistics()
        with tabs[1]:
            show_student_statistics()
        with tabs[2]:
            show_passage_statistics()


def format_feedback_report(student, passage, results):
    """첨삭 보고서 HTML 형식 생성"""
    report_html = f"""
    <div class="report-container">
        <div class="report-header">
            <h2 class="passage-title">{passage[1]}</h2>
            <div class="student-info">
                <p><strong>학생명:</strong> {student[1]}</p>
                <p><strong>학교:</strong> {student[2]}</p>
                <p><strong>학번:</strong> {student[3]}</p>
            </div>
        </div>

        <div class="report-summary">
            <h3>종합 평가</h3>
            <p>총 문항: {len(results)}개</p>
            <p>평균 점수: {sum(r[3] for r in results) / len(results):.1f}점</p>
        </div>

        <style>
            .report-container {{
                padding: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }}
            .report-header {{
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
            }}
            .passage-title {{
                color: #2c3e50;
                margin-bottom: 20px;
            }}
            .student-info {{
                display: flex;
                justify-content: space-around;
                margin-top: 20px;
            }}
            .student-info p {{
                margin: 0;
            }}
            .report-summary {{
                margin: 20px 0;
                padding: 15px;
                background: #e9ecef;
                border-radius: 8px;
            }}
            .question-card {{
                margin: 20px 0;
                padding: 20px;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                position: relative;
            }}
            .score-badge {{
                position: absolute;
                top: 20px;
                right: 20px;
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 1.2em;
            }}
            .answer-section {{
                margin: 15px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }}
            .feedback-section {{
                margin-top: 15px;
                padding: 15px;
                background: #e9ecef;
                border-radius: 5px;
            }}
        </style>
    """

    for i, result in enumerate(results, 1):
        question, model_answer, student_answer, score, feedback = result
        report_html += f"""
        <div class="question-card">
            <div class="score-badge">{score}점</div>

            <h4>문제</h4>
            <p>{question}</p>

            <div class="answer-section">
                <h5>모범답안</h5>
                <p>{model_answer}</p>
            </div>

            <div class="answer-section">
                <h5>학생답안</h5>
                <p>{student_answer}</p>
            </div>

            <div class="feedback-section">
                <h5>첨삭 내용</h5>
                <p>{feedback}</p>
            </div>
        </div>
        """

    report_html += "</div>"
    return report_html


def generate_pdf_report(student, passage, results):
    """PDF 보고서 생성"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    # 스타일 정의
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,
        fontName=BASE_FONT
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        fontName=BASE_FONT
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        fontName=BASE_FONT
    )

    # 문서 요소 생성
    elements = []

    # 제목 및 학생 정보
    elements.append(Paragraph(passage[1], title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"학생명: {student[1]}", normal_style))
    elements.append(Paragraph(f"학교: {student[2]}", normal_style))
    elements.append(Paragraph(f"학번: {student[3]}", normal_style))
    elements.append(Spacer(1, 20))

    # 문제별 분석
    for i, result in enumerate(results, 1):
        question, model_answer, student_answer, score, feedback = result

        elements.append(Paragraph(f"[점수: {score}점]", heading_style))
        elements.append(Paragraph("문제:", normal_style))
        elements.append(Paragraph(question, normal_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("모범답안:", normal_style))
        elements.append(Paragraph(model_answer, normal_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("학생답안:", normal_style))
        elements.append(Paragraph(student_answer, normal_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("첨삭 내용:", normal_style))
        elements.append(Paragraph(feedback, normal_style))
        elements.append(Spacer(1, 20))

    # PDF 생성
    doc.build(elements)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


def analyze_feedback():
    st.subheader("AI 첨삭")

    # 학생 검색 및 선택
    st.write("### 학생 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색", key="feedback_student_search")

    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    if search_student:
        cursor.execute("""
            SELECT * FROM students 
            WHERE name LIKE ? OR student_number LIKE ?
        """, (f"%{search_student}%", f"%{search_student}%"))
    else:
        cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    if not students:
        st.warning("검색된 학생이 없습니다.")
        return

    with col2:
        selected_student = st.selectbox(
            "학생 선택",
            students,
            format_func=lambda x: f"{x[1]} ({x[2]} - {x[3]})",
            key="feedback_student_select"
        )

    # 지문 검색 및 선택
    st.write("### 지문 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_passage = st.text_input("지문 제목 검색", key="feedback_passage_search")

    if search_passage:
        cursor.execute("""
            SELECT * FROM passages 
            WHERE title LIKE ?
        """, (f"%{search_passage}%",))
    else:
        cursor.execute("SELECT * FROM passages")
    passages = cursor.fetchall()

    if not passages:
        st.warning("검색된 지문이 없습니다.")
        return

    with col2:
        selected_passage = st.selectbox(
            "지문 선택",
            passages,
            format_func=lambda x: x[1],
            key="feedback_passage_select"
        )

    if selected_student and selected_passage:
        # 저장된 답안 확인
        cursor.execute("""
            SELECT q.id, q.question, q.model_answer, sa.student_answer, sa.score, sa.feedback
            FROM questions q
            LEFT JOIN student_answers sa ON q.id = sa.question_id 
                AND sa.student_id = ?
            WHERE q.passage_id = ?
            ORDER BY q.id
        """, (selected_student[0], selected_passage[0]))
        answers = cursor.fetchall()

        if not any(answer[3] for answer in answers):
            st.warning("저장된 답안이 없습니다. 답안 관리 탭에서 먼저 답안을 입력해주세요.")
            return

        # 답안 표시 및 분석
        st.write("### 저장된 답안")
        answers_to_analyze = {}

        for answer in answers:
            if answer[3]:  # 답안이 있는 경우만 표시
                with st.expander(f"{answer[1]}", expanded=True):
                    st.write("**모범답안:**")
                    st.info(answer[2])

                    st.write("**학생답안:**")
                    st.info(answer[3])

                    if answer[4] is not None:
                        st.write("**현재 점수:**", f"{answer[4]}점")
                        st.write("**피드백:**", answer[5] if answer[5] else "")

                    answers_to_analyze[answer[0]] = {
                        'question_text': answer[1],
                        'model_answer': answer[2],
                        'student_answer': answer[3]
                    }

        if answers_to_analyze:
            if st.button("📝 AI 첨삭 분석 시작", type="primary"):
                system_prompt = load_prompt("prompt.txt")
                if system_prompt is None:
                    return

                with st.spinner("AI가 답안을 분석중입니다..."):
                    analysis_results = []
                    progress_bar = st.progress(0)
                    progress_text = st.empty()

                    for i, (question_id, data) in enumerate(answers_to_analyze.items()):
                        progress_text.text(f"분석 진행중... ({i + 1}/{len(answers_to_analyze)})")
                        progress_bar.progress((i + 1) / len(answers_to_analyze))

                        user_prompt = f"""
                        문제: {data['question_text']}
                        모범답안: {data['model_answer']}
                        학생답안: {data['student_answer']}
                        """

                        result = call_llm(system_prompt, user_prompt)
                        if result:
                            try:
                                score_text = result.split('점수:')[1].split('\n')[0]
                                score = int(score_text.replace('점', '').strip())
                                feedback = result.split('피드백:')[1].split('개선사항:')[0].strip()

                                analysis_results.append({
                                    'question_id': question_id,
                                    'score': score,
                                    'feedback': feedback
                                })
                            except Exception as e:
                                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")

                    progress_text.empty()
                    progress_bar.empty()

                    if analysis_results:
                        try:
                            for result in analysis_results:
                                cursor.execute("""
                                    UPDATE student_answers 
                                    SET score = ?, feedback = ?
                                    WHERE student_id = ? AND question_id = ?
                                """, (result['score'], result['feedback'],
                                      selected_student[0], result['question_id']))
                            conn.commit()
                            st.success("첨삭 보고서가 저장되었습니다. 분석 결과 탭에서 확인할 수 있습니다.")
                            st.rerun()

                        except Exception as e:
                            st.error(f"결과 저장 중 오류가 발생했습니다: {str(e)}")

    conn.close()

def generate_pdf_report(student, passage, results):
    """PDF 보고서 생성"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    # 스타일 정의
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # center alignment
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12
    )
    normal_style = styles['Normal']

    # 문서 요소 생성
    elements = []

    # 제목 및 학생 정보
    elements.append(Paragraph(passage[1], title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"학생명: {student[1]}", normal_style))
    elements.append(Paragraph(f"학교: {student[2]}", normal_style))
    elements.append(Paragraph(f"학번: {student[3]}", normal_style))
    elements.append(Spacer(1, 20))

    # 문제별 분석
    for i, result in enumerate(results, 1):
        question, model_answer, student_answer, score, feedback = result

        elements.append(Paragraph(f"문제 {i} (점수: {score}점)", heading_style))
        elements.append(Paragraph(f"문제: {question}", normal_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("모범답안:", normal_style))
        elements.append(Paragraph(model_answer, normal_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("학생답안:", normal_style))
        elements.append(Paragraph(student_answer, normal_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("첨삭 내용:", normal_style))
        elements.append(Paragraph(feedback, normal_style))
        elements.append(Spacer(1, 20))

    # PDF 생성
    doc.build(elements)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

def show_detailed_analysis():
    st.subheader("분석 결과")

    # 학생 검색 및 선택
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색", key="analysis_student_search")

    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
    if search_student:
        cursor.execute("""
            SELECT DISTINCT s.* FROM students s
            JOIN student_answers sa ON s.id = sa.student_id
            WHERE s.name LIKE ? OR s.student_number LIKE ?
        """, (f"%{search_student}%", f"%{search_student}%"))
    else:
        cursor.execute("""
            SELECT DISTINCT s.* FROM students s
            JOIN student_answers sa ON s.id = sa.student_id
        """)
    students = cursor.fetchall()

    if not students:
        st.info("분석된 답안이 있는 학생이 없습니다.")
        return

    with col2:
        selected_student = st.selectbox(
            "학생 선택",
            students,
            format_func=lambda x: f"{x[1]} ({x[2]} - {x[3]})"
        )

    if selected_student:
        cursor.execute("""
            SELECT DISTINCT p.* FROM passages p
            JOIN questions q ON p.id = q.passage_id
            JOIN student_answers sa ON q.id = sa.question_id
            WHERE sa.student_id = ?
            ORDER BY p.id DESC
        """, (selected_student[0],))
        passages = cursor.fetchall()

        if passages:
            selected_passage = st.selectbox(
                "지문 선택",
                passages,
                format_func=lambda x: x[1]
            )

            if selected_passage:
                # 분석 결과 조회
                cursor.execute("""
                    SELECT 
                        q.question,
                        q.model_answer,
                        sa.student_answer,
                        sa.score,
                        sa.feedback
                    FROM questions q
                    JOIN student_answers sa ON q.id = sa.question_id
                    WHERE sa.student_id = ? AND q.passage_id = ?
                    ORDER BY q.id
                """, (selected_student[0], selected_passage[0]))
                results = cursor.fetchall()

                if results:
                    # PDF 다운로드 버튼
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        pdf_data = generate_pdf_report(selected_student, selected_passage, results)
                        st.download_button(
                            label="📑 PDF 저장",
                            data=pdf_data,
                            file_name=f"{selected_student[1]}_{selected_passage[1]}_첨삭보고서.pdf",
                            mime="application/pdf"
                        )

                    # HTML 형식의 보고서 표시
                    report_html = format_feedback_report(selected_student, selected_passage, results)
                    st.markdown(report_html, unsafe_allow_html=True)

        else:
            st.info("분석된 답안이 없습니다.")

    conn.close()


def show_overall_statistics():
    st.subheader("전체 통계")

    # 데이터베이스에서 전체 통계 데이터 가져오기
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()

    # 전체 평균 점수
    cursor.execute("SELECT AVG(score) FROM student_answers")
    total_avg = cursor.fetchone()[0] or 0

    # 총 답안 수
    cursor.execute("SELECT COUNT(*) FROM student_answers")
    total_answers = cursor.fetchone()[0] or 0

    # 구간별 분포
    cursor.execute("""
        SELECT 
            CASE 
                WHEN score >= 90 THEN 'A (90-100)'
                WHEN score >= 80 THEN 'B (80-89)'
                WHEN score >= 70 THEN 'C (70-79)'
                WHEN score >= 60 THEN 'D (60-69)'
                ELSE 'F (0-59)'
            END as grade,
            COUNT(*) as count
        FROM student_answers
        GROUP BY grade
        ORDER BY grade
    """)
    grade_distribution = cursor.fetchall()

    # 통계 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 평균", f"{total_avg:.1f}점")
    with col2:
        st.metric("총 답안 수", f"{total_answers:,}개")
    with col3:
        st.metric("응시 학생 수", f"{len(fetch_students()):,}명")

    # 점수 분포 시각화
    if grade_distribution:
        df = pd.DataFrame(grade_distribution, columns=['등급', '학생 수'])
        fig = plt.figure(figsize=(10, 5))
        plt.bar(df['등급'], df['학생 수'])
        plt.title('전체 점수 분포')
        st.pyplot(fig)
        plt.close()


def show_student_statistics():
    st.subheader("학생별 분석")

    # 학생 선택
    students = fetch_students()
    selected_student = st.selectbox(
        "학생 선택",
        students,
        format_func=lambda x: f"{x[1]} ({x[2]})"
    )

    if selected_student:
        # 선택된 학생의 통계 데이터 가져오기
        conn = sqlite3.connect("Literable.db")
        cursor = conn.cursor()

        # 학생의 평균 점수 및 전체 평균과의 비교
        cursor.execute("""
            SELECT 
                AVG(sa.score) as student_avg,
                (SELECT AVG(score) FROM student_answers) as total_avg
            FROM student_answers sa
            WHERE sa.student_id = ?
        """, (selected_student[0],))
        avg_data = cursor.fetchone()

        if avg_data[0]:
            student_avg, total_avg = avg_data

            # 평균 비교 표시
            col1, col2 = st.columns(2)
            with col1:
                st.metric("학생 평균", f"{student_avg:.1f}점")
            with col2:
                diff = student_avg - total_avg
                st.metric("전체 평균과의 차이", f"{diff:+.1f}점")

            # 시간에 따른 점수 변화
            cursor.execute("""
                SELECT p.title, sa.score, sa.created_at
                FROM student_answers sa
                JOIN questions q ON sa.question_id = q.id
                JOIN passages p ON q.passage_id = p.id
                WHERE sa.student_id = ?
                ORDER BY sa.created_at
            """, (selected_student[0],))
            progress_data = cursor.fetchall()

            if progress_data:
                progress_df = pd.DataFrame(progress_data, columns=['지문', '점수', '날짜'])
                fig = plt.figure(figsize=(10, 5))
                plt.plot(range(len(progress_df)), progress_df['점수'], marker='o')
                plt.title('시간에 따른 점수 변화')
                plt.xticks(range(len(progress_df)), progress_df['지문'], rotation=45)
                plt.grid(True, alpha=0.3)
                st.pyplot(fig)
                plt.close()


def show_passage_statistics():
    st.subheader("지문별 분석")

    # 지문 선택
    passages = fetch_passages()
    selected_passage = st.selectbox(
        "지문 선택",
        passages,
        format_func=lambda x: f"{x[1]}"
    )

    if selected_passage:
        conn = sqlite3.connect("Literable.db")
        cursor = conn.cursor()

        # 지문별 평균 점수 및 문제별 평균
        cursor.execute("""
            SELECT 
                q.question,
                AVG(sa.score) as avg_score,
                COUNT(sa.id) as attempt_count
            FROM questions q
            LEFT JOIN student_answers sa ON q.id = sa.question_id
            WHERE q.passage_id = ?
            GROUP BY q.id
        """, (selected_passage[0],))
        question_stats = cursor.fetchall()

        if question_stats:
            # 문제별 평균 점수 시각화
            df = pd.DataFrame(question_stats, columns=['문제', '평균 점수', '응시 횟수'])

            fig = plt.figure(figsize=(10, 5))
            plt.bar(range(len(df)), df['평균 점수'])
            plt.title('문제별 평균 점수')
            plt.xticks(range(len(df)), [f'문제 {i + 1}' for i in range(len(df))], rotation=0)
            plt.ylim(0, 100)
            plt.grid(True, alpha=0.3)

            # 평균 점수 표시
            for i, v in enumerate(df['평균 점수']):
                plt.text(i, v + 1, f'{v:.1f}점', ha='center')

            st.pyplot(fig)
            plt.close()

            # 상세 통계 표시
            st.write("### 문제별 상세 통계")
            st.dataframe(df)


if __name__ == "__main__":
    st.set_page_config(
        page_title="Literable",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()