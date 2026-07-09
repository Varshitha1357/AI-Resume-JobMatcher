document.addEventListener('DOMContentLoaded', function() {
    const uploadFileBtn = document.getElementById('uploadFileBtn');
    const pasteTextBtn = document.getElementById('pasteTextBtn');
    const fileInput = document.getElementById('fileInput');
    const resumeText = document.getElementById('resumeText');
    const skillsText = document.getElementById('skillsText');
    const findJobsBtn = document.getElementById('findJobsBtn');
    const charCount = document.querySelector('.char-count');
    const jobsList = document.getElementById('jobsList');
    const emptyState = document.getElementById('emptyState');
    const loadingState = document.getElementById('loadingState');
    const aiSummary = document.getElementById('aiSummary');

    let currentJobs = [];
    let currentIndex = 0;
    let uploadedFile = null;

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value == null ? '' : String(value);
        return div.innerHTML;
    }

    // Handle file upload
    uploadFileBtn.addEventListener('click', () => {
        fileInput.click();
    });

    // Handle paste text
    pasteTextBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            resumeText.value = text;
            updateCharCount();
            uploadedFile = null;
        } catch (err) {
            alert('Unable to read clipboard. Please manually paste your resume.');
        }
    });

    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        uploadedFile = file;

        if (file.type === 'application/pdf') {
            resumeText.value = `[PDF File Selected: ${file.name}]\n\nText will be extracted on the server. Click "Find My Perfect Jobs" to continue.`;
            updateCharCount();
        } else {
            const reader = new FileReader();
            reader.onload = function(ev) {
                resumeText.value = ev.target.result;
                updateCharCount();
            };
            reader.readAsText(file);
        }
    });

    // Update character count
    resumeText.addEventListener('input', updateCharCount);

    function updateCharCount() {
        charCount.textContent = resumeText.value.length + ' characters';
    }

    // Find jobs button
    findJobsBtn.addEventListener('click', async () => {
        const resumeContent = resumeText.value.trim();
        const skills = skillsText.value.trim();

        if (!resumeContent && !uploadedFile) {
            alert('Please upload or paste your resume content');
            return;
        }

        loadingState.style.display = 'flex';
        emptyState.style.display = 'none';
        aiSummary.style.display = 'none';
        jobsList.innerHTML = '';
        findJobsBtn.disabled = true;

        try {
            const formData = new FormData();

            if (uploadedFile) {
                formData.append('resume', uploadedFile);
            } else {
                formData.append('resume_text', resumeContent);
            }
            formData.append('skills_interests', skills);

            const response = await fetch('/match', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch jobs');
            }

            currentJobs = data.match_results || [];
            currentIndex = 0;
            displaySummary(data.ai_summary);
            displayJobs();
        } catch (error) {
            console.error('Error:', error);
            emptyState.innerHTML = '<p>Error: ' + escapeHtml(error.message) + '</p>';
            emptyState.style.display = 'flex';
        } finally {
            loadingState.style.display = 'none';
            findJobsBtn.disabled = false;
        }
    });

    function displaySummary(summary) {
        if (!summary) {
            aiSummary.style.display = 'none';
            return;
        }
        aiSummary.innerHTML =
            '<h3 class="summary-title">Career Analysis</h3>' +
            '<p class="summary-text">' + escapeHtml(summary).replace(/\n/g, '<br>') + '</p>';
        aiSummary.style.display = 'block';
    }

    function displayJobs() {
        jobsList.innerHTML = '';

        if (currentJobs.length === 0) {
            emptyState.innerHTML = '<p>No jobs found. Try different keywords.</p>';
            emptyState.style.display = 'flex';
            return;
        }

        emptyState.style.display = 'none';

        currentJobs.forEach((job, index) => {
            jobsList.appendChild(createJobCard(job, index));
        });
    }

    function createJobCard(job, index) {
        const card = document.createElement('div');
        card.className = 'job-card';

        const score = Math.round(Number(job.match_score) || 0);
        const matchedTags = (job.matched_skills || [])
            .map(s => '<span class="tag skill">' + escapeHtml(s) + '</span>')
            .join('');
        const gapTags = (job.skill_gaps || [])
            .map(s => '<span class="tag gap">' + escapeHtml(s) + '</span>')
            .join('');
        const applyLink = job.url
            ? '<a class="apply-link" href="' + escapeHtml(job.url) + '" target="_blank" rel="noopener noreferrer">Apply ↗</a>'
            : '';

        card.innerHTML = `
            <div class="job-header">
                <span class="job-rank">${String(index + 1).padStart(2, '0')}</span>
                <div class="job-title-company">
                    <div class="job-title">${escapeHtml(job.title)}</div>
                    <div class="job-company">${escapeHtml(job.company)}</div>
                </div>
                <div class="match-badge">${score}%<br><span style="font-size: 10px; font-weight: 500; letter-spacing: 0.08em;">MATCH</span></div>
            </div>
            <div class="job-meta">
                <div class="job-meta-item">${escapeHtml(job.location || 'Remote')}</div>
                <div class="job-meta-item">·&nbsp; ${escapeHtml(job.source || '')}</div>
                <div class="job-meta-item">·&nbsp; ${escapeHtml(job.similarity)}% similarity</div>
            </div>
            <div class="job-description">${escapeHtml((job.description || '').substring(0, 220))}...</div>
            ${job.reason ? '<div class="job-reason">' + escapeHtml(job.reason) + '</div>' : ''}
            ${matchedTags ? '<div class="job-tags"><span class="tags-label">You have</span>' + matchedTags + '</div>' : ''}
            ${gapTags ? '<div class="job-tags"><span class="tags-label">To learn</span>' + gapTags + '</div>' : ''}
            ${applyLink}
        `;

        return card;
    }

    // Carousel navigation
    document.querySelector('.carousel-btn.prev').addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            scrollToJob(currentIndex);
        }
    });

    document.querySelector('.carousel-btn.next').addEventListener('click', () => {
        if (currentIndex < currentJobs.length - 1) {
            currentIndex++;
            scrollToJob(currentIndex);
        }
    });

    function scrollToJob(index) {
        const jobCards = document.querySelectorAll('.job-card');
        if (jobCards[index]) {
            jobCards[index].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    // Initialize
    updateCharCount();
});
