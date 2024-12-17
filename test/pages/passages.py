import streamlit as st
from utils.db import db


def init_session_state():
    """세션 상태 초기화"""
    if 'question_count' not in st.session_state:
        st.session_state['question_count'] = 4
    if 'questions' not in st.session_state:
        st.session_state['questions'] = ["" for _ in range(st.session_state['question_count'])]
    if 'model_answers' not in st.session_state:
        st.session_state['model_answers'] = ["" for _ in range(st.session_state['question_count'])]
    if 'edit_mode' not in st.session_state:
        st.session_state['edit_mode'] = {}


def add_question_session():
    """문제 입력창 추가"""
    if st.session_state['question_count'] < 10:
        st.session_state['question_count'] += 1
        st.session_state['questions'].append("")
        st.session_state['model_answers'].append("")
    else:
        st.warning("최대 10개의 질문까지만 추가할 수 있습니다.")


def delete_question_session():
    """문제 입력창 삭제"""
    if st.session_state['question_count'] > 1:
        st.session_state['question_count'] -= 1
        st.session_state['questions'].pop()
        st.session_state['model_answers'].pop()
    else:
        st.warning("질문 입력창이 최소 하나는 있어야 합니다!")


def manage_passages_and_questions():
    st.subheader("📚 지문 및 문제 관리")
    init_session_state()

    # 새 지문 추가 섹션
    with st.expander("📝 새로운 지문 및 문제 추가", expanded=True):
        title = st.text_input("지문 제목", max_chars=100, key="new_passage_title")
        passage = st.text_area("지문 내용", height=200, key="new_passage_content")

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
            st.button("➕ 질문 추가", on_click=add_question_session, key="add_question_btn")
        with col2:
            st.button("➖ 질문 삭제", on_click=delete_question_session, key="delete_question_btn")

        if st.button("💾 지문 및 문제 저장", key="save_passage_btn"):
            if title and passage:
                try:
                    # 지문 저장
                    passage_id = db.add_passage(title, passage)

                    # 유효한 질문만 필터링
                    valid_questions = [
                        (q, a) for q, a in zip(st.session_state['questions'],
                                               st.session_state['model_answers'])
                        if q.strip() and a.strip()
                    ]

                    # 문제 저장
                    for question, model_answer in valid_questions:
                        db.add_question(passage_id, question, model_answer)

                    st.success("✅ 지문과 질문이 성공적으로 추가되었습니다!")
                    # 입력 필드 초기화
                    st.session_state['questions'] = ["" for _ in range(st.session_state['question_count'])]
                    st.session_state['model_answers'] = ["" for _ in range(st.session_state['question_count'])]
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {str(e)}")
            else:
                st.error("제목과 내용을 모두 입력해주세요.")

    # 지문 목록 섹션
    st.header("📋 등록된 지문 목록")
    search_query = st.text_input("🔍 지문 검색", placeholder="제목으로 검색", key="passage_search")

    passages = db.fetch_passages(search_query)
    if not passages:
        st.info("📭 등록된 지문이 없습니다.")
        return

    for passage in passages:
        with st.expander(f"🗂️ {passage[1]}", expanded=False):
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
                    key=f"edit_title_{passage[0]}",
                    max_chars=100
                )
                updated_passage = st.text_area(
                    "지문 내용",
                    value=passage[2],
                    key=f"edit_passage_{passage[0]}",
                    height=300
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 수정 저장", key=f"save_edit_{passage[0]}"):
                        if updated_title and updated_passage:
                            try:
                                db.execute_query(
                                    "UPDATE passages SET title = ?, passage = ? WHERE id = ?",
                                    (updated_title, updated_passage, passage[0])
                                )
                                st.success("✅ 지문이 수정되었습니다!")
                                st.session_state['edit_mode'][passage[0]] = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"수정 중 오류가 발생했습니다: {str(e)}")
                with col2:
                    if st.button("❌ 취소", key=f"cancel_edit_{passage[0]}"):
                        st.session_state['edit_mode'][passage[0]] = False
                        st.rerun()

            # 문제 관리 섹션
            questions = db.fetch_questions(passage[0])
            if questions:
                st.subheader("📋 등록된 문제")
                for question in questions:
                    question_edit_key = f"question_edit_{question[0]}"
                    if question_edit_key not in st.session_state:
                        st.session_state[question_edit_key] = False

                    st.divider()
                    if st.session_state[question_edit_key]:
                        # 질문 수정 모드
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
                                try:
                                    db.execute_query(
                                        "UPDATE questions SET question = ?, model_answer = ? WHERE id = ?",
                                        (updated_question, updated_answer, question[0])
                                    )
                                    st.success("✅ 문제가 수정되었습니다!")
                                    st.session_state[question_edit_key] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"수정 중 오류가 발생했습니다: {str(e)}")
                        with col2:
                            if st.button("❌ 취소", key=f"cancel_q_{question[0]}"):
                                st.session_state[question_edit_key] = False
                                st.rerun()
                    else:
                        # 질문 표시 모드
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"**질문:** {question[2]}")
                            st.markdown(f"**모범답안:** {question[3]}")
                        with col2:
                            if st.button("✏️", key=f"edit_q_btn_{question[0]}"):
                                st.session_state[question_edit_key] = True
                                st.rerun()
                        with col3:
                            if st.button("🗑️", key=f"delete_q_{question[0]}"):
                                try:
                                    # 연관된 답안 삭제
                                    db.execute_query(
                                        "DELETE FROM student_answers WHERE question_id = ?",
                                        (question[0],)
                                    )
                                    # 문제 삭제
                                    db.execute_query(
                                        "DELETE FROM questions WHERE id = ?",
                                        (question[0],)
                                    )
                                    st.success("✅ 문제가 삭제되었습니다!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"삭제 중 오류가 발생했습니다: {str(e)}")

            # 새 질문 추가 섹션
            st.divider()
            st.subheader("➕ 새 질문 추가")
            new_question = st.text_input("새 질문", key=f"new_q_{passage[0]}")
            new_answer = st.text_area("새 모범답안", key=f"new_a_{passage[0]}")

            if st.button("💾 질문 추가", key=f"add_q_{passage[0]}"):
                if new_question.strip() and new_answer.strip():
                    try:
                        db.add_question(passage[0], new_question, new_answer)
                        st.success("✅ 새로운 문제가 추가되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"추가 중 오류가 발생했습니다: {str(e)}")
                else:
                    st.error("질문과 모범답안을 모두 입력해주세요.")

            # 지문 삭제 UI
            st.divider()
            if st.session_state[delete_key]:
                st.warning("🚨 정말로 이 지문을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 예, 삭제합니다", key=f"confirm_delete_{passage[0]}"):
                        try:
                            # 연관된 데이터 삭제
                            db.execute_query("""
                                DELETE FROM student_answers 
                                WHERE question_id IN (
                                    SELECT id FROM questions WHERE passage_id = ?
                                )
                            """, (passage[0],))
                            db.execute_query(
                                "DELETE FROM questions WHERE passage_id = ?",
                                (passage[0],)
                            )
                            db.execute_query(
                                "DELETE FROM passages WHERE id = ?",
                                (passage[0],)
                            )
                            st.success("✅ 지문이 성공적으로 삭제되었습니다!")
                            st.session_state[delete_key] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 중 오류가 발생했습니다: {str(e)}")
                with col2:
                    if st.button("❌ 취소", key=f"cancel_delete_{passage[0]}"):
                        st.session_state[delete_key] = False
                        st.rerun()

            # 지문 수정/삭제 버튼
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✏️ 지문 수정", key=f"edit_mode_{passage[0]}"):
                    st.session_state['edit_mode'][passage[0]] = True
                    st.rerun()
            with col2:
                if st.button("🗑️ 지문 삭제", key=f"delete_init_{passage[0]}"):
                    st.session_state[delete_key] = True
                    st.rerun()


if __name__ == "__main__":
    st.set_page_config(page_title="지문 관리", layout="wide")
    manage_passages_and_questions()