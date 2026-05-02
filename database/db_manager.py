import sqlite3
import hashlib
import os

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
