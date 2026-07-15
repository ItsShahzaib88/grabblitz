// app.js - Main Application Logic
import { initTheme } from './theme.js';
import { formatDuration, isValidUrl } from './utils.js';
import { showToast, toggleSkeleton, setButtonLoading, updatePlatformBadge, renderHistory } from './ui.js';
import { fetchMediaInfo, downloadFile } from './downloader.js';
import { getHistory, addHistoryItem } from './history.js';

document.addEventListener('DOMContentLoaded', () => {
    // Register Service Worker for PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./sw.js')
            .then(reg => console.log('Service Worker registered', reg))
            .catch(err => console.error('Service Worker registration failed', err));
    }

    initTheme();

    const form = document.getElementById('downloadForm');
    const urlInput = document.getElementById('urlInput');
    const pasteBtn = document.getElementById('pasteBtn');
    const fetchBtn = document.getElementById('fetchBtn');
    const platformBadgeContainer = document.getElementById('platformBadgeContainer');
    
    const resultState = document.getElementById('resultState');
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    // Initial Render
    renderHistory(getHistory(), (url) => {
        urlInput.value = url;
        form.dispatchEvent(new Event('submit'));
    });

    // Paste from Clipboard
    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                urlInput.value = text;
                updatePlatformBadge(platformBadgeContainer, text);
            }
        } catch (err) {
            showToast('Failed to read clipboard', 'error');
        }
    });

    // Input changes (debounce platform detection)
    let timeout = null;
    urlInput.addEventListener('input', (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            updatePlatformBadge(platformBadgeContainer, e.target.value);
        }, 500);
    });

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();

        if (!url || !isValidUrl(url)) {
            showToast('Please enter a valid URL', 'error');
            return;
        }

        setButtonLoading(fetchBtn, true);
        toggleSkeleton(true);

        try {
            const data = await fetchMediaInfo(url);
            renderResult(data, url);
            
            // Add to history
            const newHistory = addHistoryItem({
                url,
                title: data.title,
                thumbnail: data.thumbnail,
                platformName: data.platform?.name
            });
            renderHistory(newHistory, (histUrl) => {
                urlInput.value = histUrl;
                form.dispatchEvent(new Event('submit'));
            });
            
            showToast('Media info extracted successfully');
        } catch (error) {
            showToast(error.message, 'error');
            toggleSkeleton(false);
        } finally {
            setButtonLoading(fetchBtn, false);
        }
    });

    // Tab Switching
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.getElementById('videoFormats').classList.add('hidden');
            document.getElementById('audioFormats').classList.add('hidden');
            
            const target = btn.getAttribute('data-target');
            document.getElementById(target).classList.remove('hidden');
        });
    });

    let currentPageUrl = '';

    function renderResult(data, originalUrl) {
        currentPageUrl = data.webpage_url || originalUrl;
        toggleSkeleton(false);
        resultState.classList.remove('hidden');

        document.getElementById('mediaThumbnail').src = data.thumbnail || 'https://placehold.co/640x360?text=No+Thumbnail';
        document.getElementById('mediaDuration').textContent = formatDuration(data.duration);
        document.getElementById('mediaTitle').textContent = data.title;
        document.getElementById('mediaUploader').innerHTML = `<i class="fa-solid fa-user"></i> ${data.uploader || 'Unknown'}`;
        
        if (data.platform) {
            document.getElementById('mediaPlatform').innerHTML = `<i class="fa-brands ${data.platform.icon || 'fa-globe'}" style="color: ${data.platform.color}"></i> ${data.platform.name}`;
        }

        renderFormatGrid('videoFormats', data.videos || [], data.title);
        renderFormatGrid('audioFormats', data.audios || [], data.title);
    }

    function renderFormatGrid(containerId, formats, title) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';

        if (formats.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted); padding: 1rem 0;">No formats available for this type.</p>';
            return;
        }

        formats.forEach(f => {
            const card = document.createElement('div');
            card.className = 'format-card';
            
            let quality = f.resolution || f.quality_label || 'Normal';
            if (containerId === 'audioFormats') {
                quality = f.abr ? `${Math.round(f.abr)}kbps` : 'Audio';
            }

            card.innerHTML = `
                <div class="format-quality">${quality}</div>
                <div class="format-size">${f.ext.toUpperCase()} ${f.filesize_hr ? '• ' + f.filesize_hr : ''}</div>
                <button class="btn-download" id="dl-${f.format_id}"><i class="fa-solid fa-download"></i> Download</button>
            `;

            card.querySelector('.btn-download').addEventListener('click', async () => {
                const btn = card.querySelector('.btn-download');
                btn.style.display = 'none';

                // Create PlayStore style circular progress container
                const progressContainer = document.createElement('div');
                progressContainer.className = 'progress-container';
                progressContainer.style.cssText = 'display: flex; align-items: center; gap: 12px; margin-top: 0.5rem; justify-content: center; width: 100%; background: var(--bg-secondary); padding: 8px; border-radius: 8px; border: 1px solid var(--border);';
                
                progressContainer.innerHTML = `
                    <div style="position: relative; width: 44px; height: 44px; flex-shrink: 0;">
                        <svg viewBox="0 0 36 36" style="width: 100%; height: 100%; transform: rotate(-90deg);">
                            <circle cx="18" cy="18" r="16" fill="none" stroke="var(--border)" stroke-width="3"></circle>
                            <circle class="ring-fill" cx="18" cy="18" r="16" fill="none" stroke="#3b82f6" stroke-width="3" stroke-dasharray="100.53" stroke-dashoffset="100.53" stroke-linecap="round" style="transition: stroke-dashoffset 0.2s linear;"></circle>
                        </svg>
                        <div class="progress-percent" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 0.65rem; font-weight: 700; color: var(--text);">0%</div>
                    </div>
                    <div style="display: flex; flex-direction: column; text-align: left; overflow: hidden;">
                        <span class="progress-speed" style="font-size: 0.85rem; font-weight: 600; color: var(--text); white-space: nowrap;">0 KB/s</span>
                        <span class="progress-size" style="font-size: 0.7rem; color: var(--text-muted); white-space: nowrap;">0 MB / 0 MB</span>
                    </div>
                `;
                card.appendChild(progressContainer);

                const ringFill = progressContainer.querySelector('.ring-fill');
                const percentText = progressContainer.querySelector('.progress-percent');
                const sizeText = progressContainer.querySelector('.progress-size');
                const speedText = progressContainer.querySelector('.progress-speed');

                try {
                    await downloadFile(
                        currentPageUrl,
                        f.format_id,
                        title,
                        f.ext,
                        f.filesize || f.approximate_filesize || 0,
                        (prog) => {
                            let percent = 0;
                            if (prog.total) {
                                percent = Math.min(100, Math.round((prog.loaded / prog.total) * 100));
                            }
                            
                            // Circumference is 100.53
                            const offset = 100.53 - (100.53 * percent / 100);
                            ringFill.style.strokeDashoffset = offset;
                            
                            percentText.textContent = `${percent}%`;
                            
                            const loadedMB = (prog.loaded / (1024 * 1024)).toFixed(1);
                            const totalMB = prog.total ? (prog.total / (1024 * 1024)).toFixed(1) : '?';
                            sizeText.textContent = `${loadedMB} MB / ${totalMB} MB`;

                            const speedMB = prog.speed / (1024 * 1024);
                            if (speedMB >= 1) {
                                speedText.textContent = `${speedMB.toFixed(1)} MB/s`;
                            } else {
                                speedText.textContent = `${(prog.speed / 1024).toFixed(0)} KB/s`;
                            }
                        },
                        f.has_audio
                    );
                    showToast('Download complete! File saved.', 'success');
                } catch (err) {
                    showToast(err.message || 'Download failed', 'error');
                } finally {
                    card.removeChild(progressContainer);
                    btn.style.display = 'block';
                    btn.innerHTML = '<i class="fa-solid fa-download"></i> Download';
                }
            });

            container.appendChild(card);
        });
    }
});
