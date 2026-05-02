from database.db_manager import DatabaseManager
import sqlite3

def seed_database():
    db = DatabaseManager()
    
    print("--- Starting Database Seeding ---")

    # 1. Seed Question Types
    question_types = ["MCQ", "True/False", "Short Answer", "Long Answer"]
    type_ids = {}
    conn = db._get_connection()
    try:
        cursor = conn.cursor()
        for qt in question_types:
            cursor.execute("INSERT OR IGNORE INTO question_types (name) VALUES (?)", (qt,))
            cursor.execute("SELECT id FROM question_types WHERE name = ?", (qt,))
            type_ids[qt] = cursor.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    print(f"Step 1: Seeded {len(question_types)} Question Types.")

    # 2. Seed Standards
    standards = ["8", "9", "10", "11", "12"]
    standard_ids = {}
    conn = db._get_connection()
    try:
        cursor = conn.cursor()
        for std in standards:
            cursor.execute("INSERT OR IGNORE INTO standards (name) VALUES (?)", (f"Standard {std}",))
            cursor.execute("SELECT id FROM standards WHERE name = ?", (f"Standard {std}",))
            standard_ids[std] = cursor.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    print(f"Step 2: Seeded Standards {', '.join(standards)}.")

    # 3. Seed Subjects for each Standard
    subjects = ["English", "Social Studies", "Economics", "Business Administration"]
    subject_map = {} # (std, sub_name) -> id
    conn = db._get_connection()
    try:
        cursor = conn.cursor()
        for std in standards:
            for sub in subjects:
                cursor.execute("INSERT OR IGNORE INTO subjects (standard_id, name) VALUES (?, ?)", (standard_ids[std], sub))
                cursor.execute("SELECT id FROM subjects WHERE standard_id = ? AND name = ?", (standard_ids[std], sub))
                subject_map[(std, sub)] = cursor.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    print(f"Step 3: Seeded {len(subjects)} Subjects for each Standard.")

    # 4. Seed Chapters for each Subject
    # For brevity, we'll name them Chapter 1, 2, 3
    chapter_ids = []
    conn = db._get_connection()
    try:
        cursor = conn.cursor()
        for key, sub_id in subject_map.items():
            for i in range(1, 4):
                cursor.execute("INSERT OR IGNORE INTO chapters (subject_id, name, chapter_number) VALUES (?, ?, ?)", 
                               (sub_id, f"Chapter {i}: Introduction to {key[1]}", i))
                cursor.execute("SELECT id FROM chapters WHERE subject_id = ? AND chapter_number = ?", (sub_id, i))
                chapter_ids.append(cursor.fetchone()[0])
        conn.commit()
    finally:
        conn.close()
    print(f"Step 4: Seeded 3 Chapters for every Subject.")

    # 5. Seed Questions for each Chapter
    # 10 questions per chapter: 3 MCQ, 2 T/F, 3 Short, 2 Long
    print("Step 5: Seeding 10 questions per chapter (this may take a moment)...")
    questions_count = 0
    for ch_id in chapter_ids:
        # MCQs
        for i in range(1, 4):
            db.add_question(ch_id, type_ids["MCQ"], f"Sample MCQ Question {i} for Chapter {ch_id}?", 1, "Easy")
        # T/F
        for i in range(1, 3):
            db.add_question(ch_id, type_ids["True/False"], f"Sample T/F Question {i} for Chapter {ch_id}. True or False?", 1, "Medium")
        # Short
        for i in range(1, 4):
            db.add_question(ch_id, type_ids["Short Answer"], f"Explain concept {i} in Chapter {ch_id} briefly.", 3, "Medium")
        # Long
        for i in range(1, 3):
            db.add_question(ch_id, type_ids["Long Answer"], f"Describe the detailed implications of {i} in Chapter {ch_id}.", 5, "Hard")
        questions_count += 10

    print(f"Final Step: Successfully seeded {questions_count} total questions.")
    print("--- Seeding Complete ---")

if __name__ == "__main__":
    seed_database()
