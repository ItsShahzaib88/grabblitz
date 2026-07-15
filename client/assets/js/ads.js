// ads.js - Ad Integration & Monetization Logic

// 1. Inject Popunder Scripts globally
function injectPopunders() {
    const scripts = [
        "https://fixesconsessionconsession.com/1e/f5/fc/1ef5fccc0a05021f0f1f9d3b6f52157b.js",
        "https://fixesconsessionconsession.com/90/3b/db/903bdb124f3159321378b8ed76578020.js"
    ];

    scripts.forEach(src => {
        const s = document.createElement('script');
        s.src = src;
        s.async = true;
        document.head.appendChild(s);
    });
}

// 2. Setup Ad Modal overlay for downloads
function createAdModal() {
    if (document.getElementById('downloadAdModal')) return;

    const modal = document.createElement('div');
    modal.innerHTML = `
        <div id="downloadAdModal" class="ad-modal-overlay hidden">
            <div class="ad-modal-content">
                <h3 style="margin-bottom: 0.5rem; color: var(--text);">Processing Download...</h3>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;">
                    Please wait <span id="adCountdown" style="color: var(--accent-primary); font-weight: bold; font-size: 1.2rem;">10</span> seconds.
                </p>
                
                <div class="ad-container" id="adContainerBox" style="min-height: 250px; min-width: 300px; display: flex; justify-content: center; align-items: center; background: var(--bg-secondary); border-radius: 8px; overflow: hidden; margin-bottom: 1rem;">
                    <iframe src="ads/banner-300x250.html" width="300" height="250" frameborder="0" scrolling="no" style="border:none;overflow:hidden;"></iframe>
                </div>
                
                <div style="font-size: 0.75rem; color: var(--text-muted);">Advertisement</div>
            </div>
        </div>
        <style>
            .ad-modal-overlay {
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(15, 23, 42, 0.9);
                backdrop-filter: blur(5px);
                z-index: 9999;
                display: flex; justify-content: center; align-items: center;
                opacity: 1; transition: opacity 0.3s ease;
            }
            .ad-modal-overlay.hidden {
                opacity: 0; pointer-events: none;
            }
            .ad-modal-content {
                background: var(--bg-primary);
                padding: 2rem;
                border-radius: var(--radius-lg);
                border: 1px solid var(--border-color);
                box-shadow: var(--shadow-lg);
                text-align: center;
                max-width: 90%;
            }
        </style>
    `;
    document.body.appendChild(modal);
}

export function showDownloadAdWithDelay(callback) {
    const modal = document.getElementById('downloadAdModal');
    if (!modal) {
        callback();
        return;
    }

    const countdownEl = document.getElementById('adCountdown');
    let timeLeft = 10;
    countdownEl.textContent = timeLeft;
    modal.classList.remove('hidden');

    const timer = setInterval(() => {
        timeLeft--;
        countdownEl.textContent = timeLeft;
        if (timeLeft <= 0) {
            clearInterval(timer);
            modal.classList.add('hidden');
            callback();
        }
    }, 1000);
}

// 3. Inject Banners globally (728x90 below hero, 320x50 sticky footer for mobile)
function injectBanners() {
    const mainEl = document.querySelector('main');
    if (mainEl && window.innerWidth > 768) {
        const topBannerContainer = document.createElement('div');
        topBannerContainer.style.cssText = "display: flex; justify-content: center; margin: 2rem 0; overflow: hidden; width: 100%;";
        
        topBannerContainer.innerHTML = '<iframe src="ads/banner-728x90.html" width="728" height="90" frameborder="0" scrolling="no" style="max-width:100%; border:none;"></iframe>';
        mainEl.insertBefore(topBannerContainer, mainEl.firstChild);
    }

    if (window.innerWidth <= 768) {
        const mobileBanner = document.createElement('div');
        mobileBanner.style.cssText = "position: fixed; bottom: 0; left: 0; width: 100%; height: 50px; display: flex; justify-content: center; background: var(--bg-primary); z-index: 999; border-top: 1px solid var(--border-color); box-shadow: 0 -2px 10px rgba(0,0,0,0.5);";
        
        mobileBanner.innerHTML = '<iframe src="ads/banner-320x50.html" width="320" height="50" frameborder="0" scrolling="no" style="border:none;"></iframe>';
        
        document.body.appendChild(mobileBanner);
        
        // Add padding to body to prevent content from hiding behind sticky footer
        document.body.style.paddingBottom = "55px";
    }
}

// Init all ads
function initAds() {
    injectPopunders();
    createAdModal();
    // Delay banner injection slightly so it doesn't block main render
    setTimeout(injectBanners, 500);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAds);
} else {
    initAds();
}
