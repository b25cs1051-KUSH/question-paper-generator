// static/js/main.js

let questionTypes = [];
let currentSubjectChapters = [];
let lastGeneratedPaper = null;

document.addEventListener('DOMContentLoaded', () => {
    console.log('Advanced Paper Generator Initialized');
    
    // Initial fetch
    fetchStandards();
    fetchQuestionTypes();

    // Event Listeners
    document.getElementById('add-section-btn').addEventListener('click', () => addSection());
    document.getElementById('generate-btn').addEventListener('click', generatePaper);
    document.getElementById('export-docx-btn').addEventListener('click', exportToDocx);
    document.getElementById('close-modal').addEventListener('click', () => {
        document.getElementById('modal-overlay').classList.add('hidden');
    });

    // Data Management Listeners
    document.getElementById('add-std-btn').onclick = addStandard;
    document.getElementById('del-std-btn').onclick = deleteSelectedStandard;
    document.getElementById('add-sub-btn').onclick = addSubject;
    document.getElementById('del-sub-btn').onclick = deleteSelectedSubject;
    document.getElementById('add-chapter-btn').onclick = addNewChapter;
    document.getElementById('save-template-btn').onclick = saveCurrentAsTemplate;
    document.getElementById('template-select').onchange = loadSelectedTemplate;

    // Add initial section
    addSection();
});

async function fetchQuestionTypes() {
    try {
        const response = await fetch('/api/question_types');
        questionTypes = await response.json();
    } catch (err) {
        console.error('Error fetching question types:', err);
    }
}

async function fetchStandards() {
    try {
        const response = await fetch('/api/standards');
        const standards = await response.json();
        const select = document.getElementById('standard-select');
        
        const currentValue = select.value;
        select.innerHTML = '<option value="">Select Standard</option>';
        standards.forEach(std => {
            const option = document.createElement('option');
            option.value = std.id;
            option.textContent = std.name;
            select.appendChild(option);
        });
        
        if (currentValue) select.value = currentValue;

        select.onchange = (e) => {
            if (e.target.value) {
                fetchSubjects(e.target.value);
            } else {
                document.getElementById('subject-select').disabled = true;
                document.getElementById('subject-select').innerHTML = '<option value="">Select Subject</option>';
            }
        };
    } catch (err) {
        console.error('Error fetching standards:', err);
    }
}

async function addStandard() {
    const name = prompt("Enter New Standard Name (e.g., 'Standard 10'):");
    if (!name) return;

    const response = await fetch('/api/standards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
    });

    if (response.ok) fetchStandards();
    else alert('Failed to add standard');
}

async function deleteSelectedStandard() {
    const id = document.getElementById('standard-select').value;
    if (!id) return alert('Select a standard first');
    if (!confirm('Are you sure? This will delete all associated subjects, chapters, and questions.')) return;

    const response = await fetch(`/api/standards/${id}`, { method: 'DELETE' });
    if (response.ok) {
        document.getElementById('standard-select').value = "";
        fetchStandards();
    }
}

async function fetchSubjects(standardId) {
    try {
        const response = await fetch(`/api/subjects/${standardId}`);
        const subjects = await response.json();
        const select = document.getElementById('subject-select');
        
        const currentValue = select.value;
        select.innerHTML = '<option value="">Select Subject</option>';
        subjects.forEach(sub => {
            const option = document.createElement('option');
            option.value = sub.id;
            option.textContent = sub.name;
            select.appendChild(option);
        });
        
        select.disabled = false;
        if (currentValue) select.value = currentValue;

        select.onchange = (e) => {
            if (e.target.value) {
                fetchChapters(e.target.value);
                fetchTemplates(e.target.value);
                document.getElementById('add-chapter-btn').classList.remove('hidden');
            } else {
                document.getElementById('chapter-list').innerHTML = '<p class="empty-state">Select a subject to view chapters.</p>';
                document.getElementById('add-chapter-btn').classList.add('hidden');
            }
        };
    } catch (err) {
        console.error('Error fetching subjects:', err);
    }
}

async function addSubject() {
    const standardId = document.getElementById('standard-select').value;
    if (!standardId) return alert('Select a standard first');
    
    const name = prompt("Enter New Subject Name (e.g., 'Mathematics'):");
    if (!name) return;

    const response = await fetch('/api/subjects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ standard_id: standardId, name })
    });

    if (response.ok) fetchSubjects(standardId);
    else alert('Failed to add subject');
}

async function deleteSelectedSubject() {
    const id = document.getElementById('subject-select').value;
    if (!id) return alert('Select a subject first');
    if (!confirm('Are you sure? This will delete all associated chapters and questions.')) return;

    const response = await fetch(`/api/subjects/${id}`, { method: 'DELETE' });
    if (response.ok) {
        const standardId = document.getElementById('standard-select').value;
        document.getElementById('subject-select').value = "";
        fetchSubjects(standardId);
    }
}

async function fetchChapters(subjectId) {
    try {
        const response = await fetch(`/api/chapters/${subjectId}`);
        currentSubjectChapters = await response.json();
        renderSyllabus();
        document.getElementById('sections-container').innerHTML = '';
        addSection();
    } catch (err) { console.error(err); }
}

async function fetchTemplates(subjectId) {
    try {
        const response = await fetch(`/api/templates/${subjectId}`);
        const templates = await response.json();
        const select = document.getElementById('template-select');
        select.innerHTML = '<option value="">Load Template...</option>';
        templates.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.dataset.config = t.config_json;
            opt.textContent = `${t.name} (${t.total_marks}M)`;
            select.appendChild(opt);
        });
    } catch (err) { console.error(err); }
}

async function saveCurrentAsTemplate() {
    const stdId = document.getElementById('standard-select').value;
    const subId = document.getElementById('subject-select').value;
    if (!subId) return alert('Select a subject first');

    const name = prompt("Enter Template Name (e.g., 'Final Exam Format'):");
    if (!name) return;

    const sections = getPaperStructure();
    const totalMarks = calculateTotalMarks({ sections: Object.fromEntries(sections.map(s => [s.name, s])) });

    const response = await fetch('/api/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            standard_id: stdId,
            subject_id: subId,
            name: name,
            config_json: JSON.stringify(sections),
            total_marks: totalMarks
        })
    });

    if (response.ok) {
        alert('Template saved!');
        fetchTemplates(subId);
    }
}

function loadSelectedTemplate(e) {
    const opt = e.target.selectedOptions[0];
    if (!opt || !opt.dataset.config) return;

    if (!confirm('This will replace your current structure. Continue?')) return;

    const sections = JSON.parse(opt.dataset.config);
    const container = document.getElementById('sections-container');
    container.innerHTML = '';

    sections.forEach(s => {
        const sectionChar = s.name.replace('Section ', '');
        addSection(sectionChar);
        const lastSection = container.lastElementChild;
        const blocksContainer = lastSection.querySelector('.blocks-container');
        blocksContainer.innerHTML = '';

        s.blocks.forEach(b => {
            addBlock(blocksContainer);
            const lastBlock = blocksContainer.lastElementChild;
            lastBlock.querySelector('.type-select').value = b.type_id;
            lastBlock.querySelector('.count-input').value = b.count;
            lastBlock.querySelector('.marks-input').value = b.marks;
            lastBlock.querySelectorAll('.chapter-option input').forEach(cb => {
                cb.checked = b.chapters.includes(parseInt(cb.value));
            });
        });
    });
}

function getPaperStructure() {
    return Array.from(document.querySelectorAll('.section-wrapper')).map(sw => {
        const blocks = Array.from(sw.querySelectorAll('.rule-block')).map(rb => {
            const selectedCh = Array.from(rb.querySelectorAll('.chapter-option input:checked')).map(i => parseInt(i.value));
            return {
                type_id: parseInt(rb.querySelector('.type-select').value),
                chapters: selectedCh,
                count: parseInt(rb.querySelector('.count-input').value),
                marks: parseInt(rb.querySelector('.marks-input').value)
            };
        });
        return { name: sw.dataset.name, blocks: blocks };
    });
}

async function addNewChapter() {
    const subjectId = document.getElementById('subject-select').value;
    if (!subjectId) return;

    const name = prompt("Enter New Chapter Name:");
    if (!name) return;

    const response = await fetch('/api/chapters', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject_id: subjectId, name })
    });

    if (response.ok) fetchChapters(subjectId);
}

function renderSyllabus() {
    const list = document.getElementById('chapter-list');
    list.innerHTML = currentSubjectChapters.length === 0 ? '<p class="empty-state">No chapters found.</p>' : '';

    currentSubjectChapters.forEach(ch => {
        const div = document.createElement('div');
        div.className = 'chapter-item';
        div.innerHTML = `
            <input type="text" class="chapter-name-input" value="${ch.name}">
            <button class="manage-q-btn">QUESTIONS</button>
            <button class="del-ch-btn">&times;</button>
        `;
        
        const input = div.querySelector('.chapter-name-input');
        input.onchange = async (e) => {
            await updateChapterName(ch.id, e.target.value);
            ch.name = e.target.value;
            updateAllBlockChapters();
        };

        div.querySelector('.manage-q-btn').onclick = () => openQuestionManager(ch);
        div.querySelector('.del-ch-btn').onclick = async () => {
            if (confirm(`Delete '${ch.name}'?`)) {
                await fetch(`/api/chapters/${ch.id}`, { method: 'DELETE' });
                fetchChapters(document.getElementById('subject-select').value);
            }
        };

        list.appendChild(div);
    });
}

async function updateChapterName(id, name) {
    await fetch(`/api/chapters/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
    });
}

function updateAllBlockChapters() {
    document.querySelectorAll('.chapter-selector-mini').forEach(container => {
        const checkedIds = Array.from(container.querySelectorAll('input:checked')).map(i => i.value);
        container.innerHTML = currentSubjectChapters.map(ch => `
            <label class="chapter-option">
                <input type="checkbox" value="${ch.id}" ${checkedIds.includes(ch.id.toString()) ? 'checked' : ''}>
                <span>${ch.name}</span>
            </label>
        `).join('');
    });
}

async function openQuestionManager(chapter) {
    const modal = document.getElementById('modal-overlay');
    document.getElementById('modal-title').textContent = `Manage: ${chapter.name}`;
    const body = document.getElementById('modal-body');
    
    body.innerHTML = `
        <div class="add-q-section">
            <h4 style="margin-bottom:10px; color:var(--accent-primary)">ADD NEW QUESTION</h4>
            <div class="add-q-form">
                <div class="input-group">
                    <label>Content</label>
                    <textarea id="new-q-content" placeholder="Type question here..."></textarea>
                </div>
                <div class="input-group">
                    <label>Type</label>
                    <select id="new-q-type">
                        ${questionTypes.map(t => `<option value="${t.id}">${t.name}</option>`).join('')}
                    </select>
                </div>
                <div class="input-group">
                    <label>Marks</label>
                    <input type="number" id="new-q-marks" value="1" style="width:60px">
                </div>
                <button id="save-q-btn" class="primary-btn" style="height:40px">SAVE</button>
            </div>
            
            <div class="bulk-import-section">
                <h4 style="margin-bottom:10px; color:var(--accent-secondary)">BULK IMPORT (CSV)</h4>
                <div style="display:flex; justify-content:space-between; align-items:center">
                    <p style="font-size:11px; color:var(--text-secondary)">Format: content,type_id,marks</p>
                    <a href="#" id="download-sample-csv" style="font-size:10px; color:var(--accent-primary); text-decoration:none; border:1px solid; padding:2px 5px">Download Sample CSV</a>
                </div>
                <div class="file-input-wrapper">
                    <input type="file" id="bulk-q-file" accept=".csv">
                    <button id="import-q-btn" class="secondary-btn" style="padding:4px 12px; font-size:12px">IMPORT</button>
                </div>
            </div>
        </div>
        <div id="chapter-q-list" class="q-list-container">Loading...</div>
    `;

    modal.classList.remove('hidden');

    document.getElementById('save-q-btn').onclick = async () => {
        const content = document.getElementById('new-q-content').value;
        const type_id = document.getElementById('new-q-type').value;
        const marks = document.getElementById('new-q-marks').value;
        if (!content) return alert('Content required');

        const response = await fetch('/api/questions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chapter_id: chapter.id, type_id, content, marks })
        });

        if (response.ok) {
            document.getElementById('new-q-content').value = '';
            loadChapterQuestions(chapter.id);
        } else alert('Error saving question');
    };

    document.getElementById('import-q-btn').onclick = async () => {
        const fileInput = document.getElementById('bulk-q-file');
        if (!fileInput.files[0]) return alert('Select a CSV file');
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('chapter_id', chapter.id);

        const response = await fetch('/api/questions/import', { method: 'POST', body: formData });
        if (response.ok) {
            const res = await response.json();
            alert(`Imported ${res.count} questions!`);
            loadChapterQuestions(chapter.id);
        } else alert('Import failed');
    };

    document.getElementById('download-sample-csv').onclick = (e) => {
        e.preventDefault();
        const content = "content,type_id,marks,difficulty\nExplain photosynthesis,3,5,Medium\nWhat is 2+2?,1,1,Easy";
        const blob = new Blob([content], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'sample_questions.csv';
        a.click();
    };

    loadChapterQuestions(chapter.id);
}

async function loadChapterQuestions(chapterId) {
    const listContainer = document.getElementById('chapter-q-list');
    try {
        const response = await fetch(`/api/questions/chapter/${chapterId}`);
        const questions = await response.json();
        
        if (questions.length === 0) {
            listContainer.innerHTML = '<p style="text-align:center; color:var(--text-secondary)">No questions found.</p>';
            return;
        }

        const grouped = {};
        questions.forEach(q => {
            if (!grouped[q.type_name]) grouped[q.type_name] = [];
            grouped[q.type_name].push(q);
        });

        listContainer.innerHTML = '';
        for (const [typeName, qs] of Object.entries(grouped)) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'q-type-group';
            groupDiv.innerHTML = `<div class="q-type-label">${typeName}</div>`;
            qs.forEach(q => {
                const qItem = document.createElement('div');
                qItem.className = 'managed-q-item';
                qItem.innerHTML = `
                    <div class="managed-q-text">${q.content} <span style="color:var(--accent-secondary)">[${q.marks}M]</span></div>
                    <button class="delete-q-btn">DELETE</button>
                `;
                qItem.querySelector('.delete-q-btn').onclick = async () => {
                    if (confirm('Delete this question?')) {
                        await fetch(`/api/questions/${q.id}`, { method: 'DELETE' });
                        loadChapterQuestions(chapterId);
                    }
                };
                groupDiv.appendChild(qItem);
            });
            listContainer.appendChild(groupDiv);
        }
    } catch (err) { listContainer.textContent = 'Error loading questions.'; }
}

function addSection(name = null) {
    const container = document.getElementById('sections-container');
    const sectionIndex = container.children.length;
    const sectionChar = name || String.fromCharCode(65 + sectionIndex);

    const sectionWrapper = document.createElement('div');
    sectionWrapper.className = 'section-wrapper';
    sectionWrapper.dataset.name = `Section ${sectionChar}`;
    
    sectionWrapper.innerHTML = `
        <div class="section-header">
            <h3>Section ${sectionChar}</h3>
            <button class="remove-block-btn" onclick="this.closest('.section-wrapper').remove()">&times;</button>
        </div>
        <div class="blocks-container"></div>
        <button class="secondary-btn add-block-btn">+ Add Question Block</button>
    `;

    sectionWrapper.querySelector('.add-block-btn').onclick = () => addBlock(sectionWrapper.querySelector('.blocks-container'));
    container.appendChild(sectionWrapper);
    addBlock(sectionWrapper.querySelector('.blocks-container'));
}

function addBlock(container) {
    const block = document.createElement('div');
    block.className = 'rule-block';
    const chaptersHtml = currentSubjectChapters.map(ch => `
        <label class="chapter-option">
            <input type="checkbox" value="${ch.id}" checked>
            <span>${ch.name}</span>
        </label>
    `).join('');

    block.innerHTML = `
        <div class="block-header">
            <span class="block-title">Question Rule</span>
            <button class="remove-block-btn" onclick="this.closest('.rule-block').remove()">&times;</button>
        </div>
        <div class="block-controls">
            <div class="input-group">
                <label>Type</label>
                <select class="type-select">
                    ${questionTypes.map(t => `<option value="${t.id}">${t.name}</option>`).join('')}
                </select>
            </div>
            <div class="input-group">
                <label>Count</label>
                <input type="number" class="count-input" value="5" min="1">
            </div>
            <div class="input-group">
                <label>Marks</label>
                <input type="number" class="marks-input" value="1" min="1">
            </div>
        </div>
        <label style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-secondary); display: block; margin-bottom: 5px;">Source Chapters</label>
        <div class="chapter-selector-mini">${chaptersHtml || '<p style="font-size: 12px; color: var(--accent-primary)">Select a Subject first</p>'}</div>
    `;
    container.appendChild(block);
}

async function generatePaper() {
    const sections = getPaperStructure();
    if (sections.length === 0) return alert('Add at least one section.');

    const payload = {
        sections: sections,
        seed: parseInt(document.getElementById('paper-seed').value) || 42,
        meta: {
            institution: document.getElementById('inst-name').value,
            exam_name: document.getElementById('exam-name').value,
            time_limit: document.getElementById('time-limit').value
        }
    };

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (response.ok) {
            lastGeneratedPaper = result;
            displayPaper(result);
        } else alert(result.error);
    } catch (err) { console.error(err); }
}

function displayPaper(paper) {
    const panel = document.getElementById('preview-panel');
    const content = document.getElementById('paper-content');
    panel.classList.remove('hidden');
    content.innerHTML = '';

    const headerDiv = document.createElement('div');
    headerDiv.style.textAlign = 'center'; headerDiv.style.marginBottom = '30px';
    headerDiv.innerHTML = `
        <h1 style="margin-bottom:5px">${paper.meta.institution || 'ACADEMIC INSTITUTION'}</h1>
        <h2 style="margin-bottom:15px">${paper.meta.exam_name || 'ANNUAL EXAMINATION'}</h2>
        <div style="display:flex; justify-content:space-between; border-bottom:2px solid #000; padding-bottom:5px">
            <span>Total Marks: ${calculateTotalMarks(paper)}</span>
            <span>Time: ${paper.meta.time_limit}</span>
        </div>
    `;
    content.appendChild(headerDiv);

    for (const [sectionName, sectionData] of Object.entries(paper.sections)) {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'paper-section';
        sectionDiv.innerHTML = `<div class="paper-section-title">${sectionName}</div>`;

        let qCounter = 1;
        sectionData.blocks.forEach(block => {
            const typeName = questionTypes.find(t => t.id === block.rule.type_id)?.name || 'Questions';
            const instr = document.createElement('div');
            instr.className = 'paper-block-instr';
            instr.textContent = `Answer the following ${typeName} (${block.rule.count} x ${block.rule.marks} = ${block.rule.count * block.rule.marks} Marks)`;
            sectionDiv.appendChild(instr);

            block.questions.forEach(q => {
                const qDiv = document.createElement('div');
                qDiv.className = 'question-item';
                qDiv.innerHTML = `<div class="question-text">${qCounter}. ${q.content}</div><div class="question-marks">[${q.marks}]</div>`;
                sectionDiv.appendChild(qDiv);
                qCounter++;
            });
        });
        content.appendChild(sectionDiv);
    }
    panel.scrollIntoView({ behavior: 'smooth' });
}

function calculateTotalMarks(paper) {
    let total = 0;
    for (const section of Object.values(paper.sections)) {
        for (const block of section.blocks) total += block.rule.count * block.rule.marks;
    }
    return total;
}

async function exportToDocx() {
    if (!lastGeneratedPaper) return alert('Generate a paper first.');
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lastGeneratedPaper)
        });
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = 'Question_Paper.docx';
            document.body.appendChild(a); a.click();
            window.URL.revokeObjectURL(url); a.remove();
        }
    } catch (err) { console.error(err); }
}

function showModal(title, content) {
    const modal = document.getElementById('modal-overlay');
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').textContent = content;
    modal.classList.remove('hidden');
}
