(() => {
    const toggle = document.querySelector('[data-theme-toggle]');
    if (!toggle) return;
    const icon = toggle.querySelector('[data-theme-icon]');
    const label = toggle.querySelector('[data-theme-label]');
    const updateToggle = (theme) => {
        const isDark = theme === 'dark';
        icon.textContent = isDark ? '☀' : '☾';
        label.textContent = isDark ? 'Thème clair' : 'Thème sombre';
        toggle.setAttribute('aria-label', isDark ? 'Activer le thème clair' : 'Activer le thème sombre');
    };
    updateToggle(document.documentElement.dataset.bsTheme);
    toggle.addEventListener('click', () => {
        const nextTheme = document.documentElement.dataset.bsTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.dataset.bsTheme = nextTheme;
        localStorage.setItem('reservation-theme', nextTheme);
        updateToggle(nextTheme);
    });
})();
