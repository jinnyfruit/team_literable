import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
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

def format_feedback_report(student: Tuple, passage: Tuple, results: List[Tuple]) -> str:
    """첨삭 보고서 HTML 형식 생성"""
    report_html = f"""
    <div class="report-container">
        <div class="report-header">
            <h2 class="passage-title">{passage[1]}</h2>
            <div class="student-info">
                <p><strong>학생명:</strong> {student[1]}</p>
                <p><strong>학교:</strong> {student[2]}</p>
                <p><strong>학번:</strong> {student[3]}</p>
            </div>
        </div>

        <div class="report-summary">
            <h3>종합 평가</h3>
            <p>총 문항: {len(results)}개</p>
            <p>평균 점수: {sum(r[3] for r in results) / len(results):.1f}점</p>
        </div>

        <style>
            .report-container {{
                padding: 20px;
                max-width: 1200px;
                margin: 0 auto;
            }}
            .report-header {{
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
            }}
            .passage-title {{
                color: #2c3e50;
                margin-bottom: 20px;
            }}
            .student-info {{
                display: flex;
                justify-content: space-around;
                margin-top: 20px;
            }}
            .student-info p {{
                margin: 0;
            }}
            .report-summary {{
                margin: 20px 0;
                padding: 15px;
                background: #e9ecef;
                border-radius: 8px;
            }}
            .question-card {{
                margin: 20px 0;
                padding: 20px;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                position: relative;
            }}
            .score-badge {{
                position: absolute;
                top: 20px;
                right: 20px;
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 1.2em;
            }}
            .answer-section {{
                margin: 15px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }}
            .feedback-section {{
                margin-top: 15px;
                padding: 15px;
                background: #e9ecef;
                border-radius: 5px;
            }}
        </style>
    """

    for i, result in enumerate(results, 1):
        question, model_answer, student_answer, score, feedback = result
        report_html += f"""
        <div class="question-card">
            <div class="score-badge">{score}점</div>

            <h4>문제</h4>
            <p>{question}</p>

            <div class="answer-section">
                <h5>모범답안</h5>
                <p>{model_answer}</p>
            </div>

            <div class="answer-section">
                <h5>학생답안</h5>
                <p>{student_answer}</p>
            </div>

            <div class="feedback-section">
                <h5>첨삭 내용</h5>
                <p>{feedback}</p>
            </div>
        </div>
        """

    report_html += "</div>"
    return report_html