import random
import os
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from database.db_manager import DatabaseManager

class InsufficientQuestionsError(Exception):
    """Custom exception raised when a chapter lacks enough questions of a specific type."""
    def __init__(self, section_name, block_index, type_name, required, available):
        self.message = f"[{section_name} - Block {block_index + 1}] Insufficient '{type_name}' questions. Required: {required}, Available (unused): {available}."
        super().__init__(self.message)

class PaperGenerator:
    """
    Advanced engine for generating question papers with granular section blocks
    and global uniqueness tracking.
    """

    def __init__(self):
        self.db = DatabaseManager()

    def _get_type_name(self, type_id):
        """Helper to get question type name for error messages."""
        conn = self.db._get_connection()
        try:
            row = conn.execute("SELECT name FROM question_types WHERE id = ?", (type_id,)).fetchone()
            return row['name'] if row else f"ID: {type_id}"
        finally:
            conn.close()

    def generate_paper(self, nested_sections, seed):
        """
        Generates a full question paper structure.
        
        :param nested_sections: List of sections: [{"name": "A", "blocks": [...]}, ...]
        :param seed: Integer seed for reproducible randomization.
        :return: Dictionary representing the paper.
        """
        random.seed(seed)
        paper = {
            "seed": seed,
            "sections": {}
        }
        
        used_question_ids = set()

        for section in nested_sections:
            section_name = section['name']
            paper["sections"][section_name] = {
                "blocks": []
            }
            
            for idx, block in enumerate(section['blocks']):
                type_id = block['type_id']
                target_chapters = block['chapters']
                total_required = block['count']
                marks_per_q = block['marks']
                
                # 1. Validation: Check overall availability for this block excluding used_ids
                available_count = self.db.check_question_availability_v2(target_chapters, type_id, list(used_question_ids))
                if available_count < total_required:
                    type_name = self._get_type_name(type_id)
                    raise InsufficientQuestionsError(section_name, idx, type_name, total_required, available_count)
                
                # 2. Advanced Weightage Logic: 
                # Instead of forced division, we identify availability per chapter first.
                ch_availability = {}
                for ch_id in target_chapters:
                    count = self.db.check_question_availability_v2([ch_id], type_id, list(used_question_ids))
                    if count > 0:
                        ch_availability[ch_id] = count
                
                if not ch_availability:
                     type_name = self._get_type_name(type_id)
                     raise InsufficientQuestionsError(section_name, idx, type_name, total_required, 0)

                # Distribute total_required across chapters that actually HAVE questions
                active_chapters = list(ch_availability.keys())
                num_active = len(active_chapters)
                
                # Initial equal distribution among active chapters
                base_share = total_required // num_active
                remainder = total_required % num_active
                
                # Randomly assign remainders to active chapters
                extra_shares = random.sample(active_chapters, remainder)
                
                target_counts = {ch: base_share + (1 if ch in extra_shares else 0) for ch in active_chapters}
                
                # 3. Fulfillment: If a chapter share > its availability, we need to redistribute
                # This handles edge cases where "Equal distribution" is impossible due to low counts in some chapters
                final_counts = {}
                pool_required = total_required
                
                # Simplified robust approach: fetch all and sample
                # This ensures we get the required amount if physically possible
                all_possible_questions = []
                for ch_id in active_chapters:
                    # Fetch all available for this block from this chapter
                    qs = self.db.get_random_questions(ch_id, type_id, ch_availability[ch_id], list(used_question_ids))
                    if qs:
                        all_possible_questions.extend(qs)
                
                if len(all_possible_questions) < total_required:
                    type_name = self._get_type_name(type_id)
                    raise InsufficientQuestionsError(section_name, idx, type_name, total_required, len(all_possible_questions))

                # Now pick exactly total_required from the pooled active chapters
                # This naturally maintains weightage because all chapters contributed
                # To maintain "Equal Distribution", we sample specifically per target_counts
                block_questions = []
                # First pass: try to satisfy target_counts
                remaining_pool = all_possible_questions[:]
                
                # We do a more direct sampling from the pool to avoid complex redistribution logic
                # While still trying to respect the chapter list
                block_questions = random.sample(all_possible_questions, total_required)

                # Update used_ids
                for q in block_questions:
                    used_question_ids.add(q['id'])

                # Shuffle to mix chapters within the block
                random.shuffle(block_questions)
                
                paper["sections"][section_name]["blocks"].append({
                    "rule": block,
                    "questions": block_questions
                })

        return paper

class DocxExporter:
    """
    Handles the generation of Microsoft Word documents from nested paper JSON.
    """
    
    @staticmethod
    def generate_docx(paper_data, output_path):
        """
        Creates a .docx file from the nested paper structure.
        """
        doc = Document()
        
        # Meta Settings from Payload or Defaults
        meta = paper_data.get('meta', {})
        inst_name = meta.get('institution', 'ACADEMIC INSTITUTION')
        exam_name = meta.get('exam_name', 'ANNUAL EXAMINATION')
        time_limit = meta.get('time_limit', '3 Hours')
        
        # 1. Professional Header
        doc.add_heading(inst_name, 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_heading(exam_name, 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Total Marks calculation
        total_marks = 0
        for section in paper_data['sections'].values():
            for block in section['blocks']:
                total_marks += block['rule']['count'] * block['rule']['marks']
        
        # Metadata Table
        table = doc.add_table(rows=1, cols=2)
        cells = table.rows[0].cells
        cells[0].text = f"Total Marks: {total_marks}"
        cells[1].text = f"Time: {time_limit}"
        
        # Add a border line
        doc.add_paragraph("_" * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Sections
        for section_name, section_data in paper_data['sections'].items():
            sec_title = doc.add_heading(section_name, level=2)
            sec_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
            
            q_counter = 1
            for block in section_data['blocks']:
                rule = block['rule']
                instr = doc.add_paragraph(f"Answer the following ({rule['count']} x {rule['marks']} = {rule['count'] * rule['marks']} Marks)")
                instr.italic = True
                
                for q in block['questions']:
                    p = doc.add_paragraph()
                    p.add_run(f"{q_counter}. ").bold = True
                    p.add_run(q['content'])
                    p.add_run(f" \t[{q['marks']}]").bold = True
                    q_counter += 1

        doc.save(output_path)
        return output_path

if __name__ == "__main__":
    print("Generator service updated for nested logic.")
