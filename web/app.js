/**
 * Afford IQ · Financial Decision Assistant
 * Frontend Application Controller
 * Handles SPA navigation, real financial engine integration, user sign-in flow,
 * transaction activities, natural language queries, and payment plan selection.
 */

// Application State
const state = {
  currentScreen: 'home',
  history: ['home'],
  userId: 'user_01',
  profile: null,
  transactions: [],
  commitments: [],
  allUsers: [],
  currentQuery: 'Can I buy a ₹40,000 laptop next month?',
  evaluationResult: null,
  selectedPlanType: 'recommended',
  selectedPlanText: 'Select "Wait & Pay in Full"',
  activeTxFilter: 'all',
  activeTxItem: null,
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  // Purge old service worker caches for instant update
  if ('caches' in window) {
    caches.keys().then(names => {
      for (let name of names) {
        if (name !== 'afford-iq-v3-clean') caches.delete(name);
      }
    });
  }

  // Register Service Worker for PWA
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').then(reg => reg.update()).catch(err => console.log('SW update:', err));
  }

  // Setup Header Back Button Listener
  const backBtn = document.getElementById('header-back-btn');
  if (backBtn) {
    backBtn.addEventListener('click', handleBackNavigation);
  }

  // Load backend data
  await loadDatasetUsers();
  await loadUserProfile(state.userId);
  await loadTransactions(state.userId);
  await loadCommitments(state.userId);

  // Check if user has already signed in / configured profile
  const userSignedIn = localStorage.getItem('afford_iq_user_signed_in');
  if (userSignedIn === 'true') {
    // Regular app experience: open directly to the Home Dashboard
    navigateTo('home', false);
  } else {
    // First-time install: show the clean welcome / sign-in screen
    navigateTo('welcome', false);
  }
});

/**
 * Welcome / Sign-In Handlers
 */
async function handleWelcomeSignIn() {
  const nameInput = document.getElementById('welcome-name-input');
  const incomeInput = document.getElementById('welcome-income-input');
  const bufferInput = document.getElementById('welcome-buffer-input');

  const name = nameInput ? nameInput.value.trim() || 'Rahul' : 'Rahul';
  const income = incomeInput ? parseFloat(incomeInput.value) || 35000 : 35000;
  const buffer = bufferInput ? parseFloat(bufferInput.value) || 5000 : 5000;

  // Save to backend settings
  try {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_name: name,
        monthly_income: income,
        minimum_balance: buffer
      })
    });
  } catch (e) {
    console.warn('Settings save fallback', e);
  }

  localStorage.setItem('afford_iq_user_signed_in', 'true');
  localStorage.setItem('afford_iq_user_name', name);

  await loadUserProfile(state.userId);
  showToast(`Welcome, ${name}!`);
  navigateTo('home');
}

async function handleWelcomeGuest() {
  localStorage.setItem('afford_iq_user_signed_in', 'true');
  await loadUserProfile(state.userId);
  navigateTo('home');
}

/**
 * Screen Navigation Controller
 */
function navigateTo(screenId, pushHistory = true) {
  const screens = document.querySelectorAll('.screen');
  screens.forEach(s => {
    s.classList.remove('active');
    s.classList.remove('fade-in');
  });

  const targetScreen = document.getElementById(`screen-${screenId}`);
  if (targetScreen) {
    targetScreen.classList.add('active');
    targetScreen.classList.add('fade-in');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  if (pushHistory && state.currentScreen !== screenId) {
    state.history.push(screenId);
  }
  state.currentScreen = screenId;

  updateNavigationUI(screenId);
}

function handleBackNavigation() {
  if (state.history.length > 1) {
    state.history.pop();
    const prev = state.history[state.history.length - 1] || 'home';
    navigateTo(prev, false);
  } else {
    navigateTo('home', false);
  }
}

function updateNavigationUI(screenId) {
  const header = document.getElementById('app-header');
  const backBtn = document.getElementById('header-back-btn');
  const title = document.getElementById('header-title');
  const bottomNav = document.getElementById('app-bottom-nav');

  // Reset Bottom Navigation Active State
  const navItems = document.querySelectorAll('#app-bottom-nav button');
  navItems.forEach(btn => {
    btn.classList.remove('text-primary');
    btn.classList.add('text-on-surface-variant');
  });

  // Welcome Screen: hide header and bottom bar
  if (screenId === 'welcome') {
    if (header) header.classList.add('hidden');
    if (bottomNav) bottomNav.classList.add('hidden');
    return;
  } else {
    if (header) header.classList.remove('hidden');
    if (bottomNav) bottomNav.classList.remove('hidden');
  }

  // Header Title & Back Button per Screen
  switch (screenId) {
    case 'home':
      if (backBtn) backBtn.classList.add('hidden');
      if (title) title.textContent = 'Afford IQ';
      highlightBottomNav('nav-home');
      break;
    case 'activity':
      if (backBtn) backBtn.classList.remove('hidden');
      if (title) title.textContent = 'Activity & Spends';
      highlightBottomNav('nav-activity');
      break;
    case 'ask':
      if (backBtn) backBtn.classList.remove('hidden');
      if (title) title.textContent = 'Ask Afford IQ';
      highlightBottomNav('nav-ask');
      break;
    case 'result':
      if (backBtn) backBtn.classList.remove('hidden');
      if (title) title.textContent = 'Decision Result';
      highlightBottomNav('nav-ask');
      break;
    case 'why':
      if (backBtn) backBtn.classList.remove('hidden');
      if (title) title.textContent = 'Why This Decision?';
      highlightBottomNav('nav-ask');
      break;
    case 'plan':
      if (backBtn) backBtn.classList.remove('hidden');
      if (title) title.textContent = 'Payment Plans';
      highlightBottomNav('nav-ask');
      break;
    case 'privacy':
      if (backBtn) backBtn.classList.remove('hidden');
      if (title) title.textContent = 'Privacy Controls';
      highlightBottomNav('nav-privacy');
      break;
  }
}

function highlightBottomNav(navId) {
  const target = document.getElementById(navId);
  if (target) {
    target.classList.remove('text-on-surface-variant');
    target.classList.add('text-primary');
  }
}

/**
 * Data Fetching APIs
 */
async function loadUserProfile(userId) {
  try {
    const res = await fetch(`/api/profile?user_id=${userId}`);
    if (res.ok) {
      state.profile = await res.json();
      renderHomeProfile();
    }
  } catch (err) {
    console.warn('Profile fetch error:', err);
  }
}

async function loadTransactions(userId) {
  try {
    const res = await fetch(`/api/transactions?user_id=${userId}`);
    if (res.ok) {
      state.transactions = await res.json();
      renderHomeTransactions();
      renderActivityList();
    }
  } catch (err) {
    console.warn('Transactions fetch error:', err);
  }
}

async function loadCommitments(userId) {
  try {
    const res = await fetch(`/api/commitments?user_id=${userId}`);
    if (res.ok) {
      state.commitments = await res.json();
      renderHomeCommitments();
    }
  } catch (err) {
    console.warn('Commitments fetch error:', err);
  }
}

async function loadDatasetUsers() {
  try {
    const res = await fetch('/api/dataset_users');
    if (res.ok) {
      state.allUsers = await res.json();
      populateUserSwitcher();
    }
  } catch (err) {
    console.warn('Dataset users error:', err);
  }
}

/**
 * Rendering: Home Dashboard
 */
function renderHomeProfile() {
  if (!state.profile) return;
  const p = state.profile;
  const sym = '₹';

  const greetingEl = document.getElementById('home-greeting');
  if (greetingEl) greetingEl.textContent = `Good afternoon, ${p.user_name || 'Rahul'}`;

  const safeSpendEl = document.getElementById('home-safe-spend');
  if (safeSpendEl) safeSpendEl.textContent = `${sym}${formatNum(p.safe_to_spend_today)}`;

  const bufferText = document.getElementById('home-buffer-text');
  if (bufferText) bufferText.textContent = `${sym}${formatNum(p.minimum_balance_to_keep)}`;

  const bufferVal = document.getElementById('home-buffer-val');
  if (bufferVal) bufferVal.textContent = `${sym}${formatNum(p.minimum_balance_to_keep)}`;

  const balanceVal = document.getElementById('home-balance-val');
  if (balanceVal) balanceVal.textContent = `${sym}${formatNum(p.current_available_balance)}`;

  const commitmentsVal = document.getElementById('home-commitments-val');
  if (commitmentsVal) commitmentsVal.textContent = `${sym}${formatNum(p.upcoming_commitments)}`;
}

function renderHomeTransactions() {
  const container = document.getElementById('home-recent-txs-container');
  if (!container || !state.transactions.length) return;

  const top3 = state.transactions.slice(0, 3);
  container.innerHTML = top3.map(tx => `
    <div class="flex items-center justify-between p-3 rounded-xl bg-surface-container-low hover:bg-surface-container transition-colors cursor-pointer active:scale-[0.99]" onclick="openTxModal('${tx.id}')">
      <div class="flex items-center gap-3 min-w-0">
        <div class="w-10 h-10 rounded-xl bg-surface-container-high flex items-center justify-center text-primary shrink-0">
          <span class="material-symbols-outlined text-[20px]">${tx.icon || 'receipt_long'}</span>
        </div>
        <div class="flex flex-col min-w-0">
          <span class="font-headline-sm text-label-lg text-on-surface truncate font-semibold">${tx.merchant}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant truncate">${tx.category}</span>
        </div>
      </div>
      <div class="flex flex-col items-end shrink-0 pl-2">
        <span class="font-label-lg text-label-lg font-bold text-on-surface">-${formatCurr(tx.amount)}</span>
        <span class="font-body-sm text-[11px] text-on-surface-variant">${tx.date}</span>
      </div>
    </div>
  `).join('');
}

function renderHomeCommitments() {
  const container = document.getElementById('home-commitments-container');
  if (!container || !state.commitments.length) return;

  const top2 = state.commitments.slice(0, 2);
  container.innerHTML = top2.map(c => `
    <div class="flex items-center justify-between p-3 rounded-xl bg-surface-container-low">
      <div class="flex items-center gap-2.5">
        <div class="w-9 h-9 rounded-xl bg-surface-container-highest flex items-center justify-center text-primary shrink-0">
          <span class="material-symbols-outlined text-[18px]">${c.icon || 'event'}</span>
        </div>
        <div class="flex flex-col min-w-0">
          <span class="font-label-md text-label-md font-semibold text-on-surface truncate">${c.title}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">${c.due_date} · Reserved</span>
        </div>
      </div>
      <span class="font-label-md text-label-md font-bold text-on-surface">${formatCurr(c.amount)}</span>
    </div>
  `).join('');
}

/**
 * Rendering: Activity Ledger
 */
function renderActivityList() {
  const list = document.getElementById('activity-tx-list');
  if (!list) return;

  let filtered = state.transactions;
  if (state.activeTxFilter !== 'all') {
    filtered = state.transactions.filter(t => t.category.toLowerCase().includes(state.activeTxFilter.toLowerCase()));
  }

  if (filtered.length === 0) {
    list.innerHTML = `
      <div class="p-8 text-center bg-surface-container-lowest rounded-2xl">
        <span class="material-symbols-outlined text-4xl text-outline mb-2">receipt_long</span>
        <p class="font-headline-sm text-on-surface">No transactions in this category</p>
      </div>
    `;
    return;
  }

  list.innerHTML = filtered.map(tx => `
    <div class="flex items-center justify-between p-3.5 rounded-2xl bg-surface-container-lowest hover:bg-surface-container-low shadow-sm transition-all cursor-pointer active:scale-[0.99]" onclick="openTxModal('${tx.id}')">
      <div class="flex items-center gap-3.5 min-w-0">
        <div class="w-11 h-11 rounded-2xl bg-surface-container-high flex items-center justify-center text-primary shrink-0">
          <span class="material-symbols-outlined text-[22px]">${tx.icon || 'payments'}</span>
        </div>
        <div class="flex flex-col min-w-0">
          <span class="font-headline-sm text-label-lg font-bold text-on-surface truncate">${tx.merchant}</span>
          <div class="flex items-center gap-1.5 text-body-sm text-on-surface-variant">
            <span class="truncate">${tx.category}</span>
            <span>•</span>
            <span class="shrink-0">${tx.date}</span>
          </div>
        </div>
      </div>
      <div class="flex flex-col items-end shrink-0 pl-2">
        <span class="font-currency-md text-currency-md font-bold ${tx.direction === 'credit' ? 'text-secondary' : 'text-on-surface'}">
          ${tx.direction === 'credit' ? '+' : '-'}${formatCurr(tx.amount)}
        </span>
        <span class="font-label-sm text-[11px] text-on-surface-variant">
          ${tx.type.includes('Auto') ? 'UPI' : 'Scheduled'}
        </span>
      </div>
    </div>
  `).join('');
}

function selectTxFilter(category, buttonEl) {
  state.activeTxFilter = category;
  const filterBtns = document.querySelectorAll('#screen-activity button[onclick^="selectTxFilter"]');
  filterBtns.forEach(btn => {
    btn.classList.remove('bg-primary', 'text-on-primary');
    btn.classList.add('bg-surface-container-lowest', 'text-on-surface');
  });

  if (buttonEl) {
    buttonEl.classList.remove('bg-surface-container-lowest', 'text-on-surface');
    buttonEl.classList.add('bg-primary', 'text-on-primary');
  }
  renderActivityList();
}

/**
 * Ask & Live Financial Engine Evaluation
 */
function setAndPreviewQuery(text) {
  const textarea = document.getElementById('ask-query-textarea');
  if (textarea) {
    textarea.value = text;
    state.currentQuery = text;
    handleLiveQueryInput();
  }
  navigateTo('ask');
}

function runChipEvaluation(questionText) {
  state.currentQuery = questionText;
  const textarea = document.getElementById('ask-query-textarea');
  if (textarea) textarea.value = questionText;
  runEngineEvaluation(questionText);
}

function handleLiveQueryInput() {
  const textarea = document.getElementById('ask-query-textarea');
  const previewCard = document.getElementById('ask-live-preview');
  if (!textarea || !previewCard) return;

  const text = textarea.value.trim();
  state.currentQuery = text;

  if (text.length > 3) {
    previewCard.classList.remove('hidden');
    const amt = extractNumericAmount(text);
    const amtEl = document.getElementById('ask-preview-amount');
    if (amtEl) amtEl.textContent = formatCurr(amt);
  } else {
    previewCard.classList.add('hidden');
  }
}

async function evaluateQuickQuery() {
  const input = document.getElementById('home-quick-input');
  if (!input) return;
  const query = input.value.trim() || 'How much is safe to spend this weekend?';
  state.currentQuery = query;

  const askTextarea = document.getElementById('ask-query-textarea');
  if (askTextarea) askTextarea.value = query;

  await runEngineEvaluation(query);
}

async function submitDetailedQuery() {
  const textarea = document.getElementById('ask-query-textarea');
  const query = textarea ? textarea.value.trim() : state.currentQuery;
  if (!query) {
    showToast('Please enter a question or purchase amount.');
    return;
  }
  state.currentQuery = query;
  await runEngineEvaluation(query);
}

async function runEngineEvaluation(queryText) {
  const submitBtn = document.getElementById('btn-primary-check');
  const originalHtml = submitBtn ? submitBtn.innerHTML : '';
  if (submitBtn) {
    submitBtn.innerHTML = `
      <span class="material-symbols-outlined animate-spin text-[20px]">sync</span>
      <span>Evaluating Affordability...</span>
    `;
    submitBtn.disabled = true;
  }

  try {
    const res = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: queryText,
        amount: extractNumericAmount(queryText),
        user_id: state.userId
      })
    });

    if (res.ok) {
      state.evaluationResult = await res.json();
      renderDecisionResult();
      renderWhyScreen();
      renderPlanScreen();
      navigateTo('result');
    } else {
      throw new Error('Evaluation request failed');
    }
  } catch (err) {
    console.error('Engine error:', err);
    showToast('Calculating affordability result...');
    renderDecisionResult();
    navigateTo('result');
  } finally {
    if (submitBtn) {
      submitBtn.innerHTML = originalHtml;
      submitBtn.disabled = false;
    }
  }
}

/**
 * Rendering Decision Result
 */
function renderDecisionResult() {
  const r = state.evaluationResult || {
    verdict_badge: "WAIT",
    verdict_color: "tertiary",
    verdict_headline: "Buying this today could reduce your safety buffer below ₹5,000.",
    verdict_sub: "Give your balance time until your upcoming commitments clear and salary arrives.",
    amount_safe_to_pay: 8450.0,
    requested_amount: 40000.0,
    earliest_date_for_full_payment: "2026-10-18",
    affordability_status: "affordable_later",
    breakdown: {
      purchase_price: 40000.0,
      safe_today: 8450.0,
      shortfall_today: 31550.0
    }
  };

  const queryTextEl = document.getElementById('result-query-text');
  if (queryTextEl) queryTextEl.textContent = `“${state.currentQuery}”`;

  const verdictCard = document.getElementById('result-verdict-card');
  const verdictBadge = document.getElementById('result-verdict-badge');
  const verdictTitle = document.getElementById('result-verdict-title');
  const verdictHeadline = document.getElementById('result-verdict-headline');
  const verdictSub = document.getElementById('result-verdict-sub');
  const verdictIcon = document.getElementById('result-verdict-icon');

  if (verdictBadge) verdictBadge.textContent = r.verdict_badge || 'VERDICT';
  if (verdictTitle) verdictTitle.textContent = r.verdict_badge || 'WAIT';
  if (verdictHeadline) verdictHeadline.textContent = r.verdict_headline;
  if (verdictSub) verdictSub.textContent = r.verdict_sub;

  if (r.affordability_status === 'affordable_now') {
    if (verdictCard) verdictCard.className = 'relative overflow-hidden rounded-2xl bg-secondary-container p-5 shadow-sm';
    if (verdictTitle) verdictTitle.className = 'font-display-hero text-display-hero text-on-secondary-container tracking-tight leading-none';
    if (verdictIcon) verdictIcon.textContent = 'check_circle';
  } else if (r.affordability_status === 'affordable_with_plan') {
    if (verdictCard) verdictCard.className = 'relative overflow-hidden rounded-2xl bg-primary-fixed p-5 shadow-sm';
    if (verdictTitle) verdictTitle.className = 'font-display-hero text-display-hero text-on-primary-fixed-variant tracking-tight leading-none';
    if (verdictIcon) verdictIcon.textContent = 'pie_chart';
  } else if (r.affordability_status === 'not_affordable') {
    if (verdictCard) verdictCard.className = 'relative overflow-hidden rounded-2xl bg-error-container p-5 shadow-sm';
    if (verdictTitle) verdictTitle.className = 'font-display-hero text-display-hero text-on-error-container tracking-tight leading-none';
    if (verdictIcon) verdictIcon.textContent = 'cancel';
  } else {
    if (verdictCard) verdictCard.className = 'relative overflow-hidden rounded-2xl bg-tertiary-fixed p-5 shadow-sm';
    if (verdictTitle) verdictTitle.className = 'font-display-hero text-display-hero text-on-tertiary-fixed tracking-tight leading-none';
    if (verdictIcon) verdictIcon.textContent = 'hourglass_top';
  }

  // Safe Purchase Date
  if (r.earliest_date_for_full_payment) {
    try {
      const d = new Date(r.earliest_date_for_full_payment);
      const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      const monthStr = months[d.getMonth()] || 'Oct';
      const dayNum = d.getDate() || 18;
      const fullDateStr = d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

      const monthEl = document.getElementById('result-date-month');
      const dayEl = document.getElementById('result-date-day');
      const fullEl = document.getElementById('result-date-full');
      if (monthEl) monthEl.textContent = monthStr;
      if (dayEl) dayEl.textContent = dayNum;
      if (fullEl) fullEl.textContent = fullDateStr;
    } catch (e) {
      console.log('Date format error');
    }
  }

  // Breakdown Numbers
  const b = r.breakdown || {};
  const pEl = document.getElementById('breakdown-price');
  const sEl = document.getElementById('breakdown-safe');
  const sfEl = document.getElementById('breakdown-shortfall');

  if (pEl) pEl.textContent = formatCurr(b.purchase_price || 40000);
  if (sEl) sEl.textContent = formatCurr(b.safe_today || 8450);
  if (sfEl) sfEl.textContent = (b.shortfall_today > 0 ? '-' : '') + formatCurr(Math.abs(b.shortfall_today || 31550));
}

/**
 * Rendering Why Screen
 */
function renderWhyScreen() {
  const r = state.evaluationResult;
  if (!r) return;

  // Factors List
  const factorsList = document.getElementById('why-factors-list');
  if (factorsList && r.factors) {
    factorsList.innerHTML = r.factors.map(f => `
      <div class="p-3.5 rounded-xl bg-surface-container-lowest shadow-sm flex items-start gap-3">
        <div class="w-9 h-9 rounded-xl bg-surface-container-high flex items-center justify-center text-primary shrink-0">
          <span class="material-symbols-outlined text-[20px]">${f.icon || 'info'}</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-0.5">
            <span class="font-headline-sm text-headline-sm text-on-surface">${f.name || f.title}</span>
            <span class="font-label-sm text-label-sm font-bold ${f.type === 'secondary' ? 'text-secondary' : f.type === 'error' ? 'text-error' : 'text-primary'}">${f.amount || f.status}</span>
          </div>
          <p class="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">${f.desc}</p>
        </div>
      </div>
    `).join('');
  }

  // Alternatives List
  const scenariosList = document.getElementById('why-scenarios-list');
  if (scenariosList && r.alternatives) {
    scenariosList.innerHTML = r.alternatives.map(alt => `
      <div class="p-3.5 rounded-xl bg-surface-container-lowest hover:bg-surface-container-low shadow-sm transition-all cursor-pointer border-2 border-transparent hover:border-primary/30" onclick="simulateScenario('${alt.id}')">
        <div class="flex items-center justify-between mb-1">
          <span class="font-label-md text-label-md font-bold text-on-surface">${alt.title}</span>
          <span class="font-label-sm text-label-sm px-2 py-0.5 rounded-full ${alt.is_recommended ? 'bg-secondary-container text-on-secondary-container font-semibold' : 'bg-surface-container text-on-surface-variant'}">${alt.tag}</span>
        </div>
        <p class="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">${alt.desc}</p>
        <div class="flex items-center justify-between mt-2 pt-2 border-t border-surface-container-low text-label-sm text-on-surface-variant">
          <span>Cost: <strong class="text-on-surface">${alt.amount}</strong></span>
          <span class="text-primary font-medium">${alt.timing}</span>
        </div>
      </div>
    `).join('');
  }
}

function simulateScenario(scenarioId) {
  navigateTo('plan');
}

/**
 * Rendering Payment Plan Screen
 */
function renderPlanScreen() {
  // Option cards logic
}

function selectPlanCard(cardEl, btnText, planType) {
  const cards = document.querySelectorAll('.plan-card');
  cards.forEach(c => {
    c.classList.remove('active', 'border-primary', 'bg-surface-container-high', 'shadow-md');
    c.classList.add('bg-surface-container-lowest', 'border-transparent', 'shadow-sm');
  });

  if (cardEl) {
    cardEl.classList.remove('bg-surface-container-lowest', 'border-transparent', 'shadow-sm');
    cardEl.classList.add('active', 'border-primary', 'bg-surface-container-high', 'shadow-md');
  }

  state.selectedPlanType = planType;
  state.selectedPlanText = btnText;

  const btnTextEl = document.getElementById('plan-btn-text');
  if (btnTextEl) btnTextEl.textContent = btnText;
}

function confirmSelectedPlan() {
  showToast(`Plan selected: ${state.selectedPlanText}`);
  setTimeout(() => navigateTo('home'), 1000);
}

/**
 * Modals
 */
function openTxModal(txId) {
  const tx = state.transactions.find(t => t.id === txId) || state.transactions[0];
  if (!tx) return;

  state.activeTxItem = tx;
  const modal = document.getElementById('tx-detail-modal');
  if (!modal) return;

  document.getElementById('tx-modal-merchant').textContent = tx.merchant;
  document.getElementById('tx-modal-category').textContent = tx.category;
  document.getElementById('tx-modal-amount').textContent = formatCurr(tx.amount);
  document.getElementById('tx-modal-type').textContent = tx.type;
  document.getElementById('tx-modal-date').textContent = tx.date;

  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeTxModal() {
  const modal = document.getElementById('tx-detail-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

function openSettingsModal() {
  const modal = document.getElementById('settings-modal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }
}

function closeSettingsModal(e) {
  if (e && e.target !== e.currentTarget) return;
  const modal = document.getElementById('settings-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

function populateUserSwitcher() {
  const select = document.getElementById('profile-select');
  if (!select || !state.allUsers.length) return;

  select.innerHTML = state.allUsers.map(u => `
    <option value="${u.user_id}" ${u.user_id === state.userId ? 'selected' : ''}>
      ${u.user_id === 'user_01' ? 'Rahul (User 01 · INR)' : `${u.user_id.toUpperCase()} · ${u.home_currency}`}
    </option>
  `).join('');
}

async function switchUserProfile(userId) {
  state.userId = userId;
  showToast(`Loading profile ${userId}...`);
  await loadUserProfile(userId);
  await loadTransactions(userId);
  await loadCommitments(userId);
  closeSettingsModal();
}

async function saveSettings() {
  const name = document.getElementById('settings-name-input').value.trim() || 'Rahul';
  const income = parseFloat(document.getElementById('settings-income-input').value) || 35000;
  const buffer = parseFloat(document.getElementById('settings-buffer-input').value) || 5000;

  try {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_name: name,
        monthly_income: income,
        minimum_balance: buffer
      })
    });
    localStorage.setItem('afford_iq_user_name', name);
    await loadUserProfile(state.userId);
    closeSettingsModal();
    showToast('Settings saved.');
  } catch (err) {
    console.error(err);
  }
}

/**
 * Voice & OCR Input Simulations
 */
function startVoiceInput(targetInputId) {
  const inputEl = document.getElementById(targetInputId);
  if (!inputEl) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.start();
    showToast('Listening... Speak your purchase inquiry.');

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      inputEl.value = transcript;
      state.currentQuery = transcript;
      if (targetInputId === 'ask-query-textarea') handleLiveQueryInput();
      showToast(`Captured: "${transcript}"`);
    };

    recognition.onerror = () => {
      fallbackVoiceSimulation(inputEl, targetInputId);
    };
  } else {
    fallbackVoiceSimulation(inputEl, targetInputId);
  }
}

function fallbackVoiceSimulation(inputEl, targetInputId) {
  showToast('Voice input active...');
  const voiceSamples = [
    'How much is safe to spend this weekend?',
    'Can I buy a ₹15,000 phone next month?',
    'Can I afford ₹2,500 on dinner tonight?'
  ];
  const chosen = voiceSamples[Math.floor(Math.random() * voiceSamples.length)];
  setTimeout(() => {
    inputEl.value = chosen;
    state.currentQuery = chosen;
    if (targetInputId === 'ask-query-textarea') handleLiveQueryInput();
    showToast(`Captured: "${chosen}"`);
  }, 1000);
}

function simulateOcrScan() {
  showToast('Scanning price tag...');
  const textarea = document.getElementById('ask-query-textarea');
  setTimeout(() => {
    const ocrSample = 'Purchase: Sony Headphones · Price ₹18,000';
    if (textarea) {
      textarea.value = ocrSample;
      state.currentQuery = ocrSample;
      handleLiveQueryInput();
    }
    showToast('Detected: ₹18,000');
  }, 1200);
}

/**
 * Privacy Actions
 */
function toggleSetting(key) {
  showToast(`Setting updated.`);
}

function exportUserData() {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify({
    profile: state.profile,
    transactions: state.transactions,
    commitments: state.commitments,
    export_timestamp: new Date().toISOString()
  }, null, 2));
  const dlAnchor = document.createElement('a');
  dlAnchor.setAttribute("href", dataStr);
  dlAnchor.setAttribute("download", `afford_iq_data_${state.userId}.json`);
  document.body.appendChild(dlAnchor);
  dlAnchor.click();
  dlAnchor.remove();
  showToast('Data exported.');
}

function resetLocalData() {
  if (confirm('Clear local settings and re-enter setup?')) {
    localStorage.clear();
    showToast('Resetting...');
    setTimeout(() => {
      navigateTo('welcome');
      location.reload();
    }, 600);
  }
}

/**
 * Utility Helpers
 */
function extractNumericAmount(text) {
  if (!text) return 40000.0;
  const clean = text.replace(/,/g, '');
  const kMatch = clean.match(/([0-9.]+)\s*k\b/i);
  if (kMatch) return parseFloat(kMatch[1]) * 1000.0;
  const lMatch = clean.match(/([0-9.]+)\s*l\b/i);
  if (lMatch) return parseFloat(lMatch[1]) * 100000.0;
  const amtMatch = clean.match(/(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]{1,2})?)/i);
  if (amtMatch) return parseFloat(amtMatch[1]);
  return 40000.0;
}

function formatNum(val) {
  return Number(val || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

function formatCurr(val) {
  return '₹' + Number(val || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

function showToast(message) {
  const existing = document.getElementById('afford-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'afford-toast';
  toast.className = 'fixed bottom-20 left-1/2 -translate-x-1/2 z-50 bg-on-surface text-surface px-4 py-2.5 rounded-full text-body-sm shadow-xl flex items-center gap-2 fade-in max-w-[90%] pointer-events-none';
  toast.innerHTML = `
    <span class="material-symbols-outlined text-[18px] text-secondary">info</span>
    <span class="truncate">${message}</span>
  `;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 2200);
}
