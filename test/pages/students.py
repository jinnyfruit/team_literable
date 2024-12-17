import streamlit as st
from utils.db import db


def manage_students():
    st.subheader("학생 관리")

    # 학생 추가 폼
    with st.form("add_student", clear_on_submit=True):
        st.write("### 새 학생 추가")
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("학생 이름")
        with col2:
            school = st.text_input("학교")
        with col3:
            student_number = st.text_input("학번")

        if st.form_submit_button("학생 추가", use_container_width=True):
            if name and school and student_number:
                try:
                    db.add_student(name, school, student_number)
                    st.success("학생이 성공적으로 추가되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"학생 추가 중 오류가 발생했습니다: {str(e)}")
            else:
                st.error("모든 필드를 입력해주세요.")

    # 학생 검색 및 목록
    st.write("### 학생 검색")
    search_query = st.text_input("🔍 학생 이름 또는 학번으로 검색", key="student_search")
    students = db.fetch_students(search_query)

    # 검색 결과 표시
    st.write("### 등록된 학생 목록")
    if students:
        for student in students:
            with st.expander(f"{student[1]} ({student[2]} - {student[3]})"):
                with st.form(f"edit_student_{student[0]}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        updated_name = st.text_input("학생 이름", value=student[1], key=f"name_{student[0]}")
                    with col2:
                        updated_school = st.text_input("학교", value=student[2], key=f"school_{student[0]}")
                    with col3:
                        updated_student_number = st.text_input("학번", value=student[3], key=f"number_{student[0]}")

                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.form_submit_button("수정", use_container_width=True):
                            if updated_name and updated_school and updated_student_number:
                                try:
                                    db.execute_query(
                                        "UPDATE students SET name = ?, school = ?, student_number = ? WHERE id = ?",
                                        (updated_name, updated_school, updated_student_number, student[0])
                                    )
                                    st.success("학생 정보가 수정되었습니다!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"수정 중 오류가 발생했습니다: {str(e)}")
                            else:
                                st.error("모든 필드를 입력해주세요.")

                    with col2:
                        if st.form_submit_button("삭제", type="secondary", use_container_width=True):
                            try:
                                # 연관된 답안 먼저 삭제
                                db.execute_query(
                                    "DELETE FROM student_answers WHERE student_id = ?",
                                    (student[0],)
                                )
                                # 학생 정보 삭제
                                db.execute_query(
                                    "DELETE FROM students WHERE id = ?",
                                    (student[0],)
                                )
                                st.warning("학생 정보가 삭제되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"삭제 중 오류가 발생했습니다: {str(e)}")
    else:
        st.info("검색된 학생이 없습니다.")


if __name__ == "__main__":
    st.set_page_config(page_title="학생 관리", layout="wide")
    manage_students()