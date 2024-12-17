import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any


class PlotUtils:
    def __init__(self):
        # 기본 스타일 설정
        plt.style.use('seaborn')
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'danger': '#d62728',
            'info': '#17a2b8',
            'warning': '#ff9f40',
            'background': '#f8f9fa'
        }
        self.grade_colors = ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#F44336']

    def set_common_style(self, ax):
        """공통 스타일 설정"""
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_facecolor(self.colors['background'])

    def create_grade_distribution_chart(self, grade_data: List[Tuple]) -> plt.Figure:
        """점수 구간별 분포 차트 생성"""
        df = pd.DataFrame(grade_data, columns=['등급', '학생 수'])

        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(df['등급'], df['학생 수'],
                      color=self.grade_colors,
                      alpha=0.8)

        # 스타일 설정
        self.set_common_style(ax)
        ax.set_title('점수 분포', fontsize=15, pad=20)
        ax.set_ylabel('학생 수', fontsize=12)

        # 막대 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{int(height):,}명',
                    ha='center', va='bottom', fontsize=10)

        plt.xticks(rotation=0, fontsize=10)
        return fig

    def create_student_progress_chart(self, progress_data: List[Tuple]) -> plt.Figure:
        """학생 성적 추이 차트 생성"""
        df = pd.DataFrame(progress_data, columns=['지문', '평균 점수', '응시일'])

        fig, ax = plt.subplots(figsize=(12, 6))

        # 선 그래프
        line = ax.plot(range(len(df)), df['평균 점수'],
                       marker='o', linewidth=2,
                       color=self.colors['primary'])[0]

        # 배경 영역 추가
        ax.fill_between(range(len(df)), df['평균 점수'],
                        alpha=0.2, color=self.colors['primary'])

        # 스타일 설정
        self.set_common_style(ax)
        ax.set_title('시간에 따른 점수 변화', fontsize=15, pad=20)
        ax.set_ylim(0, max(100, df['평균 점수'].max() + 10))

        # x축 레이블
        plt.xticks(range(len(df)), df['지문'], rotation=45, ha='right')

        # 점수 표시
        for i, score in enumerate(df['평균 점수']):
            ax.text(i, score + 2, f'{score:.1f}점',
                    ha='center', va='bottom', fontsize=10)

        return fig

    def create_passage_analysis_chart(self, question_stats: List[Tuple]) -> Dict[str, plt.Figure]:
        """지문 분석 차트 생성"""
        df = pd.DataFrame(question_stats,
                          columns=['문제', '평균 점수', '응시 횟수', '최저 점수', '최고 점수'])

        charts = {}

        # 1. 문제별 평균 점수 차트
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        bars = ax1.bar(range(len(df)), df['평균 점수'],
                       color=self.colors['primary'],
                       alpha=0.8)

        self.set_common_style(ax1)
        ax1.set_title('문제별 평균 점수', fontsize=15, pad=20)
        ax1.set_ylim(0, 100)

        # 평균 점수 표시
        for i, v in enumerate(df['평균 점수']):
            ax1.text(i, v + 1, f'{v:.1f}점',
                     ha='center', va='bottom', fontsize=10)

        plt.xticks(range(len(df)), [f'문제 {i + 1}' for i in range(len(df))],
                   rotation=0)
        charts['average_scores'] = fig1

        # 2. 점수 분포 히트맵
        score_ranges = list(range(0, 101, 10))
        score_distribution = np.zeros((len(df), len(score_ranges) - 1))

        fig2, ax2 = plt.subplots(figsize=(12, 6))
        sns.heatmap(score_distribution,
                    cmap='YlOrRd',
                    xticklabels=[f'{i}-{i + 9}점' for i in range(0, 100, 10)],
                    yticklabels=[f'문제 {i + 1}' for i in range(len(df))],
                    annot=True, fmt='.0f',
                    ax=ax2)

        ax2.set_title('문제별 점수 분포', fontsize=15, pad=20)
        plt.xticks(rotation=45)
        charts['score_distribution'] = fig2

        # 3. 응시 횟수 및 점수 범위
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        ax3.errorbar(range(len(df)), df['평균 점수'],
                     yerr=[df['평균 점수'] - df['최저 점수'],
                           df['최고 점수'] - df['평균 점수']],
                     fmt='o', capsize=5,
                     color=self.colors['primary'],
                     ecolor=self.colors['secondary'])

        self.set_common_style(ax3)
        ax3.set_title('문제별 점수 범위', fontsize=15, pad=20)
        ax3.set_ylim(0, 100)

        plt.xticks(range(len(df)), [f'문제 {i + 1}' for i in range(len(df))],
                   rotation=0)
        charts['score_range'] = fig3

        return charts

    def create_student_performance_radar(self,
                                         student_scores: List[float],
                                         category_names: List[str]) -> plt.Figure:
        """학생 성적 레이더 차트 생성"""
        angles = np.linspace(0, 2 * np.pi, len(category_names), endpoint=False)

        # 점수를 순환 형태로 만들기
        scores = np.concatenate((student_scores, [student_scores[0]]))
        angles = np.concatenate((angles, [angles[0]]))

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        ax.plot(angles, scores, 'o-', linewidth=2, label='점수',
                color=self.colors['primary'])
        ax.fill(angles, scores, alpha=0.25, color=self.colors['primary'])

        ax.set_thetagrids(angles[:-1] * 180 / np.pi, category_names)
        ax.set_title('영역별 성취도', fontsize=15, pad=20)
        ax.grid(True)

        return fig

    def create_comparative_analysis(self,
                                    student_data: pd.DataFrame,
                                    total_avg: float) -> plt.Figure:
        """학생 성적 비교 분석 차트 생성"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 1. 전체 평균과의 비교
        student_avg = student_data['score'].mean()
        comparison = pd.DataFrame({
            '구분': ['학생 평균', '전체 평균'],
            '점수': [student_avg, total_avg]
        })

        bars = ax1.bar(comparison['구분'], comparison['점수'],
                       color=[self.colors['primary'], self.colors['secondary']])

        self.set_common_style(ax1)
        ax1.set_title('전체 평균 비교', fontsize=15, pad=20)
        ax1.set_ylim(0, 100)

        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{height:.1f}점',
                     ha='center', va='bottom')

        # 2. 성적 분포 내 위치
        sns.kdeplot(data=student_data, x='score', ax=ax2,
                    color=self.colors['primary'])
        ax2.axvline(student_avg, color=self.colors['danger'],
                    linestyle='--', label='학생 평균')
        ax2.axvline(total_avg, color=self.colors['success'],
                    linestyle='--', label='전체 평균')

        self.set_common_style(ax2)
        ax2.set_title('성적 분포 내 위치', fontsize=15, pad=20)
        ax2.legend()

        plt.tight_layout()
        return fig


plot_utils = PlotUtils()