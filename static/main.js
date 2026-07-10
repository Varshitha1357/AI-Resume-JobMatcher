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
    const resultsFilter = document.getElementById('resultsFilter');

    resultsFilter.addEventListener('change', () => {
        if (currentJobs.length > 0) displayJobs();
    });

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
        startLoadingFacts();

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
            const friendly = /failed to fetch|networkerror|load failed/i.test(error.message)
                ? 'The server took too long to respond — free hosting can be slow on the first search. Please try again in a minute.'
                : error.message;
            emptyState.innerHTML = '<p>Error: ' + escapeHtml(friendly) + '</p>';
            emptyState.style.display = 'flex';
        } finally {
            loadingState.style.display = 'none';
            findJobsBtn.disabled = false;
            stopLoadingFacts();
        }
    });

    function displaySummary(summary) {
        if (!summary) {
            aiSummary.style.display = 'none';
            return;
        }
        aiSummary.innerHTML =
            '<h3 class="summary-title">AI Career Analysis</h3>' +
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

        const limit = resultsFilter.value === 'all'
            ? currentJobs.length
            : Math.min(parseInt(resultsFilter.value, 10), currentJobs.length);
        const visibleJobs = currentJobs.slice(0, limit);

        const subtitle = document.querySelector('.matches-subtitle');
        if (subtitle) {
            const topCount = currentJobs.filter(j => j.tier === 'top').length;
            subtitle.textContent = `Showing ${visibleJobs.length} of ${currentJobs.length} related roles · top ${topCount} analyzed by AI`;
        }

        let dividerAdded = false;
        visibleJobs.forEach((job, index) => {
            if (!dividerAdded && job.tier === 'more') {
                const divider = document.createElement('div');
                divider.className = 'section-divider';
                divider.innerHTML = '<span>More related openings</span>';
                jobsList.appendChild(divider);
                dividerAdded = true;
            }
            jobsList.appendChild(createJobCard(job, index));
        });
    }

    function avatarClass(name) {
        let hash = 0;
        const str = String(name || '?');
        for (let i = 0; i < str.length; i++) {
            hash = (hash * 31 + str.charCodeAt(i)) >>> 0;
        }
        return 'avatar-' + (hash % 6);
    }

    function scoreClass(score) {
        if (score >= 70) return 'score-high';
        if (score >= 45) return 'score-mid';
        return 'score-low';
    }

    function createJobCard(job, index) {
        const card = document.createElement('div');
        card.className = 'job-card';

        const score = Math.round(Number(job.match_score) || 0);
        const initial = String(job.company || '?').trim().charAt(0).toUpperCase() || '?';
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
                <div class="company-avatar ${avatarClass(job.company)}">${escapeHtml(initial)}</div>
                <div class="job-title-company">
                    <div class="job-title">${escapeHtml(job.title)}</div>
                    <div class="job-company">${escapeHtml(job.company)}</div>
                </div>
                <div class="score-ring ${scoreClass(score)}" style="--pct: ${score}">
                    <div class="score-inner">${score}<span class="score-word">${job.reason ? 'match' : 'similar'}</span></div>
                </div>
            </div>
            <div class="job-meta">
                <div class="job-meta-item">📍 ${escapeHtml(job.location || 'Remote')}</div>
                <div class="job-meta-item">${escapeHtml(job.source || '')}</div>
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

/* ==============================================
   Interactive background: flowing aurora waves.
   Silky sine-wave ribbons drift across the page,
   bend toward the cursor, and wobble when you click.
   ============================================== */
(function initInteractiveBackground() {
    const canvas = document.getElementById('bgCanvas');
    const blobsWrap = document.getElementById('bgBlobs');
    const glow = document.getElementById('cursorGlow');
    if (!canvas || !canvas.getContext) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const ctx = canvas.getContext('2d');
    let width, height;
    let waveGradient = null;
    const mouse = { x: -9999, y: -9999 };
    const eased = { x: -9999, y: -9999 };
    const pulses = []; // click wobbles traveling through the waves

    const STEP = 7;           // px between sampled points on each wave
    const BEND_RADIUS = 260;  // how far the cursor's pull reaches horizontally
    const GLOW_RADIUS = 200;  // how close a wave point must be to light up

    const waves = [];
    const WAVE_COUNT = 8;

    function makeWaves() {
        waves.length = 0;
        for (let i = 0; i < WAVE_COUNT; i++) {
            waves.push({
                baseY: 0.12 + (i / (WAVE_COUNT - 1)) * 0.78,
                amp: 26 + Math.random() * 34,
                freq: 0.0028 + Math.random() * 0.0022,
                freq2: 0.006 + Math.random() * 0.005,
                speed: 0.00022 + Math.random() * 0.00025,
                phase: Math.random() * Math.PI * 2,
                alpha: 0.10 + Math.random() * 0.10
            });
        }
    }

    function resize() {
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        waveGradient = ctx.createLinearGradient(0, 0, width, 0);
        waveGradient.addColorStop(0, '#8b5cf6');
        waveGradient.addColorStop(0.5, '#6366f1');
        waveGradient.addColorStop(1, '#22d3ee');
    }

    window.addEventListener('resize', () => { resize(); });
    window.addEventListener('mousemove', (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });
    window.addEventListener('mouseout', () => {
        mouse.x = -9999;
        mouse.y = -9999;
    });
    window.addEventListener('click', (e) => {
        pulses.push({ x: e.clientX, t0: performance.now() });
        if (pulses.length > 5) pulses.shift();
    });
    window.addEventListener('touchmove', (e) => {
        if (e.touches[0]) {
            mouse.x = e.touches[0].clientX;
            mouse.y = e.touches[0].clientY;
        }
    }, { passive: true });
    window.addEventListener('touchstart', (e) => {
        if (e.touches[0]) {
            pulses.push({ x: e.touches[0].clientX, t0: performance.now() });
            if (pulses.length > 5) pulses.shift();
        }
    }, { passive: true });

    function waveY(w, x, t) {
        let y = w.baseY * height
            + Math.sin(x * w.freq + t * w.speed * 1000 + w.phase) * w.amp
            + Math.sin(x * w.freq2 - t * w.speed * 1400 + w.phase * 2) * w.amp * 0.35;

        // Bend toward the cursor: gaussian pull centered on mouse.x
        if (mouse.x > -999) {
            const dx = x - eased.x;
            const pull = Math.exp(-(dx * dx) / (2 * BEND_RADIUS * BEND_RADIUS));
            y += (eased.y - y) * pull * 0.38;
        }

        // Click pulses: a decaying wobble spreading outward from the click
        const now = performance.now();
        for (const p of pulses) {
            const age = (now - p.t0) / 1000;
            const dx = Math.abs(x - p.x) - age * 420; // wavefront position
            const packet = Math.exp(-(dx * dx) / (2 * 90 * 90));
            y += Math.sin(age * 18) * packet * Math.exp(-age * 1.6) * 34;
        }

        return y;
    }

    function frame(now) {
        ctx.clearRect(0, 0, width, height);
        const t = now / 1000;

        // Ease the glow + blob parallax toward the cursor
        if (mouse.x > -999) {
            eased.x += (mouse.x - eased.x) * 0.08;
            eased.y += (mouse.y - eased.y) * 0.08;
            if (glow) {
                glow.style.transform = `translate(${eased.x - 260}px, ${eased.y - 260}px)`;
            }
            if (blobsWrap) {
                const dx = (eased.x / width - 0.5) * 46;
                const dy = (eased.y / height - 0.5) * 34;
                blobsWrap.style.transform = `translate(${dx}px, ${dy}px)`;
            }
        }

        // Drop finished pulses
        for (let i = pulses.length - 1; i >= 0; i--) {
            if (now - pulses[i].t0 > 3000) pulses.splice(i, 1);
        }

        for (const w of waves) {
            // Base pass: full-width silky line
            ctx.globalAlpha = w.alpha;
            ctx.strokeStyle = waveGradient;
            ctx.lineWidth = 1.4;
            ctx.beginPath();
            for (let x = -STEP; x <= width + STEP; x += STEP) {
                const y = waveY(w, x, t);
                if (x <= 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();

            // Glow pass: brighter, thicker segment near the cursor
            if (mouse.x > -999) {
                const midY = waveY(w, eased.x, t);
                const dist = Math.abs(midY - eased.y);
                if (dist < GLOW_RADIUS) {
                    const intensity = 1 - dist / GLOW_RADIUS;
                    ctx.globalAlpha = Math.min(0.85, w.alpha + intensity * 0.55);
                    ctx.lineWidth = 1.6 + intensity * 1.6;
                    ctx.shadowBlur = 14 * intensity;
                    ctx.shadowColor = 'rgba(34, 211, 238, 0.8)';
                    ctx.beginPath();
                    const from = Math.max(-STEP, eased.x - 240);
                    const to = Math.min(width + STEP, eased.x + 240);
                    for (let x = from; x <= to; x += STEP) {
                        const y = waveY(w, x, t);
                        if (x <= from) ctx.moveTo(x, y);
                        else ctx.lineTo(x, y);
                    }
                    ctx.stroke();
                    ctx.shadowBlur = 0;
                }
            }
        }
        ctx.globalAlpha = 1;

        requestAnimationFrame(frame);
    }

    resize();
    makeWaves();
    requestAnimationFrame(frame);
})();

/* ==============================================
   Rotating facts while jobs load
   ============================================== */
const LOADING_FACTS = [
    "Recruiters spend an average of just 6–7 seconds on their first scan of a resume.",
    "About 75% of resumes are filtered out by ATS software before a human sees them — semantic matching like this skips the keyword games.",
    "The average corporate job opening attracts around 250 resumes. Tailored applications are ~3x more likely to get interviews.",
    "Tip: quantify your achievements — “cut load time by 40%” lands far better than “improved performance”.",
    "Tip: mirror the exact skill names from the job posting — both recruiters and screening software scan for them.",
    "The first known resume was written by Leonardo da Vinci in 1482, pitching his skills to the Duke of Milan.",
    "The first computer bug was a literal moth, found in a Harvard Mark II relay in 1947.",
    "Python is named after Monty Python, not the snake.",
    "Your phone has millions of times more computing power than the Apollo 11 guidance computer.",
    "The first 1 GB hard drive (1980) weighed over 250 kg and cost $40,000.",
    "GPS satellites correct for Einstein’s relativity — without it, positions would drift ~10 km per day.",
    "Wi-Fi doesn’t stand for anything — it was invented as a catchy marketing name.",
    "The QWERTY keyboard layout was designed to slow typists down and stop typewriter jams.",
    "Right now, your resume is being converted into a 384-dimensional vector — jobs are ranked by the angle between vectors.",
    "FAISS, the search engine ranking these jobs, was built by Meta AI to search billions of vectors in milliseconds.",
    "The AI analyzing your matches runs on Groq LPU chips that generate hundreds of words per second.",
    "The word “robot” comes from the Czech “robota”, meaning forced labor — coined in a 1920 play.",
    "Referred candidates are roughly 4x more likely to be hired — a follow-up message on LinkedIn can go a long way."
];

let factTimer = null;

function startLoadingFacts() {
    const el = document.getElementById('loadingFact');
    if (!el) return;
    let i = Math.floor(Math.random() * LOADING_FACTS.length);
    const show = () => {
        el.classList.remove('fact-show');
        void el.offsetWidth; // restart the fade-in animation
        el.textContent = LOADING_FACTS[i % LOADING_FACTS.length];
        el.classList.add('fact-show');
        i++;
    };
    show();
    factTimer = setInterval(show, 5000);
}

function stopLoadingFacts() {
    if (factTimer) {
        clearInterval(factTimer);
        factTimer = null;
    }
}
