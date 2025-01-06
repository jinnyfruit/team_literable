import streamlit as st
import requests
from database_manager import db
from typing import Optional, Dict, Any
import pandas as pd
from components import generate_pdf_report, format_feedback_report


# GPT-4 API 설정
# GPT-4o API 설정
FN_CALL_KEY = "5acf6c1d1aed44eaa670dd059c8c84ce"
FN_CALL_ENDPOINT = "https://apscus-prd-aabc2-openai.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"

headers_fn_call = {
    "Content-Type": "application/json",
    "api-key": FN_CALL_KEY
}

# 파일 상단에 추가
CATEGORY_PROMPT_MAP = {
    '사실적 독해': 'factual',
    '추론적 독해': 'inferential',
    '비판적 독해': 'critical',
    '창의적 독해': 'creative',
    '': 'default'
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


def load_prompt(category: str) -> Optional[str]:
    """카테고리별 프롬프트 파일 로드 함수"""
    try:
        prompt_type = CATEGORY_PROMPT_MAP.get(category, 'default')
        prompt_filename = f"prompts/{prompt_type}.txt"

        with open(prompt_filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        st.error(f"프롬프트 파일을 찾을 수 없습니다: {prompt_filename}")
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
                    'student_answer': answer[3],
                    'category': question[4]  # 카테고리 추가
                }
                questions_order.append(i)

        if answers_to_analyze:
            if 'analysis_started' not in st.session_state:
                st.session_state.analysis_started = False

            # 분석 시작 버튼
            if st.button("📝 AI 첨삭 분석 시작", type="primary") or st.session_state.analysis_started:
                if not st.session_state.analysis_started:
                    st.session_state.analysis_started = True

                    with st.spinner("AI가 답안을 분석중입니다..."):
                        analysis_results = []
                        progress_bar = st.progress(0)

                        for i, q_num in enumerate(questions_order):
                            try:
                                data = answers_to_analyze[q_num]
                                progress_text = st.empty()
                                progress_text.text(f"분석 진행중... ({i + 1}/{len(questions_order)})")
                                progress_bar.progress((i + 1) / len(questions_order))

                                # 카테고리별 프롬프트 로드
                                category = data.get('category', '')  # 카테고리가 없을 경우 빈 문자열
                                system_prompt = load_prompt(category)

                                if system_prompt is None:
                                    st.warning(f"카테고리 '{category}'에 대한 프롬프트를 찾을 수 없어 기본 프롬프트를 사용합니다.")
                                    system_prompt = load_prompt('')  # 빈 문자열을 전달하여 default.txt 사용
                                    if system_prompt is None:
                                        continue

                                user_prompt = f"""
                                문제: {data['question_text']}
                                모범답안: {data['model_answer']}
                                학생답안: {data['student_answer']}
                                """

                                try:
                                    result = call_llm(system_prompt, user_prompt)
                                    if result:
                                        score_text = result.split('점수:')[1].split('\n')[0]
                                        score = int(score_text.replace('점', '').strip())
                                        feedback = result.split('첨삭:')[1].strip()

                                        analysis_results.append({
                                            'question_id': data['question_id'],
                                            'score': score,
                                            'feedback': feedback
                                        })
                                except Exception as e:
                                    st.error(f"결과 파싱 중 오류가 발생했습니다: {str(e)}")
                                    continue

                            except Exception as e:
                                st.error(f"문제 분석 중 오류가 발생했습니다: {str(e)}")
                                continue

                        progress_text.empty()
                        progress_bar.empty()

                        if analysis_results:
                            st.session_state['analysis_results'] = analysis_results
                            st.session_state['selected_student'] = selected_student
                            st.success("분석이 완료되었습니다!")

                # 분석 결과 표시
                if 'analysis_results' in st.session_state:
                    st.write("### 분석 결과")
                    for result in st.session_state.analysis_results:
                        question_id = result['question_id']
                        question = next(q for q in questions if q[0] == question_id)

                        with st.expander(f"{question[2]}", expanded=True):
                            st.write(f"**점수:** {result['score']}점")
                            st.write("**피드백:**")
                            st.warning(result['feedback'])

                    # 저장하기 섹션
                    if 'saving_in_progress' not in st.session_state:
                        st.session_state.saving_in_progress = False

                    if st.button("✅ 결과 저장하기", key="save_results", use_container_width=True):
                        st.session_state.saving_in_progress = True

                    if st.session_state.saving_in_progress:
                        progress_placeholder = st.empty()
                        status_placeholder = st.empty()
                        save_success = True

                        try:
                            for idx, result in enumerate(st.session_state.analysis_results):
                                progress_placeholder.progress((idx + 1) / len(st.session_state.analysis_results))
                                status_placeholder.text(f"저장 중... ({idx + 1}/{len(st.session_state.analysis_results)})")

                                current_question = next(
                                    (ans['student_answer'] for ans in answers_to_analyze.values()
                                     if ans['question_id'] == result['question_id']),
                                    None
                                )

                                if current_question is None:
                                    save_success = False
                                    st.error(f"답안을 찾을 수 없음 - 질문 ID: {result['question_id']}")
                                    break

                                success = db.save_student_answer(
                                    student_id=st.session_state.selected_student[0],
                                    question_id=result['question_id'],
                                    answer=current_question,
                                    score=result['score'],
                                    feedback=result['feedback']
                                )

                                if not success:
                                    save_success = False
                                    st.error(f"답안 저장 실패 - 질문 ID: {result['question_id']}")
                                    break

                            # 저장 완료 후 UI 정리
                            progress_placeholder.empty()
                            status_placeholder.empty()

                            if save_success:
                                st.success("✅ 모든 답안이 성공적으로 저장되었습니다!")
                                st.session_state.saving_in_progress = False
                                st.session_state.analysis_started = False
                            else:
                                st.error("일부 답안 저장에 실패했습니다. 다시 시도해주세요.")
                                st.session_state.saving_in_progress = False

                        except Exception as e:
                            progress_placeholder.empty()
                            status_placeholder.empty()
                            st.error(f"저장 중 오류 발생: {str(e)}")
                            st.session_state.saving_in_progress = False

def show_detailed_analysis():
    """분석 결과 표시 UI 컴포넌트"""
    st.subheader("분석 결과")

    # 학생 검색 및 선택
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색", key="analysis_student_search")

    # 답안이 있는 학생만 조회
    students = [student for student in db.fetch_students(search_student)
                if db.fetch_student_answers(student[0], None)]

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
                questions = db.fetch_questions(selected_passage[0])  # 문제 정보 가져오기
                answers = db.fetch_student_answers(selected_student[0], selected_passage[0])

                if answers:
                    formatted_results = []
                    for ans in answers:
                        formatted_results.append((
                            ans[7],  # 문제 (questions.question)
                            ans[8],  # 모범답안 (questions.model_answer)
                            ans[3],  # 학생답안
                            ans[4],  # 점수
                            ans[5]  # 피드백
                        ))

                    if formatted_results:
                        for idx, result in enumerate(formatted_results, 1):
                            question, model_answer, student_answer, score, feedback = result
                            with st.expander(f"문제 {idx}", expanded=True):
                                col1, col2 = st.columns([1, 4])
                                with col1:
                                    st.metric("점수", f"{score}점")
                                with col2:
                                    st.write("**문제:**")
                                    st.info(question)

                                    st.write("**모범답안:**")
                                    st.info(model_answer)

                                    st.write("**학생답안:**")
                                    st.info(student_answer)

                                    if feedback:
                                        st.write("**첨삭 내용:**")
                                        st.warning(feedback)

                        total_score = sum(r[3] for r in formatted_results if r[3] is not None)
                        avg_score = total_score / len(formatted_results)
                        st.metric(label="총점", value=f"{total_score}점", delta=f"평균: {avg_score:.1f}점")

                        pdf_data = generate_pdf_report(selected_student, selected_passage, formatted_results)
                        if pdf_data:
                            st.download_button(
                                label="📑 PDF 저장",
                                data=pdf_data,
                                file_name=f"{selected_student[1]}_{selected_passage[1]}_첨삭보고서.pdf",
                                mime="application/pdf"
                            )


                else:
                    st.info("분석된 답안이 없습니다.")
        else:
            st.info("답안이 있는 지문이 없습니다.")
