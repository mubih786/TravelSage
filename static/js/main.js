// ============================================
// TravelSage - Main JavaScript
// ============================================

// ---- TOAST NOTIFICATION ----
function showToast(msg, duration = 3000) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), duration);
}

// ---- WISHLIST TOGGLE ----
async function toggleWishlist(destId, btn) {
  const res = await fetch('/api/wishlist/toggle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dest_id: destId })
  });
  const data = await res.json();
  if (data.status === 'added') {
    btn.textContent = '❤️';
    btn.classList.add('active');
    showToast('❤️ Added to Wishlist!');
  } else {
    btn.textContent = '🤍';
    btn.classList.remove('active');
    showToast('💔 Removed from Wishlist');
  }
  // Update nav wishlist badge if exists
  updateWishlistBadge(data.status === 'added' ? 1 : -1);
}

function updateWishlistBadge(delta) {
  const badge = document.querySelector('.wishlist-badge');
  if (badge) {
    let count = parseInt(badge.textContent || '0') + delta;
    badge.textContent = count > 0 ? count : '';
  }
}

// ---- COMPARE ----
let compareCount = 0;

async function addToCompare(destId, btn) {
  const res = await fetch('/api/compare/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dest_id: destId })
  });
  const data = await res.json();
  if (data.status === 'full') {
    showToast('⚠️ Max 3 destinations for comparison. Clear first.');
  } else {
    compareCount = data.count;
    document.getElementById('compareCount').textContent = compareCount;
    const floatEl = document.getElementById('compareFloat');
    if (floatEl) {
      floatEl.classList.add('visible');
    }
    btn.style.borderColor = 'var(--primary)';
    btn.style.color = 'var(--primary)';
    showToast('⚖️ Added to Compare list!');
  }
}

async function clearCompare() {
  await fetch('/api/compare/clear', { method: 'POST' });
  compareCount = 0;
  document.getElementById('compareCount').textContent = '0';
  document.getElementById('compareFloat').classList.remove('visible');
  showToast('🗑 Compare list cleared');
}

// ---- CARD HOVER ANIMATION ----
document.querySelectorAll('.dest-card').forEach(card => {
  card.addEventListener('mouseenter', () => {
    card.style.transform = 'translateY(-4px)';
  });
  card.addEventListener('mouseleave', () => {
    card.style.transform = '';
  });
});

// ---- SCORE BAR ANIMATION ON SCROLL ----
function animateScoreBars() {
  const bars = document.querySelectorAll('.score-bar-fill');
  bars.forEach(bar => {
    const width = bar.style.width;
    bar.style.width = '0';
    setTimeout(() => { bar.style.width = width; }, 100);
  });
}

// Run on load
document.addEventListener('DOMContentLoaded', () => {
  animateScoreBars();

  // Restore compare float if items in compare
  const countEl = document.getElementById('compareCount');
  if (countEl && parseInt(countEl.textContent) > 0) {
    document.getElementById('compareFloat').classList.add('visible');
  }
});

// ---- FORM COLLAPSE TOGGLE ----
function toggleSection(header) {
  header.parentElement.classList.toggle('collapsed');
  const icon = header.querySelector('.toggle-icon');
  if (icon) {
    icon.style.transform = header.parentElement.classList.contains('collapsed')
      ? 'rotate(-90deg)' : 'rotate(0deg)';
  }
}
