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