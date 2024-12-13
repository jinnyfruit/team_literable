import sqlite3
import streamlit as st

def connect_db():
    conn = sqlite3.connect("passages.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
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
                        FOREIGN KEY (passage_id) REFERENCES passages (id) ON DELETE CASCADE
                    )''')
    conn.commit()
    return conn

def fetch_passages(search_query=""):
    conn = connect_db()
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
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE passage_id = ?", (passage_id,))
        questions = cursor.fetchall()
        return questions
    finally:
        conn.close()

def add_passage(title, passage):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO passages (title, passage) VALUES (?, ?)", (title, passage))
        passage_id = cursor.lastrowid
        conn.commit()
        return passage_id
    finally:
        conn.close()

def add_question(passage_id, question, model_answer):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO questions (passage_id, question, model_answer) VALUES (?, ?, ?)", (passage_id, question, model_answer))
        conn.commit()
    finally:
        conn.close()

def delete_passage(passage_id):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions WHERE passage_id = ?", (passage_id,))
        cursor.execute("DELETE FROM passages WHERE id = ?", (passage_id,))
        conn.commit()
    finally:
        conn.close()

def delete_question(question_id):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
    finally:
        conn.close()

def manage_QA():
    import streamlit as st

    st.subheader("지문 및 문제 관리")

    # 세션 상태 초기화
    if 'question_count' not in st.session_state:
        st.session_state['question_count'] = 4
    if 'questions' not in st.session_state:
        st.session_state['questions'] = ["" for _ in range(st.session_state['question_count'])]
    if 'model_answers' not in st.session_state:
        st.session_state['model_answers'] = ["" for _ in range(st.session_state['question_count'])]

    # 버튼 동작
    def add_question():
        st.session_state['question_count'] += 1
        st.session_state['questions'].append("")
        st.session_state['model_answers'].append("")

    def delete_question():
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
            st.text_input(f"질문 {i+1}", value=st.session_state['questions'][i], key=f"question_{i}")
            st.text_area(f"모범답안 {i+1}", value=st.session_state['model_answers'][i], key=f"model_answer_{i}")

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



# 메인 프로그램
if __name__ == "__main__":
    menu = st.sidebar.radio("메뉴", ["지문 및 문제 관리", "답안 작성"])

    if menu == "지문 및 문제 관리":
        manage_QA()
