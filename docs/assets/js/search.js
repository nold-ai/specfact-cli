(function() {
  var searchRoot = document.querySelector('.docs-search');
  var searchInput = document.querySelector('.docs-search-input');
  var searchResults = document.querySelector('.docs-search-results');
  if (!searchRoot || !searchInput || !searchResults) return;

  var lunrIndex = null;
  var searchData = null;
  var debounceTimer = null;
  var highlightedIndex = -1;
  var loadFailed = false;

  function setSearchStatus(message) {
    searchResults.textContent = message;
    searchResults.style.display = 'block';
    searchResults.classList.add('docs-search-empty');
  }

  function clearSearchStatus() {
    searchResults.classList.remove('docs-search-empty');
  }

  function isSafeRelativeUrl(url) {
    return typeof url === 'string' && /^\/(?!\/)/.test(url);
  }

  function loadIndex() {
    if (lunrIndex) return Promise.resolve();
    if (loadFailed) return Promise.reject(new Error('Search index previously failed to load.'));

    var indexUrl = searchRoot.getAttribute('data-search-index-url') || '/assets/js/search-index.json';
    return fetch(indexUrl)
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        searchData = data;
        lunrIndex = lunr(function() {
          this.ref('url');
          this.field('title', { boost: 10 });
          this.field('keywords', { boost: 5 });
          this.field('content');
          data.forEach(function(doc) {
            this.add({
              url: doc.url,
              title: doc.title || '',
              keywords: Array.isArray(doc.keywords) ? doc.keywords.join(' ') : (doc.keywords || ''),
              content: doc.content || ''
            });
          }.bind(this));
        });
        loadFailed = false;
      })
      .catch(function(error) {
        loadFailed = true;
        lunrIndex = null;
        searchData = null;
        setSearchStatus('Search is temporarily unavailable.');
        console.error('Failed to load SpecFact search index.', error);
        throw error;
      });
  }

  function getDoc(url) {
    if (!Array.isArray(searchData)) return null;
    for (var i = 0; i < searchData.length; i++) {
      if (searchData[i].url === url) return searchData[i];
    }
    return null;
  }

  function createResultTag(tag) {
    var tagEl = document.createElement('span');
    tagEl.className = 'result-tag';
    tagEl.textContent = tag;
    return tagEl;
  }

  function createResultLink(doc) {
    var link = document.createElement('a');
    link.className = 'docs-search-result';
    link.href = isSafeRelativeUrl(doc.url) ? doc.url : '/';

    var titleEl = document.createElement('div');
    titleEl.className = 'result-title';
    titleEl.textContent = doc.title || '';
    link.appendChild(titleEl);

    var snippetEl = document.createElement('div');
    snippetEl.className = 'result-snippet';
    snippetEl.textContent = ((doc.content || '').substring(0, 120) + '...').trim();
    link.appendChild(snippetEl);

    var audience = Array.isArray(doc.audience) ? doc.audience : [];
    var expertise = Array.isArray(doc.expertise_level) ? doc.expertise_level : [];
    var tags = audience.concat(expertise).filter(Boolean);
    if (tags.length) {
      var tagsEl = document.createElement('div');
      tagsEl.className = 'result-tags';
      tags.forEach(function(tag) {
        tagsEl.appendChild(createResultTag(tag));
      });
      link.appendChild(tagsEl);
    }

    return link;
  }

  function renderResults(results) {
    highlightedIndex = -1;
    clearSearchStatus();
    if (results.length === 0) {
      setSearchStatus('No results found');
      return;
    }

    searchResults.innerHTML = '';
    results.slice(0, 10).forEach(function(result) {
      var doc = getDoc(result.ref);
      if (!doc) return;
      searchResults.appendChild(createResultLink(doc));
    });

    if (!searchResults.children.length) {
      setSearchStatus('No results found');
      return;
    }

    searchResults.style.display = 'block';
  }

  function doSearch(query) {
    if (!lunrIndex || loadFailed || query.length < 2) {
      clearSearchStatus();
      searchResults.style.display = 'none';
      return;
    }
    try {
      var results = lunrIndex.search(query + '*');
      renderResults(results);
    } catch (error) {
      try {
        var fallbackResults = lunrIndex.search(query);
        renderResults(fallbackResults);
      } catch (fallbackError) {
        setSearchStatus('Search is temporarily unavailable.');
        console.error('SpecFact search query failed.', fallbackError);
      }
    }
  }

  function updateHighlight(items) {
    items.forEach(function(item, i) {
      item.classList.toggle('highlighted', i === highlightedIndex);
    });
  }

  searchInput.addEventListener('focus', function() {
    loadIndex().catch(function(error) {
      loadFailed = true;
      lunrIndex = null;
      console.error('SpecFact search focus initialization failed.', error);
    });
  });

  searchInput.addEventListener('input', function() {
    clearTimeout(debounceTimer);
    var query = searchInput.value.trim();
    debounceTimer = setTimeout(function() {
      doSearch(query);
    }, 150);
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
      clearSearchStatus();
      searchResults.style.display = 'none';
      searchInput.blur();
    }
  });

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.docs-search')) {
      clearSearchStatus();
      searchResults.style.display = 'none';
    }
  });

  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
  });
})();
