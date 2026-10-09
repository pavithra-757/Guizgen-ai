/**
 * QuizGen AI — SPA Frontend Script & State Management
 */
const app = {
    // State
    apiBase: '',
    token: localStorage.getItem('quizgen_token') || null,
    user: JSON.parse(localStorage.getItem('quizgen_user')) || null,
    currentView: 'home',
    currentQuizPreview: null,
    currentTakingQuiz: null,
    quizTimerInterval: null,
    quizTimeSeconds: 0,

    init() {
        this.renderNavbar();
        this.checkAuthStatus();
        this.navigateTo(this.user ? (this.user.role === 'faculty' ? 'faculty-dashboard' : 'student-dashboard') : 'home');
    },

    // --- API Helpers ---
    async apiCall(endpoint, method = 'GET', body = null) {
        const headers = { 'Content-Type': 'application/json' };
        
        // Do not send Authorization header to login or register endpoints
        const isAuthEndpoint = endpoint.startsWith('/api/auth/register') || endpoint.startsWith('/api/auth/login');
        if (this.token && !isAuthEndpoint) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const config = { method, headers };
        if (body) config.body = JSON.stringify(body);

        try {
            const res = await fetch(`${this.apiBase}${endpoint}`, config);
            
            let data = {};
            const contentType = res.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                data = await res.json();
            } else {
                const rawText = await res.text();
                data = { detail: rawText.trim() || res.statusText || `HTTP Error ${res.status}` };
            }

            if (!res.ok) {
                let errorMsg = 'API Request Failed';
                if (typeof data.detail === 'string') {
                    errorMsg = data.detail;
                } else if (data.detail && typeof data.detail === 'object') {
                    errorMsg = JSON.stringify(data.detail);
                } else if (data.message) {
                    errorMsg = data.message;
                }

                if (res.status === 401 && !isAuthEndpoint) {
                    this.logoutSilently();
                }

                throw new Error(errorMsg);
            }
            return data;
        } catch (err) {
            this.showToast(err.message, 'error');
            throw err;
        }
    },

    // --- Auth Management ---
    checkAuthStatus() {
        if (this.token && !this.user) {
            this.apiCall('/api/auth/me')
                .then(res => {
                    this.user = res.user;
                    localStorage.setItem('quizgen_user', JSON.stringify(this.user));
                    this.renderNavbar();
                })
                .catch(() => this.logoutSilently());
        }
    },

    logoutSilently() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('quizgen_token');
        localStorage.removeItem('quizgen_user');
        this.renderNavbar();
        this.navigateTo('home');
    },

    logout() {
        this.logoutSilently();
        this.showToast('Logged out successfully.', 'success');
    },

    // --- View Navigation ---
    navigateTo(viewId) {
        this.currentView = viewId;
        document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
        const target = document.getElementById(`view-${viewId}`);
        if (target) target.classList.add('active');

        // Refresh dynamic view contents
        if (viewId === 'faculty-dashboard') this.loadFacultyDashboard();
        if (viewId === 'student-dashboard') this.loadStudentDashboard();

        this.renderNavbar();
    },

    navigateToDashboard() {
        if (!this.user) return this.navigateTo('home');
        this.navigateTo(this.user.role === 'faculty' ? 'faculty-dashboard' : 'student-dashboard');
    },

    renderNavbar() {
        const menu = document.getElementById('nav-menu');
        const userArea = document.getElementById('nav-user-area');

        if (!this.user) {
            menu.innerHTML = `
                <a class="nav-link ${this.currentView === 'home' ? 'active' : ''}" onclick="app.navigateTo('home')">Home</a>
            `;
            userArea.innerHTML = `
                <button class="btn btn-outline" onclick="app.showAuthModal('login')"><i class="fa-solid fa-right-to-bracket"></i> Login</button>
                <button class="btn btn-primary" onclick="app.showAuthModal('register')"><i class="fa-solid fa-user-plus"></i> Register</button>
            `;
        } else {
            if (this.user.role === 'faculty') {
                menu.innerHTML = `
                    <a class="nav-link ${this.currentView === 'faculty-dashboard' ? 'active' : ''}" onclick="app.navigateTo('faculty-dashboard')">Faculty Portal</a>
                    <a class="nav-link ${this.currentView === 'create-quiz' ? 'active' : ''}" onclick="app.navigateTo('create-quiz')">+ Create AI Quiz</a>
                `;
            } else {
                menu.innerHTML = `
                    <a class="nav-link ${this.currentView === 'student-dashboard' ? 'active' : ''}" onclick="app.navigateTo('student-dashboard')">Student Hub</a>
                `;
            }

            userArea.innerHTML = `
                <div class="user-badge" style="display:flex; align-items:center; gap:0.5rem;">
                    <span class="pill-badge pill-violet"><i class="fa-solid fa-user"></i> ${this.user.name} (${this.user.role})</span>
                    <button class="btn btn-secondary btn-sm" onclick="app.logout()"><i class="fa-solid fa-right-from-bracket"></i> Logout</button>
                </div>
            `;
        }
    },

    handleHeroGetStarted() {
        if (!this.user) {
            this.showAuthModal('register');
        } else {
            this.navigateToDashboard();
        }
    },

    // --- Auth Modal & Forms ---
    showAuthModal(type = 'login') {
        const modal = document.getElementById('auth-modal');
        const container = document.getElementById('auth-form-container');
        
        if (type === 'login') {
            container.innerHTML = `
                <h2><i class="fa-solid fa-right-to-bracket text-violet"></i> Sign In to QuizGen AI</h2>
                <form onsubmit="app.handleLoginSubmit(event)" class="mt-3">
                    <div class="form-group">
                        <label>Email Address</label>
                        <input type="email" id="login-email" required placeholder="faculty@quizgen.edu or student@quizgen.edu">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="login-password" required placeholder="••••••••">
                    </div>
                    <button type="submit" class="btn btn-primary btn-block"><i class="fa-solid fa-arrow-right-to-bracket"></i> Login</button>
                    <p class="mt-3 text-center" style="font-size:0.9rem; color:var(--text-muted)">
                        Don't have an account? <a href="#" onclick="app.showAuthModal('register')" style="color:var(--violet-light)">Register here</a>
                    </p>
                </form>
            `;
        } else {
            container.innerHTML = `
                <h2><i class="fa-solid fa-user-plus text-violet"></i> Create Your Account</h2>
                <form onsubmit="app.handleRegisterSubmit(event)" class="mt-3">
                    <div class="form-group">
                        <label>Full Name</label>
                        <input type="text" id="reg-name" required placeholder="Dr. Sarah Smith or Student John">
                    </div>
                    <div class="form-group">
                        <label>Email Address</label>
                        <input type="email" id="reg-email" required placeholder="name@domain.edu">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="reg-password" required placeholder="••••••••">
                    </div>
                    <div class="form-group">
                        <label>Account Role</label>
                        <select id="reg-role" required>
                            <option value="faculty">Faculty / Instructor</option>
                            <option value="student">Student</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary btn-block"><i class="fa-solid fa-user-check"></i> Register Account</button>
                    <p class="mt-3 text-center" style="font-size:0.9rem; color:var(--text-muted)">
                        Already registered? <a href="#" onclick="app.showAuthModal('login')" style="color:var(--violet-light)">Sign in</a>
                    </p>
                </form>
            `;
        }
        modal.classList.remove('hidden');
    },

    closeAuthModal() {
        document.getElementById('auth-modal').classList.add('hidden');
    },

    async handleLoginSubmit(e) {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            const data = await this.apiCall('/api/auth/login', 'POST', { email, password });
            this.token = data.access_token;
            this.user = data.user;
            localStorage.setItem('quizgen_token', this.token);
            localStorage.setItem('quizgen_user', JSON.stringify(this.user));
            this.closeAuthModal();
            this.showToast(`Welcome back, ${this.user.name}!`, 'success');
            this.navigateToDashboard();
        } catch (err) {
            // Handled in apiCall
        }
    },

    async handleRegisterSubmit(e) {
        e.preventDefault();
        const name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const role = document.getElementById('reg-role').value;

        try {
            const data = await this.apiCall('/api/auth/register', 'POST', { name, email, password, role });
            this.token = data.access_token;
            this.user = data.user;
            localStorage.setItem('quizgen_token', this.token);
            localStorage.setItem('quizgen_user', JSON.stringify(this.user));
            this.closeAuthModal();
            this.showToast(`Account created successfully as ${role.toUpperCase()}!`, 'success');
            this.navigateToDashboard();
        } catch (err) {
            // Handled
        }
    },

    // --- Faculty Dashboard Loading ---
    async loadFacultyDashboard() {
        if (!this.user || this.user.role !== 'faculty') return;

        try {
            const [summary, quizzesData, reportsData] = await Promise.all([
                this.apiCall('/api/analytics/faculty-summary'),
                this.apiCall('/api/quizzes/'),
                this.apiCall('/api/reports/faculty/pending')
            ]);

            // Stats
            document.getElementById('stat-total-quizzes').innerText = summary.total_quizzes;
            document.getElementById('stat-pending-approvals').innerText = summary.total_quizzes - summary.published_quizzes;
            document.getElementById('stat-published-quizzes').innerText = summary.published_quizzes;
            document.getElementById('stat-total-submissions').innerText = summary.total_submissions;

            // Quizzes Table
            const quizBody = document.getElementById('faculty-quiz-table-body');
            if (!quizzesData.quizzes || quizzesData.quizzes.length === 0) {
                quizBody.innerHTML = `<tr><td colspan="6" class="text-center">No quizzes created yet. Click "+ Create New AI Quiz" to get started!</td></tr>`;
            } else {
                quizBody.innerHTML = quizzesData.quizzes.map(q => {
                    const statusPill = q.status === 'published' ? '<span class="pill-badge pill-emerald">Published</span>' :
                                      q.status === 'approved' ? '<span class="pill-badge pill-amber">Approved (Ready)</span>' :
                                      '<span class="pill-badge pill-rose">Pending Approval</span>';
                    return `
                        <tr>
                            <td><strong>${q.title}</strong><br><small class="text-muted">${q.topic}</small></td>
                            <td><span class="pill-badge">${q.difficulty}</span></td>
                            <td>${q.question_count} Items</td>
                            <td>${statusPill}</td>
                            <td>${new Date(q.created_at).toLocaleDateString()}</td>
                            <td>
                                <button class="btn btn-secondary btn-sm" onclick="app.viewQuizApproval(${q.id})">
                                    <i class="fa-solid fa-eye"></i> Review / Edit
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
            }

            // Reports Table
            const repBody = document.getElementById('faculty-reports-table-body');
            if (!reportsData.reports || reportsData.reports.length === 0) {
                repBody.innerHTML = `<tr><td colspan="6" class="text-center">No student weak-area reports logged yet.</td></tr>`;
            } else {
                repBody.innerHTML = reportsData.reports.map(r => {
                    const weakList = r.weak_topics.map(w => `<span class="pill-badge pill-rose">${w.subtopic} (${w.accuracy}%)</span>`).join(' ');
                    const statusBadge = r.status === 'faculty_approved' ?
                        '<span class="pill-badge pill-emerald"><i class="fa-solid fa-check"></i> Approved</span>' :
                        '<span class="pill-badge pill-amber">Pending Faculty Signoff</span>';
                    
                    return `
                        <tr>
                            <td><strong>${r.student_name}</strong><br><small class="text-muted">${r.student_email}</small></td>
                            <td>${r.quiz_title}</td>
                            <td><strong>${r.score} / ${r.max_score} (${r.percentage}%)</strong></td>
                            <td>${weakList || 'None'}</td>
                            <td>${statusBadge}</td>
                            <td>
                                ${r.status !== 'faculty_approved' ?
                                    `<button class="btn btn-primary btn-sm" onclick="app.handleApproveReport(${r.id})"><i class="fa-solid fa-pen-to-square"></i> Review & Signoff</button>` :
                                    `<span class="text-muted"><i class="fa-solid fa-circle-check text-emerald"></i> Signed off</span>`
                                }
                            </td>
                        </tr>
                    `;
                }).join('');
            }

        } catch (err) {
            console.error("Dashboard error:", err);
        }
    },

    // --- Quiz Creation & Agent Stepper ---
    async handleCreateQuiz(e) {
        e.preventDefault();
        const title = document.getElementById('quiz-title').value;
        const topic = document.getElementById('quiz-topic').value;
        const difficulty = document.getElementById('quiz-difficulty').value;
        const num_questions = parseInt(document.getElementById('quiz-count').value);

        const types = [];
        if (document.getElementById('qt-mcq').checked) types.push('mcq');
        if (document.getElementById('qt-tf').checked) types.push('tf');
        if (document.getElementById('qt-short').checked) types.push('short_answer');

        if (types.length === 0) {
            return this.showToast('Please select at least one question type.', 'error');
        }

        const btn = document.getElementById('btn-generate-submit');
        const stepper = document.getElementById('agent-stepper');
        btn.disabled = true;
        stepper.classList.remove('hidden');

        // Simulate multi-agent stepper visual feedback
        const s1 = document.getElementById('stepper-step-1');
        const s2 = document.getElementById('stepper-step-2');
        const s3 = document.getElementById('stepper-step-3');

        s1.className = 'step-item text-violet';
        s2.className = 'step-item';
        s3.className = 'step-item';

        setTimeout(() => { s2.className = 'step-item text-violet'; }, 800);
        setTimeout(() => { s3.className = 'step-item text-violet'; }, 1600);

        try {
            const data = await this.apiCall('/api/quizzes/generate', 'POST', {
                title, topic, difficulty, num_questions, question_types: types
            });

            this.showToast(`Quiz generated! ${data.flagged_count} item(s) flagged for human verification.`, 'success');
            btn.disabled = false;
            stepper.classList.add('hidden');
            this.viewQuizApproval(data.quiz_id);
        } catch (err) {
            btn.disabled = false;
            stepper.classList.add('hidden');
        }
    },

    // --- Quiz Preview & Human Approval ---
    async viewQuizApproval(quizId) {
        try {
            const data = await this.apiCall(`/api/quizzes/${quizId}`);
            this.currentQuizPreview = data.quiz;
            this.renderQuizApprovalView();
            this.navigateTo('quiz-approval');
        } catch (err) {}
    },

    renderQuizApprovalView() {
        const q = this.currentQuizPreview;
        if (!q) return;

        document.getElementById('preview-quiz-title').innerText = q.title;
        document.getElementById('preview-quiz-meta').innerText = `Topic: ${q.topic} | Difficulty: ${q.difficulty} | Total Items: ${q.questions.length}`;
        
        const statusEl = document.getElementById('preview-quiz-status');
        statusEl.className = `pill-badge ${q.status === 'published' ? 'pill-emerald' : q.status === 'approved' ? 'pill-amber' : 'pill-rose'}`;
        statusEl.innerText = q.status.toUpperCase().replace('_', ' ');

        const container = document.getElementById('approval-questions-container');
        container.innerHTML = q.questions.map((item, idx) => {
            const isFlagged = item.status === 'flagged';
            const qualityBadge = item.quality_score >= 0.85 ?
                `<span class="pill-badge pill-emerald"><i class="fa-solid fa-shield-check"></i> Quality Score: ${item.quality_score}</span>` :
                `<span class="pill-badge pill-amber"><i class="fa-solid fa-triangle-exclamation"></i> Flagged Score: ${item.quality_score}</span>`;

            let optionsHtml = '';
            if (item.question_type === 'mcq' && item.options) {
                optionsHtml = `<div class="q-option-list">` +
                    item.options.map(opt => `<div class="q-option-item ${opt === item.correct_answer ? 'correct' : ''}">Choice: ${opt} ${opt === item.correct_answer ? '✓ (Correct)' : ''}</div>`).join('') +
                    `</div>`;
            } else if (item.question_type === 'tf') {
                optionsHtml = `<div class="q-option-list"><div class="q-option-item correct">Answer: ${item.correct_answer}</div></div>`;
            } else {
                optionsHtml = `<div class="q-option-list"><div class="q-option-item correct">Canonical Answer Key: ${item.correct_answer}</div></div>`;
            }

            return `
                <div class="question-card ${isFlagged ? 'flagged' : ''}">
                    <div class="question-card-header">
                        <div>
                            <strong>Item #${idx + 1} (${item.question_type.toUpperCase()}) — Subtopic: ${item.subtopic || 'General'}</strong>
                            <div class="mt-1">${qualityBadge} <span class="pill-badge">${item.status}</span></div>
                        </div>
                        <div class="gap-2 flex-end">
                            <button class="btn btn-secondary btn-sm" onclick="app.openEditQuestionModal(${item.id})"><i class="fa-solid fa-pen"></i> Edit Item</button>
                            <button class="btn btn-success btn-sm" onclick="app.handleApproveQuestion(${item.id})"><i class="fa-solid fa-check"></i> Approve Item</button>
                        </div>
                    </div>

                    <h4 class="mt-2">${item.question_text}</h4>
                    ${optionsHtml}

                    <div class="mt-2 text-muted" style="font-size:0.9rem; background:rgba(0,0,0,0.2); padding:0.6rem; border-radius:4px;">
                        <strong><i class="fa-solid fa-lightbulb text-amber"></i> AI Explanation Key:</strong> ${item.explanation}
                    </div>

                    ${item.feedback_notes ? `<div class="mt-2 text-amber" style="font-size:0.85rem;"><i class="fa-solid fa-circle-info"></i> Auditor Note: ${item.feedback_notes}</div>` : ''}
                </div>
            `;
        }).join('');
    },

    // --- Faculty Editing & Approval Handlers ---
    openEditQuestionModal(qId) {
        const q = this.currentQuizPreview.questions.find(item => item.id === qId);
        if (!q) return;

        document.getElementById('edit-q-id').value = q.id;
        document.getElementById('edit-q-text').value = q.question_text;
        document.getElementById('edit-q-correct').value = q.correct_answer;
        document.getElementById('edit-q-explanation').value = q.explanation;
        document.getElementById('edit-q-subtopic').value = q.subtopic || '';

        const optsContainer = document.getElementById('edit-q-options-container');
        if (q.question_type === 'mcq') {
            optsContainer.classList.remove('hidden');
            const inputs = optsContainer.querySelectorAll('.edit-opt-input');
            (q.options || []).forEach((opt, idx) => {
                if (inputs[idx]) inputs[idx].value = opt;
            });
        } else {
            optsContainer.classList.add('hidden');
        }

        document.getElementById('edit-question-modal').classList.remove('hidden');
    },

    closeEditQuestionModal() {
        document.getElementById('edit-question-modal').classList.add('hidden');
    },

    async handleSaveEditedQuestion(e) {
        e.preventDefault();
        const qId = parseInt(document.getElementById('edit-q-id').value);
        const quizId = this.currentQuizPreview.id;
        const qText = document.getElementById('edit-q-text').value;
        const correctAns = document.getElementById('edit-q-correct').value;
        const explanation = document.getElementById('edit-q-explanation').value;
        const subtopic = document.getElementById('edit-q-subtopic').value;

        const optsContainer = document.getElementById('edit-q-options-container');
        let options = null;
        if (!optsContainer.classList.contains('hidden')) {
            options = Array.from(optsContainer.querySelectorAll('.edit-opt-input')).map(i => i.value).filter(v => v.trim() !== '');
        }

        try {
            await this.apiCall(`/api/quizzes/${quizId}/questions/${qId}`, 'PUT', {
                question_text: qText,
                correct_answer: correctAns,
                explanation: explanation,
                subtopic: subtopic,
                options: options
            });

            this.showToast('Question updated by faculty.', 'success');
            this.closeEditQuestionModal();
            this.viewQuizApproval(quizId);
        } catch (err) {}
    },

    async handleApproveQuestion(qId) {
        const quizId = this.currentQuizPreview.id;
        try {
            await this.apiCall(`/api/quizzes/${quizId}/questions/${qId}/approve`, 'POST');
            this.showToast(`Question #${qId} approved.`, 'success');
            this.viewQuizApproval(quizId);
        } catch (err) {}
    },

    async handleApproveEntireQuiz() {
        const quizId = this.currentQuizPreview.id;
        try {
            await this.apiCall(`/api/quizzes/${quizId}/approve`, 'POST');
            this.showToast('Entire quiz approved by faculty!', 'success');
            this.viewQuizApproval(quizId);
        } catch (err) {}
    },

    async handlePublishQuiz() {
        const quizId = this.currentQuizPreview.id;
        try {
            const data = await this.apiCall(`/api/quizzes/${quizId}/publish`, 'POST');
            this.showToast(data.message, 'success');
            this.viewQuizApproval(quizId);
        } catch (err) {
            // Handled in apiCall - blocks publishing if unapproved!
        }
    },

    // --- Student Dashboard & Quiz Taking ---
    async loadStudentDashboard() {
        if (!this.user || this.user.role !== 'student') return;

        try {
            const [pubData, subData] = await Promise.all([
                this.apiCall('/api/quizzes/published/list'),
                this.apiCall('/api/submissions/student/my-submissions')
            ]);

            // Published Quizzes Grid
            const grid = document.getElementById('student-published-grid');
            if (!pubData.quizzes || pubData.quizzes.length === 0) {
                grid.innerHTML = `<div class="p-4 text-center text-muted">No published quizzes available right now. Check back soon!</div>`;
            } else {
                grid.innerHTML = pubData.quizzes.map(q => `
                    <div class="quiz-card-student">
                        <div>
                            <span class="pill-badge pill-violet">${q.difficulty}</span>
                            <h3 class="mt-2">${q.title}</h3>
                            <p class="text-muted" style="font-size:0.9rem;">Topic: ${q.topic}</p>
                            <p class="text-muted" style="font-size:0.85rem;">Instructor: ${q.creator_name || 'Faculty'}</p>
                        </div>
                        <button class="btn btn-primary btn-block mt-3" onclick="app.startQuizAttempt(${q.id})">
                            <i class="fa-solid fa-play"></i> Start Quiz Attempt
                        </button>
                    </div>
                `).join('');
            }

            // Submissions History Table
            const subBody = document.getElementById('student-submissions-table-body');
            if (!subData.submissions || subData.submissions.length === 0) {
                subBody.innerHTML = `<tr><td colspan="6" class="text-center">You haven't attempted any quizzes yet.</td></tr>`;
            } else {
                subBody.innerHTML = subData.submissions.map(s => {
                    const statusBadge = s.report_status === 'faculty_approved' ?
                        '<span class="pill-badge pill-emerald"><i class="fa-solid fa-shield-check"></i> Faculty Approved</span>' :
                        '<span class="pill-badge pill-amber">Report Pending Review</span>';

                    return `
                        <tr>
                            <td><strong>${s.quiz_title}</strong><br><small class="text-muted">${s.quiz_topic}</small></td>
                            <td>${s.score} / ${s.max_score}</td>
                            <td><strong>${s.percentage}%</strong></td>
                            <td>${statusBadge}</td>
                            <td>${new Date(s.submitted_at).toLocaleString()}</td>
                            <td>
                                <button class="btn btn-secondary btn-sm" onclick="app.viewSubmissionResult(${s.id})">
                                    <i class="fa-solid fa-chart-pie"></i> View Report
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
            }

        } catch (err) {}
    },

    async startQuizAttempt(quizId) {
        try {
            const data = await this.apiCall(`/api/quizzes/${quizId}`);
            this.currentTakingQuiz = data.quiz;
            this.renderTakeQuizView();
            this.navigateTo('take-quiz');
            this.startTimer();
        } catch (err) {}
    },

    startTimer() {
        if (this.quizTimerInterval) clearInterval(this.quizTimerInterval);
        this.quizTimeSeconds = 0;
        const timerEl = document.getElementById('quiz-timer');

        this.quizTimerInterval = setInterval(() => {
            this.quizTimeSeconds++;
            const m = String(Math.floor(this.quizTimeSeconds / 60)).padStart(2, '0');
            const s = String(this.quizTimeSeconds % 60).padStart(2, '0');
            if (timerEl) timerEl.innerText = `${m}:${s}`;
        }, 1000);
    },

    stopTimer() {
        if (this.quizTimerInterval) clearInterval(this.quizTimerInterval);
    },

    renderTakeQuizView() {
        const q = this.currentTakingQuiz;
        if (!q) return;

        document.getElementById('take-quiz-title').innerText = q.title;
        document.getElementById('take-quiz-topic').innerText = `Topic: ${q.topic} | Difficulty: ${q.difficulty}`;

        const container = document.getElementById('take-questions-container');
        container.innerHTML = q.questions.map((item, idx) => {
            let optionsHtml = '';
            if (item.question_type === 'mcq' && item.options) {
                optionsHtml = item.options.map(opt => `
                    <label class="radio-option">
                        <input type="radio" name="q_${item.id}" value="${opt.replace(/"/g, '&quot;')}" required>
                        <span>${opt}</span>
                    </label>
                `).join('');
            } else if (item.question_type === 'tf') {
                optionsHtml = `
                    <label class="radio-option">
                        <input type="radio" name="q_${item.id}" value="True" required>
                        <span>True</span>
                    </label>
                    <label class="radio-option">
                        <input type="radio" name="q_${item.id}" value="False" required>
                        <span>False</span>
                    </label>
                `;
            } else {
                optionsHtml = `
                    <textarea class="form-group" name="q_${item.id}" rows="3" placeholder="Type your answer here..." required></textarea>
                `;
            }

            return `
                <div class="take-q-block">
                    <h4>Question ${idx + 1}: ${item.question_text}</h4>
                    <div class="mt-2">${optionsHtml}</div>
                </div>
            `;
        }).join('');
    },

    async handleStudentQuizSubmit(e) {
        e.preventDefault();
        this.stopTimer();

        const quiz = this.currentTakingQuiz;
        const answers = {};

        quiz.questions.forEach(item => {
            if (item.question_type === 'short_answer') {
                const txt = document.querySelector(`textarea[name="q_${item.id}"]`);
                answers[item.id] = txt ? txt.value : '';
            } else {
                const rad = document.querySelector(`input[name="q_${item.id}"]:checked`);
                answers[item.id] = rad ? rad.value : '';
            }
        });

        try {
            const data = await this.apiCall(`/api/quizzes/${quiz.id}/submit`, 'POST', { answers });
            this.showToast('Quiz submitted & evaluated by AI Evaluation Agent!', 'success');
            this.renderSubmissionResultView(data);
            this.navigateTo('results-report');
        } catch (err) {}
    },

    // --- Results & Weak-Area Reports Rendering ---
    async viewSubmissionResult(submissionId) {
        try {
            const data = await this.apiCall(`/api/submissions/${submissionId}`);
            this.renderSubmissionResultView({
                score: data.submission.score,
                max_score: data.submission.max_score,
                percentage: data.submission.percentage,
                breakdown: data.answers,
                report: data.report
            });
            this.navigateTo('results-report');
        } catch (err) {}
    },

    renderSubmissionResultView(res) {
        document.getElementById('result-score-pct').innerText = `${res.percentage}%`;
        document.getElementById('result-score-raw').innerText = `${res.score} / ${res.max_score} pts`;

        // Render Weak Area Analysis
        const report = res.report || {};
        const weakContent = document.getElementById('weak-area-content');
        
        const weakBadges = (report.weak_topics || []).map(w =>
            `<span class="pill-badge pill-rose mb-2"><i class="fa-solid fa-circle-exclamation"></i> ${w.subtopic} (${w.accuracy}% accuracy)</span>`
        ).join(' ') || '<span class="text-emerald">No severe weak areas detected!</span>';

        const recsList = (report.recommendations || []).map(rec =>
            `<li class="mb-1"><i class="fa-solid fa-angle-right text-violet"></i> ${rec}</li>`
        ).join('');

        const statusSignoff = report.status === 'faculty_approved' ?
            `<div class="alert alert-info mt-3"><i class="fa-solid fa-circle-check text-emerald"></i> <strong>Faculty Note & Approval:</strong> ${report.faculty_notes || 'Report reviewed and approved by faculty.'}</div>` :
            `<div class="alert alert-warning mt-3"><i class="fa-solid fa-clock"></i> <strong>Faculty Review Status:</strong> Report generated by AI; awaiting faculty sign-off.</div>`;

        weakContent.innerHTML = `
            <div class="mb-3">
                <strong>Target Concepts Needing Attention:</strong><br>
                <div class="mt-2">${weakBadges}</div>
            </div>
            <div>
                <strong>Personalized AI Remedial Plan:</strong>
                <ul style="list-style:none; padding:0; margin-top:0.5rem;">${recsList}</ul>
            </div>
            ${statusSignoff}
        `;

        // Render Breakdown
        const breakdownContainer = document.getElementById('result-breakdown-container');
        breakdownContainer.innerHTML = (res.breakdown || []).map((item, idx) => {
            const isCorrect = item.is_correct === 1 || item.points_awarded >= 0.7;
            const badge = isCorrect ?
                `<span class="pill-badge pill-emerald"><i class="fa-solid fa-check"></i> Correct (+${item.points_awarded} pt)</span>` :
                `<span class="pill-badge pill-rose"><i class="fa-solid fa-xmark"></i> Incorrect (${item.points_awarded} pt)</span>`;

            return `
                <div class="question-card mt-3">
                    <div class="flex-between">
                        <strong>Item #${idx + 1}: ${item.question_text || 'Question'}</strong>
                        ${badge}
                    </div>
                    <div class="mt-2" style="font-size:0.92rem;">
                        <div><strong>Your Submission:</strong> ${item.student_answer || 'No Answer'}</div>
                        <div><strong>Correct Key:</strong> ${item.correct_answer || 'Key'}</div>
                        <div class="text-muted mt-1"><em>${item.feedback}</em></div>
                    </div>
                </div>
            `;
        }).join('');
    },

    // --- Faculty Report Approval ---
    async handleApproveReport(reportId) {
        const notes = prompt("Enter optional faculty note for the student:", "Great progress. Review weak subtopics before next exam.");
        if (notes === null) return;

        try {
            await this.apiCall(`/api/reports/${reportId}/approve`, 'POST', { faculty_notes: notes });
            this.showToast('Weak-area report approved & signed off by faculty.', 'success');
            this.loadFacultyDashboard();
        } catch (err) {}
    },

    // --- Architecture Modal & UI Helpers ---
    showArchitectureModal() {
        document.getElementById('arch-modal').classList.remove('hidden');
    },
    closeArchitectureModal() {
        document.getElementById('arch-modal').classList.add('hidden');
    },

    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fa-solid fa-${type === 'success' ? 'circle-check text-emerald' : 'circle-xmark text-rose'}"></i>
            <span>${message}</span>
        `;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => app.init());
