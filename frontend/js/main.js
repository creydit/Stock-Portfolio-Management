document.addEventListener('DOMContentLoaded', () => {
    // Dynamic copyright year update
    const yearEl = document.getElementById('year');
    if (yearEl) {
        yearEl.textContent = new Date().getFullYear();
    }
});