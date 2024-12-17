import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.db import db


def show_overall_statistics():
    """전체 통계 표시"""
    st.subheader("전체 통계")

    # 기본 통계 데이터 조회
    total_avg = db.execute_query("SELECT AVG(score) FROM student_answers")[0][0] or 0
    total_answers = db.execute_query("SELECT COUNT(*) FROM student_answers")[0][0] or 0
    total_students = len(db.fetch_students())

    # 통계 메트릭 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 평균", f"{total_avg:.1f}점")
    with col2:
        st.metric("총 답안 수", f"{total_answers:,}개")
    with col3:
        st.metric("응시 학생 수", f"{total_students:,}명")

    # 점수 구간별 분포
    grade_distribution = db.execute_query("""
        SELECT 
            CASE 
                WHEN score >= 90 THEN 'A (90-100)'
                WHEN score >= 80 THEN 'B (80-89)'
                WHEN score >= 70 THEN 'C (70-79)'
                WHEN score >= 60 THEN 'D (60-69)'
                ELSE 'F (0-59)'
            END as grade,
            COUNT(*) as count
        FROM student_answers
        WHERE score IS NOT NULL
        GROUP BY grade
        ORDER BY grade
    """)

    if grade_distribution:
        st.subheader("점수 분포")
        df = pd.DataFrame(grade_distribution, columns=['등급', '학생 수'])

        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(df['등급'], df['학생 수'])
        ax.set_title('전체 점수 분포')
        ax.set_ylabel('학생 수')

        # 막대 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{int(height):,}명',
                    ha='center', va='bottom')

        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()

        # 상세 통계 테이블
        st.write("### 상세 통계")
        styled_df = df.style.format({'학생 수': '{:,}'})
        st.dataframe(styled_df, use_container_width=True)


def show_student_statistics():
    """학생별 분석"""
    st.subheader("학생별 분석")

    # 학생 선택
    students = db.execute_query("""
        SELECT DISTINCT s.* 
        FROM students s
        JOIN student_answers sa ON s.id = sa.student_id
        WHERE sa.score IS NOT NULL
        ORDER BY s.name
    """)

    if not students:
        st.info("분석할 데이터가 없습니다.")
        return

    selected_student = st.selectbox(
        "학생 선택",
        students,
        format_func=lambda x: f"{x[1]} ({x[2]} - {x[3]})",
        key="stat_student_select"
    )

    if selected_student:
        # 학생의 전체 통계
        stats = db.execute_query("""
            SELECT 
                COUNT(sa.id) as total_answers,
                AVG(sa.score) as avg_score,
                MIN(sa.score) as min_score,
                MAX(sa.score) as max_score,
                (SELECT AVG(score) FROM student_answers) as total_avg
            FROM student_answers sa
            WHERE sa.student_id = ? AND sa.score IS NOT NULL
        """, (selected_student[0],))

        if stats and stats[0][0] > 0:  # 답안이 있는 경우
            total_answers, avg_score, min_score, max_score, total_avg = stats[0]

            # 통계 메트릭
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("응시 문제 수", f"{total_answers:,}개")
            with col2:
                st.metric("평균 점수", f"{avg_score:.1f}점")
            with col3:
                diff = avg_score - (total_avg or 0)
                st.metric("전체 평균과의 차이", f"{diff:+.1f}점")

            # 시간에 따른 점수 변화
            progress_data = db.execute_query("""
                SELECT 
                    p.title,
                    AVG(sa.score) as avg_score,
                    MIN(sa.created_at) as attempt_date
                FROM student_answers sa
                JOIN questions q ON sa.question_id = q.id
                JOIN passages p ON q.passage_id = p.id
                WHERE sa.student_id = ? AND sa.score IS NOT NULL
                GROUP BY p.id
                ORDER BY attempt_date
            """, (selected_student[0],))

            if progress_data:
                st.subheader("성적 추이")
                df = pd.DataFrame(progress_data, columns=['지문', '평균 점수', '응시일'])

                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(range(len(df)), df['평균 점수'], marker='o')
                ax.set_title('시간에 따른 점수 변화')
                ax.set_xticks(range(len(df)))
                ax.set_xticklabels(df['지문'], rotation=45, ha='right')
                ax.grid(True, alpha=0.3)

                # 점수 표시
                for i, score in enumerate(df['평균 점수']):
                    ax.text(i, score, f'{score:.1f}점', ha='center', va='bottom')

                st.pyplot(fig)
                plt.close()


def show_passage_statistics():
    """지문별 분석"""
    st.subheader("지문별 분석")

    # 지문 선택
    passages = db.execute_query("""
        SELECT DISTINCT p.* 
        FROM passages p
        JOIN questions q ON p.id = q.passage_id
        JOIN student_answers sa ON q.id = sa.question_id
        WHERE sa.score IS NOT NULL
        ORDER BY p.title
    """)

    if not passages:
        st.info("분석할 데이터가 없습니다.")
        return

    selected_passage = st.selectbox(
        "지문 선택",
        passages,
        format_func=lambda x: x[1],
        key="stat_passage_select"
    )

    if selected_passage:
        # 문제별 통계
        question_stats = db.execute_query("""
            SELECT 
                q.question,
                AVG(sa.score) as avg_score,
                COUNT(sa.id) as attempt_count,
                MIN(sa.score) as min_score,
                MAX(sa.score) as max_score
            FROM questions q
            LEFT JOIN student_answers sa ON q.id = sa.question_id
            WHERE q.passage_id = ? AND sa.score IS NOT NULL
            GROUP BY q.id
            ORDER BY q.id
        """, (selected_passage[0],))

        if question_stats:
            # 전체 통계
            df = pd.DataFrame(question_stats, columns=[
                '문제', '평균 점수', '응시 횟수', '최저 점수', '최고 점수'
            ])

            # 문제별 평균 점수 차트
            st.subheader("문제별 평균 점수")
            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.bar(range(len(df)), df['평균 점수'])
            ax.set_title('문제별 평균 점수')
            ax.set_ylim(0, 100)
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels([f'문제 {i + 1}' for i in range(len(df))], rotation=0)
            ax.grid(True, alpha=0.3)

            # 평균 점수 표시
            for i, v in enumerate(df['평균 점수']):
                ax.text(i, v + 1, f'{v:.1f}점', ha='center')

            st.pyplot(fig)
            plt.close()

            # 상세 통계 테이블
            st.write("### 문제별 상세 통계")
            styled_df = df.copy()
            styled_df.columns = ['문제', '평균 점수', '응시 횟수', '최저 점수', '최고 점수']
            styled_df = styled_df.style.format({
                '평균 점수': '{:.1f}',
                '최저 점수': '{:.1f}',
                '최고 점수': '{:.1f}',
                '응시 횟수': '{:,}'
            })
            st.dataframe(styled_df, use_container_width=True)

            # 점수 분포
            st.subheader("점수 분포")
            score_distribution = db.execute_query("""
                SELECT 
                    CASE 
                        WHEN score >= 90 THEN 'A (90-100)'
                        WHEN score >= 80 THEN 'B (80-89)'
                        WHEN score >= 70 THEN 'C (70-79)'
                        WHEN score >= 60 THEN 'D (60-69)'
                        ELSE 'F (0-59)'
                    END as grade,
                    COUNT(*) as count
                FROM questions q
                JOIN student_answers sa ON q.id = sa.question_id
                WHERE q.passage_id = ? AND sa.score IS NOT NULL
                GROUP BY grade
                ORDER BY grade
            """, (selected_passage[0],))

            if score_distribution:
                df = pd.DataFrame(score_distribution, columns=['등급', '학생 수'])
                fig, ax = plt.subplots(figsize=(10, 5))
                bars = ax.bar(df['등급'], df['학생 수'])
                ax.set_title('점수 분포')

                # 값 표시
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{int(height):,}명',
                            ha='center', va='bottom')

                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
                st.pyplot(fig)
                plt.close()


if __name__ == "__main__":
    st.set_page_config(page_title="통계 대시보드", layout="wide")

    tabs = st.tabs(["📈 종합 통계", "👥 학생별 분석", "📚 지문별 분석"])
    with tabs[0]:
        show_overall_statistics()
    with tabs[1]:
        show_student_statistics()
    with tabs[2]:
        show_passage_statistics()