(function() {
  var searchRoot = document.querySelector('.docs-search');
  var searchInput = document.querySelector('.docs-search-input');
  var searchResults = document.querySelector('.docs-search-results');
  if (!searchRoot || !searchInput || !searchResults) return;

  var lunrIndex = null;
  var searchData = null;
  var debounceTimer = null;
  var highlightedIndex = -1;

  function loadIndex() {
    if (lunrIndex) return Promise.resolve();
    var indexUrl = searchRoot.getAttribute('data-search-index-url') || '/assets/js/search-index.json';
    return fetch(indexUrl)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        searchData = data;
        lunrIndex = lunr(function() {
          this.ref('url');
          this.field('title', { boost: 10 });
          this.field('keywords', { boost: 5 });
          this.field('content');
          data.forEach(function(doc) {
            var entry = {
              url: doc.url,
              title: doc.title || '',
              keywords: Array.isArray(doc.keywords) ? doc.keywords.join(' ') : (doc.keywords || ''),
              content: doc.content || ''
            };
            this.add(entry);
          }.bind(this));
        });
      });
  }

  function getDoc(url) {
    for (var i = 0; i < searchData.length; i++) {
      if (searchData[i].url === url) return searchData[i];
    }
    return null;
  }

  function renderResults(results) {
    highlightedIndex = -1;
    if (results.length === 0) {
      searchResults.innerHTML = '<div class="docs-search-empty">No results found</div>';
      searchResults.style.display = 'block';
      return;
    }

    var html = '';
    results.slice(0, 10).forEach(function(result) {
      var doc = getDoc(result.ref);
      if (!doc) return;
      var snippet = (doc.content || '').substring(0, 120) + '...';
      var tags = '';
      var audience = Array.isArray(doc.audience) ? doc.audience : [];
      var expertise = Array.isArray(doc.expertise_level) ? doc.expertise_level : [];
      audience.concat(expertise).forEach(function(tag) {
        if (tag) tags += '<span class="result-tag">' + tag + '</span>';
      });

      html += '<a href="' + doc.url + '" class="docs-search-result">';
      html += '<div class="result-title">' + (doc.title || '') + '</div>';
      html += '<div class="result-snippet">' + snippet + '</div>';
      if (tags) html += '<div class="result-tags">' + tags + '</div>';
      html += '</a>';
    });

    searchResults.innerHTML = html;
    searchResults.style.display = 'block';
  }

  function doSearch(query) {
    if (!lunrIndex || query.length < 2) {
      searchResults.style.display = 'none';
      return;
    }
    try {
      var results = lunrIndex.search(query + '*');
      renderResults(results);
    } catch (e) {
      try {
        var results = lunrIndex.search(query);
        renderResults(results);
      } catch (e2) {
        searchResults.style.display = 'none';
      }
    }
  }

  searchInput.addEventListener('focus', function() {
    loadIndex();
  });

  searchInput.addEventListener('input', function() {
    clearTimeout(debounceTimer);
    var query = searchInput.value.trim();
    debounceTimer = setTimeout(function() { doSearch(query); }, 150);
  });

  searchInput.addEventListener('keydown', function(e) {
    var items = searchResults.querySelectorAll('.docs-search-result');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      highlightedIndex = Math.min(highlightedIndex + 1, items.length - 1);
      updateHighlight(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      highlightedIndex = Math.max(highlightedIndex - 1, 0);
      updateHighlight(items);
    } else if (e.key === 'Enter' && highlightedIndex >= 0 && items[highlightedIndex]) {
      e.preventDefault();
      items[highlightedIndex].click();
    } else if (e.key === 'Escape') {
      searchResults.style.display = 'none';
      searchInput.blur();
    }
  });

  function updateHighlight(items) {
    items.forEach(function(item, i) {
      item.classList.toggle('highlighted', i === highlightedIndex);
    });
  }

  // Close results when clicking outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.docs-search')) {
      searchResults.style.display = 'none';
    }
  });

  // Keyboard shortcut: Ctrl+K / Cmd+K
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
  });
})();
