import streamlit as st
import sqlite3
from openai import OpenAI
import json


# Database initialization
def init_db():
    conn = sqlite3.connect("Literable.db")
    cursor = conn.cursor()
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
                        question_id INTEGER,
                        student_answer TEXT,
                        score INTEGER,
                        feedback TEXT,
                        FOREIGN KEY (question_id) REFERENCES questions (id)
                    )''')
    conn.commit()
    conn.close()


# OpenAI setup (replace with your OpenAI API key)
openai_api_key = "5acf6c1d1aed44eaa670dd059c8c84ce"
openai_client = OpenAI(api_key=openai_api_key)


def fetch_table_data(table_name):
    conn = sqlite3.connect("essay_service.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()
    conn.close()
    return data


def update_table(table_name, set_clause, where_clause, params):
    conn = sqlite3.connect("essay_service.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}", params)
    conn.commit()
    conn.close()


def delete_from_table(table_name, where_clause, params):
    conn = sqlite3.connect("essay_service.db")
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE {where_clause}", params)
    conn.commit()
    conn.close()


def add_passage(title, passage):
    conn = sqlite3.connect("essay_service.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO passages (title, passage) VALUES (?, ?)", (title, passage))
    conn.commit()
    conn.close()


def add_question(passage_id, question, model_answer):
    conn = sqlite3.connect("essay_service.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO questions (passage_id, question, model_answer) VALUES (?, ?, ?)",
                   (passage_id, question, model_answer))
    conn.commit()
    conn.close()


def generate_questions_and_answers(passage):
    # Example: Call OpenAI API to generate questions and answers
    # Replace with actual implementation
    response = openai_client.Completion.create(
        model="text-davinci-003",
        prompt=f"Create 4 questions and model answers for the following passage:\n\n{passage}",
        max_tokens=500
    )
    return json.loads(response["choices"][0]["text"])


# Streamlit pages
st.title("AI 논술 첨삭 서비스")

menu = st.sidebar.radio("메뉴", ["지문 검색 및 문제 보기", "학생 답안 입력", "첨삭 보고서 생성", "데이터 추가", "관리자 도구", "DB 관리"])

# 지문 검색 및 문제 보기
if menu == "지문 검색 및 문제 보기":
    st.header("지문 검색 및 문제 보기")
    passages = fetch_table_data("passages")
    if passages:
        selected_passage = st.selectbox("지문 선택", passages, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        if selected_passage:
            st.subheader("선택한 지문")
            st.text_area("지문 내용", selected_passage[2], height=200, disabled=True)

            questions = fetch_table_data("questions")
            related_questions = [q for q in questions if q[1] == selected_passage[0]]

            st.subheader("관련 문제")
            for question in related_questions:
                st.text_area(f"문제 (ID: {question[0]})", question[2], height=100, disabled=True)
                st.text_area("모범 답안", question[3], height=100, disabled=True)
    else:
        st.warning("저장된 지문이 없습니다.")

# 학생 답안 입력
if menu == "학생 답안 입력":
    st.header("학생 답안 입력")
    passages = fetch_table_data("passages")
    if passages:
        selected_passage = st.selectbox("지문 선택", passages, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        if selected_passage:
            questions = fetch_table_data("questions")
            related_questions = [q for q in questions if q[1] == selected_passage[0]]

            answers = {}
            for question in related_questions:
                st.subheader(f"문제 (ID: {question[0]})")
                st.text_area("문제 내용", question[2], height=100, disabled=True)
                answers[question[0]] = st.text_area(f"학생 답안 (문제 {question[0]})", height=100)

            if st.button("답안 저장"):
                conn = sqlite3.connect("essay_service.db")
                cursor = conn.cursor()
                for question_id, answer in answers.items():
                    cursor.execute("INSERT INTO student_answers (question_id, student_answer) VALUES (?, ?)",
                                   (question_id, answer))
                conn.commit()
                conn.close()
                st.success("답안이 저장되었습니다.")
    else:
        st.warning("저장된 지문이 없습니다.")

# 첨삭 보고서 생성
if menu == "첨삭 보고서 생성":
    st.header("첨삭 보고서 생성")
    answers = fetch_table_data("student_answers")
    if answers:
        for answer in answers:
            st.subheader(f"문제 ID: {answer[1]}의 답안")
            st.text_area("학생 답안", answer[2], height=100, disabled=True)
            st.text("첨삭 중...")

            # Example feedback and score
            feedback = "Good effort, but needs more detail."
            score = 85

            st.text_area("피드백", feedback, height=100)
            st.text(f"점수: {score}/100")

            if st.button(f"저장 (답안 ID: {answer[0]})"):
                update_table("student_answers", "score = ?, feedback = ?", "id = ?",
                             [score, feedback, answer[0]])
                st.success("첨삭 결과가 저장되었습니다.")
    else:
        st.warning("학생 답안이 없습니다.")

# 데이터 추가
if menu == "데이터 추가":
    # 데이터 추가
    if menu == "데이터 추가":
        st.header("데이터 추가")

        # 새 지문 추가
        st.subheader("새 지문 추가")
        title = st.text_input("지문 제목")
        passage = st.text_area("지문 텍스트", height=200)

        st.subheader("문제 및 모범 답안 추가")

        # 문제와 모범 답안을 입력받는 텍스트 필드
        question1 = st.text_area("문제 1", height=100)
        model_answer1 = st.text_area("문제 1 모범 답안", height=100)

        question2 = st.text_area("문제 2", height=100)
        model_answer2 = st.text_area("문제 2 모범 답안", height=100)

        question3 = st.text_area("문제 3", height=100)
        model_answer3 = st.text_area("문제 3 모범 답안", height=100)

        question4 = st.text_area("문제 4", height=100)
        model_answer4 = st.text_area("문제 4 모범 답안", height=100)

        # 데이터 저장 버튼
        if st.button("지문 및 문제 저장"):
            if title and passage and all([question1, model_answer1, question2, model_answer2,
                                          question3, model_answer3, question4, model_answer4]):
                # 지문 저장
                conn = sqlite3.connect("essay_service.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO passages (title, passage) VALUES (?, ?)", (title, passage))
                passage_id = cursor.lastrowid  # 저장된 지문의 ID 가져오기

                # 문제와 모범 답안 저장
                cursor.execute("INSERT INTO questions (passage_id, question, model_answer) VALUES (?, ?, ?)",
                               (passage_id, question1, model_answer1))
                cursor.execute("INSERT INTO questions (passage_id, question, model_answer) VALUES (?, ?, ?)",
                               (passage_id, question2, model_answer2))
                cursor.execute("INSERT INTO questions (passage_id, question, model_answer) VALUES (?, ?, ?)",
                               (passage_id, question3, model_answer3))
                cursor.execute("INSERT INTO questions (passage_id, question, model_answer) VALUES (?, ?, ?)",
                               (passage_id, question4, model_answer4))

                conn.commit()
                conn.close()

                st.success("지문과 문제 및 모범 답안이 저장되었습니다.")
            else:
                st.error("모든 필드를 입력해주세요.")

# 관리자 도구
if menu == "관리자 도구":
    st.header("관리자 도구")
    passages = fetch_table_data("passages")
    if passages:
        selected_passage = st.selectbox("지문 선택", passages, format_func=lambda x: f"{x[1]} (ID: {x[0]})")
        if selected_passage:
            if st.button("질문 및 모범 답안 생성"):
                data = generate_questions_and_answers(selected_passage[2])
                for qa in data:
                    add_question(selected_passage[0], qa["question"], qa["model_answer"])
                st.success("질문과 모범 답안이 생성되었습니다.")
    else:
        st.warning("저장된 지문이 없습니다.")

# DB 관리
if menu == "DB 관리":
    st.header("DB 관리 페이지")

    db_menu = st.radio("관리할 데이터 선택", ["지문 관리", "문제 관리", "학생 답안 관리"])

    # Passage Management
    if db_menu == "지문 관리":
        st.subheader("지문 관리")
        passages = fetch_table_data("passages")

        # Display all passages
        st.write("현재 지문 데이터:")
        for passage in passages:
            st.text(f"ID: {passage[0]}, 제목: {passage[1]}, 지문: {passage[2]}")

        # Update Passage
        st.subheader("지문 수정")
        passage_id = st.number_input("수정할 지문의 ID", min_value=1, step=1)
        new_title = st.text_input("새 제목")
        new_passage = st.text_area("새 지문 내용", height=200)
        if st.button("지문 수정 저장"):
            if new_title and new_passage:
                update_table("passages", "title = ?, passage = ?", "id = ?", [new_title, new_passage, passage_id])
                st.success("지문이 수정되었습니다.")

        # Delete Passage
        st.subheader("지문 삭제")
        delete_id = st.number_input("삭제할 지문의 ID", min_value=1, step=1)
        if st.button("지문 삭제"):
            delete_from_table("passages", "id = ?", [delete_id])
            st.success("지문이 삭제되었습니다.")

    # Question Management
    elif db_menu == "문제 관리":
        st.subheader("문제 관리")
        questions = fetch_table_data("questions")

        # Display all questions
        st.write("현재 문제 데이터:")
        for question in questions:
            st.text(f"ID: {question[0]}, 지문 ID: {question[1]}, 문제: {question[2]}, 모범 답안: {question[3]}")

        # Update Question
        st.subheader("문제 수정")
        question_id = st.number_input("수정할 문제의 ID", min_value=1, step=1)
        new_question = st.text_area("새 문제 내용", height=100)
        new_model_answer = st.text_area("새 모범 답안", height=100)
        if st.button("문제 수정 저장"):
            if new_question and new_model_answer:
                update_table("questions", "question = ?, model_answer = ?", "id = ?",
                             [new_question, new_model_answer, question_id])
                st.success("문제가 수정되었습니다.")

        # Delete Question
        st.subheader("문제 삭제")
        delete_id = st.number_input("삭제할 문제의 ID", min_value=1, step=1)
        if st.button("문제 삭제"):
            delete_from_table("questions", "id = ?", [delete_id])
            st.success("문제가 삭제되었습니다.")

    # Student Answer Management
    elif db_menu == "학생 답안 관리":
        st.subheader("학생 답안 관리")
        answers = fetch_table_data("student_answers")

        # Display all answers
        st.write("현재 학생 답안 데이터:")
        for answer in answers:
            st.text(f"ID: {answer[0]}, 문제 ID: {answer[1]}, 답안: {answer[2]}, 점수: {answer[3]}, 피드백: {answer[4]}")

        # Update Student Answer
        st.subheader("학생 답안 수정")
        answer_id = st.number_input("수정할 답안의 ID", min_value=1, step=1)
        new_answer = st.text_area("새 학생 답안", height=100)
        new_score = st.number_input("새 점수", min_value=0, max_value=100, step=1)
        new_feedback = st.text_area("새 피드백", height=100)
        if st.button("답안 수정 저장"):
            if new_answer:
                update_table("student_answers", "student_answer = ?, score = ?, feedback = ?", "id = ?",
                             [new_answer, new_score, new_feedback, answer_id])
                st.success("학생 답안이 수정되었습니다.")

        # Delete Student Answer
        st.subheader("학생 답안 삭제")
        delete_id = st.number_input("삭제할 답안의 ID", min_value=1, step=1)
        if st.button("답안 삭제"):
            delete_from_table("student_answers", "id = ?", [delete_id])
            st.success("답안이 삭제되었습니다.")