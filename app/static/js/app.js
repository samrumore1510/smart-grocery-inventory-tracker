/**
 * Smart Grocery Inventory & Expiry Tracker
 * Frontend interactive controller & API integration
 */

// 1. Theme Management (Dark / Light Mode)
function initTheme() {
  const savedTheme = localStorage.getItem('sg_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeButton(savedTheme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const newTheme = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('sg_theme', newTheme);
  updateThemeButton(newTheme);
}

function updateThemeButton(theme) {
  const btn = document.getElementById('themeToggleBtn');
  if (btn) {
    btn.innerHTML = theme === 'dark' ? '☀️ Light' : '🌙 Dark';
  }
}

// 2. Toast Notifications
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || '✨'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// 3. Modal Helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// 4. API Request Wrapper with Error Handling
async function apiRequest(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    });

    if (res.status === 401) {
      window.location.href = '/login?msg=Session+expired.+Please+log+in+again.';
      return null;
    }

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || data.message || `Request failed (${res.status})`);
    }
    return data;
  } catch (err) {
    showToast(err.message, 'error');
    throw err;
  }
}

// 5. Quantity Stepper
async function adjustStock(productId, delta) {
  try {
    const updated = await apiRequest(`/api/inventory/${productId}/adjust?delta=${delta}`, {
      method: 'PATCH'
    });
    if (updated) {
      showToast(`Stock updated: ${updated.name} (${updated.quantity} ${updated.unit})`, 'success');
      // If table row exists, update row dynamically without reload
      const qtyElem = document.getElementById(`qty-${productId}`);
      const stockBadge = document.getElementById(`stock-badge-${productId}`);
      if (qtyElem) qtyElem.textContent = `${updated.quantity} ${updated.unit}`;
      if (stockBadge) {
        stockBadge.className = `badge badge-${updated.stock_status.replace('_', '-')}`;
        stockBadge.textContent = updated.stock_badge_text;
      }
    }
  } catch (err) {
    console.error('Adjust stock error:', err);
  }
}

// 6. Delete Product Confirmation
async function confirmDeleteProduct(productId, productName) {
  if (!confirm(`Are you sure you want to delete "${productName}" from inventory?`)) {
    return;
  }
  try {
    await apiRequest(`/api/inventory/${productId}`, { method: 'DELETE' });
    showToast(`Deleted ${productName}`, 'success');
    const row = document.getElementById(`product-row-${productId}`);
    if (row) {
      row.style.opacity = '0';
      setTimeout(() => row.remove(), 300);
    }
  } catch (err) {
    console.error('Delete error:', err);
  }
}

// 7. Shopping List - Mark as Purchased
async function markShoppingPurchased(itemId, itemName) {
  try {
    await apiRequest(`/api/shopping-list/${itemId}/mark-purchased`, { method: 'POST' });
    showToast(`Restocked "${itemName}" and updated inventory!`, 'success');
    setTimeout(() => window.location.reload(), 800);
  } catch (err) {
    console.error('Shopping purchased error:', err);
  }
}

// 8. Auto-Sync Low Stock to Shopping List
async function autoSyncShoppingList() {
  try {
    const res = await apiRequest('/api/shopping-list/auto-sync', { method: 'POST' });
    showToast(res.message, 'success');
    setTimeout(() => window.location.reload(), 900);
  } catch (err) {
    console.error('Sync error:', err);
  }
}

// 9. Logout Handler
async function handleLogout() {
  try {
    await apiRequest('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
  } catch (err) {
    window.location.href = '/login';
  }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  
  // Close modals on backdrop click
  document.querySelectorAll('.modal-backdrop').forEach(b => {
    b.addEventListener('click', (e) => {
      if (e.target === b) {
        b.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });
});
