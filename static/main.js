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

    let currentJobs = [];
    let currentIndex = 0;
    let uploadedFile = null;

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

    fileInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (file) {
            uploadedFile = file;
            
            // If it's a PDF, try to extract text
            if (file.type === 'application/pdf') {
                try {
                    // For now, just show that file is selected
                    resumeText.value = `[PDF File Selected: ${file.name}]\n\nFile is ready to process. Click "Find My Perfect Jobs" to continue.`;
                    updateCharCount();
                } catch (error) {
                    console.error('Error reading PDF:', error);
                    resumeText.value = `[PDF File Selected: ${file.name}]\n\nFile is ready to process. Click "Find My Perfect Jobs" to continue.`;
                    updateCharCount();
                }
            } else {
                // For text files, read the content
                const reader = new FileReader();
                reader.onload = function(e) {
                    resumeText.value = e.target.result;
                    updateCharCount();
                };
                reader.readAsText(file);
            }
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

        if (!resumeContent) {
            alert('Please upload or paste your resume content');
            return;
        }

        loadingState.style.display = 'flex';
        emptyState.style.display = 'none';
        jobsList.innerHTML = '';

        try {
            const formData = new FormData();
            
            // If file was uploaded, use it; otherwise use text content
            if (uploadedFile) {
                formData.append('resume', uploadedFile);
            } else {
                // Create a text file from the textarea content
                const blob = new Blob([resumeContent], { type: 'text/plain' });
                const file = new File([blob], 'resume.txt', { type: 'text/plain' });
                formData.append('resume', file);
            }
            
            formData.append('skills_interests', skills);

            const response = await fetch('/match', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                currentJobs = data.match_results || [];
                currentIndex = 0;
                displayJobs();
                loadingState.style.display = 'none';
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch jobs');
            }
        } catch (error) {
            console.error('Error:', error);
            loadingState.style.display = 'none';
            emptyState.innerHTML = '<p>Error: ' + error.message + '</p>';
            emptyState.style.display = 'flex';
        }
    });

    function displayJobs() {
        jobsList.innerHTML = '';
        
        if (currentJobs.length === 0) {
            emptyState.innerHTML = '<p>No jobs found. Try different keywords.</p>';
            emptyState.style.display = 'flex';
            return;
        }

        emptyState.style.display = 'none';

        currentJobs.forEach((job, index) => {
            const jobCard = createJobCard(job, index);
            jobsList.appendChild(jobCard);
        });
    }

    function createJobCard(job, index) {
        const card = document.createElement('div');
        card.className = 'job-card';

        // Extract match percentage from match_details
        const matchPercentageMatch = job.match_details.match(/(\d+(?:\.\d+)?)%/);
        const matchPercentage = matchPercentageMatch ? matchPercentageMatch[1] : '85';

        card.innerHTML = `
            <div class="job-header">
                <span class="job-rank">#${index + 1}</span>
                <div class="job-title-company">
                    <div class="job-title">${job.title}</div>
                    <div class="job-company">${job.company}</div>
                </div>
                <div class="match-badge">${matchPercentage}%<br><span style="font-size: 11px;">Match</span></div>
            </div>
            <div class="job-meta">
                <div class="job-meta-item">📍 ${job.location || 'Remote'}</div>
                <div class="job-meta-item">💼 ${job.deadline || 'Full-time'}</div>
            </div>
            <div class="job-description">
                ${job.match_details.split('|')[0].trim().replace('Match Score:', '').trim().substring(0, 150)}...
            </div>
            <div class="job-tags">
                <span class="tag skill">Python</span>
                <span class="tag framework">Development</span>
                <span class="tag skill">Problem Solving</span>
                <span class="tag">+more</span>
            </div>
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


