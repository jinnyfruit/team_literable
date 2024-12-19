import streamlit as st
import requests
from database_manager import db
from typing import Optional, Dict, Any
import pandas as pd
from components import generate_pdf_report, format_feedback_report

# GPT-4 API 설정
FN_CALL_KEY = "5acf6c1d1aed44eaa670dd059c8c84ce"
FN_CALL_ENDPOINT = "https://apscus-prd-aabc2-openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"

headers_fn_call = {
    "Content-Type": "application/json",
    "api-key": FN_CALL_KEY
}


def call_llm(system_prompt: str, user_prompt: str) -> Optional[str]:
    """AI 모델 호출 함수"""
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


def load_prompt(filename: str) -> Optional[str]:
    """프롬프트 파일 로드 함수"""
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
    """AI 첨삭 분석 UI 컴포넌트"""
    st.subheader("AI 첨삭")

    # 학생 검색 및 선택
    st.write("### 학생 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색", key="feedback_student_search")

    students = db.fetch_students(search_student)
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

    passages = db.fetch_passages(search_passage)
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
        # 모든 문제와 답안 가져오기
        questions = db.fetch_questions(selected_passage[0])
        student_answers = db.fetch_student_answers(selected_student[0], selected_passage[0])
        student_answers_dict = {ans[2]: ans for ans in student_answers}  # question_id를 키로 사용

        if not any(q[0] in student_answers_dict for q in questions):
            st.warning("저장된 답안이 없습니다. 답안 관리 탭에서 먼저 답안을 입력해주세요.")
            return

        # 답안 표시 및 분석 준비
        answers_to_analyze = {}
        questions_order = []

        for i, question in enumerate(questions, 1):
            if question[0] in student_answers_dict:  # 답안이 있는 경우만 처리
                answer = student_answers_dict[question[0]]
                with st.expander(f"{question[2]}", expanded=True):
                    st.write("**모범답안:**")
                    st.info(question[3])

                    st.write("**학생답안:**")
                    st.info(answer[3])

                    if answer[4] is not None:
                        st.write("**현재 점수:**", f"{answer[4]}점")
                        st.write("**피드백:**", answer[5] if answer[5] else "")

                answers_to_analyze[i] = {
                    'question_id': question[0],
                    'question_text': question[2],
                    'model_answer': question[3],
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
                                    'score': score,
                                    'feedback': feedback
                                })
                            except Exception as e:
                                st.error(f"분석 중 오류가 발생했습니다: {str(e)}")

                    progress_text.empty()
                    progress_bar.empty()

                    if analysis_results:
                        # 결과 저장
                        try:
                            for result in analysis_results:
                                db.save_student_answer(
                                    student_id=selected_student[0],
                                    question_id=result['question_id'],
                                    answer=student_answers_dict[result['question_id']][3],
                                    score=result['score'],
                                    feedback=result['feedback']
                                )
                            st.success("첨삭 보고서가 저장되었습니다. 분석 결과 탭에서 확인할 수 있습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"결과 저장 중 오류가 발생했습니다: {str(e)}")


def show_detailed_analysis():
    """분석 결과 표시 UI 컴포넌트"""
    st.subheader("분석 결과")

    # 학생 검색 및 선택
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색", key="analysis_student_search")

    # 답안이 있는 학생만 조회
    students = [student for student in db.fetch_students(search_student)
                if db.fetch_student_answers(student[0], None)]  # None은 모든 지문에 대한 답안 조회

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
        # 학생이 답안을 제출한 지문만 조회
        passages_with_answers = []
        for passage in db.fetch_passages():
            if db.fetch_student_answers(selected_student[0], passage[0]):
                passages_with_answers.append(passage)

        if passages_with_answers:
            selected_passage = st.selectbox(
                "지문 선택",
                passages_with_answers,
                format_func=lambda x: x[1]
            )

            if selected_passage:
                # 분석 결과 조회
                answers = db.fetch_student_answers(selected_student[0], selected_passage[0])

                if answers:
                    # PDF 다운로드 버튼
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        pdf_data = generate_pdf_report(selected_student, selected_passage, answers)
                        st.download_button(
                            label="📑 PDF 저장",
                            data=pdf_data,
                            file_name=f"{selected_student[1]}_{selected_passage[1]}_첨삭보고서.pdf",
                            mime="application/pdf"
                        )

                    # HTML 형식의 보고서 표시
                    report_html = format_feedback_report(selected_student, selected_passage, answers)
                    st.markdown(report_html, unsafe_allow_html=True)

        else:
            st.info("분석된 답안이 없습니다.")