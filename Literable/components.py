from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import streamlit as st
import pdfkit
from typing import List, Tuple

def generate_pdf_report(student: Tuple, passage: Tuple, results: List[Tuple]) -> bytes:
    """PDF 보고서 생성"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # 스타일 정의
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10
    )

    # 문서 요소 생성
    elements = []

    # 제목 및 학생 정보
    elements.append(Paragraph(passage[1], title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"학생명: {student[1]}", normal_style))
    elements.append(Paragraph(f"학교: {student[2]}", normal_style))
    elements.append(Paragraph(f"학번: {student[3]}", normal_style))
    elements.append(Spacer(1, 20))

    # 문제별 분석
    for i, result in enumerate(results, 1):
        question, model_answer, student_answer, score, feedback = result

        elements.append(Paragraph(f"[점수: {score}점]", heading_style))
        elements.append(Paragraph("문제:", normal_style))
        elements.append(Paragraph(question, normal_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("모범답안:", normal_style))
        elements.append(Paragraph(model_answer, normal_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("학생답안:", normal_style))
        elements.append(Paragraph(student_answer, normal_style))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("첨삭 내용:", normal_style))
        elements.append(Paragraph(feedback, normal_style))
        elements.append(Spacer(1, 20))

    # PDF 생성
    doc.build(elements)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

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