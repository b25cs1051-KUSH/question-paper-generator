from database.db_manager import DatabaseManager
import sqlite3
import json
import hashlib

def generate_hash(content: str) -> str:
    return hashlib.sha256(content.strip().lower().encode('utf-8')).hexdigest()

def seed_database():
    db = DatabaseManager()
    conn = db._get_connection()
    
    print("--- Starting Database Restructuring & Seeding ---")

    try:
        # 0. Cleanup and Setup
        conn.execute("BEGIN TRANSACTION;")
        
        # Keep standards table but delete subjects to trigger cascade delete for chapters, questions, templates, sections
        # However, we only want to delete subjects that shouldn't be there, 
        # but to keep it simple and clean, let's delete all and re-add according to rules.
        conn.execute("DELETE FROM subjects;")
        conn.execute("DELETE FROM question_types;")
        # standards table is kept as per instruction. 
        # We ensure 8-12 exist.
        for std_num in ["8", "9", "10", "11", "12"]:
            conn.execute("INSERT OR IGNORE INTO standards (name) VALUES (?)", (f"Standard {std_num}",))
        
        # Get standard IDs
        standards = {}
        for row in conn.execute("SELECT id, name FROM standards").fetchall():
            standards[row['name']] = row['id']

        # 1. Question Types
        q_types = ["MCQ", "True/False", "Short Answer", "Long Answer", "Fill-ups"]
        type_ids = {}
        for qt in q_types:
            cursor = conn.execute("INSERT INTO question_types (name) VALUES (?)", (qt,))
            type_ids[qt] = cursor.lastrowid
        
        # 2. Subject Mapping
        subject_config = {
            "Standard 8": ["English", "Social Science"],
            "Standard 9": ["English", "Social Science"],
            "Standard 10": ["English", "Social Science"],
            "Standard 11": ["Accounts", "Statistics", "Economics"],
            "Standard 12": ["Accounts", "Statistics", "Economics"]
        }

        # 3. Chapters and 4. Questions
        # Marks and Difficulty
        type_meta = {
            "MCQ": {"marks": 1, "difficulty": "Easy"},
            "True/False": {"marks": 1, "difficulty": "Easy"},
            "Fill-ups": {"marks": 1, "difficulty": "Easy"},
            "Short Answer": {"marks": 3, "difficulty": "Medium"},
            "Long Answer": {"marks": 5, "difficulty": "Hard"}
        }

        print("Seeding subjects, chapters, and questions...")
        for std_name, subs in subject_config.items():
            std_id = standards[std_name]
            for sub_name in subs:
                # Add Subject
                cursor = conn.execute("INSERT INTO subjects (standard_id, name) VALUES (?, ?)", (std_id, sub_name))
                sub_id = cursor.lastrowid
                
                # Add 10 Chapters
                for ch_num in range(1, 11):
                    ch_name = f"Chapter {ch_num}"
                    cursor = conn.execute("INSERT INTO chapters (subject_id, name, chapter_number) VALUES (?, ?, ?)", 
                                         (sub_id, ch_name, ch_num))
                    ch_id = cursor.lastrowid
                    
                    # Add 10 Questions per type
                    for qt_name in q_types:
                        qt_id = type_ids[qt_name]
                        meta = type_meta[qt_name]
                        
                        questions_to_insert = []
                        for q_num in range(1, 11):
                            content = f"{std_name} - {sub_name} - {ch_name} - {qt_name} - Question {q_num}"
                            content_hash = generate_hash(content)
                            questions_to_insert.append((ch_id, qt_id, content, meta['marks'], meta['difficulty'], content_hash))
                        
                        conn.executemany("""
                            INSERT INTO questions (chapter_id, type_id, content, marks, difficulty, content_hash)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, questions_to_insert)

        # 5. Templates
        print("Seeding templates and sections...")
        for std_name, subs in subject_config.items():
            std_id = standards[std_name]
            # Need to get subject IDs again because they were just created
            for sub_name in subs:
                row = conn.execute("SELECT id FROM subjects WHERE standard_id = ? AND name = ?", (std_id, sub_name)).fetchone()
                sub_id = row['id']
                
                # Template 1: Basic Pattern
                # Section A: 5 MCQ, 5 True/False
                # Section B: 5 Short Answer, 5 Long Answer
                t1_name = "Basic Pattern"
                t1_total_marks = (5 * 1) + (5 * 1) + (5 * 3) + (5 * 5) # 5+5+15+25 = 50
                
                t1_config = [
                    {
                        "name": "Section A",
                        "blocks": [
                            {"type_id": type_ids["MCQ"], "count": 5, "marks": 1},
                            {"type_id": type_ids["True/False"], "count": 5, "marks": 1}
                        ]
                    },
                    {
                        "name": "Section B",
                        "blocks": [
                            {"type_id": type_ids["Short Answer"], "count": 5, "marks": 3},
                            {"type_id": type_ids["Long Answer"], "count": 5, "marks": 5}
                        ]
                    }
                ]
                
                cursor = conn.execute("""
                    INSERT INTO templates (name, standard_id, subject_id, total_marks, config_json)
                    VALUES (?, ?, ?, ?, ?)
                """, (t1_name, std_id, sub_id, t1_total_marks, json.dumps(t1_config)))
                t1_id = cursor.lastrowid
                
                # Sections for T1
                conn.execute("INSERT INTO sections (template_id, name, question_type_id, question_count, marks_per_question) VALUES (?, ?, ?, ?, ?)",
                             (t1_id, "Section A", type_ids["MCQ"], 5, 1))
                conn.execute("INSERT INTO sections (template_id, name, question_type_id, question_count, marks_per_question) VALUES (?, ?, ?, ?, ?)",
                             (t1_id, "Section A", type_ids["True/False"], 5, 1))
                conn.execute("INSERT INTO sections (template_id, name, question_type_id, question_count, marks_per_question) VALUES (?, ?, ?, ?, ?)",
                             (t1_id, "Section B", type_ids["Short Answer"], 5, 3))
                conn.execute("INSERT INTO sections (template_id, name, question_type_id, question_count, marks_per_question) VALUES (?, ?, ?, ?, ?)",
                             (t1_id, "Section B", type_ids["Long Answer"], 5, 5))

                # Template 2: Balanced Pattern
                # Section A: 10 MCQ
                # Section B: 5 Fill-ups, 5 Short Answer
                # Section C: 5 Long Answer
                t2_name = "Balanced Pattern"
                t2_total_marks = (10 * 1) + (5 * 1) + (5 * 3) + (5 * 5) # 10+5+15+25 = 55
                
                t2_config = [
                    {
                        "name": "Section A",
                        "blocks": [
                            {"type_id": type_ids["MCQ"], "count": 10, "marks": 1}
                        ]
                    },
                    {
                        "name": "Section B",
                        "blocks": [
                            {"type_id": type_ids["Fill-ups"], "count": 5, "marks": 1},
                            {"type_id": type_ids["Short Answer"], "count": 5, "marks": 3}
                        ]
                    },
                    {
                        "name": "Section C",
                        "blocks": [
                            {"type_id": type_ids["Long Answer"], "count": 5, "marks": 5}
                        ]
                    }
                ]
                
                cursor = conn.execute("""
                    INSERT INTO templates (name, standard_id, subject_id, total_marks, config_json)
                    VALUES (?, ?, ?, ?, ?)
                """, (t2_name, std_id, sub_id, t2_total_marks, json.dumps(t2_config)))
                t2_id = cursor.lastrowid
                
                # Sections for T2
                conn.execute("INSERT INTO sections (template_id, name, question_type_id, question_count, marks_per_question) VALUES (?, ?, ?, ?, ?)",
                             (t2_id, "Section A", type_ids["MCQ"], 10, 1))
                conn.execute("INSERT INTO sections (template_id, name, question_type_id, question_count, marks_per_question) VALUES (?, ?, ?, ?, ?)",
                             (t2_id, "Section B", type_ids["Fill-ups"], 5, 1))
                conn.execute("INSERT INTO sections (template_id, name, question_type_id, question_count, marks_per_question) VALUES (?, ?, ?, ?, ?)",
                             (t2_id, "Section B", type_ids["Short Answer"], 5, 3))
                conn.execute("INSERT INTO sections (template_id, name, question_type_id, question_count, marks_per_question) VALUES (?, ?, ?, ?, ?)",
                             (t2_id, "Section C", type_ids["Long Answer"], 5, 5))

        conn.commit()
        print("--- Seeding Complete ---")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
