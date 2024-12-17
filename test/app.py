import streamlit as st
from streamlit_option_menu import option_menu
from pages import students, passages, reports, analysis, statistics


def main():
    st.set_page_config(
        page_title="Literable",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    with st.sidebar:
        st.image("assets/Logo.png", width=50)
        st.title("Literable")
        st.markdown("---")
        selected = option_menu(
            menu_title=None,
            options=["데이터 관리", "AI 첨삭 분석", "통계 대시보드"],
            icons=["gear", "robot", "graph-up"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important"},
                "icon": {"font-size": "1rem"},
                "nav-link": {
                    "font-size": "0.9rem",
                    "text-align": "left",
                    "--hover-color": "#eee",
                },
            },
        )
        st.markdown("---")
        st.caption("© 2024 Literable")

    if selected == "데이터 관리":
        tabs = st.tabs(["👥 학생 관리", "📚 지문/문제 관리", "📝 답안 작성"])
        with tabs[0]:
            students.manage_students()
        with tabs[1]:
            passages.manage_passages_and_questions()
        with tabs[2]:
            reports.manage_report()

    elif selected == "AI 첨삭 분석":
        tabs = st.tabs(["🤖 AI 첨삭", "📊 분석 결과"])
        with tabs[0]:
            analysis.analyze_feedback()
        with tabs[1]:
            analysis.show_detailed_analysis()

    elif selected == "통계 대시보드":
        tabs = st.tabs(["📈 종합 통계", "👥 학생별 분석", "📚 지문별 분석"])
        with tabs[0]:
            statistics.show_overall_statistics()
        with tabs[1]:
            statistics.show_student_statistics()
        with tabs[2]:
            statistics.show_passage_statistics()


if __name__ == "__main__":
    main()
