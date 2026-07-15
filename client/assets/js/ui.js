// ui.js - UI manipulation and Toasts

export function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
    
    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);

    // Remove after 3s
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

export function toggleSkeleton(show) {
    const skeleton = document.getElementById('loadingState');
    const result = document.getElementById('resultState');
    
    if (show) {
        skeleton.classList.remove('hidden');
        result.classList.add('hidden');
    } else {
        skeleton.classList.add('hidden');
        // result is shown manually when data is ready
    }
}

export function setButtonLoading(btn, isLoading) {
    if (isLoading) {
        btn.classList.add('loading');
    } else {
        btn.classList.remove('loading');
    }
}

export function updatePlatformBadge(container, url) {
    // Simple basic detection for immediate feedback (more detailed handled by backend)
    container.innerHTML = '';
    if (!url) return;
    
    let platform = 'Generic Link';
    let icon = 'fa-link';
    let color = '#6b7280';

    if (url.includes('youtube.com') || url.includes('youtu.be')) {
        platform = 'YouTube';
        icon = 'fa-youtube';
        color = '#ef4444';
    } else if (url.includes('tiktok.com')) {
        platform = 'TikTok';
        icon = 'fa-tiktok';
        color = '#000000';
    } else if (url.includes('instagram.com')) {
        platform = 'Instagram';
        icon = 'fa-instagram';
        color = '#ec4899';
    } else if (url.includes('twitter.com') || url.includes('x.com')) {
        platform = 'Twitter / X';
        icon = 'fa-twitter';
        color = '#1da1f2';
    }

    container.innerHTML = `
        <div class="platform-badge" style="border-color: ${color}40">
            <i class="fa-brands ${icon}" style="color: ${color}"></i>
            <span>${platform} Detected</span>
        </div>
    `;
}

export function renderHistory(history, onSelect) {
    const section = document.getElementById('historySection');
    const grid = document.getElementById('historyGrid');
    
    if (!history || history.length === 0) {
        section.classList.add('hidden');
        return;
    }

    section.classList.remove('hidden');
    grid.innerHTML = '';

    history.forEach(item => {
        const card = document.createElement('div');
        card.className = 'history-card';
        card.innerHTML = `
            <img src="${item.thumbnail}" alt="Thumbnail" class="history-img" onerror="this.src='https://via.placeholder.com/300x169?text=No+Image'">
            <div class="history-info">
                <div class="history-title">${item.title}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted)">
                    <i class="fa-solid fa-globe"></i> ${item.platformName || 'Unknown Platform'}
                </div>
            </div>
        `;
        card.addEventListener('click', () => onSelect(item.url));
        grid.appendChild(card);
    });
}
