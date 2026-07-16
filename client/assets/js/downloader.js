// downloader.js - API calls

const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
// Connected to the live Back4App API!
const API_BASE = isLocalhost ? 'http://localhost:8000/api' : 'https://frabblitzapi-eo6fejy6.b4a.run/api';

export async function fetchMediaInfo(url) {
    try {
        const response = await fetch(`${API_BASE}/info`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail?.message || data.message || 'Failed to fetch media info');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Download file using server-side task and polling
 * @param {string} pageUrl   - Original video page URL
 * @param {string} formatId  - yt-dlp format_id to download
 * @param {string} title     - Used as the filename base
 * @param {string} ext       - File extension (mp4, mp3, webm, etc.)
 * @param {number} expectedSize - Expected file size in bytes
 * @param {function} onProgress - Callback for progress updates
 * @param {boolean} hasAudio - Whether the format already contains audio
 */
export async function downloadFile(pageUrl, formatId, title, ext = 'mp4', expectedSize = 0, onProgress = null, hasAudio = false) {
    // 1. Start backend download task
    const response = await fetch(`${API_BASE}/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            url: pageUrl,
            format_id: formatId,
            title: title || 'GrabBlitz_download',
            ext: ext || 'mp4',
            has_audio: hasAudio
        })
    });

    if (!response.ok) {
        let errMsg = 'Download failed to start on server.';
        try {
            const errData = await response.json();
            errMsg = errData.detail?.message || errMsg;
        } catch (_) {}
        throw new Error(errMsg);
    }

    const { task_id } = await response.json();
    if (!task_id) throw new Error('No task ID returned from server.');

    // 2. Poll for progress
    return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
            try {
                const progRes = await fetch(`${API_BASE}/progress/${task_id}`);
                if (!progRes.ok) throw new Error('Failed to get progress');
                
                const task = await progRes.json();
                
                if (task.status === 'error') {
                    clearInterval(interval);
                    reject(new Error(task.error_msg || 'Server download error'));
                } else if (task.status === 'completed') {
                    clearInterval(interval);
                    // Ensure 100% progress is shown
                    if (onProgress) {
                        onProgress({ loaded: task.total || expectedSize, total: task.total || expectedSize, speed: 0, status: 'completed' });
                    }
                    
                    // 3. Trigger native browser download
                    const downloadUrl = `${API_BASE}/serve/${task_id}`;
                    const a = document.createElement('a');
                    a.href = downloadUrl;
                    a.download = ''; // Browser will use Content-Disposition header
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    
                    resolve();
                } else if (task.status === 'downloading' && onProgress) {
                    onProgress({
                        loaded: task.loaded,
                        total: task.total || expectedSize,
                        speed: task.speed,
                        status: 'downloading'
                    });
                }
            } catch (err) {
                console.error('Polling error:', err);
                clearInterval(interval);
                reject(new Error('Lost connection to server during download'));
            }
        }, 500);
    });
}
