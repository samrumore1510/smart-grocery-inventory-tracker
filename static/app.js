/**
 * Smart Grocery Tracker • Frontend Single Page Application (SPA)
 * Pure Vanilla JavaScript • Zero Jinja2 • Direct REST API
 */

const state = {
  currentTab: 'dashboard',
  token: localStorage.getItem('sg_token') || '',
  user: null,
  categories: [],
  inventory: [],
  shoppingItems: [],
  filterExpiry: 'all',
  filterStock: 'all',
  filterCategory: 'all',
  searchQuery: '',
  charts: {},
};

// -----------------------------------------------------------------------------
// API Helper
// -----------------------------------------------------------------------------
async function apiCall(endpoint, method = 'GET', body = null) {
  const headers = {
    'Content-Type': 'application/json',
  };
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }

  const config = { method, headers };
  if (body) {
    config.body = JSON.stringify(body);
  }

  try {
    const res = await fetch(endpoint, config);
    if (res.status === 401) {
      // Auto fallback to demo user login if unauthorized
      console.warn('Session expired, auto-refreshing demo user...');
      await quickLogin('user', 'user123', false);
      return apiCall(endpoint, method, body);
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'API request failed');
    }
    return await res.json();
  } catch (err) {
    console.error('API Error:', err);
    showToast(err.message, 'error');
    throw err;
  }
}

// -----------------------------------------------------------------------------
// Initialization & Authentication
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  initTabNavigation();
  await initAuth();
  await loadCategories();
  await refreshCurrentTab();
});

function initTabNavigation() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      switchTab(target);
    });
  });

  document.getElementById('btnSwitchAccount').addEventListener('click', () => {
    document.getElementById('loginModal').style.display = 'flex';
  });

  document.getElementById('btnLogout').addEventListener('click', logout);
}

async function initAuth() {
  if (!state.token) {
    // Perform seamless initial login with user account
    await quickLogin('user', 'user123', false);
    return;
  }

  try {
    const user = await apiCall('/api/auth/me');
    setUserProfile(user);
  } catch {
    await quickLogin('user', 'user123', false);
  }
}

function setUserProfile(user) {
  state.user = user;
  document.getElementById('userName').textContent = user.full_name || user.username;
  document.getElementById('userRoleBadge').textContent = user.role;
  document.getElementById('userAvatar').textContent = (user.full_name || user.username).charAt(0).toUpperCase();
}

async function quickLogin(username, password, showNotification = true) {
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');

    state.token = data.access_token;
    localStorage.setItem('sg_token', data.access_token);
    setUserProfile(data.user);
    closeLoginModal();
    if (showNotification) {
      showToast(`Logged in as ${data.user.full_name} (${data.user.role})`, 'success');
      await refreshCurrentTab();
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function customLogin(e) {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value;
  await quickLogin(username, password, true);
}

function logout() {
  localStorage.removeItem('sg_token');
  state.token = '';
  showToast('Logged out. Re-logging as guest demo...', 'info');
  quickLogin('user', 'user123', false).then(() => {
    refreshCurrentTab();
  });
}

function closeLoginModal() {
  document.getElementById('loginModal').style.display = 'none';
}

// -----------------------------------------------------------------------------
// Tab Switching
// -----------------------------------------------------------------------------
function switchTab(tabName, queryOpts = null) {
  state.currentTab = tabName;
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tabName);
  });
  document.querySelectorAll('.tab-content').forEach(c => {
    c.classList.toggle('active', c.id === `tab-${tabName}`);
  });

  if (queryOpts) {
    if (queryOpts.expiry) setExpiryFilter(queryOpts.expiry);
    if (queryOpts.stock) setStockFilter(queryOpts.stock);
  }

  refreshCurrentTab();
}

async function refreshCurrentTab() {
  if (state.currentTab === 'dashboard') {
    await loadDashboard();
  } else if (state.currentTab === 'inventory') {
    await loadInventory();
  } else if (state.currentTab === 'shopping') {
    await loadShoppingList();
  } else if (state.currentTab === 'expenses') {
    await loadExpenses();
  }
}

// -----------------------------------------------------------------------------
// Categories
// -----------------------------------------------------------------------------
async function loadCategories() {
  try {
    const cats = await apiCall('/api/categories');
    state.categories = cats;

    // Populate category filter in inventory
    const catSelect = document.getElementById('categoryFilter');
    catSelect.innerHTML = '<option value="all">All Categories</option>';
    cats.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.name;
      opt.textContent = `${c.icon || '🏷️'} ${c.name}`;
      catSelect.appendChild(opt);
    });

    // Populate category dropdown in product modal
    const modalCat = document.getElementById('modalProductCategory');
    const modalShopCat = document.getElementById('modalShopCategory');
    const modalExpCat = document.getElementById('modalExpCategory');

    modalCat.innerHTML = '';
    modalShopCat.innerHTML = '';
    modalExpCat.innerHTML = '';

    cats.forEach(c => {
      const opt1 = document.createElement('option');
      opt1.value = c.name;
      opt1.textContent = `${c.icon || '🏷️'} ${c.name}`;
      modalCat.appendChild(opt1);

      const opt2 = document.createElement('option');
      opt2.value = c.name;
      opt2.textContent = `${c.icon || '🏷️'} ${c.name}`;
      modalShopCat.appendChild(opt2);

      const opt3 = document.createElement('option');
      opt3.value = c.name;
      opt3.textContent = `${c.icon || '🏷️'} ${c.name}`;
      modalExpCat.appendChild(opt3);
    });
  } catch (err) {
    console.warn('Could not load categories:', err);
  }
}

// -----------------------------------------------------------------------------
// 1. Dashboard Tab
// -----------------------------------------------------------------------------
async function loadDashboard() {
  try {
    const data = await apiCall('/api/dashboard');
    const kpis = data.kpis;

    // Update 5 Core KPIs
    document.getElementById('kpiTotalProducts').textContent = kpis.total_products;
    document.getElementById('kpiExpiringSoon').textContent = kpis.expiring_soon;
    document.getElementById('kpiExpired').textContent = kpis.expired;
    document.getElementById('kpiLowStock').textContent = kpis.low_stock;
    document.getElementById('kpiMonthlySpending').textContent = `₹${kpis.monthly_spending.toLocaleString('en-IN')}`;

    // Render Recommendations
    renderRecommendations(data.recommendations);

    // Render Priority Expiry Watchlist
    renderDashExpiring(data.expiring_preview);

    // Render Low Stock Restock Alerts
    renderDashLowStock(data.low_stock_preview);

    // Render Dashboard Charts
    renderDashboardCharts(data.expense_analysis);

    // Update Shopping Nav Badge
    updateShoppingBadge();
  } catch (err) {
    console.error('Failed to load dashboard:', err);
  }
}

function renderRecommendations(recs) {
  const container = document.getElementById('recsContainer');
  document.getElementById('recsCountBadge').textContent = `${recs.length} Insights Active`;
  if (!recs || recs.length === 0) {
    container.innerHTML = '<div class="rec-card rec-info"><div class="rec-header">✅ All Clear!</div><div class="rec-message">Inventory is fully balanced and fresh.</div></div>';
    return;
  }

  container.innerHTML = recs.map(r => `
    <div class="rec-card rec-${r.severity || 'info'}">
      <div class="rec-header">
        <span>${r.icon || '💡'}</span>
        <span>${escapeHtml(r.title)}</span>
      </div>
      <div class="rec-message">${escapeHtml(r.message)}</div>
    </div>
  `).join('');
}

function renderDashExpiring(products) {
  const tbody = document.getElementById('dashExpiringTbody');
  if (!products || products.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No items currently expiring soon.</td></tr>';
    return;
  }

  tbody.innerHTML = products.map(p => `
    <tr class="${p.expiry_status === 'expired' ? 'row-expired' : 'row-critical'}">
      <td>
        <div class="product-cell">
          <span class="product-name">${escapeHtml(p.name)}</span>
          <span class="product-brand">${escapeHtml(p.brand || p.category_name)}</span>
        </div>
      </td>
      <td><strong>${p.quantity}</strong> ${p.unit}</td>
      <td>${p.expiry_date}</td>
      <td><span class="badge badge-${p.expiry_status}">${p.expiry_badge_text}</span></td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="adjustProductQty('${p.id}', -1)" title="Mark 1 unit consumed">
          🍽️ Use
        </button>
      </td>
    </tr>
  `).join('');
}

function renderDashLowStock(products) {
  const tbody = document.getElementById('dashLowStockTbody');
  if (!products || products.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">All grocery items are well stocked!</td></tr>';
    return;
  }

  tbody.innerHTML = products.map(p => `
    <tr>
      <td>
        <div class="product-cell">
          <span class="product-name">${escapeHtml(p.name)}</span>
          <span class="product-brand">${escapeHtml(p.brand || '')}</span>
        </div>
      </td>
      <td>${escapeHtml(p.category_name)}</td>
      <td><span class="badge badge-${p.stock_status}">${p.quantity} ${p.unit}</span></td>
      <td>${p.min_quantity} ${p.unit}</td>
      <td>
        <button class="btn btn-primary btn-sm" onclick="adjustProductQty('${p.id}', 1)" title="Add 1 to pantry">
          ➕ Restock
        </button>
      </td>
    </tr>
  `).join('');
}

function renderDashboardCharts(analysis) {
  if (!analysis) return;

  // 1. Daily Trend Line Chart
  const trendCtx = document.getElementById('dashTrendChart')?.getContext('2d');
  if (trendCtx) {
    if (state.charts.dashTrend) state.charts.dashTrend.destroy();
    state.charts.dashTrend = new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: analysis.daily_trend.labels.slice(-14),
        datasets: [{
          label: 'Daily Spend (₹)',
          data: analysis.daily_trend.values.slice(-14),
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 3,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 2. Category Donut Chart
  const catCtx = document.getElementById('dashCategoryChart')?.getContext('2d');
  if (catCtx) {
    if (state.charts.dashCat) state.charts.dashCat.destroy();
    state.charts.dashCat = new Chart(catCtx, {
      type: 'doughnut',
      data: {
        labels: analysis.category_distribution.labels.slice(0, 6),
        datasets: [{
          data: analysis.category_distribution.values.slice(0, 6),
          backgroundColor: [
            '#2563eb', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6'
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } }
        },
        cutout: '65%'
      }
    });
  }
}

// -----------------------------------------------------------------------------
// 2. Inventory Tab
// -----------------------------------------------------------------------------
let debounceTimer;
function debounceInventorySearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    state.searchQuery = document.getElementById('inventorySearch').value.trim();
    loadInventory();
  }, 250);
}

function setExpiryFilter(val) {
  state.filterExpiry = val;
  document.querySelectorAll('#expiryFilterPills .filter-pill').forEach(b => {
    b.classList.toggle('active', b.dataset.expiry === val);
  });
  loadInventory();
}

function setStockFilter(val) {
  state.filterStock = val;
  document.querySelectorAll('#stockFilterPills .filter-pill').forEach(b => {
    b.classList.toggle('active', b.dataset.stock === val);
  });
  loadInventory();
}

function resetInventoryFilters() {
  state.searchQuery = '';
  state.filterExpiry = 'all';
  state.filterStock = 'all';
  state.filterCategory = 'all';
  document.getElementById('inventorySearch').value = '';
  document.getElementById('categoryFilter').value = 'all';
  setExpiryFilter('all');
  setStockFilter('all');
}

async function loadInventory() {
  try {
    const params = new URLSearchParams();
    if (state.searchQuery) params.append('search', state.searchQuery);
    const cat = document.getElementById('categoryFilter').value;
    if (cat && cat !== 'all') params.append('category', cat);
    if (state.filterExpiry !== 'all') params.append('expiry_status', state.filterExpiry);
    if (state.filterStock !== 'all') params.append('stock_status', state.filterStock);

    const items = await apiCall(`/api/inventory?${params.toString()}`);
    state.inventory = items;

    const tbody = document.getElementById('inventoryTbody');
    const emptyState = document.getElementById('inventoryEmptyState');

    if (!items || items.length === 0) {
      tbody.innerHTML = '';
      emptyState.style.display = 'block';
      return;
    }

    emptyState.style.display = 'none';
    tbody.innerHTML = items.map(p => `
      <tr class="${p.expiry_status === 'expired' ? 'row-expired' : p.expiry_status === 'critical' ? 'row-critical' : ''}">
        <td>
          <div class="product-cell">
            <span class="product-name">${escapeHtml(p.name)}</span>
            <span class="product-brand">${escapeHtml(p.brand || '')} • 📍 ${escapeHtml(p.storage_location || 'Pantry')}</span>
          </div>
        </td>
        <td>${escapeHtml(p.category_name)}</td>
        <td>
          <div class="qty-stepper">
            <button class="qty-btn" onclick="adjustProductQty('${p.id}', -1)">-</button>
            <span class="qty-val">${p.quantity}</span>
            <button class="qty-btn" onclick="adjustProductQty('${p.id}', 1)">+</button>
            <span class="qty-unit">${p.unit}</span>
          </div>
        </td>
        <td><span class="badge badge-${p.stock_status}">${p.stock_badge_text}</span></td>
        <td>${p.expiry_date}</td>
        <td><span class="badge badge-${p.expiry_status}">${p.expiry_badge_text}</span></td>
        <td>₹${parseFloat(p.unit_price || 0).toFixed(2)}</td>
        <td><strong>₹${parseFloat(p.total_value || 0).toFixed(2)}</strong></td>
        <td class="text-right">
          <button class="btn btn-ghost btn-sm" onclick="openEditProductModal('${p.id}')" title="Edit">✏️</button>
          <button class="btn btn-ghost btn-sm text-danger" onclick="deleteProduct('${p.id}')" title="Delete">🗑️</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load inventory:', err);
  }
}

async function adjustProductQty(productId, delta) {
  try {
    const res = await apiCall(`/api/inventory/${productId}/adjust`, 'PATCH', { delta });
    showToast(`Updated ${res.name}: ${res.quantity} ${res.unit}`, 'info');
    if (state.currentTab === 'inventory') {
      await loadInventory();
    } else if (state.currentTab === 'dashboard') {
      await loadDashboard();
    }
  } catch (err) {
    showToast('Failed to adjust quantity', 'error');
  }
}

function openProductModal(isEdit = false) {
  document.getElementById('productForm').reset();
  document.getElementById('modalProductId').value = '';
  document.getElementById('productModalTitle').textContent = isEdit ? 'Edit Product' : 'Add New Product';

  // Default dates
  const today = new Date().toISOString().split('T')[0];
  const nextWeek = new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0];
  document.getElementById('modalProductPurchaseDate').value = today;
  document.getElementById('modalProductExpiryDate').value = nextWeek;

  document.getElementById('productModal').style.display = 'flex';
}

function openEditProductModal(productId) {
  const p = state.inventory.find(i => i.id === productId);
  if (!p) return;

  openProductModal(true);
  document.getElementById('modalProductId').value = p.id;
  document.getElementById('modalProductName').value = p.name;
  document.getElementById('modalProductBrand').value = p.brand || '';
  document.getElementById('modalProductCategory').value = p.category_name;
  document.getElementById('modalProductQuantity').value = p.quantity;
  document.getElementById('modalProductUnit').value = p.unit;
  document.getElementById('modalProductMinQty').value = p.min_quantity;
  document.getElementById('modalProductPrice').value = p.unit_price;
  document.getElementById('modalProductPurchaseDate').value = p.purchase_date;
  document.getElementById('modalProductExpiryDate').value = p.expiry_date;
  document.getElementById('modalProductLocation').value = p.storage_location || 'Pantry';
}

function closeProductModal() {
  document.getElementById('productModal').style.display = 'none';
}

async function saveProduct(e) {
  e.preventDefault();
  const pid = document.getElementById('modalProductId').value;
  const payload = {
    name: document.getElementById('modalProductName').value.trim(),
    brand: document.getElementById('modalProductBrand').value.trim(),
    category_name: document.getElementById('modalProductCategory').value,
    quantity: parseFloat(document.getElementById('modalProductQuantity').value),
    unit: document.getElementById('modalProductUnit').value,
    min_quantity: parseFloat(document.getElementById('modalProductMinQty').value),
    unit_price: parseFloat(document.getElementById('modalProductPrice').value),
    purchase_date: document.getElementById('modalProductPurchaseDate').value,
    expiry_date: document.getElementById('modalProductExpiryDate').value,
    storage_location: document.getElementById('modalProductLocation').value,
  };

  try {
    if (pid) {
      await apiCall(`/api/inventory/${pid}`, 'PUT', payload);
      showToast('Product updated successfully!', 'success');
    } else {
      await apiCall('/api/inventory', 'POST', payload);
      showToast('Product added to inventory!', 'success');
    }
    closeProductModal();
    loadInventory();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function deleteProduct(productId) {
  if (!confirm('Are you sure you want to remove this grocery item?')) return;
  try {
    await apiCall(`/api/inventory/${productId}`, 'DELETE');
    showToast('Product removed from inventory', 'info');
    loadInventory();
  } catch (err) {
    showToast('Failed to delete product', 'error');
  }
}

// -----------------------------------------------------------------------------
// 3. Shopping List Tab
// -----------------------------------------------------------------------------
async function loadShoppingList() {
  try {
    const data = await apiCall('/api/shopping');
    state.shoppingItems = data.items;

    document.getElementById('shopPendingCount').textContent = data.pending_count;
    document.getElementById('shopEstimatedCost').textContent = `₹${data.total_estimated_cost.toLocaleString('en-IN')}`;
    document.getElementById('navShoppingBadge').textContent = data.pending_count;

    const container = document.getElementById('shoppingItemsContainer');
    if (!data.items || data.items.length === 0) {
      container.innerHTML = '<div class="empty-state span-2"><div class="empty-icon">🎉</div><h3>Shopping list is empty!</h3><p>Click "Auto-Sync from Inventory" to populate with low stock items.</p></div>';
      return;
    }

    container.innerHTML = data.items.map(item => `
      <div class="shop-card ${item.is_purchased ? 'purchased' : ''}">
        <input type="checkbox" class="shop-check" ${item.is_purchased ? 'checked' : ''} onchange="toggleShoppingItem('${item.id}')" title="Mark purchased" />
        <div class="shop-info">
          <div class="shop-name">${escapeHtml(item.product_name)}</div>
          <div class="shop-meta">
            ${escapeHtml(item.category_name)} • Need: <strong>${item.target_quantity} ${item.unit}</strong>
            ${item.auto_added ? '• <span class="badge badge-lowstock">Auto-Restock</span>' : ''}
          </div>
        </div>
        <div class="shop-price">₹${parseFloat(item.estimated_price || 0).toFixed(2)}</div>
        <button class="shop-delete" onclick="deleteShoppingItem('${item.id}')" title="Remove">✕</button>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load shopping list:', err);
  }
}

async function updateShoppingBadge() {
  try {
    const data = await apiCall('/api/shopping');
    document.getElementById('navShoppingBadge').textContent = data.pending_count;
  } catch {}
}

async function toggleShoppingItem(itemId) {
  try {
    const res = await apiCall(`/api/shopping/${itemId}/toggle`, 'PATCH');
    if (res.is_purchased) {
      showToast('Item purchased! Auto-restocked into pantry.', 'success');
    }
    loadShoppingList();
  } catch (err) {
    showToast('Failed to update status', 'error');
  }
}

async function syncShoppingList() {
  try {
    const res = await apiCall('/api/shopping/sync', 'POST');
    showToast(`Inventory scanned! Added ${res.synced_items} low-stock items.`, 'success');
    if (state.currentTab === 'shopping') {
      loadShoppingList();
    } else {
      updateShoppingBadge();
    }
  } catch (err) {
    showToast('Failed to sync shopping list', 'error');
  }
}

async function deleteShoppingItem(itemId) {
  try {
    await apiCall(`/api/shopping/${itemId}`, 'DELETE');
    loadShoppingList();
  } catch (err) {
    showToast('Failed to remove item', 'error');
  }
}

async function clearPurchasedItems() {
  try {
    const res = await apiCall('/api/shopping/clear-purchased', 'DELETE');
    showToast(`Cleared ${res.deleted_count} purchased items`, 'info');
    loadShoppingList();
  } catch (err) {
    showToast('Failed to clear purchased items', 'error');
  }
}

function copyShoppingListWhatsApp() {
  const pending = state.shoppingItems.filter(i => !i.is_purchased);
  if (pending.length === 0) {
    showToast('No pending items on shopping list!', 'info');
    return;
  }

  const total = pending.reduce((sum, i) => sum + (i.estimated_price || 0), 0);
  let text = `🛒 *Smart Grocery Shopping Checklist*\n📅 Date: ${new Date().toLocaleDateString()}\n\n`;
  pending.forEach((item, idx) => {
    text += `${idx + 1}. [ ] ${item.product_name} - ${item.target_quantity} ${item.unit} (~₹${item.estimated_price})\n`;
  });
  text += `\n*Estimated Total:* ₹${total.toLocaleString('en-IN')}\n_Auto-generated via SmartGrocery Tracker_`;

  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard! Ready to paste into WhatsApp.', 'success');
  }).catch(() => {
    showToast('Could not copy automatically. Clipboard permission required.', 'error');
  });
}

function openShoppingModal() {
  document.getElementById('shoppingForm').reset();
  document.getElementById('shoppingModal').style.display = 'flex';
}

function closeShoppingModal() {
  document.getElementById('shoppingModal').style.display = 'none';
}

async function saveShoppingItem(e) {
  e.preventDefault();
  const payload = {
    product_name: document.getElementById('modalShopName').value.trim(),
    category_name: document.getElementById('modalShopCategory').value,
    target_quantity: parseFloat(document.getElementById('modalShopQty').value),
    unit: document.getElementById('modalShopUnit').value,
    estimated_price: parseFloat(document.getElementById('modalShopPrice').value) || 0,
  };

  try {
    await apiCall('/api/shopping', 'POST', payload);
    showToast('Item added to shopping list', 'success');
    closeShoppingModal();
    loadShoppingList();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// -----------------------------------------------------------------------------
// 4. Expenses & Analytics Tab
// -----------------------------------------------------------------------------
async function loadExpenses() {
  try {
    const data = await apiCall('/api/expenses');
    const an = data.analysis;

    document.getElementById('expAllTime').textContent = `₹${an.total_expenses_all_time.toLocaleString('en-IN')}`;
    const monthlySum = an.monthly_trend.values.slice(-1)[0] || 0;
    document.getElementById('expThisMonth').textContent = `₹${monthlySum.toLocaleString('en-IN')}`;

    // Calculate potential wastage from dashboard metrics
    const dash = await apiCall('/api/dashboard');
    document.getElementById('expWastage').textContent = `₹${dash.kpis.wastage_cost.toLocaleString('en-IN')}`;

    // Render Charts
    renderExpenseCharts(an);

    // Render Top Expenses
    const topTbody = document.getElementById('topExpensesTbody');
    topTbody.innerHTML = (an.top_expenses || []).map(t => `
      <tr>
        <td><strong>${escapeHtml(t.product_name)}</strong></td>
        <td>₹${parseFloat(t.amount).toLocaleString('en-IN')}</td>
      </tr>
    `).join('');

    // Render Logs Table
    const logsTbody = document.getElementById('expenseLogsTbody');
    logsTbody.innerHTML = (data.expenses || []).map(e => `
      <tr>
        <td>${e.expense_date}</td>
        <td><strong>${escapeHtml(e.product_name)}</strong></td>
        <td>${escapeHtml(e.category_name)}</td>
        <td>${e.quantity} ${e.unit || ''}</td>
        <td><span class="badge badge-info">${e.payment_method || 'UPI'}</span></td>
        <td><strong>₹${parseFloat(e.amount).toFixed(2)}</strong></td>
        <td class="text-muted">${escapeHtml(e.notes || '-')}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load expenses:', err);
  }
}

function renderExpenseCharts(analysis) {
  // 1. Daily Bar Chart
  const dailyCtx = document.getElementById('expenseDailyChart')?.getContext('2d');
  if (dailyCtx) {
    if (state.charts.expDaily) state.charts.expDaily.destroy();
    state.charts.expDaily = new Chart(dailyCtx, {
      type: 'bar',
      data: {
        labels: analysis.daily_trend.labels.slice(-20),
        datasets: [{
          label: 'Spending (₹)',
          data: analysis.daily_trend.values.slice(-20),
          backgroundColor: '#2563eb',
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 2. Category Pie Chart
  const catCtx = document.getElementById('expenseCategoryChart')?.getContext('2d');
  if (catCtx) {
    if (state.charts.expCat) state.charts.expCat.destroy();
    state.charts.expCat = new Chart(catCtx, {
      type: 'pie',
      data: {
        labels: analysis.category_distribution.labels,
        datasets: [{
          data: analysis.category_distribution.values,
          backgroundColor: [
            '#2563eb', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6', '#f97316'
          ],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } }
        }
      }
    });
  }

  // 3. Payment Methods Doughnut
  const payCtx = document.getElementById('expensePaymentChart')?.getContext('2d');
  if (payCtx) {
    if (state.charts.expPay) state.charts.expPay.destroy();
    state.charts.expPay = new Chart(payCtx, {
      type: 'doughnut',
      data: {
        labels: analysis.payment_methods.labels,
        datasets: [{
          data: analysis.payment_methods.values,
          backgroundColor: ['#10b981', '#f59e0b', '#2563eb', '#64748b'],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%'
      }
    });
  }
}

function openExpenseModal() {
  document.getElementById('expenseForm').reset();
  document.getElementById('modalExpDate').value = new Date().toISOString().split('T')[0];
  document.getElementById('expenseModal').style.display = 'flex';
}

function closeExpenseModal() {
  document.getElementById('expenseModal').style.display = 'none';
}

async function saveExpense(e) {
  e.preventDefault();
  const payload = {
    product_name: document.getElementById('modalExpName').value.trim(),
    category_name: document.getElementById('modalExpCategory').value,
    amount: parseFloat(document.getElementById('modalExpAmount').value),
    expense_date: document.getElementById('modalExpDate').value,
    payment_method: document.getElementById('modalExpPayment').value,
    notes: document.getElementById('modalExpNotes').value.trim(),
  };

  try {
    await apiCall('/api/expenses', 'POST', payload);
    showToast('Expense logged successfully!', 'success');
    closeExpenseModal();
    loadExpenses();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// -----------------------------------------------------------------------------
// Utilities
// -----------------------------------------------------------------------------
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
