// --- API Endpoints ---
const isHttpPage = window.location.protocol === 'http:' || window.location.protocol === 'https:';
const isBackendPort = window.location.port === '7860';
const API_BASE_URL = isHttpPage
    ? (isBackendPort ? window.location.origin : `${window.location.protocol}//${window.location.hostname}:7860`)
    : 'http://127.0.0.1:7860';

const PREDICT_API_URL = `${API_BASE_URL}/predict`;
const SCRAPE_API_URL = `${API_BASE_URL}/scrape-and-predict`;
const FILE_ANALYSIS_URL = `${API_BASE_URL}/analyze-file`;
const CROSS_CHECK_API_URL = `${API_BASE_URL}/cross-check-review`;

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing handlers...');

    // File Analysis Elements
    const fileAnalysis = {
        form: document.getElementById('file-upload-form'),
        input: document.getElementById('file-input'),
        button: document.getElementById('analyze-file-btn'),
        results: document.getElementById('file-result'), // Main container for results/errors
        uploadUI: {
            fileInfo: document.querySelector('.file-info'),
            fileName: document.getElementById('file-name'),
            removeBtn: document.getElementById('remove-file'),
            uploadProgress: document.querySelector('.upload-progress'),
            progressFill: document.querySelector('.progress-fill'),
            uploadPercentage: document.getElementById('upload-percentage')
        },
        progress: {
            container: document.querySelector('.progress-container'),
        },
        stats: {
            container: document.querySelector('.stats-container'),
            total: document.getElementById('total-reviews'),
            real: document.getElementById('real-reviews'),
            fake: document.getElementById('fake-reviews')
        },
        downloadBtn: document.getElementById('download-results-btn')
    };

    // Set up File Analysis if we're on that page
    if (fileAnalysis.form) {
        console.log('Setting up file analysis handler');

        fileAnalysis.input.addEventListener('change', (event) => {
            const file = event.target.files[0];
            
            if (file && file.name.toLowerCase().endsWith('.csv')) {
                if(fileAnalysis.button) fileAnalysis.button.disabled = false;
                if(fileAnalysis.uploadUI.fileInfo) fileAnalysis.uploadUI.fileInfo.style.display = 'flex';
                if(fileAnalysis.uploadUI.fileName) {
                    fileAnalysis.uploadUI.fileName.textContent = file.name;
                    fileAnalysis.uploadUI.fileName.title = file.name;
                }
                console.log('File selected:', file.name);
            } else {
                if(fileAnalysis.button) fileAnalysis.button.disabled = true;
                if(fileAnalysis.uploadUI.fileInfo) fileAnalysis.uploadUI.fileInfo.style.display = 'none';
                if(fileAnalysis.uploadUI.fileName) {
                    fileAnalysis.uploadUI.fileName.textContent = 'No file selected';
                    fileAnalysis.uploadUI.fileName.title = '';
                }
                if (file) {
                    alert('Please select a CSV file.');
                }
            }
        });

        if (fileAnalysis.uploadUI.removeBtn) {
            fileAnalysis.uploadUI.removeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if(fileAnalysis.input) fileAnalysis.input.value = '';
                if(fileAnalysis.uploadUI.fileInfo) fileAnalysis.uploadUI.fileInfo.style.display = 'none';
                if(fileAnalysis.button) fileAnalysis.button.disabled = true;
                console.log('File removed');
            });
        }
        
        // ## START: UPDATED AND CORRECTED SUBMIT HANDLER ##
        // REPLACE THE ENTIRE fileAnalysis.form.addEventListener(...) block with this:

fileAnalysis.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log('File analysis form submitted');

    const file = fileAnalysis.input ? fileAnalysis.input.files[0] : null;
    if (!file) {
        alert('Please select a CSV file first.');
        return;
    }
    
    // Add the new error display to our elements object
    fileAnalysis.errorDisplay = document.getElementById('file-error-display');

    let progressInterval;

    // --- UI Reset ---
    if (fileAnalysis.button) fileAnalysis.button.disabled = true;
    if (fileAnalysis.results) fileAnalysis.results.style.display = 'none';
    if (fileAnalysis.errorDisplay) fileAnalysis.errorDisplay.style.display = 'none'; // Hide old errors
    if (fileAnalysis.progress.container) fileAnalysis.progress.container.style.display = 'block';
    if (fileAnalysis.stats.container) fileAnalysis.stats.container.style.display = 'none';
    if (fileAnalysis.downloadBtn) fileAnalysis.downloadBtn.classList.add('hidden');
    if (fileAnalysis.uploadUI.uploadProgress) fileAnalysis.uploadUI.uploadProgress.style.display = 'block';
    
    try {
        // --- Progress Bar Simulation ---
        if (fileAnalysis.uploadUI.progressFill && fileAnalysis.uploadUI.uploadPercentage) {
            fileAnalysis.uploadUI.progressFill.style.width = '0%';
            fileAnalysis.uploadUI.uploadPercentage.textContent = '0%';
            let progress = 0;
            progressInterval = setInterval(() => {
                if (progress < 90) {
                    progress += 5;
                    fileAnalysis.uploadUI.progressFill.style.width = `${progress}%`;
                    fileAnalysis.uploadUI.uploadPercentage.textContent = `${progress}%`;
                }
            }, 200);
        }

        // --- API Call ---
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(FILE_ANALYSIS_URL, {
            method: 'POST',
            body: formData,
        });

        if(progressInterval) clearInterval(progressInterval);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Server returned an invalid error format.' }));
            throw new Error(errorData.error || 'Server error occurred.');
        }

        const results = await response.json();
        
        // --- Display successful results ---
        if (fileAnalysis.uploadUI.progressFill) fileAnalysis.uploadUI.progressFill.style.width = '100%';
        if (fileAnalysis.uploadUI.uploadPercentage) fileAnalysis.uploadUI.uploadPercentage.textContent = '100%';
        
        if (fileAnalysis.stats.total) fileAnalysis.stats.total.textContent = results.length;
        if (fileAnalysis.stats.real) fileAnalysis.stats.real.textContent = results.filter(r => r.prediction === 'REAL').length;
        if (fileAnalysis.stats.fake) fileAnalysis.stats.fake.textContent = results.filter(r => r.prediction === 'FAKE').length;
        
        window.fileResults = results;

        setTimeout(() => {
            if (fileAnalysis.uploadUI.uploadProgress) fileAnalysis.uploadUI.uploadProgress.style.display = 'none';
            if (fileAnalysis.progress.container) fileAnalysis.progress.container.style.display = 'none';
            if (fileAnalysis.stats.container) fileAnalysis.stats.container.style.display = 'block';
            if (fileAnalysis.results) fileAnalysis.results.style.display = 'block'; // Show the main results container
            if (fileAnalysis.downloadBtn) fileAnalysis.downloadBtn.classList.remove('hidden');
        }, 500);

    } catch (error) {
        console.error('Analysis failed:', error);
        if (progressInterval) clearInterval(progressInterval);
        
        // --- Safely display error message in the NEW container ---
        if (fileAnalysis.uploadUI.uploadProgress) fileAnalysis.uploadUI.uploadProgress.style.display = 'none';
        if (fileAnalysis.progress.container) fileAnalysis.progress.container.style.display = 'none';
        if (fileAnalysis.results) fileAnalysis.results.style.display = 'none'; // Ensure results are hidden

        if (fileAnalysis.errorDisplay) {
            fileAnalysis.errorDisplay.textContent = `Failed to analyze file: ${error.message}`;
            fileAnalysis.errorDisplay.style.display = 'block'; // Show the error
        } else {
            alert(`Failed to analyze file: ${error.message}`);
        }
    } finally {
        if (fileAnalysis.button) fileAnalysis.button.disabled = false;
        console.log('File analysis completed');
    }
});
        // ## END: UPDATED AND CORRECTED SUBMIT HANDLER ##


        if (fileAnalysis.downloadBtn) {
            fileAnalysis.downloadBtn.addEventListener('click', () => {
                if (!window.fileResults || !window.fileResults.length) {
                    alert('No results to download');
                    return;
                }

                const csvContent = [
                    ['Review', 'Prediction', 'Confidence Score'],
                    ...window.fileResults.map(result => [
                        `"${result.review.replace(/"/g, '""')}"`,
                        result.prediction,
                        `${result.confidence_score}`
                    ])
                ].map(row => row.join(',')).join('\n');

                const blob = new Blob([csvContent], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'review-analysis-results.csv';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            });
        }
    }

    // Text Analysis Elements
    const textAnalysis = {
        button: document.getElementById('analyze-text-btn'),
        input: document.getElementById('text-input'),
        results: document.getElementById('text-result'),
        confidenceScore: document.getElementById('confidence-score'),
        analysisTime: document.getElementById('analysis-time')
    };

    // Set up Text Analysis if we're on that page
    if (textAnalysis.button && textAnalysis.input && textAnalysis.results) {
        console.log('Setting up text analysis handler');
        
        textAnalysis.button.addEventListener('click', async () => {
            const text = textAnalysis.input.value;
            if (!text) {
                alert('Please enter text to analyze.');
                return;
            }

            const startTime = Date.now();

            textAnalysis.button.textContent = 'Analyzing...';
            textAnalysis.button.disabled = true;
            textAnalysis.results.style.display = 'none';

            try {
                const response = await fetch(PREDICT_API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ review: text })
                });

                if (!response.ok) {
                    throw new Error('Failed to analyze text');
                }

                const data = await response.json();

                const resultIcon = textAnalysis.results.querySelector('.result-icon');
                const resultText = textAnalysis.results.querySelector('.result-text');
                
                resultIcon.innerHTML = data.prediction === 'REAL' 
                    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 12l2 2 4-4"></path><circle cx="12" cy="12" r="10"></circle></svg>'
                    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';

                resultIcon.className = `result-icon ${data.prediction.toLowerCase()}`;

                resultText.textContent = data.prediction === 'REAL' 
                    ? 'This text appears to be real.'
                    : 'This text appears to be fake.';

                textAnalysis.confidenceScore.textContent = data.confidence_score;
                textAnalysis.analysisTime.textContent = `${((Date.now() - startTime) / 1000).toFixed(2)}s`;

                textAnalysis.results.style.display = 'block';
        
            } catch (error) {
                console.error('Analysis failed:', error);
                textAnalysis.results.style.display = 'block';
                textAnalysis.results.innerHTML = `
                    <p class="error-message">
                        Failed to analyze text: ${error.message}
                    </p>
                `;
            } finally {
                textAnalysis.button.textContent = 'Analyze Text';
                textAnalysis.button.disabled = false;
            }
        });
    }

    // URL Analysis Elements
    const urlAnalysis = {
        button: document.getElementById('analyze-url-btn'),
        input: document.getElementById('url-input'),
        results: document.getElementById('result-box'),
        content: document.querySelector('#result-box .result-content'),
        downloadBtn: document.getElementById('download-btn')
    };

    // Set up URL Analysis if we're on that page
    if (urlAnalysis.button && urlAnalysis.input && urlAnalysis.results) {
        console.log('Setting up URL analysis handler');
        
        urlAnalysis.button.addEventListener('click', async () => {
            const url = urlAnalysis.input.value;
            if (!url) {
                alert('Please enter a URL to analyze.');
                return;
            }

            urlAnalysis.button.textContent = 'Analyzing...';
            urlAnalysis.button.disabled = true;
            urlAnalysis.results.style.display = 'block';
            urlAnalysis.content.innerHTML = '<p>Analyzing reviews... Please wait...</p>';

            try {
                const response = await fetch(SCRAPE_API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                if (!response.ok) {
                    throw new Error('Failed to fetch results');
                }

                const results = await response.json();
                
                if (results.length === 0) {
                    urlAnalysis.content.innerHTML = '<p class="error-message">No reviews found at this URL.</p>';
                    return;
                }

                const table = document.createElement('table');
                table.innerHTML = `
                    <thead>
                        <tr>
                            <th>Count</th>
                            <th>Review</th>
                            <th>Prediction</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${results.map((result, index) => `
                            <tr class="${result.prediction.toLowerCase()}-row">
                                <td>${index + 1}</td>
                                <td>${result.review_text}</td>
                                <td>${result.prediction}</td>
                                <td>${result.confidence_score}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                `;

                urlAnalysis.content.innerHTML = '';
                urlAnalysis.content.appendChild(table);
                urlAnalysis.downloadBtn.classList.remove('hidden');
                window.latestResults = results;

            } catch (error) {
                console.error('Analysis failed:', error);
                urlAnalysis.content.innerHTML = `
                    <p class="error-message">
                        Failed to analyze reviews: ${error.message}
                    </p>
                `;
            } finally {
                urlAnalysis.button.textContent = 'Analyze URL';
                urlAnalysis.button.disabled = false;
            }
        });

        if (urlAnalysis.downloadBtn) {
            urlAnalysis.downloadBtn.addEventListener('click', () => {
                if (!window.latestResults || !window.latestResults.length) {
                    alert('No results to download');
                    return;
                }

                const csv = [
                    ['Count', 'Review', 'Prediction', 'Confidence Score'],
                    ...window.latestResults.map((result, index) => [
                        index + 1,
                        `"${result.review_text.replace(/"/g, '""')}"`,
                        result.prediction,
                        `${result.confidence_score}`
                    ])
                ].map(row => row.join(',')).join('\n');

                const blob = new Blob([csv], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'review-analysis.csv';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            });
        }
    }

    // ## FINAL CORRECTED VERSION ## - Cross-Check Analysis Handler
    const crossCheck = {
        form: document.getElementById('cross-check-form'),
        hotelInput: document.getElementById('hotel-name-input'),
        reviewInput: document.getElementById('review-text-input'),
        button: document.getElementById('cross-check-btn'),
        resultsContainer: document.getElementById('cross-check-result'),
    };

    if (crossCheck.form) {
        console.log('Setting up GRANULAR cross-check analysis handler');
        
        crossCheck.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const hotelName = crossCheck.hotelInput.value;
            const reviewText = crossCheck.reviewInput.value;

            if (!hotelName || !reviewText) {
                alert('Please provide both a hotel name and a review text.');
                return;
            }

            crossCheck.button.textContent = 'Analyzing...';
            crossCheck.button.disabled = true;
            crossCheck.resultsContainer.style.display = 'none';
            crossCheck.resultsContainer.innerHTML = ''; // Clear previous results

            try {
                const response = await fetch(CROSS_CHECK_API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        hotel_name: hotelName,
                        review_text: reviewText
                    })
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.error || 'Server returned an error.');
                }

                const data = await response.json();
                
                // --- DYNAMICALLY BUILD THE NEW RESULTS UI ---

                // 1. Create the main header for the overall verdict
                const resultHeader = document.createElement('div');
                resultHeader.className = 'result-header';
                
                const verdictIcon = document.createElement('div');
                verdictIcon.className = 'result-icon';

                const verdictText = document.createElement('h3');
                verdictText.id = 'result-verdict-text';

                resultHeader.append(verdictIcon, verdictText);

                // 2. Set content based on the overall verdict
                // ## UPDATED FOR USER-FRIENDLY LABELS ##
                if (data.overall_verdict === 'FAKE_REVIEW') {
                    verdictIcon.classList.add('fake'); // Red icon
                    verdictIcon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
                    verdictText.textContent = 'Fake Review';
                } else if (data.overall_verdict === 'GENUINE_REVIEW') {
                    verdictIcon.classList.add('real'); // Green icon
                    verdictIcon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 12l2 2 4-4"></path><circle cx="12" cy="12" r="10"></circle></svg>';
                    verdictText.textContent = 'Genuine Review';
                } else { // Inconclusive
                    verdictIcon.classList.add('neutral'); // Gray icon
                    verdictIcon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
                    verdictText.textContent = 'Inconclusive';
                }
                
                crossCheck.resultsContainer.appendChild(resultHeader);
                
                // 3. Create the detailed breakdown for each clause
                if (data.analysis && data.analysis.length > 0) {
                    const analysisList = document.createElement('div');
                    analysisList.className = 'analysis-breakdown';

                    data.analysis.forEach(item => {
                        const card = document.createElement('div');
                        card.className = `analysis-card-item ${item.is_outlier ? 'outlier' : 'consistent'}`;
                        
                        card.innerHTML = `
                            <div class="analysis-card-header">
                                <span class="clause-text">"${item.clause}"</span>
                            </div>
                            <div class="analysis-card-body">
                                <div class="detail-item">
                                    <span class="detail-label">Detected Aspect</span>
                                    <span class="detail-value">${item.aspect}</span>
                                 </div>
                                <div class="detail-item">
                                    <span class="detail-label">Sentiment</span>
                                    <span class="detail-value sentiment-${item.sentiment}">${item.sentiment}</span>
                                </div>
                            </div>
                            <div class="analysis-card-footer">
                                <p class="reason">${item.reason}</p>
                            </div>
                        `;
                        analysisList.appendChild(card);
                    });

                    crossCheck.resultsContainer.appendChild(analysisList);
                } else if (data.reason) { // Handle inconclusive cases with a reason
                    const reasonPara = document.createElement('p');
                    reasonPara.className = 'result-reason';
                    reasonPara.textContent = data.reason;
                    crossCheck.resultsContainer.appendChild(reasonPara);
                }

                crossCheck.resultsContainer.style.display = 'block';

            } catch (error) {
                console.error('Cross-check failed:', error);
                crossCheck.resultsContainer.innerHTML = `<p class="error-message">An error occurred: ${error.message}</p>`;
                crossCheck.resultsContainer.style.display = 'block';
            } finally {
                crossCheck.button.textContent = 'Cross-Check Review';
                crossCheck.button.disabled = false;
            }
        });
    }

});
