from database.db_manager import DatabaseManager
import json
import sqlite3
import os

def seed_perfect_data():
    # Ensure database is clean
    if os.path.exists("database/app_data.db"):
        os.remove("database/app_data.db")
    
    db = DatabaseManager()
    print("--- Starting Perfect Database Seeding ---")

    # 1. Seed Question Types
    question_types = ["MCQ", "True/False", "Short Answer", "Long Answer"]
    type_ids = {}
    conn = db._get_connection()
    try:
        for qt in question_types:
            cursor = conn.execute("INSERT INTO question_types (name) VALUES (?)", (qt,))
            type_ids[qt] = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    print(f"Seeded {len(question_types)} Question Types.")

    # 2. Seed Standards
    standards_list = ["Standard 8", "Standard 9", "Standard 10", "Standard 11", "Standard 12"]
    std_map = {}
    for std in standards_list:
        std_id = db.add_standard(std)
        std_map[std] = std_id
    print(f"Seeded Standards: {', '.join(standards_list)}.")

    # 3. Subjects and Chapters Data
    curriculum = {
        "Standard 10": {
            "Mathematics": [
                "Real Numbers", "Polynomials", "Quadratic Equations", 
                "Arithmetic Progressions", "Triangles", "Coordinate Geometry"
            ],
            "Science": [
                "Chemical Reactions", "Acids, Bases and Salts", "Metals and Non-metals", 
                "Life Processes", "Control and Coordination", "Light Reflection and Refraction"
            ]
        },
        "Standard 12": {
            "Physics": [
                "Electric Charges and Fields", "Electrostatic Potential", 
                "Current Electricity", "Moving Charges", "Magnetism and Matter"
            ],
            "Chemistry": [
                "Solutions", "Electrochemistry", "Chemical Kinetics", 
                "d-and f-Block Elements", "Coordination Compounds"
            ]
        }
    }

    # Helper for generating questions
    def get_sample_questions(ch_name, type_name):
        if type_name == "MCQ":
            return [
                f"Which of the following best describes the core concept of {ch_name}?",
                f"In the context of {ch_name}, what does the constant 'k' typically represent?",
                f"Identify the SI unit used for measurements in {ch_name}."
            ]
        elif type_name == "True/False":
            return [
                f"The fundamental theorem of {ch_name} states that all variables are constant.",
                f"In {ch_name}, the rate of change is always inversely proportional to time."
            ]
        elif type_name == "Short Answer":
            return [
                f"Define the principle of superposition as applied to {ch_name}.",
                f"State the three main laws governing {ch_name}.",
                f"Explain the relationship between pressure and volume in {ch_name}."
            ]
        elif type_name == "Long Answer":
            return [
                f"Derive the general equation for {ch_name} from first principles and discuss its applications.",
                f"Compare and contrast the different methodologies used to analyze {ch_name} in modern research."
            ]
        return []

    # 4. Seed Subjects, Chapters, and Questions
    for std_name, subjects in curriculum.items():
        std_id = std_map[std_name]
        for sub_name, chapters in subjects.items():
            sub_id = db.add_subject(std_id, sub_name)
            for i, ch_name in enumerate(chapters):
                ch_id = db.add_chapter(sub_id, ch_name, i + 1)
                
                # Add Questions for each type
                for qt_name, qt_id in type_ids.items():
                    qs = get_sample_questions(ch_name, qt_name)
                    marks = 1 if qt_name in ["MCQ", "True/False"] else (3 if qt_name == "Short Answer" else 5)
                    difficulty = "Easy" if qt_name == "MCQ" else ("Hard" if qt_name == "Long Answer" else "Medium")
                    
                    for content in qs:
                        db.add_question(ch_id, qt_id, content, marks, difficulty)
    
    print("Seeded Subjects, Chapters, and Questions for Standard 10 & 12.")

    # 5. Seed Templates (Updated Format: No Chapters Stored)
    # We will seed for Standard 10 Mathematics as a primary example
    conn = db._get_connection()
    try:
        row = conn.execute(
            "SELECT s.id FROM subjects s JOIN standards st ON s.standard_id = st.id WHERE st.name = 'Standard 10' AND s.name = 'Mathematics'"
        ).fetchone()
        std10_math_id = row[0]
    finally:
        conn.close()
    std10_id = std_map["Standard 10"]

    templates = [
        {
            "name": "Mid-Term Assessment",
            "total_marks": 25,
            "config": [
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
                        {"type_id": type_ids["Short Answer"], "count": 5, "marks": 3}
                    ]
                }
            ]
        },
        {
            "name": "Final Board Pattern",
            "total_marks": 80,
            "config": [
                {
                    "name": "Section A",
                    "blocks": [
                        {"type_id": type_ids["MCQ"], "count": 20, "marks": 1}
                    ]
                },
                {
                    "name": "Section B",
                    "blocks": [
                        {"type_id": type_ids["Short Answer"], "count": 10, "marks": 3}
                    ]
                },
                {
                    "name": "Section C",
                    "blocks": [
                        {"type_id": type_ids["Long Answer"], "count": 6, "marks": 5}
                    ]
                }
            ]
        }
    ]

    for t in templates:
        db.save_template(std10_id, std10_math_id, t["name"], json.dumps(t["config"]), t["total_marks"])

    print("Seeded Sample Templates for Standard 10 Mathematics.")
    print("--- Perfect Seeding Complete ---")

if __name__ == "__main__":
    seed_perfect_data()
