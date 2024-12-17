from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(student, passage, results):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=30)
    elements = []

    # 제목 및 학생 정보
    elements.append(Paragraph(passage[1], title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"학생명: {student[1]}", styles['Normal']))
    elements.append(Spacer(1, 20))

    for i, result in enumerate(results, 1):
        elements.append(Paragraph(f"문제 {i}: {result[0]}", styles['Normal']))
        elements.append(Paragraph(f"점수: {result[3]}점", styles['Normal']))
        elements.append(Spacer(1, 12))

    doc.build(elements)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data
