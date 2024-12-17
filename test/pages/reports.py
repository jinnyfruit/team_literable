import streamlit as st
from utils.db import db

def manage_report():
    st.subheader("답안 관리")

    # 학생 검색 및 선택
    st.write("### 학생 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색", key="report_student_search")

    # 학생 검색 쿼리
    students = db.fetch_students(search_student) if search_student else db.fetch_students()

    if not students:
        st.warning("검색된 학생이 없습니다.")
        return

    with col2:
        selected_student = st.selectbox(
            "학생 선택",
            students,
            format_func=lambda x: f"{x[1]} ({x[2]} - {x[3]})",  # 이름 (학교 - 학번)
            key="report_student_select"
        )

    # 지문 검색 및 선택
    st.write("### 지문 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_passage = st.text_input("지문 제목 검색", key="report_passage_search")

    # 지문 검색 쿼리
    passages = db.fetch_passages(search_passage) if search_passage else db.fetch_passages()

    if not passages:
        st.warning("검색된 지문이 없습니다.")
        return

    with col2:
        selected_passage = st.selectbox(
            "지문 선택",
            passages,
            format_func=lambda x: x[1],  # 지문 제목만 표시
            key="report_passage_select"
        )

    if selected_student and selected_passage:
        # 지문 내용 표시
        with st.expander("지문 내용 보기", expanded=False):
            st.write(selected_passage[2])

        # 선택된 지문의 문제들 가져오기
        questions = db.fetch_questions(selected_passage[0])
        if not questions:
            st.warning("선택된 지문에 등록된 문제가 없습니다.")
            return

        # 선택된 학생의 답안들 가져오기
        existing_answers = {}
        try:
            results = db.execute_query("""
                SELECT sa.*, q.question, q.model_answer 
                FROM student_answers sa 
                JOIN questions q ON sa.question_id = q.id 
                WHERE sa.student_id = ? AND q.passage_id = ?
            """, (selected_student[0], selected_passage[0]))
            existing_answers = {answer[2]: answer for answer in results}  # question_id를 키로 사용
        except Exception as e:
            st.error(f"답안을 불러오는 중 오류가 발생했습니다: {str(e)}")
            return

        # 답안 관리 섹션
        st.write("### 답안 입력 및 수정")

        # 전체 답안 상태 표시
        total_questions = len(questions)
        answered_questions = len(existing_answers)
        st.write(f"답안 작성 현황: {answered_questions}/{total_questions} 문제 완료")
        progress = answered_questions / total_questions if total_questions > 0 else 0
        st.progress(progress)

        # 각 문제별 답안 입력/수정
        for question in questions:
            with st.expander(question[2], expanded=True):
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
                        height=150,
                        key=f"answer_input_{question[0]}"
                    )

                    col1, col2 = st.columns([2, 2])
                    with col1:
                        score = st.number_input(
                            "점수",
                            min_value=0,
                            max_value=100,
                            value=existing_answer[4] if existing_answer else 0,
                            key=f"score_input_{question[0]}"
                        )
                    with col2:
                        feedback = st.text_area(
                            "피드백",
                            value=existing_answer[5] if existing_answer else "",
                            height=100,
                            key=f"feedback_input_{question[0]}"
                        )

                    col1, col2 = st.columns([1, 1])
                    with col1:
                        submit = st.form_submit_button(
                            "저장",
                            use_container_width=True,
                            type="primary"
                        )
                    with col2:
                        if existing_answer:
                            delete = st.form_submit_button(
                                "삭제",
                                type="secondary",
                                use_container_width=True
                            )

                    if submit and student_answer:
                        try:
                            if existing_answer:
                                # 기존 답안 수정
                                db.execute_query("""
                                    UPDATE student_answers 
                                    SET student_answer = ?, score = ?, feedback = ? 
                                    WHERE id = ?
                                """, (student_answer, score, feedback, existing_answer[0]))
                            else:
                                # 새로운 답안 추가
                                db.execute_query("""
                                    INSERT INTO student_answers 
                                    (student_id, question_id, student_answer, score, feedback) 
                                    VALUES (?, ?, ?, ?, ?)
                                """, (selected_student[0], question[0], student_answer, score, feedback))
                            st.success("답안이 저장되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"저장 중 오류가 발생했습니다: {str(e)}")

                    elif submit and not student_answer:
                        st.error("답안을 입력해주세요.")

                    if existing_answer and delete:
                        try:
                            db.execute_query(
                                "DELETE FROM student_answers WHERE id = ?",
                                (existing_answer[0],)
                            )
                            st.warning("답안이 삭제되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    st.set_page_config(page_title="답안 관리", layout="wide")
    manage_report()