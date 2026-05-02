 const grid = document.getElementById('newsGrid');
    const emptyState = document.getElementById('emptyState');
    const countBadge = document.getElementById('countBadge');
    const totalSaved = document.getElementById('totalSaved');
    const resultCount = document.getElementById('resultCount');
    const searchInput = document.getElementById('searchInput');
    const sortSelect = document.getElementById('sortSelect');

    function showToast(msg, type = 'green') {
      const toast = document.getElementById('toast');
      const dot = document.getElementById('toastDot');
      document.getElementById('toastMsg').textContent = msg;
      dot.className = 'toast-dot' + (type === 'red' ? ' red' : '');
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2800);
    }

    function updateCounts() {
      const visible = [...grid.querySelectorAll('.news-card:not([style*="display: none"])')];
      const total = grid.querySelectorAll('.news-card').length;
      countBadge.textContent = total;
      totalSaved.textContent = total;
      resultCount.textContent = visible.length;
      emptyState.style.display = visible.length === 0 ? 'block' : 'none';
    }

    // Remove card
    grid.addEventListener('click', e => {
      const removeBtn = e.target.closest('.remove-overlay, .btn-icon.star');
      if (!removeBtn) return;
      const card = removeBtn.closest('.news-card');
      card.style.transition = 'all 0.35s ease';
      card.style.opacity = '0';
      card.style.transform = 'scale(0.92)';
      setTimeout(() => {
        card.remove();
        updateCounts();
        showToast('Artigo removido dos favoritos', 'red');
      }, 350);
    });

    // Filter chips
    document.querySelectorAll('.filter-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        applyFilters();
      });
    });

    // Collection cards
    document.querySelectorAll('.collection-card').forEach(col => {
      col.addEventListener('click', () => {
        document.querySelectorAll('.collection-card').forEach(c => c.classList.remove('active'));
        col.classList.add('active');
      });
    });

    // Search
    searchInput.addEventListener('input', applyFilters);

    // Sort
    sortSelect.addEventListener('change', () => {
      const cards = [...grid.querySelectorAll('.news-card')];
      const val = sortSelect.value;
      cards.sort((a, b) => {
        if (val === 'recent') return b.dataset.date.localeCompare(a.dataset.date);
        if (val === 'oldest') return a.dataset.date.localeCompare(b.dataset.date);
        if (val === 'az') return a.dataset.title.localeCompare(b.dataset.title);
      });
      cards.forEach(c => grid.appendChild(c));
    });

    function applyFilters() {
      const activeFilter = document.querySelector('.filter-chip.active')?.dataset.filter || 'all';
      const query = searchInput.value.toLowerCase().trim();
      const cards = grid.querySelectorAll('.news-card');
      cards.forEach(card => {
        const cat = card.dataset.category || '';
        const title = card.dataset.title?.toLowerCase() || '';
        const catMatch = activeFilter === 'all' || cat === activeFilter;
        const searchMatch = !query || title.includes(query);
        card.style.display = catMatch && searchMatch ? '' : 'none';
      });
      updateCounts();
    }

    // View toggle
    document.getElementById('gridViewBtn').addEventListener('click', () => {
      grid.classList.remove('list-view');
      document.getElementById('gridViewBtn').classList.add('active');
      document.getElementById('listViewBtn').classList.remove('active');
    });
    document.getElementById('listViewBtn').addEventListener('click', () => {
      grid.classList.add('list-view');
      document.getElementById('listViewBtn').classList.add('active');
      document.getElementById('gridViewBtn').classList.remove('active');
    });

    // Clear all
    document.getElementById('clearAllBtn').addEventListener('click', () => {
      if (!confirm('Tem a certeza? Todos os favoritos serão removidos.')) return;
      const cards = [...grid.querySelectorAll('.news-card')];
      cards.forEach((card, i) => {
        setTimeout(() => {
          card.style.transition = 'all 0.3s ease';
          card.style.opacity = '0';
          card.style.transform = 'scale(0.92)';
          setTimeout(() => { card.remove(); updateCounts(); }, 300);
        }, i * 60);
      });
      showToast('Todos os favoritos foram removidos', 'red');
    });

    function resetFilters() {
      document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      document.querySelector('[data-filter="all"]').classList.add('active');
      searchInput.value = '';
      applyFilters();
    }

    updateCounts();