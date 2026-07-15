// history.js - Manage local storage download history

const MAX_HISTORY = 10;
const STORAGE_KEY = 'GrabBlitz_history';

export function getHistory() {
    try {
        const data = localStorage.getItem(STORAGE_KEY);
        return data ? JSON.parse(data) : [];
    } catch (e) {
        console.error('Failed to parse history', e);
        return [];
    }
}

export function addHistoryItem(item) {
    // item needs: id, title, thumbnail, url, platformName
    const history = getHistory();
    
    // Remove if already exists (to move it to top)
    const filtered = history.filter(i => i.url !== item.url);
    
    filtered.unshift({
        ...item,
        timestamp: Date.now()
    });
    
    // Keep only top N items
    const limited = filtered.slice(0, MAX_HISTORY);
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(limited));
    return limited;
}

export function clearHistory() {
    localStorage.removeItem(STORAGE_KEY);
}
