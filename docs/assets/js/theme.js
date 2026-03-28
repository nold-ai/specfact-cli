// Theme initialization - runs in <head> to prevent FOUC
(function() {
  var stored = localStorage.getItem('specfact-theme');
  var theme = stored || (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  document.documentElement.setAttribute('data-theme', theme);
})();

function toggleTheme() {
  var current = document.documentElement.getAttribute('data-theme') || 'dark';
  var next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('specfact-theme', next);

  // Update toggle button icons
  var sunIcon = document.querySelector('.theme-toggle .icon-sun');
  var moonIcon = document.querySelector('.theme-toggle .icon-moon');
  if (sunIcon && moonIcon) {
    sunIcon.style.display = next === 'dark' ? 'none' : 'block';
    moonIcon.style.display = next === 'dark' ? 'block' : 'none';
  }

  // Re-render mermaid diagrams if available
  if (typeof rerenderMermaid === 'function') {
    rerenderMermaid(next);
  }
}
