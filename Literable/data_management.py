import streamlit as st
from database_manager import db
from typing import List, Tuple, Dict, Any


def manage_students():
    """학생 관리 UI 컴포넌트"""
    st.subheader("학생 관리")

    # 학생 추가
    with st.form("add_student"):
        name = st.text_input("학생 이름")
        school = st.text_input("학교")
        student_number = st.text_input("학번")
        submitted = st.form_submit_button("학생 추가")
        if submitted:
            if name and school and student_number:
                db.add_student(name, school, student_number)
                st.success("학생이 성공적으로 추가되었습니다!")
            else:
                st.error("모든 필드를 입력해주세요.")

    # 학생 검색
    st.write("### 학생 검색")
    search_query = st.text_input("학생 이름 검색")
    students = db.fetch_students(search_query)

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
                            db.update_student(student[0], updated_name, updated_school, updated_student_number)
                            st.success("학생 정보가 수정되었습니다!")
                            st.rerun()
                        else:
                            st.error("모든 필드를 입력해주세요.")

                    if delete_submitted:
                        db.delete_student(student[0])
                        st.warning("학생이 삭제되었습니다.")
                        st.rerun()
    else:
        st.info("검색된 학생이 없습니다.")


def manage_passages_and_questions():
    """지문 및 문제 관리 UI 컴포넌트"""
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
    if 'needs_rerun' not in st.session_state:
        st.session_state['needs_rerun'] = False
    if 'show_warning' not in st.session_state:
        st.session_state['show_warning'] = False

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
            st.session_state['needs_rerun'] = True
        else:
            warnings = st.empty()
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
                passage_id = db.add_passage(title, passage)
                valid_questions = [
                    (q, a) for q, a in zip(st.session_state['questions'], st.session_state['model_answers'])
                    if q.strip() and a.strip()
                ]
                for question, model_answer in valid_questions:
                    db.add_question(passage_id, question, model_answer)
                st.success("✅ 지문과 질문이 성공적으로 추가되었습니다!")
                st.session_state['questions'] = ["" for _ in range(st.session_state['question_count'])]
                st.session_state['model_answers'] = ["" for _ in range(st.session_state['question_count'])]
                st.rerun()
            else:
                st.error("제목과 내용을 모두 입력해주세요.")

    # 지문 목록 섹션
    st.header("📋 등록된 지문 목록")
    search_query = st.text_input("🔍 지문 검색", placeholder="제목 또는 내용으로 검색")

    passages = db.fetch_passages(search_query)
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
                            db.update_passage(passage[0], updated_title, updated_passage)
                            st.success("✅ 지문이 수정되었습니다!")
                            st.session_state['edit_mode'][passage[0]] = False
                            st.rerun()
                with col2:
                    if st.button("❌ 취소", key=f"cancel_edit_mode_{passage[0]}"):
                        st.session_state['edit_mode'][passage[0]] = False
                        st.rerun()

            # 질문 관리 섹션
            questions = db.fetch_questions(passage[0])
            if questions:
                st.subheader("📋 등록된 문제")
                for question in questions:
                    question_edit_key = f"question_edit_state_{question[0]}"
                    if question_edit_key not in st.session_state:
                        st.session_state[question_edit_key] = False

                    st.divider()
                    if st.session_state[question_edit_key]:
                        # 질문 수정 모드
                        updated_question = st.text_input(
                            "질문",
                            value=question[2],
                            key=f"edit_question_input_{question[0]}"
                        )
                        updated_answer = st.text_area(
                            "모범답안",
                            value=question[3],
                            key=f"edit_answer_input_{question[0]}"
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 저장", key=f"save_question_{question[0]}"):
                                db.update_question(question[0], updated_question, updated_answer)
                                st.success("✅ 문제가 수정되었습니다!")
                                st.session_state[question_edit_key] = False
                                st.rerun()
                        with col2:
                            if st.button("❌ 취소", key=f"cancel_question_{question[0]}"):
                                st.session_state[question_edit_key] = False
                                st.rerun()
                    else:
                        # 질문 표시 모드
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"**질문:** {question[2]}")
                            st.markdown(f"**모범답안:** {question[3]}")
                        with col2:
                            if st.button("✏️", key=f"edit_question_button_{question[0]}"):
                                st.session_state[question_edit_key] = True
                                st.rerun()
                        with col3:
                            if st.button("🗑️", key=f"delete_question_{question[0]}"):
                                db.delete_question(question[0])
                                st.success("✅ 문제가 삭제되었습니다!")
                                st.rerun()

            # 새 질문 추가 섹션
            st.divider()
            st.subheader("➕ 새 질문 추가")
            col_q, col_a = st.columns(2)
            with col_q:
                new_question = st.text_input("새 질문", key=f"new_question_{passage[0]}")
            with col_a:
                new_answer = st.text_area("새 모범답안", key=f"new_answer_{passage[0]}")

            if st.button("💾 질문 추가", key=f"add_question_{passage[0]}"):
                if new_question.strip() and new_answer.strip():
                    db.add_question(passage[0], new_question, new_answer)
                    st.success("✅ 새로운 문제가 추가되었습니다!")
                    st.rerun()
                else:
                    st.error("질문과 모범답안을 모두 입력해주세요.")

            # 삭제 확인 UI
            if st.session_state[delete_key]:
                st.warning("🚨 정말로 이 지문을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 예, 삭제합니다", key=f"confirm_delete_{passage[0]}"):
                        db.delete_passage(passage[0])
                        st.success("✅ 지문이 성공적으로 삭제되었습니다!")
                        st.session_state[delete_key] = False
                        st.rerun()
                with col2:
                    if st.button("❌ 취소", key=f"cancel_delete_{passage[0]}"):
                        st.session_state[delete_key] = False
                        st.rerun()

            # 지문 수정/삭제 버튼
            st.divider()
            col1, col2, col3 = st.columns([2, 2, 8])
            with col1:
                if st.button("✏️ 지문 수정", key=f"edit_mode_toggle_{passage[0]}"):
                    st.session_state['edit_mode'][passage[0]] = True
                    st.rerun()
            with col2:
                if st.button("🗑️ 지문 삭제", key=f"delete_init_button_{passage[0]}"):
                    st.session_state[delete_key] = True
                    st.rerun()

    if st.session_state.get('show_warning', False):
        st.session_state['show_warning'] = False

def manage_report():
    """답안 관리 UI 컴포넌트"""
    st.subheader("답안 관리")

    # 학생 검색 및 선택
    st.write("### 학생 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_student = st.text_input("학생 이름/학번 검색")

    students = db.fetch_students(search_student)
    if not students:
        st.warning("검색된 학생이 없습니다.")
        return

    with col2:
        selected_student = st.selectbox(
            "학생 선택",
            students,
            format_func=lambda x: f"{x[1]} ({x[2]} - {x[3]})",
            key="student_select"
        )

    # 지문 검색 및 선택
    st.write("### 지문 선택")
    col1, col2 = st.columns([2, 2])
    with col1:
        search_passage = st.text_input("지문 제목 검색")

    passages = db.fetch_passages(search_passage)
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
    questions = db.fetch_questions(selected_passage[0])
    if not questions:
        st.warning("선택된 지문에 등록된 문제가 없습니다.")
        return

    # 선택된 학생의 답안들 가져오기
    existing_answers = db.fetch_student_answers(selected_student[0], selected_passage[0])
    existing_answers_dict = {answer[2]: answer for answer in existing_answers}  # question_id를 키로 사용

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
            existing_answer = existing_answers_dict.get(question[0])

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
                    db.save_student_answer(
                        selected_student[0],
                        question[0],
                        student_answer,
                        score,
                        feedback
                    )
                    st.success("답안이 성공적으로 저장되었습니다!")
                    st.rerun()
                elif submit and not student_answer:
                    st.error("답안을 입력해주세요.")

                if existing_answer and delete:
                    db.delete_student_answer(existing_answer[0])
                    st.warning("답안이 삭제되었습니다.")
                    st.rerun()