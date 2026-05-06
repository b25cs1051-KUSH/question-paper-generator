import sqlite3
import hashlib
import os
import sys
import shutil

def get_base_path():
    """Returns the base path: the folder where the .exe or .py file is located."""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller executable
        return os.path.dirname(sys.executable)
    else:
        # Running as a standard Python script
        # Go up one level from the database folder to reach the project root
        return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    PyInstaller stores data files in sys._MEIPASS at runtime.
    """
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(get_base_path(), relative_path)

class DatabaseManager:
    """
    Manages all database operations for the Question Paper Generator.
    Ensures persistence by placing the DB next to the executable.
    """

    def __init__(self):
        # The persistent DB file should live next to the .exe for the user
        self.db_path = os.path.join(get_base_path(), "app_data.db")
        
        # The schema and starter DB (if any) are bundled as resources
        self.schema_path = get_resource_path(os.path.join("database", "schema.sql"))
        self.bundled_db_path = get_resource_path(os.path.join("database", "app_data.db"))
        
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """
        Ensures the persistent database exists. 
        If it doesn't, we copy the pre-seeded one from the bundle or create a new one.
        """
        if not os.path.exists(self.db_path):
            if os.path.exists(self.bundled_db_path):
                # Copy the pre-seeded database from the bundle to the local user directory
                shutil.copy2(self.bundled_db_path, self.db_path)
            else:
                # If no bundled DB, initialize from schema
                self._initialize_database()

    def _get_connection(self):
        """Returns a sqlite3 connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_database(self):
        """Initializes the database using the schema.sql file."""
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

    # --- Standards ---
    def get_standards(self):
        query = "SELECT id, name FROM standards ORDER BY name ASC"
        conn = self._get_connection()
        try:
            return [dict(row) for row in conn.execute(query).fetchall()]
        finally:
            conn.close()

    def add_standard(self, name):
        query = "INSERT INTO standards (name) VALUES (?)"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (name,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def delete_standard(self, standard_id):
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM standards WHERE id = ?", (standard_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    # --- Subjects ---
    def get_subjects(self, standard_id):
        query = "SELECT id, name FROM subjects WHERE standard_id = ? ORDER BY name ASC"
        conn = self._get_connection()
        try:
            return [dict(row) for row in conn.execute(query, (standard_id,)).fetchall()]
        finally:
            conn.close()

    def add_subject(self, standard_id, name):
        query = "INSERT INTO subjects (standard_id, name) VALUES (?, ?)"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (standard_id, name))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def delete_subject(self, subject_id):
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    # --- Chapters ---
    def get_chapters(self, subject_id):
        query = "SELECT id, name, chapter_number FROM chapters WHERE subject_id = ? ORDER BY chapter_number ASC"
        conn = self._get_connection()
        try:
            return [dict(row) for row in conn.execute(query, (subject_id,)).fetchall()]
        finally:
            conn.close()

    def add_chapter(self, subject_id, name, chapter_number=None):
        query = "INSERT INTO chapters (subject_id, name, chapter_number) VALUES (?, ?, ?)"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (subject_id, name, chapter_number))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def update_chapter_name(self, chapter_id, new_name):
        conn = self._get_connection()
        try:
            conn.execute("UPDATE chapters SET name = ? WHERE id = ?", (new_name, chapter_id))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def delete_chapter(self, chapter_id):
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    # --- Question Types ---
    def get_question_types(self):
        query = "SELECT id, name FROM question_types ORDER BY id ASC"
        conn = self._get_connection()
        try:
            return [dict(row) for row in conn.execute(query).fetchall()]
        finally:
            conn.close()

    def get_type_id_by_name(self, type_name):
        """Resolves a type name (e.g. 'MCQ') to its ID."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT id FROM question_types WHERE name = ?", (type_name.strip(),)).fetchone()
            return row['id'] if row else None
        finally:
            conn.close()

    def add_question_type(self, name):
        """Adds a new question type manually."""
        query = "INSERT INTO question_types (name) VALUES (?)"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (name.strip(),))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def get_or_create_type_id(self, type_name):
        """Resolves a type name to its ID, creating it if it doesn't exist."""
        type_name = type_name.strip()
        if not type_name: return None
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Try to get existing
            row = cursor.execute("SELECT id FROM question_types WHERE name = ?", (type_name,)).fetchone()
            if row:
                return row['id']
            
            # Create new
            cursor.execute("INSERT INTO question_types (name) VALUES (?)", (type_name,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Handle race condition
            row = cursor.execute("SELECT id FROM question_types WHERE name = ?", (type_name,)).fetchone()
            return row['id'] if row else None
        finally:
            conn.close()

    # --- Questions ---
    def get_questions_for_chapter(self, chapter_id):
        query = """
            SELECT q.*, qt.name as type_name 
            FROM questions q 
            JOIN question_types qt ON q.type_id = qt.id 
            WHERE q.chapter_id = ?
        """
        conn = self._get_connection()
        try:
            return [dict(row) for row in conn.execute(query, (chapter_id,)).fetchall()]
        finally:
            conn.close()

    def add_question(self, chapter_id, type_id, content, marks, difficulty="Medium"):
        """Adds a question to a chapter. Returns lastrowid or None on duplicate."""
        try:
            chapter_id = int(chapter_id)
            type_id = int(type_id)
            marks = int(marks)
        except (ValueError, TypeError):
            return None

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
            return None
        finally:
            conn.close()

    def delete_question(self, question_id):
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def check_question_availability(self, chapter_ids, type_id):
        if not chapter_ids:
            return 0
        placeholders = ', '.join(['?'] * len(chapter_ids))
        query = f"SELECT COUNT(*) as count FROM questions WHERE chapter_id IN ({placeholders}) AND type_id = ?"
        params = list(chapter_ids) + [type_id]
        conn = self._get_connection()
        try:
            result = conn.execute(query, params).fetchone()
            return result['count'] if result else 0
        finally:
            conn.close()

    # --- Templates ---
    def save_template(self, standard_id, subject_id, name, config_json, total_marks):
        query = "INSERT INTO templates (standard_id, subject_id, name, config_json, total_marks) VALUES (?, ?, ?, ?, ?)"
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Note: schema.sql needs config_json column if we use it, 
            # or we store sections separately as per original schema. 
            # I will update schema.sql to include config_json for simplicity as per app.py.
            cursor.execute(query, (standard_id, subject_id, name, config_json, total_marks))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_templates_by_std_sub(self, standard_id, subject_id):
        query = "SELECT id, name, config_json, total_marks FROM templates WHERE standard_id = ? AND subject_id = ?"
        conn = self._get_connection()
        try:
            return [dict(row) for row in conn.execute(query, (standard_id, subject_id)).fetchall()]
        finally:
            conn.close()

    def delete_template(self, template_id):
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
