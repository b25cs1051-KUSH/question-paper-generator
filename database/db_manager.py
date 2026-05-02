import sqlite3
import hashlib
import os
import random

class DatabaseManager:
    """
    Manages all database operations for the Question Paper Generator.
    Follows a singleton-like pattern or direct instantiation for local SQLite access.
    """

    def __init__(self, db_path="database/app_data.db", schema_path="database/schema.sql"):
        self.db_path = db_path
        self.schema_path = schema_path
        self._initialize_database()

    def _get_connection(self):
        """Returns a sqlite3 connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_database(self):
        """Initializes the database using the schema.sql file if it doesn't exist."""
        if not os.path.exists(self.db_path):
            with open(self.schema_path, 'r') as f:
                schema_script = f.read()
            
            conn = self._get_connection()
            try:
                conn.executescript(schema_script)
                conn.commit()
            finally:
                conn.close()

    def generate_content_hash(self, content: str) -> str:
        """
        Generates a SHA-256 hash of the question content.
        Used to prevent duplicate entries.
        """
        return hashlib.sha256(content.strip().lower().encode('utf-8')).hexdigest()

    def add_question(self, chapter_id, type_id, content, marks, difficulty="Medium"):
        """
        Adds a new question to the database.
        Returns the ID of the inserted question or None if it's a duplicate.
        """
        content_hash = self.generate_content_hash(content)
        query = """
            INSERT INTO questions (chapter_id, type_id, content, marks, difficulty, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (chapter_id, type_id, content, marks, difficulty, content_hash))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Likely a UNIQUE constraint failure on content_hash
            return None
        finally:
            conn.close()

    def get_standards(self):
        """Retrieves all available standards."""
        query = "SELECT id, name FROM standards ORDER BY name ASC"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_subjects(self, standard_id):
        """Retrieves all subjects for a specific standard."""
        query = "SELECT id, name FROM subjects WHERE standard_id = ? ORDER BY name ASC"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (standard_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_question_types(self):
        """Retrieves all available question types."""
        query = "SELECT id, name FROM question_types ORDER BY id ASC"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_chapters(self, subject_id):
        """
        Retrieves all chapters associated with a specific subject.
        """
        query = "SELECT id, name, chapter_number FROM chapters WHERE subject_id = ? ORDER BY chapter_number ASC"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (subject_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_chapter_name(self, chapter_id, new_name):
        """Updates the name of a specific chapter."""
        query = "UPDATE chapters SET name = ? WHERE id = ?"
        conn = self._get_connection()
        try:
            conn.execute(query, (new_name, chapter_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating chapter: {e}")
            return False
        finally:
            conn.close()

    def add_chapter(self, subject_id, name, chapter_number=None):
        """Adds a new chapter to a subject."""
        query = "INSERT INTO chapters (subject_id, name, chapter_number) VALUES (?, ?, ?)"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (subject_id, name, chapter_number))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error adding chapter: {e}")
            return None
        finally:
            conn.close()

    def delete_chapter(self, chapter_id):
        """Deletes a chapter and all its questions."""
        query = "DELETE FROM chapters WHERE id = ?"
        conn = self._get_connection()
        try:
            conn.execute(query, (chapter_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting chapter: {e}")
            return False
        finally:
            conn.close()

    def add_standard(self, name):
        """Adds a new academic standard."""
        query = "INSERT INTO standards (name) VALUES (?)"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (name,))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error adding standard: {e}")
            return None
        finally:
            conn.close()

    def delete_standard(self, standard_id):
        """Deletes a standard and all its subjects/chapters."""
        query = "DELETE FROM standards WHERE id = ?"
        conn = self._get_connection()
        try:
            conn.execute(query, (standard_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting standard: {e}")
            return False
        finally:
            conn.close()

    def add_subject(self, standard_id, name):
        """Adds a new subject to a standard."""
        query = "INSERT INTO subjects (standard_id, name) VALUES (?, ?)"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (standard_id, name))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error adding subject: {e}")
            return None
        finally:
            conn.close()

    def delete_subject(self, subject_id):
        """Deletes a subject and all its chapters."""
        query = "DELETE FROM subjects WHERE id = ?"
        conn = self._get_connection()
        try:
            conn.execute(query, (subject_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting subject: {e}")
            return False
        finally:
            conn.close()

    def save_template(self, standard_id, subject_id, name, config_json, total_marks):
        """Saves a paper configuration template."""
        query = """
            INSERT INTO templates (standard_id, subject_id, name, config_json, total_marks)
            VALUES (?, ?, ?, ?, ?)
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (standard_id, subject_id, name, config_json, total_marks))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error saving template: {e}")
            return None
        finally:
            conn.close()

    def get_templates(self, subject_id):
        """Retrieves all saved templates for a specific subject."""
        query = "SELECT * FROM templates WHERE subject_id = ? ORDER BY id DESC"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (subject_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_template(self, template_id):
        """Deletes a template."""
        query = "DELETE FROM templates WHERE id = ?"
        conn = self._get_connection()
        try:
            conn.execute(query, (template_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting template: {e}")
            return False
        finally:
            conn.close()

    def get_questions_for_chapter(self, chapter_id):
        """Retrieves all questions for a specific chapter, including type names."""
        query = """
            SELECT q.*, qt.name as type_name 
            FROM questions q 
            JOIN question_types qt ON q.type_id = qt.id 
            WHERE q.chapter_id = ? 
            ORDER BY q.type_id ASC, q.id DESC
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (chapter_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_question(self, question_id):
        """Deletes a specific question from the database."""
        query = "DELETE FROM questions WHERE id = ?"
        conn = self._get_connection()
        try:
            conn.execute(query, (question_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting question: {e}")
            return False
        finally:
            conn.close()

    def check_question_availability_v2(self, chapter_ids, type_id, exclude_ids=None):
        """
        Checks availability while excluding already used question IDs.
        """
        if not chapter_ids:
            return 0
            
        exclude_ids = exclude_ids or []
        placeholders_ch = ', '.join(['?'] * len(chapter_ids))
        
        query = f"""
            SELECT COUNT(*) as count 
            FROM questions 
            WHERE chapter_id IN ({placeholders_ch}) AND type_id = ?
        """
        params = list(chapter_ids) + [type_id]

        if exclude_ids:
            placeholders_ex = ', '.join(['?'] * len(exclude_ids))
            query += f" AND id NOT IN ({placeholders_ex})"
            params.extend(exclude_ids)
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result['count'] if result else 0
        finally:
            conn.close()

    def get_random_questions(self, chapter_id, type_id, count, exclude_ids=None):
        """
        Fetches a random set of questions for a specific chapter and type, excluding used IDs.
        """
        exclude_ids = exclude_ids or []
        query = "SELECT * FROM questions WHERE chapter_id = ? AND type_id = ?"
        params = [chapter_id, type_id]

        if exclude_ids:
            placeholders = ', '.join(['?'] * len(exclude_ids))
            query += f" AND id NOT IN ({placeholders})"
            params.extend(exclude_ids)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            all_available = [dict(row) for row in cursor.fetchall()]
            
            if len(all_available) < count:
                return None # Should be caught by availability check earlier
                
            return random.sample(all_available, count)
        finally:
            conn.close()

    def check_question_availability(self, chapter_ids, type_id):
        """
        Checks the total count of available questions for a given type across multiple chapters.
        Crucial for UI validation to ensure the paper can be generated.
        """
        if not chapter_ids:
            return 0
            
        placeholders = ', '.join(['?'] * len(chapter_ids))
        query = f"""
            SELECT COUNT(*) as count 
            FROM questions 
            WHERE chapter_id IN ({placeholders}) AND type_id = ?
        """
        params = list(chapter_ids) + [type_id]
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result['count'] if result else 0
        finally:
            conn.close()

if __name__ == "__main__":
    # Quick sanity check
    db = DatabaseManager()
    print("Database initialized successfully.")
