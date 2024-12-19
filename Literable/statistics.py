import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from database_manager import db


def show_overall_statistics():
    """전체 통계 표시"""
    st.subheader("전체 통계")

    # 전체 통계 데이터 가져오기
    stats = db.get_overall_statistics()

    # 주요 지표 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 평균", f"{stats['average_score']:.1f}점")
    with col2:
        st.metric("총 답안 수", f"{stats['total_answers']:,}개")
    with col3:
        st.metric("응시 학생 수", f"{len(db.fetch_students()):,}명")

    # 점수 분포 시각화
    if stats['grade_distribution']:
        df = pd.DataFrame(stats['grade_distribution'], columns=['등급', '학생 수'])

        # 막대 그래프 생성
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(df['등급'], df['학생 수'])
        ax.set_title('전체 점수 분포', pad=20)
        ax.set_xlabel('등급')
        ax.set_ylabel('학생 수')

        # 막대 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{int(height):,}명',
                    ha='center', va='bottom')

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # 상세 통계 표시
        st.write("### 등급별 상세 통계")
        st.dataframe(df.style.format({'학생 수': '{:,}명'.format}))


def show_student_statistics():
    """학생별 분석 표시"""
    st.subheader("학생별 분석")

    # 학생 선택
    students = db.fetch_students()
    if not students:
        st.info("등록된 학생이 없습니다.")
        return

    selected_student = st.selectbox(
        "학생 선택",
        students,
        format_func=lambda x: f"{x[1]} ({x[2]})"
    )

    if selected_student:
        # 학생 통계 데이터 가져오기
        stats = db.get_student_statistics(selected_student[0])

        if stats['student_average']:
            # 평균 비교 표시
            col1, col2 = st.columns(2)
            with col1:
                st.metric("학생 평균", f"{stats['student_average']:.1f}점")
            with col2:
                diff = stats['student_average'] - stats['total_average']
                st.metric("전체 평균과의 차이", f"{diff:+.1f}점")

            # 시간에 따른 점수 변화 시각화
            if stats['progression']:
                progress_df = pd.DataFrame(stats['progression'],
                                           columns=['지문', '점수', '제출일'])

                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(range(len(progress_df)), progress_df['점수'],
                        marker='o', linewidth=2, markersize=8)

                ax.set_title('시간에 따른 점수 변화', pad=20)
                ax.set_xticks(range(len(progress_df)))
                ax.set_xticklabels(progress_df['지문'], rotation=45, ha='right')
                ax.set_ylabel('점수')
                ax.grid(True, alpha=0.3)

                # 점수 표시
                for i, score in enumerate(progress_df['점수']):
                    ax.text(i, score + 1, f'{score:.1f}점',
                            ha='center', va='bottom')

                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

                # 상세 데이터 표시
                st.write("### 제출 이력")
                display_df = progress_df.copy()
                display_df['점수'] = display_df['점수'].apply(lambda x: f'{x:.1f}점')
                display_df['제출일'] = pd.to_datetime(display_df['제출일']).dt.strftime('%Y-%m-%d %H:%M')
                st.dataframe(display_df)
        else:
            st.info("제출된 답안이 없습니다.")


def show_passage_statistics():
    """지문별 분석 표시"""
    st.subheader("지문별 분석")

    # 지문 선택
    passages = db.fetch_passages()
    if not passages:
        st.info("등록된 지문이 없습니다.")
        return

    selected_passage = st.selectbox(
        "지문 선택",
        passages,
        format_func=lambda x: f"{x[1]}"
    )

    if selected_passage:
        # 지문 통계 데이터 가져오기
        stats = db.get_passage_statistics(selected_passage[0])

        if stats:
            # 데이터프레임 생성
            df = pd.DataFrame(stats)

            # 시각화
            fig = plt.figure(figsize=(12, 6))

            # 막대 그래프
            plt.subplot(1, 2, 1)
            bars = plt.bar(range(1, len(df) + 1), df['average_score'])
            plt.title('문제별 평균 점수')
            plt.xlabel('문제 번호')
            plt.ylabel('평균 점수')
            plt.ylim(0, 100)

            # 막대 위에 값 표시
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2., height,
                         f'{height:.1f}점',
                         ha='center', va='bottom')

            # 응시 횟수 그래프
            plt.subplot(1, 2, 2)
            bars = plt.bar(range(1, len(df) + 1), df['attempts'])
            plt.title('문제별 응시 횟수')
            plt.xlabel('문제 번호')
            plt.ylabel('응시 횟수')

            # 막대 위에 값 표시
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2., height,
                         f'{int(height)}회',
                         ha='center', va='bottom')

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

            # 상세 통계 표시
            st.write("### 문제별 상세 통계")
            display_df = pd.DataFrame({
                '문제': range(1, len(df) + 1),
                '평균 점수': df['average_score'].apply(lambda x: f'{x:.1f}점'),
                '응시 횟수': df['attempts'].apply(lambda x: f'{x}회'),
                '문제 내용': df['question']
            })
            st.dataframe(display_df)
        else:
            st.info("제출된 답안이 없습니다.")