/**
 * TalentPulse AI — Application Controller
 * 100% Real End-to-End API Integration with Python (spaCy, PDFPlumber), Flask, and PostgreSQL/SQLite.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Dynamic API Base URL: Works both when served by Flask AND when opened directly in browser
    const API_BASE = (window.location.protocol === 'file:' || !window.location.host) 
        ? 'http://127.0.0.1:5000' 
        : '';

    // Application State
    let fileQueue = [];
    let skillsChartInstance = null;
    let debounceTimer = null;
    let notesDebounceTimer = null;
    let selectedForCompare = new Set();
    let currentCandidateId = null;
    let isJdMatchActive = false;
    let currentStatusFilter = "";

    // DOM Elements: Theme Toggle
    const htmlElement = document.documentElement;
    const themeToggleBtn = document.getElementById("themeToggleBtn");
    const themeIcon = document.getElementById("themeIcon");
    const dbDialectBadge = document.getElementById("dbDialectBadge");

    // DOM Elements: Upload & Dropzone
    const dropZone = document.getElementById("dropZone");
    const resumeFileInput = document.getElementById("resumeFileInput");
    const browseFilesBtn = document.getElementById("browseFilesBtn");
    const uploadQueueContainer = document.getElementById("uploadQueueContainer");
    const fileQueueList = document.getElementById("fileQueueList");
    const fileCount = document.getElementById("fileCount");
    const clearQueueBtn = document.getElementById("clearQueueBtn");
    const startUploadBtn = document.getElementById("startUploadBtn");
    const parseProgressContainer = document.getElementById("parseProgressContainer");
    const parseProgressBar = document.getElementById("parseProgressBar");
    const progressPercent = document.getElementById("progressPercent");
    const progressStatusText = document.getElementById("progressStatusText");
    const uploadAlert = document.getElementById("uploadAlert");

    // DOM Elements: Search & Filters
    const searchInput = document.getElementById("searchInput");
    const skillFilterSelect = document.getElementById("skillFilterSelect");
    const degreeFilterSelect = document.getElementById("degreeFilterSelect");
    const expFilterSelect = document.getElementById("expFilterSelect");
    const sortBySelect = document.getElementById("sortBySelect");
    const resetFiltersBtn = document.getElementById("resetFiltersBtn");
    const activeFiltersContainer = document.getElementById("activeFiltersContainer");
    const filterPills = document.getElementById("filterPills");
    const refreshListBtn = document.getElementById("refreshListBtn");
    const statusFilterTabs = document.getElementById("statusFilterTabs");
    const matchBanner = document.getElementById("matchBanner");
    const clearMatchBtn = document.getElementById("clearMatchBtn");

    // DOM Elements: Feed & Stats
    const candidatesList = document.getElementById("candidatesList");
    const candidatesLoading = document.getElementById("candidatesLoading");
    const candidatesEmptyState = document.getElementById("candidatesEmptyState");
    const candidateCountDisplay = document.getElementById("candidateCountDisplay");
    const kpiTotalResumes = document.getElementById("kpiTotalResumes");
    const kpiTopSkill = document.getElementById("kpiTopSkill");
    const kpiAvgExperience = document.getElementById("kpiAvgExperience");
    const kpiShortlistedCount = document.getElementById("kpiShortlistedCount");
    const countAll = document.getElementById("countAll");

    // DOM Elements: Candidate Modal
    const candidateModal = document.getElementById("candidateModal");
    const modalAvatar = document.getElementById("modalAvatar");
    const modalName = document.getElementById("modalName");
    const modalStatusSelect = document.getElementById("modalStatusSelect");
    const modalEmail = document.getElementById("modalEmail");
    const modalPhone = document.getElementById("modalPhone");
    const modalLocation = document.getElementById("modalLocation");
    const modalSummary = document.getElementById("modalSummary");
    const modalNotesTextarea = document.getElementById("modalNotesTextarea");
    const notesSavedIndicator = document.getElementById("notesSavedIndicator");
    const modalCategorizedSkills = document.getElementById("modalCategorizedSkills");
    const modalExperienceTimeline = document.getElementById("modalExperienceTimeline");
    const modalEducationList = document.getElementById("modalEducationList");
    const modalRawText = document.getElementById("modalRawText");
    const copyRawTextBtn = document.getElementById("copyRawTextBtn");
    const modalDownloadBtn = document.getElementById("modalDownloadBtn");

    // DOM Elements: JD Match Modal
    const jdMatchModal = document.getElementById("jdMatchModal");
    const openJdModalBtn = document.getElementById("openJdModalBtn");
    const jdInputText = document.getElementById("jdInputText");
    const runJdMatchBtn = document.getElementById("runJdMatchBtn");

    // DOM Elements: Comparison Modal
    const compareBtn = document.getElementById("compareBtn");
    const compareCountBadge = document.getElementById("compareCountBadge");
    const compareModal = document.getElementById("compareModal");
    const compareMatrixContainer = document.getElementById("compareMatrixContainer");

    // -------------------------------------------------------------
    // Initialization
    // -------------------------------------------------------------
    initTheme();
    initModalControls();
    checkBackendHealth();
    initSkillsDropdown();
    loadStats();
    loadCandidates();

    function initTheme() {
        const savedTheme = localStorage.getItem("talentpulse_theme") || "dark";
        setTheme(savedTheme);

        if (themeToggleBtn) {
            themeToggleBtn.addEventListener("click", () => {
                const currentTheme = htmlElement.getAttribute("data-bs-theme") || "dark";
                const newTheme = currentTheme === "dark" ? "light" : "dark";
                setTheme(newTheme);
            });
        }
    }

    function setTheme(theme) {
        htmlElement.setAttribute("data-bs-theme", theme);
        if (theme === "light") {
            document.body.classList.add("light-mode");
            if (themeIcon) themeIcon.textContent = "🌙";
        } else {
            document.body.classList.remove("light-mode");
            if (themeIcon) themeIcon.textContent = "☀️";
        }
        localStorage.setItem("talentpulse_theme", theme);
    }

    // Check Real Backend Health & Display Database Engine
    async function checkBackendHealth() {
        try {
            const res = await fetch(`${API_BASE}/api/status`);
            if (res.ok) {
                const data = await res.json();
                if (dbDialectBadge) {
                    dbDialectBadge.innerHTML = `Database: <strong style="color: var(--accent-emerald);">${escapeHtml(data.database_dialect)}</strong>`;
                }
            }
        } catch (e) {
            if (dbDialectBadge) {
                dbDialectBadge.innerHTML = `Backend: <strong style="color: var(--accent-amber);">Connecting...</strong>`;
            }
        }
    }

    // Modal Open/Close Controls
    function initModalControls() {
        if (openJdModalBtn) {
            openJdModalBtn.addEventListener("click", () => openModal("jdMatchModal"));
        }
        if (compareBtn) {
            compareBtn.addEventListener("click", () => {
                if (selectedForCompare.size >= 2) {
                    openModal("compareModal");
                    generateComparisonMatrix();
                }
            });
        }

        // Terms and Conditions Modal Triggers
        const openTermsModalBtn = document.getElementById("openTermsModalBtn");
        if (openTermsModalBtn) {
            openTermsModalBtn.addEventListener("click", () => openModal("termsModal"));
        }

        // Privacy Modal Triggers
        const openPrivacyModalBtn = document.getElementById("openPrivacyModalBtn");
        if (openPrivacyModalBtn) {
            openPrivacyModalBtn.addEventListener("click", () => openModal("privacyModal"));
        }

        // Footer Shortcut Buttons
        document.querySelectorAll(".footer-open-jd-btn").forEach(btn => {
            btn.addEventListener("click", () => openModal("jdMatchModal"));
        });

        document.querySelectorAll(".footer-open-compare-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                if (selectedForCompare.size >= 2) {
                    openModal("compareModal");
                    generateComparisonMatrix();
                } else {
                    alert("Please select at least 2 candidate cards using the checkboxes in the candidate feed to compare them.");
                }
            });
        });

        // Back to top smooth scroll
        const backToTopBtn = document.getElementById("backToTopBtn");
        if (backToTopBtn) {
            backToTopBtn.addEventListener("click", () => {
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
        }

        document.querySelectorAll(".modal-close-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const modalId = btn.dataset.modal;
                if (modalId) closeModal(modalId);
            });
        });

        document.querySelectorAll(".tp-modal-overlay").forEach(overlay => {
            overlay.addEventListener("click", (e) => {
                if (e.target === overlay) {
                    overlay.classList.remove("show");
                }
            });
        });
    }

    function openModal(id) {
        const el = document.getElementById(id);
        if (el) el.classList.add("show");
    }

    function closeModal(id) {
        const el = document.getElementById(id);
        if (el) el.classList.remove("show");
    }

    // -------------------------------------------------------------
    // Drag & Drop / File Selection
    // -------------------------------------------------------------
    if (dropZone && resumeFileInput) {
        if (browseFilesBtn) {
            browseFilesBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                resumeFileInput.click();
            });
        }

        dropZone.addEventListener("click", () => resumeFileInput.click());

        ["dragenter", "dragover"].forEach(evt => {
            dropZone.addEventListener(evt, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add("dragover");
            });
        });

        ["dragleave", "drop"].forEach(evt => {
            dropZone.addEventListener(evt, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove("dragover");
            });
        });

        dropZone.addEventListener("drop", (e) => {
            const droppedFiles = Array.from(e.dataTransfer.files);
            handleFilesSelected(droppedFiles);
        });

        resumeFileInput.addEventListener("change", (e) => {
            const selectedFiles = Array.from(e.target.files);
            handleFilesSelected(selectedFiles);
            resumeFileInput.value = "";
        });
    }

    function handleFilesSelected(files) {
        const validExtensions = [".pdf", ".docx", ".doc", ".txt"];
        files.forEach(file => {
            const ext = "." + file.name.split(".").pop().toLowerCase();
            if (validExtensions.includes(ext)) {
                if (!fileQueue.some(f => f.name === file.name && f.size === file.size)) {
                    fileQueue.push(file);
                }
            }
        });
        updateQueueUI();
    }

    function updateQueueUI() {
        if (!uploadQueueContainer) return;
        if (fileQueue.length > 0) {
            uploadQueueContainer.style.display = "block";
            if (fileCount) fileCount.textContent = fileQueue.length;
            if (fileQueueList) {
                fileQueueList.innerHTML = fileQueue.map((file, idx) => `
                    <li class="queue-item">
                        <div style="display:flex; align-items:center; gap:0.4rem;">
                            <span>📄</span>
                            <span class="queue-item-name">${escapeHtml(file.name)}</span>
                            <span style="font-size:0.7rem; color:var(--text-dim);">(${(file.size / (1024 * 1024)).toFixed(2)} MB)</span>
                        </div>
                        <button class="remove-file-btn" data-index="${idx}" style="background:none; border:none; color:var(--accent-rose); cursor:pointer;">✕</button>
                    </li>
                `).join("");

                document.querySelectorAll(".remove-file-btn").forEach(btn => {
                    btn.addEventListener("click", (e) => {
                        const idx = parseInt(e.currentTarget.dataset.index);
                        fileQueue.splice(idx, 1);
                        updateQueueUI();
                    });
                });
            }
        } else {
            uploadQueueContainer.style.display = "none";
        }
    }

    if (clearQueueBtn) {
        clearQueueBtn.addEventListener("click", () => {
            fileQueue = [];
            updateQueueUI();
        });
    }

    // -------------------------------------------------------------
    // Real Upload & Parsing Execution via Flask API
    // -------------------------------------------------------------
    if (startUploadBtn) {
        startUploadBtn.addEventListener("click", async () => {
            if (fileQueue.length === 0) return;

            startUploadBtn.disabled = true;
            if (parseProgressContainer) parseProgressContainer.style.display = "block";
            hideAlert();

            updateProgress(20, "Extracting text and layout with PDFPlumber...");

            const formData = new FormData();
            fileQueue.forEach(file => formData.append("resumes", file));

            try {
                setTimeout(() => updateProgress(50, "Running Named Entity Recognition (spaCy)..."), 500);
                setTimeout(() => updateProgress(80, "Classifying competencies & education patterns..."), 1000);

                const response = await fetch(`${API_BASE}/api/upload`, {
                    method: "POST",
                    body: formData
                });

                updateProgress(100, "Saving records into database...");
                const data = await response.json();

                if (response.ok && data.success) {
                    showAlert("success", `✓ Successfully parsed & stored ${data.parsed_count} candidate resume(s)!`);
                    fileQueue = [];
                    updateQueueUI();
                    loadCandidates();
                    loadStats();
                    triggerConfetti();
                } else {
                    const errMsg = (data.errors && data.errors.length > 0) 
                        ? data.errors.map(e => `${e.file}: ${e.error}`).join("; ") 
                        : (data.error || "Failed to parse resumes.");
                    showAlert("danger", errMsg);
                }
            } catch (err) {
                showAlert("danger", `Network error: Unable to connect to backend at ${API_BASE}. Ensure python app.py is running.`);
            } finally {
                startUploadBtn.disabled = false;
                setTimeout(() => {
                    if (parseProgressContainer) parseProgressContainer.style.display = "none";
                    updateProgress(0, "");
                }, 1500);
            }
        });
    }

    function updateProgress(percent, status) {
        if (parseProgressBar) parseProgressBar.style.width = `${percent}%`;
        if (progressPercent) progressPercent.textContent = `${percent}%`;
        if (progressStatusText && status) {
            progressStatusText.textContent = status;
        }
    }

    function triggerConfetti() {
        if (typeof confetti === "function") {
            confetti({
                particleCount: 70,
                spread: 75,
                origin: { y: 0.65 },
                colors: ['#6366f1', '#38bdf8', '#10b981', '#f59e0b']
            });
        }
    }

    function showAlert(type, text) {
        if (!uploadAlert) return;
        uploadAlert.style.display = "block";
        uploadAlert.style.background = type === "success" ? "rgba(16, 185, 129, 0.2)" : "rgba(244, 63, 94, 0.2)";
        uploadAlert.style.color = type === "success" ? "#34d399" : "#f43f5e";
        uploadAlert.style.border = type === "success" ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid rgba(244, 63, 94, 0.3)";
        uploadAlert.textContent = text;
    }

    function hideAlert() {
        if (uploadAlert) uploadAlert.style.display = "none";
    }

    // -------------------------------------------------------------
    // Status Filter Tabs
    // -------------------------------------------------------------
    if (statusFilterTabs) {
        statusFilterTabs.querySelectorAll(".pipeline-pill-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                statusFilterTabs.querySelectorAll(".pipeline-pill-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                currentStatusFilter = btn.dataset.status;
                loadCandidates();
            });
        });
    }

    // -------------------------------------------------------------
    // Candidate Search & Filter
    // -------------------------------------------------------------
    if (searchInput) {
        searchInput.addEventListener("input", () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                updateActiveFilters();
                loadCandidates();
            }, 250);
        });
    }

    if (skillFilterSelect) {
        skillFilterSelect.addEventListener("change", () => {
            updateActiveFilters();
            loadCandidates();
        });
    }

    if (degreeFilterSelect) {
        degreeFilterSelect.addEventListener("change", () => {
            updateActiveFilters();
            loadCandidates();
        });
    }

    if (expFilterSelect) {
        expFilterSelect.addEventListener("change", () => {
            updateActiveFilters();
            loadCandidates();
        });
    }

    if (sortBySelect) {
        sortBySelect.addEventListener("change", () => loadCandidates());
    }

    if (refreshListBtn) {
        refreshListBtn.addEventListener("click", () => {
            loadCandidates();
            loadStats();
        });
    }

    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener("click", () => {
            if (searchInput) searchInput.value = "";
            if (skillFilterSelect) skillFilterSelect.value = "";
            if (degreeFilterSelect) degreeFilterSelect.value = "";
            if (expFilterSelect) expFilterSelect.value = "";
            if (sortBySelect) sortBySelect.value = "parsed_at:desc";
            currentStatusFilter = "";
            if (statusFilterTabs) {
                statusFilterTabs.querySelectorAll(".pipeline-pill-btn").forEach(b => b.classList.remove("active"));
                const allBtn = statusFilterTabs.querySelector('[data-status=""]');
                if (allBtn) allBtn.classList.add("active");
            }
            isJdMatchActive = false;
            if (matchBanner) matchBanner.style.display = "none";
            updateActiveFilters();
            loadCandidates();
        });
    }

    if (clearMatchBtn) {
        clearMatchBtn.addEventListener("click", () => {
            isJdMatchActive = false;
            if (matchBanner) matchBanner.style.display = "none";
            loadCandidates();
        });
    }

    function updateActiveFilters() {
        const filters = [];
        if (searchInput && searchInput.value.trim()) filters.push({ label: `"${searchInput.value.trim()}"` });
        if (skillFilterSelect && skillFilterSelect.value) filters.push({ label: `Skill: ${skillFilterSelect.value}` });
        if (degreeFilterSelect && degreeFilterSelect.value) filters.push({ label: `Degree: ${degreeFilterSelect.value}` });
        if (expFilterSelect && expFilterSelect.value) filters.push({ label: `Exp: ${expFilterSelect.value}+ yrs` });
        if (currentStatusFilter) filters.push({ label: `Status: ${currentStatusFilter}` });

        if (activeFiltersContainer && filterPills) {
            if (filters.length > 0) {
                activeFiltersContainer.style.display = "flex";
                filterPills.innerHTML = filters.map(f => `
                    <span class="meta-chip" style="background: rgba(99, 102, 241, 0.15); color: var(--primary);">
                        ${escapeHtml(f.label)}
                    </span>
                `).join("");
            } else {
                activeFiltersContainer.style.display = "none";
            }
        }
    }

    // -------------------------------------------------------------
    // Real Load Candidates Feed from Database
    // -------------------------------------------------------------
    async function loadCandidates() {
        if (isJdMatchActive) return;

        if (candidatesLoading) candidatesLoading.style.display = "block";
        if (candidatesEmptyState) candidatesEmptyState.style.display = "none";
        if (candidatesList) candidatesList.innerHTML = "";

        const [sort_by, order] = (sortBySelect ? sortBySelect.value : "parsed_at:desc").split(":");
        const params = new URLSearchParams({
            query: searchInput ? searchInput.value.trim() : "",
            skills: skillFilterSelect ? skillFilterSelect.value : "",
            degree: degreeFilterSelect ? degreeFilterSelect.value : "",
            status: currentStatusFilter,
            sort_by: sort_by || "parsed_at",
            order: order || "desc"
        });
        if (expFilterSelect && expFilterSelect.value) params.append("min_exp", expFilterSelect.value);

        try {
            const res = await fetch(`${API_BASE}/api/candidates?${params.toString()}`);
            if (!res.ok) throw new Error("Could not fetch candidates");

            const data = await res.json();
            const candidates = data.candidates || [];
            const totalCount = data.total;

            if (candidateCountDisplay) candidateCountDisplay.textContent = totalCount;
            if (countAll) countAll.textContent = totalCount;

            if (candidates.length === 0) {
                if (candidatesEmptyState) candidatesEmptyState.style.display = "block";
            } else {
                if (candidatesList) {
                    candidatesList.innerHTML = candidates.map(c => renderCandidateCard(c)).join("");
                    attachCandidateCardEvents();
                }
            }
        } catch (e) {
            console.error("Error loading candidates from database:", e);
            if (candidatesEmptyState) {
                candidatesEmptyState.style.display = "block";
                candidatesEmptyState.querySelector("p").textContent = "Unable to connect to the database. Please ensure Flask app is running on port 5000.";
            }
        } finally {
            if (candidatesLoading) candidatesLoading.style.display = "none";
        }
    }

    function renderCandidateCard(c) {
        const initials = getInitials(c.name);
        const topSkills = (c.skills || []).slice(0, 7);
        const isChecked = selectedForCompare.has(c.id);
        const statusClass = getStatusClass(c.status);

        let matchScoreHtml = "";
        if (c.match_score !== undefined) {
            const scoreClass = c.match_score >= 70 ? "score-high" : (c.match_score >= 40 ? "score-med" : "score-low");
            matchScoreHtml = `
                <div class="fit-score-pill ${scoreClass}" style="display:inline-flex;align-items:center;gap:0.35rem;">
                    <img src="/static/images/svastik-universe-logo.png" class="svastik-logo-inline" alt="Score">
                    <span>${c.match_score}% Fit</span>
                </div>
            `;
        }

        return `
            <div class="candidate-card" data-id="${c.id}">
                <div class="candidate-card-layout">
                    <div class="candidate-left">
                        <!-- Compare Checkbox -->
                        <div style="margin-top: 0.35rem;" title="Select for side-by-side comparison">
                            <input class="compare-checkbox" type="checkbox" data-id="${c.id}" ${isChecked ? "checked" : ""} style="width:16px;height:16px;cursor:pointer;">
                        </div>

                        <!-- Monogram Avatar -->
                        <div class="candidate-avatar">${initials}</div>

                        <!-- Candidate Core Details -->
                        <div style="flex: 1;">
                            <div class="candidate-name-row">
                                <h4 class="candidate-name">${escapeHtml(c.name)}</h4>
                                <span class="status-pill ${statusClass}">${escapeHtml(c.status || "New")}</span>
                                <span class="meta-chip">💼 ${c.total_experience_years} yrs exp</span>
                                <span class="meta-chip">📄 ${escapeHtml(c.file_name || 'Resume')}</span>
                                ${matchScoreHtml}
                            </div>

                            <div class="contact-row">
                                <span>📧 ${escapeHtml(c.email)}</span>
                                <span>📞 ${escapeHtml(c.phone)}</span>
                                ${c.location && c.location !== 'N/A' ? `<span>📍 ${escapeHtml(c.location)}</span>` : ''}
                            </div>

                            ${c.summary ? `<div class="summary-preview">${escapeHtml(c.summary)}</div>` : ''}

                            <!-- Skills Container -->
                            <div class="skills-container">
                                ${topSkills.map(s => `<span class="skill-chip ${getSkillClass(s.category)}">${escapeHtml(s.name)}</span>`).join("")}
                                ${(c.skills || []).length > 7 ? `<span class="meta-chip">+${c.skills.length - 7} more</span>` : ''}
                            </div>
                        </div>
                    </div>

                    <!-- Actions -->
                    <div style="display:flex; align-items:center; gap:0.5rem;">
                        <button class="tp-btn tp-btn-glass view-candidate-btn" data-id="${c.id}" style="padding:0.4rem 0.9rem; font-size:0.75rem;">
                            Profile
                        </button>
                        <a href="${API_BASE}/api/candidates/${c.id}/download" class="tp-btn-icon" title="Download Document" download>
                            ⬇
                        </a>
                        <button class="tp-btn-icon text-danger delete-candidate-btn" data-id="${c.id}" data-name="${escapeHtml(c.name)}" title="Delete Candidate">
                            🗑
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function attachCandidateCardEvents() {
        document.querySelectorAll(".view-candidate-btn").forEach(btn => {
            btn.addEventListener("click", () => openCandidateProfile(btn.dataset.id));
        });

        document.querySelectorAll(".delete-candidate-btn").forEach(btn => {
            btn.addEventListener("click", () => deleteCandidate(btn.dataset.id, btn.dataset.name));
        });

        document.querySelectorAll(".compare-checkbox").forEach(chk => {
            chk.addEventListener("change", (e) => {
                const id = parseInt(e.target.dataset.id);
                if (e.target.checked) {
                    if (selectedForCompare.size >= 3) {
                        alert("You can compare up to 3 candidates simultaneously.");
                        e.target.checked = false;
                        return;
                    }
                    selectedForCompare.add(id);
                } else {
                    selectedForCompare.delete(id);
                }
                updateCompareButton();
            });
        });
    }

    function updateCompareButton() {
        if (!compareCountBadge || !compareBtn) return;
        const count = selectedForCompare.size;
        compareCountBadge.textContent = count;
        compareBtn.disabled = count < 2;
    }

    // -------------------------------------------------------------
    // Real Candidate Profile Details
    // -------------------------------------------------------------
    async function openCandidateProfile(candidateId) {
        currentCandidateId = candidateId;

        try {
            const res = await fetch(`${API_BASE}/api/candidates/${candidateId}`);
            if (!res.ok) throw new Error("Could not fetch candidate details from database");
            const c = await res.json();

            if (modalAvatar) modalAvatar.textContent = getInitials(c.name);
            if (modalName) modalName.textContent = c.name;
            if (modalStatusSelect) modalStatusSelect.value = c.status || "New";
            if (modalEmail) modalEmail.textContent = `📧 ${c.email || 'N/A'}`;
            if (modalPhone) modalPhone.textContent = `📞 ${c.phone || 'N/A'}`;
            if (modalLocation) modalLocation.textContent = `📍 ${c.location || 'N/A'}`;
            if (modalSummary) modalSummary.textContent = c.summary || "No specific executive summary detected.";
            if (modalNotesTextarea) modalNotesTextarea.value = c.notes || "";
            if (modalRawText) modalRawText.textContent = c.raw_text || "No raw text available.";
            if (modalDownloadBtn) modalDownloadBtn.href = `${API_BASE}/api/candidates/${c.id}/download`;

            // Categorized Skills
            if (modalCategorizedSkills) {
                const categories = {};
                (c.skills || []).forEach(s => {
                    const cat = s.category || "General";
                    if (!categories[cat]) categories[cat] = [];
                    categories[cat].push(s.name);
                });

                if (Object.keys(categories).length === 0) {
                    modalCategorizedSkills.innerHTML = `<span style="color:var(--text-dim);font-size:0.8rem;">No competencies detected.</span>`;
                } else {
                    modalCategorizedSkills.innerHTML = Object.entries(categories).map(([cat, skills]) => `
                        <div style="margin-bottom:0.75rem;">
                            <div style="font-size:0.75rem; font-weight:700; color:var(--text-dim); margin-bottom:0.35rem;">${escapeHtml(cat)} (${skills.length})</div>
                            <div style="display:flex; flex-wrap:wrap; gap:0.35rem;">
                                ${skills.map(s => `<span class="skill-chip ${getSkillClass(cat)}">${escapeHtml(s)}</span>`).join("")}
                            </div>
                        </div>
                    `).join("");
                }
            }

            // Experience Timeline
            if (modalExperienceTimeline) {
                if ((c.experience || []).length === 0) {
                    modalExperienceTimeline.innerHTML = `<span style="color:var(--text-dim);font-size:0.8rem;">No employment history records detected.</span>`;
                } else {
                    modalExperienceTimeline.innerHTML = c.experience.map(exp => `
                        <div class="timeline-node">
                            <div class="timeline-dot"></div>
                            <div style="font-weight:700; color:var(--text-main); font-size:0.88rem;">${escapeHtml(exp.job_title || "Role")}</div>
                            <div style="font-size:0.75rem; color:var(--primary); font-weight:600;">${escapeHtml(exp.company || "")} ${exp.start_date || exp.end_date ? `• <span style="color:var(--text-dim);">${exp.start_date || ''} - ${exp.end_date || 'Present'}</span>` : ''}</div>
                            ${exp.description ? `<p style="font-size:0.78rem; color:var(--text-muted); margin:0.35rem 0 0;">${escapeHtml(exp.description)}</p>` : ''}
                        </div>
                    `).join("");
                }
            }

            // Education List
            if (modalEducationList) {
                if ((c.education || []).length === 0) {
                    modalEducationList.innerHTML = `<span style="color:var(--text-dim);font-size:0.8rem;">No academic credentials detected.</span>`;
                } else {
                    modalEducationList.innerHTML = c.education.map(edu => `
                        <div style="background:var(--bg-card-subtle); padding:0.75rem; border-radius:12px; margin-bottom:0.5rem; border:1px solid var(--border-glass);">
                            <div style="font-weight:700; font-size:0.85rem; color:var(--text-main);">${escapeHtml(edu.degree || "Degree")}</div>
                            ${edu.field_of_study ? `<div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(edu.field_of_study)}</div>` : ''}
                            ${edu.institution ? `<div style="font-size:0.75rem; color:var(--accent-emerald);">🎓 ${escapeHtml(edu.institution)}</div>` : ''}
                            <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:var(--text-dim); margin-top:0.35rem;">
                                <span>${edu.start_year || ''} ${edu.start_year && edu.end_year ? '-' : ''} ${edu.end_year || ''}</span>
                                ${edu.grade ? `<span class="meta-chip">${escapeHtml(edu.grade)}</span>` : ''}
                            </div>
                        </div>
                    `).join("");
                }
            }

            openModal("candidateModal");
        } catch (err) {
            alert(err.message);
        }
    }

    // Real Modal Status Changer
    if (modalStatusSelect) {
        modalStatusSelect.addEventListener("change", async () => {
            if (!currentCandidateId) return;
            const newStatus = modalStatusSelect.value;

            try {
                const res = await fetch(`${API_BASE}/api/candidates/${currentCandidateId}/status`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ status: newStatus })
                });
                if (res.ok) {
                    loadCandidates();
                    loadStats();
                }
            } catch (e) {
                console.error("Error updating status:", e);
            }
        });
    }

    // Real Recruiter Notes Auto-Save
    if (modalNotesTextarea) {
        modalNotesTextarea.addEventListener("input", () => {
            clearTimeout(notesDebounceTimer);
            if (notesSavedIndicator) notesSavedIndicator.style.display = "none";
            notesDebounceTimer = setTimeout(async () => {
                if (!currentCandidateId) return;
                const notes = modalNotesTextarea.value;

                try {
                    const res = await fetch(`${API_BASE}/api/candidates/${currentCandidateId}/notes`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ notes: notes })
                    });
                    if (res.ok && notesSavedIndicator) {
                        notesSavedIndicator.style.display = "inline";
                        setTimeout(() => notesSavedIndicator.style.display = "none", 2000);
                    }
                } catch (e) {
                    console.error("Error saving notes:", e);
                }
            }, 500);
        });
    }

    if (copyRawTextBtn && modalRawText) {
        copyRawTextBtn.addEventListener("click", () => {
            navigator.clipboard.writeText(modalRawText.textContent).then(() => {
                copyRawTextBtn.textContent = "✓ Copied!";
                setTimeout(() => copyRawTextBtn.textContent = "Copy Text", 2000);
            });
        });
    }

    // Real Candidate Deletion from Database & Storage
    async function deleteCandidate(candidateId, candidateName) {
        if (!confirm(`Permanently delete candidate "${candidateName || 'Record'}"?`)) return;

        try {
            const res = await fetch(`${API_BASE}/api/candidates/${candidateId}`, { method: "DELETE" });
            if (res.ok) {
                selectedForCompare.delete(parseInt(candidateId));
                updateCompareButton();
                loadCandidates();
                loadStats();
            } else {
                alert("Failed to delete candidate.");
            }
        } catch (e) {
            alert("Error deleting candidate: " + e.message);
        }
    }

    // -------------------------------------------------------------
    // Real AI Job Description Fit Matcher
    // -------------------------------------------------------------
    if (runJdMatchBtn && jdInputText) {
        runJdMatchBtn.addEventListener("click", async () => {
            const jd = jdInputText.value.trim();
            if (!jd) {
                alert("Please paste a Job Description or required skills.");
                return;
            }

            runJdMatchBtn.disabled = true;
            runJdMatchBtn.innerHTML = '<img src="/static/images/svastik-universe-logo.png" class="svastik-logo-icon" style="margin-right:0.4rem;"> <span>Evaluating Fit...</span>';

            try {
                const res = await fetch(`${API_BASE}/api/match-jd`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ job_description: jd })
                });

                if (res.ok) {
                    const data = await res.json();
                    isJdMatchActive = true;
                    if (matchBanner) matchBanner.style.display = "flex";
                    closeModal("jdMatchModal");

                    if (candidateCountDisplay) candidateCountDisplay.textContent = data.total_evaluated;
                    if (candidatesList) {
                        candidatesList.innerHTML = data.candidates.map(c => renderCandidateCard(c)).join("");
                        attachCandidateCardEvents();
                    }
                } else {
                    const err = await res.json();
                    alert(err.error || "Failed to evaluate candidates.");
                }
            } catch (e) {
                alert("Error connecting to backend: " + e.message);
            } finally {
                runJdMatchBtn.disabled = false;
                runJdMatchBtn.innerHTML = '<img src="/static/images/svastik-universe-logo.png" class="svastik-logo-icon" style="margin-right:0.4rem;"> <span>Calculate Fit Scores</span>';
            }
        });
    }

    // -------------------------------------------------------------
    // Real Candidate Side-by-Side Comparison via API
    // -------------------------------------------------------------
    async function generateComparisonMatrix() {
        if (!compareMatrixContainer) return;
        const ids = Array.from(selectedForCompare);
        if (ids.length < 2) return;

        compareMatrixContainer.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--text-muted);">Generating comparison...</div>`;

        try {
            const res = await fetch(`${API_BASE}/api/compare`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ candidate_ids: ids })
            });

            if (!res.ok) throw new Error("Failed to compare candidates");
            const data = await res.json();
            const candidates = data.candidates || [];
            const commonSkills = data.common_skills || [];

            compareMatrixContainer.innerHTML = `
                <div style="background:var(--bg-card-subtle); padding:1rem; border-radius:14px; margin-bottom:1.25rem; border:1px solid var(--border-glass);">
                    <div style="font-weight:700; color:var(--primary); font-size:0.85rem; margin-bottom:0.4rem;">
                        Shared Competencies (${commonSkills.length})
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:0.35rem;">
                        ${commonSkills.length > 0 ? commonSkills.map(s => `<span class="skill-chip skill-framework">${escapeHtml(s)}</span>`).join("") : '<span style="color:var(--text-dim);font-size:0.75rem;">None</span>'}
                    </div>
                </div>

                <div style="display:grid; grid-template-columns: repeat(${candidates.length}, 1fr); gap:1rem;">
                    ${candidates.map(c => `
                        <div style="background:var(--bg-card-subtle); border:1px solid var(--border-glass); border-radius:16px; padding:1.25rem;">
                            <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:1rem;">
                                <div class="candidate-avatar" style="width:42px;height:42px;font-size:0.95rem;">${getInitials(c.name)}</div>
                                <div>
                                    <h4 style="margin:0;font-size:1rem;font-weight:700;">${escapeHtml(c.name)}</h4>
                                    <span class="status-pill ${getStatusClass(c.status)}">${escapeHtml(c.status || "New")}</span>
                                </div>
                            </div>

                            <div style="margin-bottom:0.85rem;">
                                <div style="font-size:0.72rem; color:var(--text-dim); font-weight:700;">EXPERIENCE</div>
                                <div style="font-weight:800; font-size:1.1rem; color:var(--accent-cyan);">${c.total_experience_years} Years</div>
                            </div>

                            <div style="margin-bottom:0.85rem;">
                                <div style="font-size:0.72rem; color:var(--text-dim); font-weight:700;">HIGHEST DEGREE</div>
                                <div style="font-size:0.8rem; color:var(--text-main); font-weight:600;">${c.top_education ? escapeHtml(c.top_education.degree) : 'N/A'}</div>
                            </div>

                            <div>
                                <div style="font-size:0.72rem; color:var(--text-dim); font-weight:700; margin-bottom:0.35rem;">UNIQUE SKILLS (${c.unique_skills.length})</div>
                                <div style="display:flex; flex-wrap:wrap; gap:0.3rem;">
                                    ${c.unique_skills.length > 0 ? c.unique_skills.map(s => `<span class="skill-chip ${getSkillClass(s)}">${escapeHtml(s)}</span>`).join("") : '<span style="color:var(--text-dim);font-size:0.75rem;">None</span>'}
                                </div>
                            </div>
                        </div>
                    `).join("")}
                </div>
            `;
        } catch (e) {
            compareMatrixContainer.innerHTML = `<div style="color:var(--accent-rose);padding:1rem;">${escapeHtml(e.message)}</div>`;
        }
    }

    // -------------------------------------------------------------
    // Real Analytics & Charts from Database
    // -------------------------------------------------------------
    async function loadStats() {
        try {
            const res = await fetch(`${API_BASE}/api/stats`);
            if (!res.ok) return;

            const stats = await res.json();
            if (kpiTotalResumes) kpiTotalResumes.textContent = stats.total_candidates;
            if (kpiAvgExperience) kpiAvgExperience.textContent = stats.average_experience;
            if (kpiTopSkill) kpiTopSkill.textContent = stats.top_skills.length > 0 ? stats.top_skills[0].name : "-";

            // Real count of shortlisted candidates
            const candRes = await fetch(`${API_BASE}/api/candidates?status=Shortlisted`);
            if (candRes.ok) {
                const candData = await candRes.json();
                if (kpiShortlistedCount) kpiShortlistedCount.textContent = candData.total || 0;
            }

            renderSkillsChart(stats.top_skills || []);
        } catch (e) {
            console.error("Error loading stats:", e);
        }
    }

    function renderSkillsChart(topSkills) {
        const chartCanvas = document.getElementById("skillsChart");
        if (!chartCanvas || typeof Chart === "undefined") return;

        const ctx = chartCanvas.getContext("2d");
        const labels = topSkills.map(s => s.name);
        const counts = topSkills.map(s => s.count);

        if (skillsChartInstance) skillsChartInstance.destroy();
        if (labels.length === 0) return;

        skillsChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: "rgba(99, 102, 241, 0.75)",
                    hoverBackgroundColor: "rgba(6, 182, 212, 0.95)",
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: "#94a3b8", font: { size: 10 } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: "rgba(255, 255, 255, 0.05)" },
                        ticks: { stepSize: 1, color: "#94a3b8", font: { size: 10 } }
                    }
                }
            }
        });
    }

    // Real Taxonomy Skills Dropdown
    async function initSkillsDropdown() {
        if (!skillFilterSelect) return;
        try {
            const res = await fetch(`${API_BASE}/api/skills`);
            if (res.ok) {
                const data = await res.json();
                const skills = data.skills || [];
                skillFilterSelect.innerHTML = `<option value="">All Skills</option>` +
                    skills.map(s => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`).join("");
            }
        } catch (e) {
            console.error("Error loading skills:", e);
        }
    }

    // -------------------------------------------------------------
    // Helper Utilities
    // -------------------------------------------------------------
    function getInitials(name) {
        if (!name) return "??";
        const parts = name.trim().split(" ");
        if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }

    function getStatusClass(status) {
        switch ((status || "").toLowerCase()) {
            case "shortlisted": return "status-shortlisted";
            case "interviewing": return "status-interviewing";
            case "hired": return "status-hired";
            case "rejected": return "status-rejected";
            default: return "status-new";
        }
    }

    function getSkillClass(category) {
        switch (category) {
            case "Programming Languages": return "skill-prog";
            case "Frameworks & Libraries": return "skill-framework";
            case "Databases & Storage": return "skill-db";
            case "Cloud & DevOps": return "skill-cloud";
            case "AI & Data Science": return "skill-ai";
            case "Soft Skills": return "skill-soft";
            default: return "skill-default";
        }
    }

    function escapeHtml(text) {
        if (!text) return "";
        return text.replace(/[&<>"']/g, m => {
            switch (m) {
                case "&": return "&amp;";
                case "<": return "&lt;";
                case ">": return "&gt;";
                case '"': return "&quot;";
                case "'": return "&#039;";
            }
        });
    }
});
