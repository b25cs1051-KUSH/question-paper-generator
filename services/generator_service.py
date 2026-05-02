import random
from database.db_manager import DatabaseManager

class InsufficientQuestionsError(Exception):
    """Custom exception raised when a chapter lacks enough questions of a specific type."""
    def __init__(self, chapter_name, type_name, required, available):
        self.message = f"Chapter '{chapter_name}' has insufficient '{type_name}' questions. Required: {required}, Available: {available}."
        super().__init__(self.message)

class PaperGenerator:
    """
    Core engine for generating question papers based on templates and weights.
    Ensures fair distribution across chapters and supports seeded randomization.
    """

    def __init__(self):
        self.db = DatabaseManager()

    def _get_chapter_name(self, chapter_id):
        """Helper to get chapter name for error messages."""
        conn = self.db._get_connection()
        try:
            row = conn.execute("SELECT name FROM chapters WHERE id = ?", (chapter_id,)).fetchone()
            return row['name'] if row else f"ID: {chapter_id}"
        finally:
            conn.close()

    def _get_type_name(self, type_id):
        """Helper to get question type name for error messages."""
        conn = self.db._get_connection()
        try:
            row = conn.execute("SELECT name FROM question_types WHERE id = ?", (type_id,)).fetchone()
            return row['name'] if row else f"ID: {type_id}"
        finally:
            conn.close()

    def generate_paper(self, selected_chapters, template_rules, seed, manual_questions=None):
        """
        Generates a full question paper structure.
        
        :param selected_chapters: List of chapter IDs to pull questions from.
        :param template_rules: List of section rules: [{'section_name': 'A', 'type_id': 1, 'count': 5, 'marks': 1}, ...]
        :param seed: Integer seed for reproducible randomization.
        :param manual_questions: List of pre-selected question IDs (not implemented in this turn's logic but reserved).
        :return: Dictionary representing the paper.
        """
        random.seed(seed)
        paper = {
            "seed": seed,
            "sections": {}
        }

        # Reserve manual questions (if any)
        # For this version, we assume manual_questions are already categorized by section.
        # But per requirements, we'll focus on the random engine logic first.
        
        for rule in template_rules:
            section_name = rule['section_name']
            type_id = rule['type_id']
            total_required = rule['count']
            
            # 1. Weightage Logic: Divide total count by number of chapters
            num_chapters = len(selected_chapters)
            base_count = total_required // num_chapters
            remainder = total_required % num_chapters
            
            # 2. Remainder Handling: Randomly pick chapters to get the extra questions
            # Using the seed ensures this choice is reproducible
            extra_chapters = random.sample(selected_chapters, remainder)
            
            section_questions = []
            
            for ch_id in selected_chapters:
                count_for_this_chapter = base_count + (1 if ch_id in extra_chapters else 0)
                
                if count_for_this_chapter == 0:
                    continue

                # 3. Validation: Check availability
                available_count = self.db.check_question_availability([ch_id], type_id)
                if available_count < count_for_this_chapter:
                    ch_name = self._get_chapter_name(ch_id)
                    type_name = self._get_type_name(type_id)
                    raise InsufficientQuestionsError(ch_name, type_name, count_for_this_chapter, available_count)
                
                # 4. Fetch Questions
                conn = self.db._get_connection()
                try:
                    query = "SELECT * FROM questions WHERE chapter_id = ? AND type_id = ?"
                    cursor = conn.execute(query, (ch_id, type_id))
                    all_questions = [dict(row) for row in cursor.fetchall()]
                    
                    # Randomly pick from available pool using the seed
                    selected = random.sample(all_questions, count_for_this_chapter)
                    section_questions.extend(selected)
                finally:
                    conn.close()

            # Shuffle the section questions to mix chapters together
            random.shuffle(section_questions)
            
            paper["sections"][section_name] = {
                "rule": rule,
                "questions": section_questions
            }

        return paper

if __name__ == "__main__":
    # Small test if run directly
    gen = PaperGenerator()
    try:
        # Assuming chapter IDs 1, 2, 3 and type_id 1 (MCQ) exist from seeder
        test_rules = [{'section_name': 'Section A', 'type_id': 1, 'count': 5, 'marks': 1}]
        paper = gen.generate_paper([1, 2, 3], test_rules, 42)
        print("Paper generated successfully with", len(paper['sections']['Section A']['questions']), "questions.")
    except Exception as e:
        print(f"Test failed: {e}")
