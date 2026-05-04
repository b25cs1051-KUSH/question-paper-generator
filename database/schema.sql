-- database/schema.sql

-- Enable Foreign Key constraints
PRAGMA foreign_keys = ON;

-- Standards (8-12)
CREATE TABLE IF NOT EXISTS standards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE -- e.g., 'Standard 8', 'Standard 12'
);

-- Subjects
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    standard_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (standard_id) REFERENCES standards(id) ON DELETE CASCADE,
    UNIQUE(standard_id, name)
);

-- Chapters
CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    chapter_number INTEGER,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    UNIQUE(subject_id, name)
);

-- Question Types (MCQ, True/False, Short, Long, etc.)
CREATE TABLE IF NOT EXISTS question_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Questions
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    type_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    marks INTEGER NOT NULL,
    difficulty TEXT CHECK(difficulty IN ('Easy', 'Medium', 'Hard')) DEFAULT 'Medium',
    content_hash TEXT UNIQUE NOT NULL, -- To prevent duplicate questions
    
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
    FOREIGN KEY (type_id) REFERENCES question_types(id) ON DELETE CASCADE
);

-- Templates for Question Papers
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    standard_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    total_marks INTEGER NOT NULL,
    config_json TEXT, -- Added for complex nested structures
    FOREIGN KEY (standard_id) REFERENCES standards(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- Sections within a Template
CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    name TEXT NOT NULL, -- e.g., 'Section A'
    question_type_id INTEGER NOT NULL,
    question_count INTEGER NOT NULL,
    marks_per_question INTEGER NOT NULL,
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
    FOREIGN KEY (question_type_id) REFERENCES question_types(id) ON DELETE CASCADE
);
