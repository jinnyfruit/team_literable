import streamlit as st
from streamlit_option_menu import option_menu
from database_manager import db
from data_management import manage_students, manage_passages_and_questions, manage_report
from analysis import analyze_feedback, show_detailed_analysis
from statistics import show_overall_statistics, show_student_statistics, show_passage_statistics

def main():
    # 페이지 설정
    st.set_page_config(
        page_title="Literable",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 사이드바 구성
    with st.sidebar:
        # 로고 및 제목
        st.image("Logo.png", width=50)
        st.title("Literable")
        st.markdown("---")

        # 메뉴 선택
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
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
            },
        )

        # 사이드바 하단 정보
        st.markdown("---")
        st.caption("© 2024 Literable")

    # 메인 컨텐츠
    if selected == "데이터 관리":
        st.title("데이터 관리")
        tabs = st.tabs(["👥 학생 관리", "📚 지문/문제 관리", "📝 답안 작성"])

        with tabs[0]:
            manage_students()
        with tabs[1]:
            manage_passages_and_questions()
        with tabs[2]:
            manage_report()

    elif selected == "AI 첨삭 분석":
        st.title("AI 첨삭 분석")
        tabs = st.tabs(["🤖 AI 첨삭", "📊 분석 결과"])

        with tabs[0]:
            analyze_feedback()
        with tabs[1]:
            show_detailed_analysis()

    else:  # 통계 대시보드
        st.title("통계 대시보드")
        tabs = st.tabs(["📈 종합 통계", "👥 학생별 분석", "📚 지문별 분석"])

        with tabs[0]:
            show_overall_statistics()
        with tabs[1]:
            show_student_statistics()
        with tabs[2]:
            show_passage_statistics()

if __name__ == "__main__":
    main()