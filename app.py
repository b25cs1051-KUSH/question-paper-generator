from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import csv
import io
import traceback
from database.db_manager import DatabaseManager
from services.generator_service import PaperGenerator, InsufficientQuestionsError, DocxExporter

app = Flask(__name__)
db = DatabaseManager()
generator = PaperGenerator()

@app.route('/')
def index():
    """Serves the main frontend page."""
    return render_template('index.html')

# --- Standards ---
@app.route('/api/standards', methods=['GET'])
def get_standards():
    return jsonify(db.get_standards())

@app.route('/api/standards', methods=['POST'])
def add_standard():
    data = request.json
    name = data.get('name')
    if not name: return jsonify({"error": "Name is required"}), 400
    res = db.add_standard(name)
    return jsonify({"success": True, "id": res}) if res else jsonify({"error": "Failed"}), 500

@app.route('/api/standards/<int:id>', methods=['DELETE'])
def delete_standard(id):
    return jsonify({"success": db.delete_standard(id)})

# --- Subjects ---
@app.route('/api/subjects/<int:standard_id>', methods=['GET'])
def get_subjects(standard_id):
    return jsonify(db.get_subjects(standard_id))

@app.route('/api/subjects', methods=['POST'])
def add_subject():
    data = request.json
    res = db.add_subject(data.get('standard_id'), data.get('name'))
    return jsonify({"success": True, "id": res}) if res else jsonify({"error": "Failed"}), 500

@app.route('/api/subjects/<int:id>', methods=['DELETE'])
def delete_subject(id):
    return jsonify({"success": db.delete_subject(id)})

# --- Chapters ---
@app.route('/api/chapters/<int:subject_id>', methods=['GET'])
def get_chapters(subject_id):
    return jsonify(db.get_chapters(subject_id))

@app.route('/api/chapters', methods=['POST'])
def add_chapter():
    data = request.json
    res = db.add_chapter(data.get('subject_id'), data.get('name'))
    return jsonify({"success": True, "id": res}) if res else jsonify({"error": "Failed"}), 500

@app.route('/api/chapters/<int:id>', methods=['PUT'])
def update_chapter(id):
    data = request.json
    return jsonify({"success": db.update_chapter_name(id, data.get('name'))})

@app.route('/api/chapters/<int:id>', methods=['DELETE'])
def delete_chapter(id):
    return jsonify({"success": db.delete_chapter(id)})

# --- Question Types ---
@app.route('/api/question_types', methods=['GET'])
def get_question_types():
    return jsonify(db.get_question_types())

# --- Questions ---
@app.route('/api/questions/chapter/<int:chapter_id>', methods=['GET'])
def get_chapter_questions(chapter_id):
    return jsonify(db.get_questions_for_chapter(chapter_id))

@app.route('/api/questions', methods=['POST'])
def add_question():
    data = request.json
    try:
        q_id = db.add_question(
            data['chapter_id'], data['type_id'], data['content'],
            data['marks'], data.get('difficulty', 'Medium')
        )
        return jsonify({"success": True, "id": q_id}) if q_id else jsonify({"error": "Duplicate"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/questions/<int:id>', methods=['DELETE'])
def delete_question(id):
    return jsonify({"success": db.delete_question(id)})

# --- CSV Import ---
@app.route('/api/questions/import', methods=['POST'])
def import_questions():
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files['file']
    chapter_id = request.form.get('chapter_id')
    if not chapter_id: return jsonify({"error": "chapter_id required"}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        imported = 0
        skipped = 0
        
        for row in reader:
            content = row.get('content')
            if not content:
                skipped += 1
                continue
            
            # Resolve type_id (either from 'type_id' or 'type_name' column)
            type_id = row.get('type_id')
            if not type_id and row.get('type_name'):
                type_id = db.get_type_id_by_name(row['type_name'])
            
            if not type_id:
                skipped += 1
                continue
                
            res = db.add_question(
                chapter_id, int(type_id), content,
                int(row.get('marks', 1)), row.get('difficulty', 'Medium')
            )
            if res: imported += 1
            else: skipped += 1
            
        return jsonify({"success": True, "imported": imported, "skipped": skipped})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Templates ---
@app.route('/api/templates', methods=['POST'])
def save_template():
    data = request.json
    t_id = db.save_template(
        data['standard_id'], data['subject_id'], data['name'],
        data['config_json'], data['total_marks']
    )
    return jsonify({"success": True, "id": t_id})

@app.route('/api/templates/<int:std_id>/<int:sub_id>', methods=['GET'])
def get_templates(std_id, sub_id):
    return jsonify(db.get_templates_by_std_sub(std_id, sub_id))

@app.route('/api/templates/<int:id>', methods=['DELETE'])
def delete_template(id):
    return jsonify({"success": db.delete_template(id)})

# --- Generation & Export ---
@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    try:
        paper = generator.generate_paper(data['sections'], data.get('seed', 42))
        paper['meta'] = data.get('meta', {})
        return jsonify(paper)
    except InsufficientQuestionsError as e:
        return jsonify({"error": e.message}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export():
    data = request.json
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp_path = tmp.name
        DocxExporter.generate_docx(data, tmp_path)
        return send_file(tmp_path, as_attachment=True, download_name='paper.docx')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
