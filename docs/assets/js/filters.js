(function() {
  var pills = document.querySelectorAll('.expertise-pill');
  var countEl = document.querySelector('.expertise-count');
  if (!pills.length) return;

  var validLevels = Array.prototype.map.call(pills, function(pill) {
    return pill.getAttribute('data-level');
  });
  var stored = 'all';
  try {
    stored = localStorage.getItem('specfact-expertise') || 'all';
  } catch (error) {
    stored = 'all';
  }
  if (validLevels.indexOf(stored) === -1) {
    stored = 'all';
  }

  function applyFilter(level) {
    // Update pills
    pills.forEach(function(p) {
      var isActive = p.getAttribute('data-level') === level;
      p.classList.toggle('active', isActive);
      p.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    var items = document.querySelectorAll('.docs-nav li[data-expertise]');
    var total = items.length;
    var visible = 0;

    items.forEach(function(li) {
      if (level === 'all') {
        li.classList.remove('hidden-by-filter');
        visible++;
      } else {
        var expertise = (li.getAttribute('data-expertise') || '').split(',');
        if (expertise.indexOf(level) !== -1) {
          li.classList.remove('hidden-by-filter');
          visible++;
        } else {
          li.classList.add('hidden-by-filter');
        }
      }
    });

    // Hide bundle sections with no visible items
    document.querySelectorAll('.docs-nav-bundle').forEach(function(details) {
      var visibleItems = details.querySelectorAll('li:not(.hidden-by-filter)');
      if (visibleItems.length === 0 && level !== 'all') {
        details.classList.add('hidden-by-filter');
      } else {
        details.classList.remove('hidden-by-filter');
      }
    });

    // Update count
    if (countEl) {
      if (level === 'all') {
        countEl.textContent = '';
      } else {
        countEl.textContent = visible + ' of ' + total;
      }
    }

    try {
      localStorage.setItem('specfact-expertise', level);
    } catch (error) {
      // Ignore storage failures in restricted environments.
    }
  }

  pills.forEach(function(pill) {
    pill.addEventListener('click', function() {
      applyFilter(pill.getAttribute('data-level'));
    });
  });

  // Apply stored filter
  applyFilter(stored);
})();
