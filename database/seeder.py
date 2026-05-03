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
    subjects = ["English", "Social Studies", "Economics", "Business Administration", "Accounts", "SS"]
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
    # Store chapters per subject for easier question/template seeding
    subject_chapters = {} # sub_id -> [ch_id, ...]
    conn = db._get_connection()
    try:
        cursor = conn.cursor()
        for key, sub_id in subject_map.items():
            subject_chapters[sub_id] = []
            for i in range(1, 4):
                cursor.execute("INSERT OR IGNORE INTO chapters (subject_id, name, chapter_number) VALUES (?, ?, ?)", 
                               (sub_id, f"Chapter {i}: Introduction to {key[1]}", i))
                cursor.execute("SELECT id FROM chapters WHERE subject_id = ? AND chapter_number = ?", (sub_id, i))
                ch_id = cursor.fetchone()[0]
                chapter_ids.append(ch_id)
                subject_chapters[sub_id].append(ch_id)
        conn.commit()
    finally:
        conn.close()
    print(f"Step 4: Seeded 3 Chapters for every Subject.")

    # 5. Seed Questions for each Chapter
    # 3 questions of EACH type per subject (1 per chapter)
    print("Step 5: Seeding 3 questions of each type per subject...")
    questions_count = 0
    for sub_id, ch_ids in subject_chapters.items():
        for qt_name, qt_id in type_ids.items():
            for i, ch_id in enumerate(ch_ids):
                # We have 3 chapters and want 3 questions per type per subject.
                # So we add 1 question of each type to each chapter.
                db.add_question(ch_id, qt_id, f"Sample {qt_name} Question for {qt_name} in Chapter {ch_id}?", 
                                1 if qt_name in ["MCQ", "True/False"] else (3 if qt_name == "Short Answer" else 5), 
                                "Easy" if qt_name == "MCQ" else "Medium")
                questions_count += 1

    print(f"Final Step: Successfully seeded {questions_count} total questions.")

    # 6. Seed Sample Templates
    print("Step 6: Seeding sample templates for every subject...")
    import json
    for (std_name, sub_name), sub_id in subject_map.items():
        std_id = standard_ids[std_name]
        sub_ch_ids = subject_chapters[sub_id]

        # Sample General Template
        config = [
            {
                "name": "Section A",
                "blocks": [
                    {"type_id": type_ids["MCQ"], "chapters": sub_ch_ids, "count": 2, "marks": 1},
                    {"type_id": type_ids["True/False"], "chapters": sub_ch_ids, "count": 1, "marks": 1}
                ]
            },
            {
                "name": "Section B",
                "blocks": [
                    {"type_id": type_ids["Short Answer"], "chapters": sub_ch_ids, "count": 1, "marks": 3}
                ]
            }
        ]
        db.save_template(std_id, sub_id, f"Standard {sub_name} Pattern", json.dumps(config), 6)

    print("--- Seeding Complete ---")

if __name__ == "__main__":
    seed_database()
