import streamlit as st
from utils.db import db
from utils.html import create_feedback_report
from utils.llm import call_llm
from utils.pdf import generate_pdf_report


def analyze_feedback():
    st.subheader("AI 첨삭")

    # 학생 검색 및 선택
    st.write("### 학생 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색", key="feedback_student_search")

    # 학생 검색 쿼리
    students = db.fetch_students(search_student) if search_student else db.fetch_students()

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

    # 지문 검색 쿼리
    passages = db.fetch_passages(search_passage) if search_passage else db.fetch_passages()

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
        answers = db.execute_query("""
            SELECT q.id, q.question, q.model_answer, sa.student_answer, sa.score, sa.feedback
            FROM questions q
            LEFT JOIN student_answers sa ON q.id = sa.question_id 
                AND sa.student_id = ?
            WHERE q.passage_id = ?
            ORDER BY q.id
        """, (selected_student[0], selected_passage[0]))

        if not any(answer[3] for answer in answers):
            st.warning("저장된 답안이 없습니다. 답안 관리 탭에서 먼저 답안을 입력해주세요.")
            return

        # 답안 표시 및 분석
        st.write("### 저장된 답안")
        answers_to_analyze = {}

        for answer in answers:
            if answer[3]:  # 답안이 있는 경우만 표시
                with st.expander(answer[1], expanded=True):
                    st.write("**모범답안:**")
                    st.info(answer[2])

                    st.write("**학생답안:**")
                    st.info(answer[3])

                    if answer[4] is not None:
                        st.write("**현재 점수:**", f"{answer[4]}점")
                        if answer[5]:
                            st.write("**피드백:**", answer[5])

                    answers_to_analyze[answer[0]] = {
                        'question_text': answer[1],
                        'model_answer': answer[2],
                        'student_answer': answer[3]
                    }

        if answers_to_analyze:
            if st.button("📝 AI 첨삭 분석 시작", type="primary", key="start_analysis"):
                with st.spinner("AI가 답안을 분석중입니다..."):
                    analysis_results = []
                    progress_bar = st.progress(0)
                    progress_text = st.empty()

                    for i, (question_id, data) in enumerate(answers_to_analyze.items()):
                        progress_text.text(f"분석 진행중... ({i + 1}/{len(answers_to_analyze)})")
                        progress_bar.progress((i + 1) / len(answers_to_analyze))

                        result = call_llm(
                            question=data['question_text'],
                            model_answer=data['model_answer'],
                            student_answer=data['student_answer']
                        )

                        if result:
                            try:
                                analysis_results.append({
                                    'question_id': question_id,
                                    'score': result['score'],
                                    'feedback': result['feedback']
                                })
                            except Exception as e:
                                st.error(f"분석 결과 처리 중 오류가 발생했습니다: {str(e)}")

                    progress_text.empty()
                    progress_bar.empty()

                    if analysis_results:
                        try:
                            # 분석 결과 저장
                            for result in analysis_results:
                                db.execute_query("""
                                    UPDATE student_answers 
                                    SET score = ?, feedback = ?
                                    WHERE student_id = ? AND question_id = ?
                                """, (result['score'], result['feedback'],
                                      selected_student[0], result['question_id']))

                            st.success("첨삭 보고서가 저장되었습니다. 분석 결과 탭에서 확인할 수 있습니다.")
                            st.rerun()

                        except Exception as e:
                            st.error(f"결과 저장 중 오류가 발생했습니다: {str(e)}")


def show_detailed_analysis():
    st.subheader("분석 결과")

    # 학생 검색 및 선택
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색", key="analysis_student_search")

    # 분석 결과가 있는 학생만 조회
    students = db.execute_query("""
        SELECT DISTINCT s.* FROM students s
        JOIN student_answers sa ON s.id = sa.student_id
        WHERE (s.name LIKE ? OR s.student_number LIKE ?) AND sa.score IS NOT NULL
    """, (f"%{search_student}%", f"%{search_student}%")) if search_student else db.execute_query("""
        SELECT DISTINCT s.* FROM students s
        JOIN student_answers sa ON s.id = sa.student_id
        WHERE sa.score IS NOT NULL
    """)

    if not students:
        st.info("분석된 답안이 있는 학생이 없습니다.")
        return

    with col2:
        selected_student = st.selectbox(
            "학생 선택",
            students,
            format_func=lambda x: f"{x[1]} ({x[2]} - {x[3]})",
            key="analysis_student_select"
        )

    if selected_student:
        # 학생의 분석된 답안이 있는 지문 목록 조회
        passages = db.execute_query("""
            SELECT DISTINCT p.* FROM passages p
            JOIN questions q ON p.id = q.passage_id
            JOIN student_answers sa ON q.id = sa.question_id
            WHERE sa.student_id = ? AND sa.score IS NOT NULL
            ORDER BY p.id DESC
        """, (selected_student[0],))

        if passages:
            selected_passage = st.selectbox(
                "지문 선택",
                passages,
                format_func=lambda x: x[1],
                key="analysis_passage_select"
            )

            if selected_passage:
                # 분석 결과 조회
                results = db.execute_query("""
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

                if results:
                    # PDF 다운로드 버튼
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        pdf_data = generate_pdf_report(selected_student, selected_passage, results)
                        st.download_button(
                            label="📑 PDF 저장",
                            data=pdf_data,
                            file_name=f"{selected_student[1]}_{selected_passage[1]}_첨삭보고서.pdf",
                            mime="application/pdf",
                            key="pdf_download"
                        )

                    # HTML 보고서 표시
                    report_html = create_feedback_report(selected_student, selected_passage, results)
                    st.components.v1.html(report_html, height=800, scrolling=True)
                else:
                    st.info("분석 결과가 없습니다.")
        else:
            st.info("분석된 답안이 없습니다.")


if __name__ == "__main__":
    st.set_page_config(page_title="AI 첨삭 분석", layout="wide")
    tabs = st.tabs(["🤖 AI 첨삭", "📊 분석 결과"])

    with tabs[0]:
        analyze_feedback()
    with tabs[1]:
        show_detailed_analysis()