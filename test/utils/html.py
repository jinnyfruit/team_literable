class HTMLTemplates:
    """HTML 템플릿 모음"""

    @staticmethod
    def get_style() -> str:
        """보고서 스타일 정의"""
        return """
        <style>
            :root {
                --primary-color: #1f77b4;
                --secondary-color: #ff7f0e;
                --success-color: #2ca02c;
                --danger-color: #d62728;
                --background-color: #ffffff;
                --border-color: #e1e4e8;
                --text-color: #24292e;
            }

            .report-container {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                padding: 2rem;
                max-width: 100%;
                margin: 0 auto;
                background-color: var(--background-color);
                color: var(--text-color);
                line-height: 1.6;
            }

            .report-header {
                background: linear-gradient(to right, #f8f9fa, #ffffff);
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }

            .passage-title {
                color: var(--primary-color);
                margin: 0 0 1rem 0;
                font-size: 1.8rem;
                font-weight: 600;
            }

            .student-info {
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
                gap: 1rem;
                margin-top: 1rem;
            }

            .student-info-item {
                background: white;
                padding: 0.8rem 1.5rem;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                min-width: 150px;
                border-left: 4px solid var(--primary-color);
            }

            .report-summary {
                background: linear-gradient(to right, #e8f0fe, #f8f9fa);
                padding: 1.5rem 2rem;
                border-radius: 8px;
                margin: 1rem 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }

            .question-section {
                background: white;
                border: 1px solid var(--border-color);
                border-radius: 10px;
                padding: 1.5rem;
                margin: 1rem 0;
                position: relative;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                transition: transform 0.2s ease;
            }

            .question-section:hover {
                transform: translateY(-2px);
            }

            .score-badge {
                position: absolute;
                top: 1rem;
                right: 1rem;
                background: var(--primary-color);
                color: white;
                padding: 0.5rem 1.5rem;
                border-radius: 20px;
                font-weight: bold;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            .answer-box {
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 5px;
                margin: 1rem 0;
                border-left: 4px solid var(--primary-color);
            }

            .feedback-box {
                background: #e8f0fe;
                padding: 1rem;
                border-radius: 5px;
                margin: 1rem 0;
                border-left: 4px solid var(--success-color);
            }

            .section-title {
                color: var(--primary-color);
                margin-bottom: 0.5rem;
                font-weight: bold;
                font-size: 1.1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .section-title::before {
                content: "•";
                color: var(--primary-color);
            }

            .content-text {
                line-height: 1.6;
                color: var(--text-color);
            }

            @media (max-width: 768px) {
                .report-container {
                    padding: 1rem;
                }
                .student-info {
                    flex-direction: column;
                }
                .student-info-item {
                    width: 100%;
                }
            }
        </style>
        """


class ReportGenerator:
    """HTML 보고서 생성 클래스"""

    def __init__(self, student: tuple, passage: tuple, results: list):
        self.student = student
        self.passage = passage
        self.results = results
        self.templates = HTMLTemplates()

    def generate_header(self) -> str:
        """보고서 헤더 생성"""
        return f"""
        <div class="report-header">
            <h2 class="passage-title">{self.passage[1]}</h2>
            <div class="student-info">
                <div class="student-info-item">
                    <strong>학생명:</strong> {self.student[1]}
                </div>
                <div class="student-info-item">
                    <strong>학교:</strong> {self.student[2]}
                </div>
                <div class="student-info-item">
                    <strong>학번:</strong> {self.student[3]}
                </div>
            </div>
        </div>
        """

    def generate_summary(self) -> str:
        """종합 평가 섹션 생성"""
        avg_score = sum(r[3] for r in self.results) / len(self.results)
        highest_score = max(r[3] for r in self.results)
        lowest_score = min(r[3] for r in self.results)

        return f"""
        <div class="report-summary">
            <h3 style="margin-top: 0;">종합 평가</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div>
                    <strong>총 문항:</strong> {len(self.results)}개
                </div>
                <div>
                    <strong>평균 점수:</strong> {avg_score:.1f}점
                </div>
                <div>
                    <strong>최고 점수:</strong> {highest_score}점
                </div>
                <div>
                    <strong>최저 점수:</strong> {lowest_score}점
                </div>
            </div>
        </div>
        """

    def generate_question_sections(self) -> str:
        """문제별 섹션 생성"""
        sections = []
        for i, (question, model_answer, student_answer, score, feedback) in enumerate(self.results, 1):
            section = f"""
            <div class="question-section">
                <div class="score-badge">{score}점</div>

                <div class="section-title">문제 {i}</div>
                <div class="content-text">{question}</div>

                <div class="answer-box">
                    <div class="section-title">모범답안</div>
                    <div class="content-text">{model_answer}</div>
                </div>

                <div class="answer-box">
                    <div class="section-title">학생답안</div>
                    <div class="content-text">{student_answer}</div>
                </div>

                <div class="feedback-box">
                    <div class="section-title">첨삭 내용</div>
                    <div class="content-text">{feedback}</div>
                </div>
            </div>
            """
            sections.append(section)
        return "\n".join(sections)

    def generate_report(self) -> str:
        """전체 보고서 생성"""
        return f"""
        {self.templates.get_style()}
        <div class="report-container">
            {self.generate_header()}
            {self.generate_summary()}
            {self.generate_question_sections()}
        </div>
        """


def create_feedback_report(student: tuple, passage: tuple, results: list) -> str:
    """피드백 보고서 생성을 위한 헬퍼 함수"""
    generator = ReportGenerator(student, passage, results)
    return generator.generate_report()