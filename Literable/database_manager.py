import sqlite3
from typing import List, Tuple, Optional, Dict, Any
import streamlit as st

class DatabaseManager:
    def __init__(self, db_name: str = "Literable.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self) -> None:
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create students table
        cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        school TEXT,
                        student_number TEXT
                    )''')

        # Create passages table
        cursor.execute('''CREATE TABLE IF NOT EXISTS passages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        passage TEXT
                    )''')

        # Create questions table
        cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        passage_id INTEGER,
                        question TEXT,
                        model_answer TEXT,
                        category TEXT DEFAULT '',
                        FOREIGN KEY (passage_id) REFERENCES passages (id)
                    )''')

        # Create student_answers table
        cursor.execute('''CREATE TABLE IF NOT EXISTS student_answers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        question_id INTEGER,
                        student_answer TEXT,
                        score INTEGER,
                        feedback TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(student_id, question_id), 
                        FOREIGN KEY (student_id) REFERENCES students (id),
                        FOREIGN KEY (question_id) REFERENCES questions (id)
                    )''')

        conn.commit()
        conn.close()

    # Student related methods
    def fetch_students(self, search_query: Optional[str] = None) -> List[Tuple]:
        """Fetch students from database with optional search query"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if search_query:
            cursor.execute("SELECT * FROM students WHERE name LIKE ? OR student_number LIKE ?",
                           (f'%{search_query}%', f'%{search_query}%'))
        else:
            cursor.execute("SELECT * FROM students")

        students = cursor.fetchall()
        conn.close()
        return students

    def add_student(self, name: str, school: str, student_number: str) -> None:
        """Add a new student to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (name, school, student_number) VALUES (?, ?, ?)",
                       (name, school, student_number))
        conn.commit()
        conn.close()

    def update_student(self, student_id: int, name: str, school: str, student_number: str) -> None:
        """Update existing student information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE students SET name = ?, school = ?, student_number = ? WHERE id = ?",
                       (name, school, student_number, student_id))
        conn.commit()
        conn.close()

    def delete_student(self, student_id: int) -> None:
        """Delete a student from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        conn.close()

    # Passage related methods
    def fetch_passages(self, search_query: str = "") -> List[Tuple]:
        """Fetch passages from database with optional search query"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM passages WHERE title LIKE ?", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT * FROM passages")
        passages = cursor.fetchall()
        conn.close()
        return passages

    def add_passage(self, title: str, passage: str) -> int:
        """Add a new passage to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO passages (title, passage) VALUES (?, ?)", (title, passage))
        passage_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return passage_id

    def update_passage(self, passage_id: int, title: str, passage: str) -> None:
        """Update existing passage"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE passages SET title = ?, passage = ? WHERE id = ?",
                       (title, passage, passage_id))
        conn.commit()
        conn.close()

    def delete_passage(self, passage_id: int) -> None:
        """Delete a passage and its related questions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Delete related student answers
        cursor.execute("""
            DELETE FROM student_answers 
            WHERE question_id IN (
                SELECT id FROM questions WHERE passage_id = ?
            )
        """, (passage_id,))
        # Delete related questions
        cursor.execute("DELETE FROM questions WHERE passage_id = ?", (passage_id,))
        # Delete passage
        cursor.execute("DELETE FROM passages WHERE id = ?", (passage_id,))
        conn.commit()
        conn.close()

    # Question related methods
    def fetch_questions(self, passage_id: int) -> List[Tuple]:
        """Fetch questions for a specific passage"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM questions WHERE passage_id = ?', (passage_id,))
            questions = cursor.fetchall()
            return questions
        finally:
            conn.close()

    def add_question(self, passage_id: int, question: str, model_answer: str, category: str) -> None:
        """Add a new question to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO questions (passage_id, question, model_answer, category)
                            VALUES (?, ?, ?, ?)''', (passage_id, question, model_answer, category))
            conn.commit()
        finally:
            conn.close()

    def update_question(self, question_id: int, question: str, model_answer: str, category: str) -> None:
        """Update existing question"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE questions SET question = ?, model_answer = ?, category = ? WHERE id = ?",
                       (question, model_answer, category, question_id))
        conn.commit()
        conn.close()

    def delete_question(self, question_id: int) -> None:
        """Delete a question and its related answers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # Delete related student answers first
        cursor.execute("DELETE FROM student_answers WHERE question_id = ?", (question_id,))
        # Delete the question
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
        conn.close()

    # Student Answer related methods
    def fetch_student_answers(self, student_id: int, passage_id: Optional[int] = None) -> List[Tuple]:
        """학생 답안 조회 함수 수정"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            if passage_id is not None:
                # 특정 지문에 대한 답안 조회
                cursor.execute("""
                    SELECT sa.id, sa.student_id, sa.question_id, sa.student_answer, 
                           sa.score, sa.feedback, sa.created_at
                    FROM student_answers sa
                    JOIN questions q ON sa.question_id = q.id
                    WHERE sa.student_id = ? AND q.passage_id = ?
                    ORDER BY q.id
                """, (student_id, passage_id))
            else:
                # 모든 답안 조회 (답안이 있는 경우만)
                cursor.execute("""
                    SELECT DISTINCT sa.id, sa.student_id, sa.question_id, sa.student_answer,
                           sa.score, sa.feedback, sa.created_at
                    FROM student_answers sa
                    WHERE sa.student_id = ? AND sa.score IS NOT NULL
                    ORDER BY sa.created_at DESC
                """, (student_id,))

            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching student answers: {e}")
            return []
        finally:
            conn.close()

    def save_student_answer(self, student_id: int, question_id: int,
                            answer: str, score: int, feedback: str) -> bool:
        """학생 답안 저장 함수 수정"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # UPSERT 구문 사용하여 저장 또는 업데이트
            cursor.execute("""
                INSERT INTO student_answers 
                (student_id, question_id, student_answer, score, feedback, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(student_id, question_id) 
                DO UPDATE SET
                    student_answer = excluded.student_answer,
                    score = excluded.score,
                    feedback = excluded.feedback,
                    created_at = CURRENT_TIMESTAMP
                WHERE student_id = ? AND question_id = ?
            """, (student_id, question_id, answer, score, feedback, student_id, question_id))

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error saving student answer: {e}")
            return False
        finally:
            conn.close()

    def save_student_answer(self, student_id: int, question_id: int,
                            answer: str, score: int, feedback: str) -> bool:
        """학생 답안 저장 함수 수정"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # UPSERT 구문 사용하여 저장 또는 업데이트
            cursor.execute("""
                INSERT INTO student_answers 
                (student_id, question_id, student_answer, score, feedback, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(student_id, question_id) 
                DO UPDATE SET
                    student_answer = excluded.student_answer,
                    score = excluded.score,
                    feedback = excluded.feedback,
                    created_at = CURRENT_TIMESTAMP
                WHERE student_id = ? AND question_id = ?
            """, (student_id, question_id, answer, score, feedback, student_id, question_id))

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error saving student answer: {e}")
            return False
        finally:
            conn.close()

    def delete_student_answer(self, answer_id: int) -> None:
        """Delete a student answer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_answers WHERE id = ?", (answer_id,))
        conn.commit()
        conn.close()

    # Statistics related methods
    def get_overall_statistics(self) -> Dict[str, Any]:
        """Get overall statistics from the database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get average score
        cursor.execute("SELECT AVG(score) FROM student_answers")
        avg_score = cursor.fetchone()[0] or 0

        # Get total answers count
        cursor.execute("SELECT COUNT(*) FROM student_answers")
        total_answers = cursor.fetchone()[0] or 0

        # Get grade distribution
        cursor.execute("""
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
            GROUP BY grade
            ORDER BY grade
        """)
        grade_distribution = cursor.fetchall()

        conn.close()
        return {
            'average_score': avg_score,
            'total_answers': total_answers,
            'grade_distribution': grade_distribution
        }

    def get_student_with_answers(self) -> List[Tuple]:
        """답안이 있는 학생만 조회하는 새로운 함수"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT DISTINCT s.* 
                FROM students s
                JOIN student_answers sa ON s.id = sa.student_id
                WHERE sa.score IS NOT NULL
                ORDER BY s.name
            """)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching students with answers: {e}")
            return []
        finally:
            conn.close()

    def get_student_statistics(self, student_id: int) -> Dict[str, Any]:
        """Get statistics for a specific student"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get student's average and total average
        cursor.execute("""
            SELECT 
                AVG(sa.score) as student_avg,
                (SELECT AVG(score) FROM student_answers) as total_avg
            FROM student_answers sa
            WHERE sa.student_id = ?
        """, (student_id,))

        avg_data = cursor.fetchone()

        # Get student's score progression
        cursor.execute("""
            SELECT p.title, sa.score, sa.created_at
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            JOIN passages p ON q.passage_id = p.id
            WHERE sa.student_id = ?
            ORDER BY sa.created_at
        """, (student_id,))

        progression_data = cursor.fetchall()

        conn.close()
        return {
            'student_average': avg_data[0] if avg_data else 0,
            'total_average': avg_data[1] if avg_data else 0,
            'progression': progression_data
        }

    def get_passage_statistics(self, passage_id: int) -> List[Dict[str, Any]]:
        """Get statistics for a specific passage"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                q.question,
                AVG(sa.score) as avg_score,
                COUNT(sa.id) as attempt_count
            FROM questions q
            LEFT JOIN student_answers sa ON q.id = sa.question_id
            WHERE q.passage_id = ?
            GROUP BY q.id
        """, (passage_id,))

        stats = cursor.fetchall()
        conn.close()

        return [
            {
                'question': stat[0],
                'average_score': stat[1] if stat[1] else 0,
                'attempts': stat[2]
            }
            for stat in stats
        ]

# Create a global instance
db = DatabaseManager()
