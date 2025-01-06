import pdfkit
from typing import List, Tuple
from fpdf import FPDF
import streamlit as st
from datetime import datetime
import os
import urllib.request


class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # 기본 마진 설정
        self.set_margin(15)
        # 한글 폰트 추가 - NanumGothic 사용
        self.add_font('NanumGothic', '', './fonts/NanumGothic.ttf', uni=True)
        self.add_font('NanumGothic-Bold', '', './fonts/NanumGothic-Bold.ttf', uni=True)


def setup_fonts():
    """폰트 디렉토리 생성 및 폰트 다운로드"""
    try:
        # 폰트 디렉토리 생성
        if not os.path.exists('fonts'):
            os.makedirs('fonts')

        # 나눔고딕 폰트 다운로드 (없는 경우)
        font_files = {
            'NanumGothic.ttf': 'https://github.com/googlefonts/nanum-gothic/raw/main/fonts/NanumGothic-Regular.ttf',
            'NanumGothic-Bold.ttf': 'https://github.com/googlefonts/nanum-gothic/raw/main/fonts/NanumGothic-Bold.ttf'
        }

        for font_name, url in font_files.items():
            font_path = f'./fonts/{font_name}'
            if not os.path.exists(font_path):
                urllib.request.urlretrieve(url, font_path)
    except Exception as e:
        st.error(f"폰트 설정 중 오류가 발생했습니다: {str(e)}")


def generate_pdf_report(student: tuple, passage: tuple, results: list) -> bytes:
    """한글 폰트를 사용하여 PDF 생성"""
    try:
        # 폰트 설정
        setup_fonts()

        # PDF 생성
        pdf = PDF()
        pdf.add_page()

        # 제목 (굵은 글씨)
        pdf.set_font('NanumGothic-Bold', size=16)
        pdf.cell(0, 10, "리터러블 문해력 솔루션 보고서", ln=True, align='C')
        pdf.ln(5)

        # 기본 정보
        pdf.set_font('NanumGothic', size=10)
        pdf.cell(0, 10, f"날짜: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
        pdf.cell(0, 10, f"학생: {student[1]}", ln=True)
        pdf.cell(0, 10, f"학년: {student[2]} {student[3]}", ln=True)
        pdf.ln(5)

        # 지문 내용
        pdf.set_font('NanumGothic-Bold', size=12)
        pdf.cell(0, 10, "지문", ln=True)
        pdf.set_font('NanumGothic', size=10)
        pdf.multi_cell(0, 10, passage[2])
        pdf.ln(5)

        # 각 문제 분석
        for idx, result in enumerate(results, 1):
            question, model_answer, student_answer, score, feedback = result

            # 문제 번호와 점수
            pdf.set_font('NanumGothic-Bold', size=12)
            pdf.cell(0, 10, f"문제 {idx} - 점수: {score}/5", ln=True)
            pdf.ln(5)

            pdf.set_font('NanumGothic-Bold', size=10)
            pdf.cell(0, 10, "문제:", ln=True)
            pdf.set_font('NanumGothic', size=10)
            pdf.multi_cell(0, 10, str(question))
            pdf.ln(5)

            pdf.set_font('NanumGothic-Bold', size=10)
            pdf.cell(0, 10, "학생 답변:", ln=True)
            pdf.set_font('NanumGothic', size=10)
            pdf.multi_cell(0, 10, str(student_answer))
            pdf.ln(5)

            pdf.set_font('NanumGothic-Bold', size=10)
            pdf.cell(0, 10, "모범 답안:", ln=True)
            pdf.set_font('NanumGothic', size=10)
            pdf.multi_cell(0, 10, str(model_answer))
            pdf.ln(5)

            pdf.set_font('NanumGothic-Bold', size=10)
            pdf.cell(0, 10, "피드백:", ln=True)
            pdf.set_font('NanumGothic', size=10)
            pdf.multi_cell(0, 10, str(feedback))
            pdf.ln(10)

        return bytes(pdf.output())

    except Exception as e:
        print(f"Error details: {str(e)}")
        st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
        return None


def get_question_type_icon(question_text: str) -> str:
    """문제 유형에 따른 아이콘 반환"""
    if '사실적' in question_text:
        return '㖐 사실적 독해'
    elif '비판적' in question_text:
        return '㖐 비판적 독해'
    elif '추론적' in question_text:
        return '㖐 추론적 독해'
    elif '창의적' in question_text:
        return '㖐 창의적 독해'
    return ''

def format_feedback_report(student: Tuple, passage: Tuple, results: List[Tuple]) -> str:
    """리터러블 스타일의 PDF 보고서 생성"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
            body {{
                font-family: 'Noto Sans KR', sans-serif;
                margin: 0;
                padding: 40px;
                color: #333;
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .title {{
                font-size: 24px;
                font-weight: bold;
                margin: 0;
                color: #2c3e50;
            }}
            .subtitle {{
                font-size: 18px;
                margin: 10px 0;
                color: #34495e;
            }}
            .info-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .info-table td {{
                padding: 8px;
                border: none;
            }}
            .question-section {{
                margin: 30px 0;
            }}
            .question-header {{
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }}
            .question-type {{
                color: #2980b9;
                font-weight: bold;
                margin-right: 10px;
            }}
            .score {{
                color: #2980b9;
                font-weight: bold;
            }}
            .content-section {{
                margin: 15px 0;
            }}
            .content-title {{
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .content-box {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 15px;
            }}
            @page {{
                size: A4;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">리터러블 문해력 솔루션 보고서</h1>
            <p class="subtitle">Literable 리터러블</p>
        </div>

        <table class="info-table">
            <tr>
                <td>솔루션 일시: {student[4] if len(student) > 4 else '2024년 12월 24일'}</td>
                <td>성명: {student[1]}</td>
                <td>학년: {student[2]} {student[3]}</td>
                <td>총점: {sum(r[3] for r in results)}/{len(results) * 5}점</td>
            </tr>
        </table>
    """

    # 지문 내용 추가
    html_content += f"""
        <div class="content-section">
            {passage[2]}
        </div>
    """

    # 각 문제별 분석
    for idx, result in enumerate(results, 1):
        question, model_answer, student_answer, score, feedback = result
        question_type = get_question_type_icon(question)

        html_content += f"""
        <div class="question-section">
            <div class="question-header">
                <span class="question-type">질문 {idx} {question_type}</span>
                <span class="score">{score}점 / 5점</span>
            </div>

            <div class="content-box">
                <div class="content-title">1. 학생 답변</div>
                <p>{student_answer}</p>
            </div>

            <div class="content-box">
                <div class="content-title">2. 모범 답안</div>
                <p>{model_answer}</p>
            </div>

            <div class="content-box">
                <div class="content-title">3. 첨삭</div>
                <p>{feedback}</p>
            </div>
        </div>
        """

    html_content += """
    </body>
    </html>
    """

    # PDF 옵션 설정
    options = {
        'page-size': 'A4',
        'margin-top': '15mm',
        'margin-right': '15mm',
        'margin-bottom': '15mm',
        'margin-left': '15mm',
        'encoding': 'UTF-8',
        'no-outline': None,
        'enable-local-file-access': None
    }

    try:
        # HTML을 PDF로 변환
        pdf_data = pdfkit.from_string(html_content, False, options=options)
        return pdf_data
    except Exception as e:
        st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
        return None