# Role
Expert Senior Python Architect & Full-Stack Developer.

# Project Overview
**QuestGen Local:** A local-first web application for generating academic question papers using a Python (Flask) backend and a Neobrutalist Vanilla JS frontend.

# Tech Stack
- **Backend:** Python 3.x, Flask
- **Database:** SQLite3 (Pure SQL, no ORM)
- **Frontend:** HTML5, CSS3 (Glassmorphism), Vanilla JS
- **Export:** `python-docx` (Professional Word document generation)

# Current Implementation Status
1.  **Database Layer (`database/`):**
    - `schema.sql`: Hierarchical structure (Standards > Subjects > Chapters > Questions).
    - `db_manager.py`: Handles all CRUD, nested question availability checks, and template persistence.
    - `seeder.py`: Seeds 6000 sample questions across all subjects for rigorous testing.
2.  **Generation Engine (`services/`):**
    - `generator_service.py`: 
        - Features a **Robust Weightage Engine** that pools questions from selected chapters and handles "Equal Distribution" even if some chapters are empty.
        - Includes `DocxExporter` for high-quality Word document generation with professional headers.
3.  **Application Core (`app.py`):**
    - REST API for Standards, Subjects, Chapters, Templates, and Generation.
    - Error handling with traceback logging for local debugging.
    - CSV Stream processing for bulk question imports.
4.  **Frontend (`static/`, `templates/`):**
    - **Neobrutalist UI:** High-contrast dark theme (#121212) with bold borders and glassmorphism.
    - **Dynamic Builder:** Users can create Sections (A, B, C) and nested "Question Blocks" with per-block chapter selection.
    - **Template System:** Save and load full paper structures (Sections, Blocks, Chapters).

# Operational Guide
- **Initial Setup:** `python -m database.seeder` (Adds 6000 questions).
- **Run Server:** `python app.py` (Runs on `http://127.0.0.1:5000`).
- **Update Database:** Use `python scripts/update_db.py` for schema migrations.
- **Bulk Import:** Use the "Download Sample CSV" link in the UI to see the required format.

# Development Standards
1.  **Surgical Edits:** Use `replace` or `write_file` for complete, error-free code.
2.  **No Placeholders:** Always output entire files.
3.  **Single Responsibility:** Keep DB logic, Routing, and UI separate.
4.  **Verification:** Always verify 200 OK responses for generation and export.
