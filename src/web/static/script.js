/**
 * YouTube Miner - Frontend JavaScript
 * With chunk-by-chunk progress tracking
 */

// State
let currentJobId = null;
let pollInterval = null;
let selectedModel = 'faster-whisper';
let selectedLanguage = 'en';
let currentChunks = [];

// DOM Elements
const elements = {
    // Tabs
    navBtns: document.querySelectorAll('.nav-btn'),
    processTab: document.getElementById('process-tab'),
    historyTab: document.getElementById('history-tab'),
    
    // Input
    urlInput: document.getElementById('url-input'),
    modelBtns: document.querySelectorAll('.model-btn'),
    processBtn: document.getElementById('process-btn'),
    
    // Progress
    progressSection: document.getElementById('progress-section'),
    progressBar: document.getElementById('progress-bar'),
    progressStage: document.getElementById('progress-stage'),
    progressPercent: document.getElementById('progress-percent'),
    videoTitle: document.getElementById('video-title'),
    
    // Chunks during processing
    chunksSection: document.getElementById('chunks-section'),
    chunksGrid: document.getElementById('chunks-grid'),
    chunksCount: document.getElementById('chunks-count'),
    
    // Chunk Modal
    chunkModal: document.getElementById('chunk-modal'),
    chunkModalTitle: document.getElementById('chunk-modal-title'),
    chunkModalClose: document.getElementById('chunk-modal-close'),
    chunkTimeRange: document.getElementById('chunk-time-range'),
    chunkDuration: document.getElementById('chunk-duration'),
    chunkWer: document.getElementById('chunk-wer'),
    chunkCer: document.getElementById('chunk-cer'),
    chunkSemantic: document.getElementById('chunk-semantic'),
    chunkHybrid: document.getElementById('chunk-hybrid'),
    chunkTranscript: document.getElementById('chunk-transcript'),
    chunkCaption: document.getElementById('chunk-caption'),
    
    // Results
    resultsSection: document.getElementById('results-section'),
    resultTitle: document.getElementById('result-title'),
    resultDuration: document.querySelector('#result-duration .meta-value'),
    resultChunks: document.querySelector('#result-chunks .meta-value'),
    resultTime: document.querySelector('#result-time .meta-value'),
    metricWer: document.getElementById('metric-wer'),
    metricCer: document.getElementById('metric-cer'),
    metricSemantic: document.getElementById('metric-semantic'),
    metricHybrid: document.getElementById('metric-hybrid'),
    barWer: document.getElementById('bar-wer'),
    barCer: document.getElementById('bar-cer'),
    barSemantic: document.getElementById('bar-semantic'),
    barHybrid: document.getElementById('bar-hybrid'),
    finalChunksGrid: document.getElementById('final-chunks-grid'),
    newProcessBtn: document.getElementById('new-process-btn'),
    
    // History
    historyList: document.getElementById('history-list'),
    historyEmpty: document.getElementById('history-empty'),
    
    // Download buttons
    downloadReport: document.getElementById('download-report'),
    downloadSrt: document.getElementById('download-srt'),
    downloadTxt: document.getElementById('download-txt'),
};

// Current folder name for downloads
let currentFolderName = null;

// Tab Navigation
elements.navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        
        // Update nav buttons
        elements.navBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Show tab content
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.getElementById(`${tab}-tab`).classList.add('active');
        
        // Load history if needed
        if (tab === 'history') {
            loadHistory();
        }
    });
});

// Model Selection
elements.modelBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        elements.modelBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selectedModel = btn.dataset.model;
    });
});

// Language Selection
const languageSelect = document.getElementById('language-select');
if (languageSelect) {
    languageSelect.addEventListener('change', (e) => {
        selectedLanguage = e.target.value;
    });
}

// Process Button
elements.processBtn.addEventListener('click', async () => {
    const url = elements.urlInput.value.trim();
    
    if (!url) {
        shakeElement(elements.urlInput);
        return;
    }
    
    if (!isValidYouTubeUrl(url)) {
        shakeElement(elements.urlInput);
        return;
    }
    
    await startProcessing(url);
});

// Enter key to submit
elements.urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        elements.processBtn.click();
    }
});

// New Process Button
elements.newProcessBtn.addEventListener('click', () => {
    resetUI();
});

// Download Buttons
elements.downloadReport.addEventListener('click', () => {
    if (currentFolderName) {
        downloadFile(currentFolderName, 'report');
    }
});

elements.downloadSrt.addEventListener('click', () => {
    if (currentFolderName) {
        downloadFile(currentFolderName, 'srt');
    }
});

elements.downloadTxt.addEventListener('click', () => {
    if (currentFolderName) {
        downloadFile(currentFolderName, 'txt');
    }
});

// Download file helper
function downloadFile(folderName, fileType) {
    const url = `/api/download/${folderName}/${fileType}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Chunk Modal Close
elements.chunkModalClose.addEventListener('click', closeChunkModal);
elements.chunkModal.addEventListener('click', (e) => {
    if (e.target === elements.chunkModal) {
        closeChunkModal();
    }
});

/**
 * Start processing a video
 */
async function startProcessing(url) {
    try {
        // Disable UI
        elements.processBtn.disabled = true;
        elements.urlInput.disabled = true;
        
        // Show progress
        elements.progressSection.classList.remove('hidden');
        elements.resultsSection.classList.add('hidden');
        elements.chunksSection.classList.add('hidden');
        
        // Reset progress
        updateProgress(5, 'Starting...', '');
        elements.chunksGrid.innerHTML = '';
        currentChunks = [];
        
        // Start processing with selected language
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                model: selectedModel,
                language: selectedLanguage,
            }),
        });
        
        if (!response.ok) {
            throw new Error('Failed to start processing');
        }
        
        const data = await response.json();
        currentJobId = data.job_id;
        
        // Start polling for status
        startPolling();
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
        resetUI();
    }
}

/**
 * Poll for job status
 */
function startPolling() {
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${currentJobId}`);
            const job = await response.json();
            
            if (job.error && job.status === 'failed') {
                stopPolling();
                showError(job.error);
                resetUI();
                return;
            }
            
            // Update progress
            updateProgress(
                job.progress || 0, 
                job.stage || 'Processing...', 
                job.video_title || ''
            );
            
            // Update chunks if available
            if (job.total_chunks > 0) {
                updateChunks(job.chunks, job.total_chunks, job.current_chunk);
            }
            
            // Check if complete
            if (job.status === 'completed') {
                stopPolling();
                showResults(job);
            }
            
        } catch (error) {
            console.error('Poll error:', error);
            stopPolling();
            showError(error.message);
            resetUI();
        }
    }, 1000);
}

/**
 * Stop polling
 */
function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

/**
 * Update progress UI
 */
function updateProgress(percent, stage, title) {
    elements.progressBar.style.width = `${percent}%`;
    elements.progressStage.textContent = stage;
    elements.progressPercent.textContent = `${Math.round(percent)}%`;
    if (title) {
        elements.videoTitle.textContent = title;
    }
}

/**
 * Update chunks display
 */
function updateChunks(chunks, total, current) {
    if (!chunks || chunks.length === 0) return;
    
    // Show chunks section
    elements.chunksSection.classList.remove('hidden');
    
    // Update count
    const completed = chunks.filter(c => c.status === 'completed').length;
    elements.chunksCount.textContent = `${completed}/${total} chunks`;
    
    // Store chunks for modal
    currentChunks = chunks;
    
    // Update or create chunk tiles
    chunks.forEach((chunk, i) => {
        let tile = document.getElementById(`chunk-tile-${i}`);
        
        if (!tile) {
            tile = document.createElement('div');
            tile.id = `chunk-tile-${i}`;
            tile.className = 'chunk-tile';
            tile.dataset.index = i;
            tile.addEventListener('click', () => openChunkModal(i));
            elements.chunksGrid.appendChild(tile);
        }
        
        // Update tile content based on status
        if (chunk.status === 'completed') {
            tile.className = 'chunk-tile completed';
            tile.innerHTML = `
                <span class="chunk-tile-number">${i + 1}</span>
                <span class="chunk-tile-score">${(chunk.hybrid_score * 100).toFixed(0)}%</span>
            `;
        } else if (chunk.status === 'processing') {
            tile.className = 'chunk-tile processing';
            tile.innerHTML = `
                <span class="chunk-tile-number">${i + 1}</span>
                <span class="chunk-tile-status">⏳</span>
            `;
        } else if (chunk.status === 'error') {
            tile.className = 'chunk-tile error';
            tile.innerHTML = `
                <span class="chunk-tile-number">${i + 1}</span>
                <span class="chunk-tile-status">❌</span>
            `;
        } else {
            tile.className = 'chunk-tile pending';
            tile.innerHTML = `
                <span class="chunk-tile-number">${i + 1}</span>
                <span class="chunk-tile-status">⋯</span>
            `;
        }
    });
}

/**
 * Open chunk detail modal
 */
function openChunkModal(index) {
    const chunk = currentChunks[index];
    
    if (!chunk || chunk.status !== 'completed') {
        return; // Don't open for incomplete chunks
    }
    
    elements.chunkModalTitle.textContent = `Chunk ${index + 1}`;
    elements.chunkTimeRange.textContent = `${formatTime(chunk.start_time)} - ${formatTime(chunk.end_time)}`;
    elements.chunkDuration.textContent = `${chunk.duration.toFixed(1)}s`;
    
    elements.chunkWer.textContent = `${(chunk.wer * 100).toFixed(1)}%`;
    elements.chunkCer.textContent = `${(chunk.cer * 100).toFixed(1)}%`;
    elements.chunkSemantic.textContent = `${(chunk.semantic_similarity * 100).toFixed(1)}%`;
    elements.chunkHybrid.textContent = `${(chunk.hybrid_score * 100).toFixed(1)}%`;
    
    elements.chunkTranscript.textContent = chunk.transcript || '(empty)';
    elements.chunkCaption.textContent = chunk.caption || '(no caption)';
    
    elements.chunkModal.classList.remove('hidden');
}

/**
 * Close chunk modal
 */
function closeChunkModal() {
    elements.chunkModal.classList.add('hidden');
}

/**
 * Show results
 */
function showResults(job) {
    // Hide progress, show results
    elements.progressSection.classList.add('hidden');
    elements.resultsSection.classList.remove('hidden');
    
    const result = job.result;
    currentChunks = job.chunks;
    
    // Store folder name for downloads
    currentFolderName = result.folder_name;
    
    // Update video info
    elements.resultTitle.textContent = result.title;
    elements.resultDuration.textContent = formatDuration(result.duration);
    elements.resultChunks.textContent = `${result.chunks} chunks`;
    elements.resultTime.textContent = `${Math.round(result.processing_time)}s`;
    
    // Update metrics with animation
    const summary = result.summary;
    
    setTimeout(() => {
        animateMetric('wer', summary.avg_wer, true);
        animateMetric('cer', summary.avg_cer, true);
        animateMetric('semantic', summary.avg_semantic_similarity, false);
        animateMetric('hybrid', summary.avg_hybrid_score, false);
    }, 300);
    
    // Show final chunks grid
    renderFinalChunks(job.chunks);
}

/**
 * Render final chunks grid
 */
function renderFinalChunks(chunks) {
    elements.finalChunksGrid.innerHTML = '';
    
    chunks.forEach((chunk, i) => {
        const tile = document.createElement('div');
        tile.className = 'chunk-tile completed';
        tile.dataset.index = i;
        
        if (chunk.status === 'completed') {
            const scoreClass = getScoreClass(chunk.hybrid_score);
            tile.innerHTML = `
                <span class="chunk-tile-number">${i + 1}</span>
                <span class="chunk-tile-score ${scoreClass}">${(chunk.hybrid_score * 100).toFixed(0)}%</span>
            `;
            tile.addEventListener('click', () => openChunkModal(i));
        } else if (chunk.status === 'error') {
            tile.className = 'chunk-tile error';
            tile.innerHTML = `
                <span class="chunk-tile-number">${i + 1}</span>
                <span class="chunk-tile-status">❌</span>
            `;
        }
        
        elements.finalChunksGrid.appendChild(tile);
    });
}

/**
 * Get CSS class based on score
 */
function getScoreClass(score) {
    if (score >= 0.85) return 'score-good';
    if (score >= 0.70) return 'score-medium';
    return 'score-poor';
}

/**
 * Animate a metric value and bar
 */
function animateMetric(type, value, isErrorRate) {
    const displayValue = `${(value * 100).toFixed(1)}%`;
    const barWidth = isErrorRate ? Math.min(value * 100, 100) : value * 100;
    
    document.getElementById(`metric-${type}`).textContent = displayValue;
    document.getElementById(`bar-${type}`).style.width = `${barWidth}%`;
}

/**
 * Load history
 */
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.videos.length === 0) {
            elements.historyList.innerHTML = '';
            elements.historyEmpty.classList.remove('hidden');
            return;
        }
        
        elements.historyEmpty.classList.add('hidden');
        elements.historyList.innerHTML = data.videos.map(video => `
            <div class="history-item glass-card" data-video-id="${video.video_id}">
                <div class="history-item-header">
                    <span class="history-item-title">${escapeHtml(video.title)}</span>
                    <span class="history-item-model">${video.model}</span>
                </div>
                <div class="history-item-metrics">
                    <div class="history-metric">
                        <span class="history-metric-label">WER</span>
                        <span class="history-metric-value ${getMetricClass(video.summary.avg_wer, true)}">${formatPercent(video.summary.avg_wer)}</span>
                    </div>
                    <div class="history-metric">
                        <span class="history-metric-label">CER</span>
                        <span class="history-metric-value ${getMetricClass(video.summary.avg_cer, true)}">${formatPercent(video.summary.avg_cer)}</span>
                    </div>
                    <div class="history-metric">
                        <span class="history-metric-label">Semantic</span>
                        <span class="history-metric-value ${getMetricClass(video.summary.avg_semantic_similarity, false)}">${formatPercent(video.summary.avg_semantic_similarity)}</span>
                    </div>
                    <div class="history-metric">
                        <span class="history-metric-label">Hybrid</span>
                        <span class="history-metric-value ${getMetricClass(video.summary.avg_hybrid_score, false)}">${formatPercent(video.summary.avg_hybrid_score)}</span>
                    </div>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

/**
 * Reset UI to initial state
 */
function resetUI() {
    elements.processBtn.disabled = false;
    elements.urlInput.disabled = false;
    elements.urlInput.value = '';
    elements.progressSection.classList.add('hidden');
    elements.resultsSection.classList.add('hidden');
    elements.chunksSection.classList.add('hidden');
    elements.chunksGrid.innerHTML = '';
    currentJobId = null;
    currentChunks = [];
    currentFolderName = null;
    stopPolling();
}

/**
 * Show error message
 */
function showError(message) {
    alert(`Error: ${message}`);
}

/**
 * Shake element animation
 */
function shakeElement(element) {
    element.style.animation = 'shake 0.5s ease';
    setTimeout(() => {
        element.style.animation = '';
    }, 500);
}

// Add shake animation to stylesheet
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
`;
document.head.appendChild(style);

/**
 * Validate YouTube URL
 */
function isValidYouTubeUrl(url) {
    const patterns = [
        /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
        /^https?:\/\/youtu\.be\/[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/,
    ];
    return patterns.some(p => p.test(url));
}

/**
 * Format time in seconds to MM:SS
 */
function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
}

/**
 * Format duration in seconds to MM:SS or HH:MM:SS
 */
function formatDuration(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    
    if (h > 0) {
        return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }
    return `${m}:${s.toString().padStart(2, '0')}`;
}

/**
 * Format percentage
 */
function formatPercent(value) {
    return `${(value * 100).toFixed(1)}%`;
}

/**
 * Get CSS class for metric value
 */
function getMetricClass(value, isErrorRate) {
    if (isErrorRate) {
        if (value < 0.15) return 'good';
        if (value < 0.30) return 'medium';
        return 'poor';
    } else {
        if (value > 0.85) return 'good';
        if (value > 0.70) return 'medium';
        return 'poor';
    }
}

/**
 * Escape HTML entities
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    elements.urlInput.focus();
});
