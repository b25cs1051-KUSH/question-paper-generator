// static/js/main.js

// --- Global State ---
let questionTypes = [];
let currentSubjectChapters = [];
let lastGeneratedPaper = null;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Paper Generator Initialized');
    
    // Core setup
    fetchStandards(); // Run immediately
    setupEventListeners(); // Run immediately
    addSection(); // Run immediately

    // Await non-critical types for dropdowns
    try {
        await fetchQuestionTypes();
        // If we have sections already, refresh their dropdowns
        document.querySelectorAll('.type-select').forEach(select => {
            const currentVal = select.value;
            select.innerHTML = questionTypes.map(t => `<option value="${t.id}" ${t.id == currentVal ? 'selected' : ''}>${t.name}</option>`).join('');
        });
    } catch (err) { console.error('Question types failed to load:', err); }
});

function setupEventListeners() {
    // Buttons
    document.getElementById('add-section-btn').addEventListener('click', () => addSection());
    document.getElementById('generate-btn').addEventListener('click', generatePaper);
    document.getElementById('export-docx-btn').addEventListener('click', exportToDocx);
    
    // Modal
    document.getElementById('close-modal').addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('modal-overlay');
        if (e.target === modal) closeModal();
    });

    // Data Management
    document.getElementById('add-std-btn').onclick = addStandard;
    document.getElementById('del-std-btn').onclick = deleteSelectedStandard;
    document.getElementById('add-sub-btn').onclick = addSubject;
    document.getElementById('del-sub-btn').onclick = deleteSelectedSubject;
    document.getElementById('add-chapter-btn').onclick = addNewChapter;

    // Template Management
    document.getElementById('template-select').addEventListener('change', loadSelectedTemplate);
    document.getElementById('del-template-btn').addEventListener('click', deleteSelectedTemplate);
    document.getElementById('save-new-template-btn').addEventListener('click', saveTemplateFromPreview);
}

// --- API Calls ---

async function fetchQuestionTypes() {
    try {
        const response = await fetch('/api/question_types');
        questionTypes = await response.json();
    } catch (err) { console.error('Error fetching question types:', err); }
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
        
        if (currentValue) {
            select.value = currentValue;
            fetchSubjects(currentValue); // Trigger the next level on refresh
        }

        select.onchange = (e) => {
            const stdId = e.target.value;
            const subSelect = document.getElementById('subject-select');
            if (stdId) {
                fetchSubjects(stdId);
            } else {
                subSelect.disabled = true;
                subSelect.innerHTML = '<option value="">Select Subject</option>';
                resetWorkspace();
            }
        };
    } catch (err) { console.error('Error fetching standards:', err); }
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
        
        if (currentValue && subjects.some(s => s.id == currentValue)) {
            select.value = currentValue;
            fetchChapters(currentValue);
            fetchTemplates(currentValue); // Important: cascades templates on reload
            document.getElementById('add-chapter-btn').classList.remove('hidden');
        }
        
        select.onchange = (e) => {
            const subId = e.target.value;
            if (subId) {
                fetchChapters(subId);
                fetchTemplates(subId);
                document.getElementById('add-chapter-btn').classList.remove('hidden');
            } else {
                resetWorkspace();
            }
        };
    } catch (err) { console.error('Error fetching subjects:', err); }
}

async function fetchChapters(subjectId) {
    try {
        const response = await fetch(`/api/chapters/${subjectId}`);
        currentSubjectChapters = await response.json();
        renderSyllabus();
        updateAllBlockChapters(); // Refresh existing blocks with new chapter list
    } catch (err) { console.error('Error fetching chapters:', err); }
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
    } catch (err) { console.error('Error fetching templates:', err); }
}

// --- UI Rendering ---

function renderSyllabus() {
    const list = document.getElementById('chapter-list');
    if (currentSubjectChapters.length === 0) {
        list.innerHTML = '<p class="empty-state">No chapters found. Add one to begin.</p>';
        return;
    }
    
    list.innerHTML = '';
    currentSubjectChapters.forEach(ch => {
        const div = document.createElement('div');
        div.className = 'chapter-item glass';
        div.innerHTML = `
            <input type="text" class="chapter-name-input" value="${ch.name}" title="Click to rename">
            <button class="manage-q-btn">QUESTIONS</button>
            <button class="del-ch-btn" title="Delete Chapter">&times;</button>
        `;
        
        const input = div.querySelector('.chapter-name-input');
        input.onchange = async (e) => {
            const success = await updateChapterName(ch.id, e.target.value);
            if (success) {
                ch.name = e.target.value;
                updateAllBlockChapters();
            }
        };

        div.querySelector('.manage-q-btn').onclick = () => openQuestionManager(ch);
        div.querySelector('.del-ch-btn').onclick = () => deleteChapter(ch);

        list.appendChild(div);
    });
}

function updateAllBlockChapters(specificContainer = null) {
    const containers = specificContainer ? [specificContainer] : document.querySelectorAll('.chapter-selector-mini');
    
    containers.forEach(container => {
        const checkedIds = Array.from(container.querySelectorAll('input:checked:not(.select-all-toggle)')).map(i => i.value);
        container.innerHTML = generateChaptersHtml(checkedIds);
        
        // --- TEMPLATE SYSTEM FIX: SELECT ALL TOGGLE BEHAVIOR ---
        const toggle = container.querySelector('.select-all-toggle');
        const normalCheckboxes = container.querySelectorAll('input[type="checkbox"]:not(.select-all-toggle)');
        
        if (toggle) {
            toggle.onchange = (e) => {
                const checked = e.target.checked;
                normalCheckboxes.forEach(cb => cb.checked = checked);
            };
            
            // Sync toggle state if individual checkboxes are changed
            normalCheckboxes.forEach(cb => {
                cb.onchange = () => {
                    const allChecked = Array.from(normalCheckboxes).every(c => c.checked);
                    toggle.checked = allChecked;
                };
            });
        }
    });
}

function generateChaptersHtml(checkedIds = []) {
    if (currentSubjectChapters.length === 0) {
        return '<p style="font-size: 11px; color: var(--accent-pink)">Add chapters to the syllabus first.</p>';
    }

    // --- TEMPLATE SYSTEM FIX: INITIALIZE TOGGLE STATE ---
    const allChecked = currentSubjectChapters.length > 0 && checkedIds.length === currentSubjectChapters.length;

    const selectAllHtml = `
        <label class="chapter-option">
            <input type="checkbox" class="select-all-toggle" ${allChecked ? 'checked' : ''}>
            <span><b>Select All</b></span>
        </label>
    `;

    const chaptersHtml = currentSubjectChapters.map(ch => `
        <label class="chapter-option">
            <input type="checkbox" value="${ch.id}" ${checkedIds.includes(ch.id.toString()) ? 'checked' : ''}>
            <span>${ch.name}</span>
        </label>
    `).join('');

    return selectAllHtml + chaptersHtml;
}

// --- Workspace Management ---

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
            <button class="remove-section-btn" style="background:none; border:none; color:white; font-size:20px; cursor:pointer">&times;</button>
        </div>
        <div class="blocks-container"></div>
        <button class="secondary-btn add-block-btn" style="margin: 15px; width: calc(100% - 30px)">+ Add Question Block</button>
    `;

    sectionWrapper.querySelector('.remove-section-btn').onclick = () => sectionWrapper.remove();
    sectionWrapper.querySelector('.add-block-btn').onclick = () => addBlock(sectionWrapper.querySelector('.blocks-container'));
    
    container.appendChild(sectionWrapper);
    addBlock(sectionWrapper.querySelector('.blocks-container'));
}

function addBlock(container) {
    const block = document.createElement('div');
    block.className = 'rule-block';
    
    block.innerHTML = `
        <div class="block-header" style="display:flex; justify-content:space-between; margin-bottom:15px">
            <span class="block-title" style="font-weight:800; color:var(--accent-yellow); font-size:12px">QUESTION RULE</span>
            <button class="remove-block-btn" style="background:none; border:none; color:#ff4444; cursor:pointer">&times;</button>
        </div>
        <div class="block-controls" style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; margin-bottom:15px">
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
        <label style="font-size: 10px; font-weight: 800; color: var(--text-secondary); display: block; margin-bottom: 5px;">SOURCE CHAPTERS</label>
        <div class="chapter-selector-mini glass" style="max-height:100px; overflow-y:auto; padding:8px">
            ${generateChaptersHtml(currentSubjectChapters.map(c => c.id.toString()))}
        </div>
    `;

    block.querySelector('.remove-block-btn').onclick = () => block.remove();
    container.appendChild(block);
    updateAllBlockChapters();
}

function resetWorkspace() {
    currentSubjectChapters = [];
    document.getElementById('chapter-list').innerHTML = '<p class="empty-state">Select a subject to view chapters.</p>';
    document.getElementById('add-chapter-btn').classList.add('hidden');
    document.getElementById('sections-container').innerHTML = '';
    document.getElementById('preview-panel').classList.add('hidden');
    addSection();
}

// --- Question Management (Modal) ---

async function openQuestionManager(chapter) {
    const modal = document.getElementById('modal-overlay');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');
    
    title.textContent = `MANAGE QUESTIONS: ${chapter.name.toUpperCase()}`;
    
    body.innerHTML = `
        <div class="add-q-section glass" style="margin-bottom:25px; padding:20px; border:1px solid var(--accent-green)">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px">
                <h4 style="color:var(--accent-green); margin:0">ADD NEW QUESTION</h4>
                <div style="display:flex; gap:10px">
                    <button id="download-sample-csv" class="secondary-btn" style="font-size:10px; padding:5px 10px; border-color:var(--accent-yellow); color:var(--accent-yellow)">Sample CSV</button>
                    <input type="file" id="csv-file-input" accept=".csv" style="display:none">
                    <button id="import-csv-btn" class="secondary-btn" style="font-size:10px; padding:5px 10px; border-color:var(--accent-pink); color:var(--accent-pink)">Bulk Import (CSV)</button>
                </div>
            </div>
            <div class="add-q-form">
                <div class="input-group">
                    <label>Question Content</label>
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
                <button id="save-q-btn" class="primary-btn" style="background:var(--accent-green); color:black; height:42px">SAVE</button>
            </div>
        </div>
        <div id="chapter-q-list" class="q-list-container">Loading questions...</div>
    `;

    modal.classList.remove('hidden');

    document.getElementById('save-q-btn').onclick = async () => {
        const content = document.getElementById('new-q-content').value.trim();
        const type_id = document.getElementById('new-q-type').value;
        const marks = document.getElementById('new-q-marks').value;
        if (!content) return alert('Question content cannot be empty.');

        const response = await fetch('/api/questions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chapter_id: chapter.id, type_id, content, marks })
        });

        if (response.ok) {
            document.getElementById('new-q-content').value = '';
            loadChapterQuestions(chapter.id);
        } else {
            const err = await response.json();
            alert(err.error || 'Failed to save question.');
        }
    };

    document.getElementById('import-csv-btn').onclick = () => document.getElementById('csv-file-input').click();
    document.getElementById('csv-file-input').onchange = (e) => importCSV(e, chapter.id);
    document.getElementById('download-sample-csv').onclick = downloadSampleCSV;

    loadChapterQuestions(chapter.id);
}

function downloadSampleCSV() {
    const headers = "content,type_name,marks,difficulty\n";
    const sampleData = "What is the capital of France?,MCQ,1,Easy\n";
    const blob = new Blob([headers + sampleData], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_questions.csv';
    a.click();
}

async function importCSV(event, chapterId) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('chapter_id', chapterId);

    try {
        const response = await fetch('/api/questions/import', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        if (response.ok) {
            alert(`Imported ${result.imported} questions. Skipped ${result.skipped}.`);
            loadChapterQuestions(chapterId);
        } else {
            alert(result.error);
        }
    } catch (err) {
        console.error(err);
        alert('Failed to import CSV.');
    }
}

async function loadChapterQuestions(chapterId) {
    const listContainer = document.getElementById('chapter-q-list');
    try {
        const response = await fetch(`/api/questions/chapter/${chapterId}`);
        const questions = await response.json();
        
        if (questions.length === 0) {
            listContainer.innerHTML = '<p style="text-align:center; color:var(--text-secondary); padding:20px">No questions added yet.</p>';
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
            groupDiv.style.marginBottom = '20px';
            groupDiv.innerHTML = `<div style="color:var(--accent-yellow); font-size:12px; font-weight:800; border-bottom:1px solid rgba(255,255,255,0.1); margin-bottom:10px; padding-bottom:5px">${typeName.toUpperCase()}</div>`;
            
            qs.forEach(q => {
                const qItem = document.createElement('div');
                qItem.className = 'managed-q-item';
                qItem.innerHTML = `
                    <div style="flex-grow:1; font-size:13px">${q.content} <span style="color:var(--accent-pink); font-weight:800">[${q.marks}M]</span></div>
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

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

// --- Paper Generation ---

async function generatePaper() {
    const sections = getPaperStructure();
    if (sections.length === 0) return alert('Please add at least one section.');

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
        } else {
            alert(result.error);
        }
    } catch (err) { 
        console.error(err);
        alert('Internal server error during generation.');
    }
}

function getPaperStructure() {
    return Array.from(document.querySelectorAll('.section-wrapper')).map(sw => {
        const blocks = Array.from(sw.querySelectorAll('.rule-block')).map(rb => {
            const selectedCh = Array.from(rb.querySelectorAll('.chapter-option input:checked:not(.select-all-toggle)')).map(i => parseInt(i.value)); 
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

function displayPaper(paper) {
    const panel = document.getElementById('preview-panel');
    const content = document.getElementById('paper-content');
    panel.classList.remove('hidden');
    content.innerHTML = '';

    const headerDiv = document.createElement('div');
    headerDiv.style.textAlign = 'center'; headerDiv.style.marginBottom = '30px';
    headerDiv.innerHTML = `
        <h1 style="margin-bottom:10px; font-size:24px">${paper.meta.institution.toUpperCase() || 'ACADEMIC INSTITUTION'}</h1>
        <h2 style="margin-bottom:20px; font-size:18px">${paper.meta.exam_name.toUpperCase() || 'ANNUAL EXAMINATION'}</h2>
        <div style="display:flex; justify-content:space-between; border-bottom:2px solid #000; padding-bottom:10px; font-weight:800">
            <span>TOTAL MARKS: ${calculateTotalMarks(paper)}</span>
            <span>TIME: ${paper.meta.time_limit.toUpperCase()}</span>
        </div>
    `;
    content.appendChild(headerDiv);

    for (const [sectionName, sectionData] of Object.entries(paper.sections)) {
        const sectionDiv = document.createElement('div');
        sectionDiv.style.marginTop = '30px';
        sectionDiv.innerHTML = `<div style="font-weight:900; font-size:1.2rem; border-bottom:1px solid #000; margin-bottom:15px">${sectionName.toUpperCase()}</div>`;

        let qCounter = 1;
        sectionData.blocks.forEach(block => {
            const typeName = questionTypes.find(t => t.id === block.rule.type_id)?.name || 'Questions';
            const instr = document.createElement('div');
            instr.style.fontStyle = 'italic';
            instr.style.fontWeight = '800';
            instr.style.marginBottom = '15px';
            instr.textContent = `Answer the following ${typeName} (${block.rule.count} x ${block.rule.marks} = ${block.rule.count * block.rule.marks} Marks)`;
            sectionDiv.appendChild(instr);

            block.questions.forEach(q => {
                const qDiv = document.createElement('div');
                qDiv.style.display = 'flex';
                qDiv.style.justifyContent = 'space-between';
                qDiv.style.marginBottom = '10px';
                qDiv.innerHTML = `<div style="max-width:90%">Q${qCounter}. ${q.content}</div><div style="font-weight:800">[${q.marks}]</div>`;
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
        } else {
            alert('Export failed.');
        }
    } catch (err) { console.error(err); }
}

// --- NEW SCRATCH-BUILT TEMPLATE SYSTEM LOGIC ---

async function fetchTemplates(subjectId) {
    const stdId = document.getElementById('standard-select').value;
    if (!stdId || !subjectId) return;

    try {
        const response = await fetch(`/api/templates/${stdId}/${subjectId}`);
        const templates = await response.json();
        const select = document.getElementById('template-select');
        select.innerHTML = '<option value="">Select a template to load...</option>';
        templates.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.dataset.config = t.config_json;
            opt.textContent = `${t.name} (${t.total_marks}M)`;
            select.appendChild(opt);
        });
    } catch (err) { console.error('Error fetching templates:', err); }
}

async function saveTemplateFromPreview() {
    const stdId = document.getElementById('standard-select').value;
    const subId = document.getElementById('subject-select').value;
    if (!subId) return alert('Select subject first.');

    const name = prompt("Enter a name for this new template:", "My Custom Template");
    if (!name) return;

    // --- TEMPLATE SYSTEM FIX: DO NOT STORE CHAPTERS ---
    const rawSections = getPaperStructure();
    const cleanSections = rawSections.map(s => ({
        name: s.name,
        blocks: s.blocks.map(b => ({
            type_id: b.type_id,
            count: b.count,
            marks: b.marks
        }))
    }));

    let totalMarks = 0;
    cleanSections.forEach(s => {
        s.blocks.forEach(b => {
            totalMarks += b.count * b.marks;
        });
    });

    try {
        const response = await fetch('/api/templates', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                standard_id: stdId,
                subject_id: subId,
                name: name,
                config_json: JSON.stringify(cleanSections),
                total_marks: totalMarks
            })
        });

        if (response.ok) {
            alert('Template saved successfully to the library!');
            fetchTemplates(subId);
        } else {
            alert('Failed to save template.');
        }
    } catch (err) { console.error(err); }
}

async function deleteSelectedTemplate() {
    const id = document.getElementById('template-select').value;
    if (!id) return alert('Select a template to delete.');
    if (!confirm('Permanently delete this template?')) return;

    try {
        const response = await fetch(`/api/templates/${id}`, { method: 'DELETE' });
        if (response.ok) {
            alert('Template deleted.');
            fetchTemplates(document.getElementById('subject-select').value);
        }
    } catch (err) { console.error(err); }
}

function loadSelectedTemplate(e) {
    const opt = e.target.selectedOptions[0];
    if (!opt || !opt.dataset.config) return;

    if (!confirm('This will clear your current structure. Load this template?')) return;

    const sections = JSON.parse(opt.dataset.config);
    const container = document.getElementById('sections-container');
    container.innerHTML = '';

    sections.forEach(s => {
        const sectionChar = s.name.replace('Section ', '');
        addSection(sectionChar);
        const lastSection = container.lastElementChild;
        const blocksContainer = lastSection.querySelector('.blocks-container');
        blocksContainer.innerHTML = ''; // Clear the default block added by addSection

        s.blocks.forEach(b => {
            addBlock(blocksContainer);
            const lastBlock = blocksContainer.lastElementChild;
            lastBlock.querySelector('.type-select').value = b.type_id;
            lastBlock.querySelector('.count-input').value = b.count;
            lastBlock.querySelector('.marks-input').value = b.marks;
            
            // Sync the Select All UI for this block
            updateAllBlockChapters(lastBlock.querySelector('.chapter-selector-mini'));
        });
    });
}

// --- Data Operations ---

async function addStandard() {
    const name = prompt("Enter New Standard Name (e.g., 'Standard 10'):");
    if (!name) return;
    const response = await fetch('/api/standards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
    });
    if (response.ok) fetchStandards();
}

async function deleteSelectedStandard() {
    const id = document.getElementById('standard-select').value;
    if (!id) return alert('Select a standard first.');
    if (!confirm('Delete this standard and all associated data?')) return;
    const response = await fetch(`/api/standards/${id}`, { method: 'DELETE' });
    if (response.ok) fetchStandards();
}

async function addSubject() {
    const stdId = document.getElementById('standard-select').value;
    if (!stdId) return alert('Select a standard first.');
    const name = prompt("Enter Subject Name:");
    if (!name) return;
    const response = await fetch('/api/subjects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ standard_id: stdId, name })
    });
    if (response.ok) fetchSubjects(stdId);
}

async function deleteSelectedSubject() {
    const id = document.getElementById('subject-select').value;
    if (!id) return alert('Select a subject first.');
    if (!confirm('Delete this subject?')) return;
    const response = await fetch(`/api/subjects/${id}`, { method: 'DELETE' });
    if (response.ok) {
        const stdId = document.getElementById('standard-select').value;
        fetchSubjects(stdId);
    }
}

async function addNewChapter() {
    const subId = document.getElementById('subject-select').value;
    if (!subId) return;
    const name = prompt("Enter Chapter Name:");
    if (!name) return;
    const response = await fetch('/api/chapters', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject_id: subId, name })
    });
    if (response.ok) fetchChapters(subId);
}

async function deleteChapter(chapter) {
    if (!confirm(`Delete '${chapter.name}' and all its questions?`)) return;
    const response = await fetch(`/api/chapters/${chapter.id}`, { method: 'DELETE' });
    if (response.ok) {
        fetchChapters(document.getElementById('subject-select').value);
    }
}

async function updateChapterName(id, name) {
    const response = await fetch(`/api/chapters/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
    });
    return response.ok;
}
