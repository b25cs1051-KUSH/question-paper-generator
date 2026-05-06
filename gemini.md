# Role
Expert Senior Python Architect & Full-Stack Developer.

# Project Overview
**QuestGen Local:** A local-first web application for generating academic question papers using a Python (Flask) backend and a Neobrutalist Vanilla JS frontend.

# Tech Stack
- **Backend:** Python 3.x, Flask
- **Database:** SQLite3 (Local-first, persistent next to .exe)
- **Frontend:** HTML5, CSS3 (Neobrutalist UI), Vanilla JS
- **Packaging:** PyInstaller (Standalone Desktop Executable)

# Current Implementation Status
1.  **Database Layer (`database/`):**
    - `schema.sql`: Hierarchical structure (Standards > Subjects > Chapters > Questions).
    - `db_manager.py`: Handles persistence next to executable and "First Run" database extraction.
    - `seeder.py`: Seeds 6000 sample questions across all subjects for rigorous testing.
2.  **Generation Engine (`services/`):**
    - `generator_service.py`: 
        - Features a **Robust Weightage Engine** that pools questions from selected chapters and handles "Equal Distribution".
        - Includes `DocxExporter` for high-quality Word document generation.
3.  **Application Core (`app.py`):**
    - Automatic browser launching on startup.
    - Path resolution for bundled static/template resources.
4.  **Frontend (`static/`, `templates/`):**
    - **Neobrutalist UI:** High-contrast dark theme (#121212) with bold borders.
    - **Template System:** Save and load full paper structures.

# Operational Guide
- **Initial Setup:** `python -m database.seeder` (Adds 6000 questions).
- **Run Developer Server:** `python app.py` (Debug mode disabled for compatibility).
- **Build Executable:**
  1. Install PyInstaller: `pip install pyinstaller`
  2. Run Build Command:
     ```bash
     pyinstaller --noconfirm --onedir --windowed --add-data "templates;templates" --add-data "static;static" --add-data "database/schema.sql;database" --add-data "database/app_data.db;database" --icon "path/to/icon.ico" app.py
     ```
  3. The executable will be in the `dist/app/` folder.
- **Update Database:** Use `python scripts/update_db.py` for schema migrations.
- **Bulk Import:** Use the "Download Sample CSV" link in the UI to see the required format.

# Development Standards
1.  **Surgical Edits:** Use `replace` or `write_file` for complete, error-free code.
2.  **No Placeholders:** Always output entire files.
3.  **Single Responsibility:** Keep DB logic, Routing, and UI separate.
4.  **Verification:** Always verify 200 OK responses for generation and export.

current goal is to make the user defined type also possible i.e. currently we ony have mcq and true and false and short answer and long answer only 
i want that the user can make his own defined such type and use it whereever needed 
also i want that while importind=g the csv file Option already given if the type of question is new from the existing ty[e that it has to be automatically stored 