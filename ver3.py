import streamlit as st
import sqlite3
import pandas as pd
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

    response = requests.post(FN_CALL_ENDPOINT, headers=headers_fn_call, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        st.error(f"Failed to get response from LLM: {response.status_code}")
        return None

# Prompt 읽기 함수
def load_prompt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        st.warning(f"Prompt 파일 '{file_path}'을 찾을 수 없습니다. 기본 템플릿을 사용합니다.")
        return "질문: {question}\n모범 답안: {model_answer}\n학생 답안: {student_answer}"

# Database 초기화 함수
def init_db():
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()

    # 학생 테이블 생성
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        school TEXT,
                        student_number TEXT
                    )''')

    # 지문 테이블 생성
    cursor.execute('''CREATE TABLE IF NOT EXISTS passages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        passage TEXT
                    )''')

    # 문제 테이블 생성
    cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        passage_id INTEGER,
                        question TEXT,
                        model_answer TEXT,
                        FOREIGN KEY (passage_id) REFERENCES passages (id)
                    )''')

    # 학생 답안 테이블 생성
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

# 데이터베이스 초기화
init_db()

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
    pdf_file = f"{student_name}_{passage_title}_첨삭결과.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter

    # PDF 내용 작성
    c.setFont("NanumGothic", 16)  # 한글 폰트 설정
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

        if y < 100:  # 새로운 페이지 추가
            c.showPage()
            y = height - 50

    c.save()
    return pdf_file

# Streamlit 앱 시작
st.title("AI 논술 첨삭 서비스")

menu = st.sidebar.radio("메뉴", ["학생 관리", "지문 검색 및 문제 보기", "학생 답안 작성","학생 답안 관리", "데이터 추가", "첨삭 보고서 생성"])

if menu == "학생 관리":
    st.header("학생 관리")
    # 검색, 생성, 수정, 삭제 기능 구현
    new_student_name = st.text_input("학생 이름", key="create_name")
    new_student_school = st.text_input("학교명", key="create_school")
    new_student_number = st.text_input("학번", key="create_number")

    if st.button("학생 추가"):
        if new_student_name and new_student_school and new_student_number:
            add_student(new_student_name, new_student_school, new_student_number)
            st.success(f"학생 '{new_student_name}' (학교: {new_student_school}, 학번: {new_student_number})이(가) 추가되었습니다.")
        else:
            st.error("모든 정보를 입력하세요.")

    search_name = st.text_input("학생 이름 검색", placeholder="학생 이름 입력")
    students = fetch_students()

    if students:
        student_df = pd.DataFrame(students, columns=["ID", "이름", "학교", "학번"])

        if search_name:
            filtered_students = student_df[student_df["이름"].str.contains(search_name, na=False)]
        else:
            filtered_students = student_df

        if not filtered_students.empty:
            st.dataframe(filtered_students)

            selected_student_id = st.selectbox(
                "수정 또는 삭제할 학생 선택 (ID)",
                filtered_students["ID"]
            )

            if selected_student_id:
                selected_student = student_df[student_df["ID"] == selected_student_id].iloc[0]

                st.subheader("학생 정보 수정")
                new_name = st.text_input("학생 이름", value=selected_student["이름"], key="edit_name")
                new_school = st.text_input("학교명", value=selected_student["학교"], key="edit_school")
                new_number = st.text_input("학번", value=selected_student["학번"], key="edit_number")

                if st.button("학생 정보 수정"):
                    update_student(selected_student_id, new_name, new_school, new_number)
                    st.success("학생 정보가 수정되었습니다.")

                if st.button("학생 삭제"):
                    delete_student(selected_student_id)
                    st.success("학생 정보가 삭제되었습니다.")
        else:
            st.info("검색 결과가 없습니다.")
    else:
        st.info("등록된 학생이 없습니다.")

elif menu == "지문 검색 및 문제 보기":
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

elif menu == "학생 답안 관리":
    st.header("학생 답안 관리")
    students = fetch_students()
    if students:
        selected_student = st.selectbox("학생 선택", students, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        questions = fetch_table_data("questions")
        answers = fetch_table_data("student_answers")

        if selected_student and questions:
            student_answers = [a for a in answers if a[1] == selected_student[0]]

            if student_answers:
                answer_df = pd.DataFrame(student_answers, columns=["답안 ID", "학생 ID", "질문 ID", "학생 답안", "점수", "피드백"])
                st.dataframe(answer_df)

                selected_answer_id = st.selectbox("수정 또는 삭제할 답안 선택 (답안 ID)", answer_df["답안 ID"])
                if selected_answer_id:
                    selected_answer = answer_df[answer_df["답안 ID"] == selected_answer_id].iloc[0]

                    st.subheader("학생 답안 수정")
                    new_answer = st.text_area("학생 답안", value=selected_answer["학생 답안"], key="edit_answer")

                    if st.button("답안 수정"):
                        update_student_answer(selected_answer_id, new_answer)
                        st.success("학생 답안이 수정되었습니다.")

                    if st.button("답안 삭제"):
                        delete_student_answer(selected_answer_id)
                        st.success("학생 답안이 삭제되었습니다.")

            st.subheader("새로운 답안 추가")
            related_questions = [q for q in questions if q[1] == selected_student[0]]
            new_answers = {}

            for question in related_questions:
                new_answers[question[0]] = st.text_area(f"새 답안 (질문: {question[2]})", key=f"new_answer_{question[0]}")

            if st.button("새 답안 저장"):
                for question_id, answer in new_answers.items():
                    if answer:
                        add_student_answer(selected_student[0], question_id, answer)
                st.success("새로운 답안이 저장되었습니다.")

            else:
                st.info("학생의 답안이 없습니다.")
    else:
        st.warning("등록된 학생 데이터가 없습니다.")

elif menu == "학생 답안 작성":
    st.header("학생 답안 작성")
    students = fetch_students()
    passages = fetch_table_data("passages")
    if students and passages:
        selected_student = st.selectbox("학생 선택", students, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        selected_passage = st.selectbox("지문 선택", passages, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        if selected_student and selected_passage:
            questions = fetch_table_data("questions")
            related_questions = [q for q in questions if q[1] == selected_passage[0]]

            st.subheader("학생 답안 작성")
            answers = {}
            for question in related_questions:
                answers[question[0]] = st.text_area(f"질문: {question[2]}", key=f"answer_{question[0]}")

            if st.button("답안 저장"):
                for question_id, answer in answers.items():
                    if answer:
                        add_student_answer(selected_student[0], question_id, answer)
                st.success("학생 답안이 저장되었습니다.")

elif menu == "데이터 추가":
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
            passage_id = add_passage(title, passage)
            for i in range(4):
                add_question(passage_id, questions[i], model_answers[i])
            st.success("지문과 문제 및 모범 답안이 저장되었습니다.")
        else:
            st.error("모든 필드를 입력해주세요.")

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

            if st.button("첨삭하기"):
                if questions and student_answers:
                    conn = sqlite3.connect("Literable.db")
                    cursor = conn.cursor()

                    prompt_template = load_prompt("prompt.txt")
                    if not prompt_template:
                        st.error("Prompt 템플릿을 로드하지 못했습니다.")
                        conn.close()
                    else:
                        evaluation_results = []
                        for idx, question in enumerate(questions):
                            question_text = question[2]
                            model_answer = question[3]
                            student_answer_record = next((a for a in student_answers if a[2] == question[0]), None)
                            if not student_answer_record:
                                continue

                            student_answer = student_answer_record[3]

                            # Prompt에 데이터 삽입
                            user_prompt = prompt_template.format(
                                question=question_text,
                                model_answer=model_answer,
                                student_answer=student_answer
                            )

                            evaluation = call_llm("You are an AI trained to evaluate essays.", user_prompt)

                            if evaluation:
                                # 평가 결과 저장
                                try:
                                    score = int(evaluation.split("점수:")[1].split("\n")[0].strip())
                                    feedback = evaluation.split("피드백:")[1].strip()

                                    cursor.execute("""
                                        UPDATE student_answers
                                        SET score = ?, feedback = ?
                                        WHERE id = ?
                                    """, (score, feedback, student_answer_record[0]))

                                    conn.commit()

                                    evaluation_results.append((question_text, model_answer, student_answer, score, feedback))

                                    # UI에 결과 출력
                                    st.subheader(f"문제 {idx + 1}")
                                    st.text_area("문제", question_text, height=100, disabled=True, key=f"report_question_{idx}")
                                    st.text_area("모범 답안", model_answer, height=100, disabled=True, key=f"report_model_answer_{idx}")
                                    st.text_area("학생 답안", student_answer, height=100, disabled=True, key=f"report_student_answer_{idx}")
                                    st.markdown(f"**LLM 평가 결과**\n- 점수: {score}\n- 피드백: {feedback}", unsafe_allow_html=True)

                                except Exception as e:
                                    st.error(f"평가 결과를 저장하는 중 오류 발생: {e}")
                        conn.close()

                        # PDF 다운로드 버튼
                        if evaluation_results:
                            pdf_file = generate_pdf(selected_student[1], selected_passage[1], evaluation_results)
                            with open(pdf_file, "rb") as file:
                                st.download_button(
                                    label="첨삭 결과 PDF 다운로드",
                                    data=file,
                                    file_name=pdf_file,
                                    mime="application/pdf"
                                )
                else:
                    st.warning("학생 답안 또는 질문 데이터가 부족합니다.")
    else:
        st.warning("학생 데이터를 추가하세요.")
