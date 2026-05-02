from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import csv
import io
from database.db_manager import DatabaseManager
from services.generator_service import PaperGenerator, InsufficientQuestionsError, DocxExporter

app = Flask(__name__)
db = DatabaseManager()
generator = PaperGenerator()

@app.route('/')
def index():
    """Serves the main frontend page."""
    return render_template('index.html')

@app.route('/api/standards', methods=['GET'])
def get_standards():
    """Returns all available standards."""
    try:
        standards = db.get_standards()
        return jsonify(standards)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/standards', methods=['POST'])
def add_standard():
    """Adds a new standard."""
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    std_id = db.add_standard(name)
    if std_id:
        return jsonify({"success": True, "id": std_id})
    return jsonify({"error": "Failed to add standard"}), 500

@app.route('/api/standards/<int:standard_id>', methods=['DELETE'])
def delete_standard(standard_id):
    """Deletes a standard."""
    if db.delete_standard(standard_id):
        return jsonify({"success": True})
    return jsonify({"error": "Failed to delete standard"}), 500

@app.route('/api/subjects/<int:standard_id>', methods=['GET'])
def get_subjects(standard_id):
    """Returns subjects for a specific standard."""
    try:
        subjects = db.get_subjects(standard_id)
        return jsonify(subjects)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/subjects', methods=['POST'])
def add_subject():
    """Adds a new subject."""
    data = request.json
    standard_id = data.get('standard_id')
    name = data.get('name')
    if not standard_id or not name:
        return jsonify({"error": "standard_id and name are required"}), 400
    
    sub_id = db.add_subject(standard_id, name)
    if sub_id:
        return jsonify({"success": True, "id": sub_id})
    return jsonify({"error": "Failed to add subject"}), 500

@app.route('/api/subjects/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    """Deletes a subject."""
    if db.delete_subject(subject_id):
        return jsonify({"success": True})
    return jsonify({"error": "Failed to delete subject"}), 500

@app.route('/api/chapters/<int:subject_id>', methods=['GET'])
def get_chapters(subject_id):
    """Returns chapters for a specific subject."""
    try:
        chapters = db.get_chapters(subject_id)
        return jsonify(chapters)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chapters', methods=['POST'])
def add_chapter():
    """Adds a new chapter."""
    data = request.json
    subject_id = data.get('subject_id')
    name = data.get('name')
    if not subject_id or not name:
        return jsonify({"error": "subject_id and name are required"}), 400
    
    ch_id = db.add_chapter(subject_id, name)
    if ch_id:
        return jsonify({"success": True, "id": ch_id})
    return jsonify({"error": "Failed to add chapter"}), 500

@app.route('/api/chapters/<int:chapter_id>', methods=['PUT'])
def update_chapter(chapter_id):
    """Updates chapter name."""
    data = request.json
    new_name = data.get('name')
    if not new_name:
        return jsonify({"error": "Name is required"}), 400
    
    if db.update_chapter_name(chapter_id, new_name):
        return jsonify({"success": True})
    return jsonify({"error": "Failed to update chapter"}), 500

@app.route('/api/chapters/<int:chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    """Deletes a chapter."""
    if db.delete_chapter(chapter_id):
        return jsonify({"success": True})
    return jsonify({"error": "Failed to delete chapter"}), 500

@app.route('/api/question_types', methods=['GET'])
def get_question_types():
    """Returns all available question types."""
    try:
        types = db.get_question_types()
        return jsonify(types)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/questions/chapter/<int:chapter_id>', methods=['GET'])
def get_chapter_questions(chapter_id):
    """Returns all questions for a chapter."""
    try:
        questions = db.get_questions_for_chapter(chapter_id)
        return jsonify(questions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/questions', methods=['POST'])
def add_question():
    """Adds a new question."""
    data = request.json
    try:
        q_id = db.add_question(
            data['chapter_id'],
            data['type_id'],
            data['content'],
            data['marks'],
            data.get('difficulty', 'Medium')
        )
        if q_id:
            return jsonify({"success": True, "id": q_id})
        return jsonify({"error": "Possible duplicate question"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """Deletes a question."""
    if db.delete_question(question_id):
        return jsonify({"success": True})
    return jsonify({"error": "Failed to delete question"}), 500

@app.route('/api/templates', methods=['POST'])
def save_template():
    """Saves a paper template."""
    data = request.json
    try:
        t_id = db.save_template(
            data['standard_id'],
            data['subject_id'],
            data['name'],
            data['config_json'],
            data['total_marks']
        )
        return jsonify({"success": True, "id": t_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates/<int:subject_id>', methods=['GET'])
def get_templates(subject_id):
    """Returns templates for a subject."""
    try:
        templates = db.get_templates(subject_id)
        return jsonify(templates)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Deletes a template."""
    if db.delete_template(template_id):
        return jsonify({"success": True})
    return jsonify({"error": "Failed to delete template"}), 500

@app.route('/api/questions/import', methods=['POST'])
def import_questions():
    """Imports questions from a CSV file."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    chapter_id = request.form.get('chapter_id')
    
    if not file or not chapter_id:
        return jsonify({"error": "File and chapter_id are required"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        
        imported_count = 0
        for row in reader:
            if not row.get('content') or not row.get('type_id'):
                continue
            db.add_question(
                chapter_id,
                int(row['type_id']),
                row['content'],
                int(row.get('marks', 1)),
                row.get('difficulty', 'Medium')
            )
            imported_count += 1
        return jsonify({"success": True, "count": imported_count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_paper():
    """
    Receives nested sections and blocks, returns generated paper JSON.
    """
    data = request.json
    sections = data.get('sections')
    seed = data.get('seed', 42)
    meta = data.get('meta', {})

    if not sections:
        return jsonify({"error": "Missing required parameter: sections"}), 400

    try:
        paper = generator.generate_paper(sections, seed)
        paper['meta'] = meta
        return jsonify(paper)
    except InsufficientQuestionsError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc() # This will print the error to the terminal
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_paper():
    """
    Receives paper JSON and returns a .docx file.
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp_path = tmp.name
        DocxExporter.generate_docx(data, tmp_path)
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name='question_paper.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
