document.addEventListener('DOMContentLoaded', function () {
  const grid = document.getElementById('newsGrid');
  const emptyState = document.getElementById('emptyState');
  const countBadge = document.getElementById('countBadge');
  const totalSaved = document.getElementById('totalSaved');
  const resultCount = document.getElementById('resultCount');
  const collectionCount = document.getElementById('collectionCount');
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
    const visible = [...grid.querySelectorAll('.news-card')].filter(c => c.style.display !== 'none');
    const total = grid.querySelectorAll('.news-card').length;
    if (countBadge) countBadge.textContent = total;
    if (totalSaved) totalSaved.textContent = total;
    if (resultCount) resultCount.textContent = visible.length;
    if (collectionCount) collectionCount.textContent = total + ' artigos';
    if (emptyState) emptyState.style.display = visible.length === 0 ? 'block' : 'none';
  }

  // Remove card com chamada real à API
  grid.addEventListener('click', async e => {
    const removeBtn = e.target.closest('.remove-overlay, .btn-icon.star');
    if (!removeBtn) return;

    const card = removeBtn.closest('.news-card');
    const favoriteId = card.dataset.id;
    if (!favoriteId) return;

    try {
      const response = await fetch(`/api/favorites/${favoriteId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });
      const result = await response.json();

      if (response.ok && result.success) {
        card.style.transition = 'all 0.35s ease';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.92)';
        setTimeout(() => { card.remove(); updateCounts(); showToast('Artigo removido dos favoritos', 'red'); }, 350);
      } else {
        showToast(result.message || 'Erro ao remover favorito', 'red');
      }
    } catch (err) {
      showToast('Erro ao conectar com o servidor', 'red');
    }
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

  // Limpar tudo — chama API para cada favorito
  document.getElementById('clearAllBtn').addEventListener('click', async () => {
    if (!confirm('Tem a certeza? Todos os favoritos serão removidos.')) return;
    const cards = [...grid.querySelectorAll('.news-card')];
    let removed = 0;
    for (const card of cards) {
      const favoriteId = card.dataset.id;
      if (!favoriteId) continue;
      try {
        const response = await fetch(`/api/favorites/${favoriteId}`, { method: 'DELETE' });
        if (response.ok) {
          card.style.opacity = '0';
          card.style.transform = 'scale(0.92)';
          card.style.transition = 'all 0.3s ease';
          await new Promise(r => setTimeout(r, 300));
          card.remove();
          removed++;
        }
      } catch (err) { /* continua */ }
    }
    updateCounts();
    showToast(`${removed} favoritos removidos`, 'red');
  });

  function resetFilters() {
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    document.querySelector('[data-filter="all"]').classList.add('active');
    searchInput.value = '';
    applyFilters();
  }

  // Expor resetFilters globalmente (usada no onclick do template)
  window.resetFilters = resetFilters;

  updateCounts();
});

// Exposta globalmente para uso no onclick do template
async function toggleRead(btn, favoriteId) {
  const isRead = btn.textContent.trim() === '✓';
  const newStatus = !isRead;
  try {
    const response = await fetch(`/api/favorites/${favoriteId}/read`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_read: newStatus })
    });
    const result = await response.json();
    if (response.ok && result.success) {
      btn.textContent = newStatus ? '✓' : '○';
      btn.classList.toggle('active', newStatus);
      btn.title = newStatus ? 'Marcar como não lido' : 'Marcar como lido';
      const toast = document.getElementById('toast');
      const dot = document.getElementById('toastDot');
      const msg = document.getElementById('toastMsg');
      if (toast && msg) {
        msg.textContent = newStatus ? 'Marcado como lido ✓' : 'Marcado como não lido';
        if (dot) dot.className = 'toast-dot';
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2800);
      }
    }
  } catch (err) { /* silencioso */ }
}
