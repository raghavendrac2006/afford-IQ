/**
 * Afford IQ · Financial Decision Assistant & Goal Accelerator
 * High-Performance Client-Side & Backend Integrated Controller
 * Supports 100% On-Device execution on Vercel, Netlify, PWA, and local Python server.
 */

// Application State
const state = {
  currentScreen: 'home',
  history: ['home'],
  userId: 'user_01',
  profile: {
    user_id: 'user_01',
    user_name: 'Rahul',
    home_currency: 'INR',
    current_available_balance: 25949.0,
    minimum_balance_to_keep: 5000.0,
    monthly_income: 35000.0,
    safe_to_spend_today: 8450.0,
    upcoming_commitments: 12499.0
  },
  transactions: [],
  commitments: [],
  allUsers: [],
  goals: [
    {
      goal_id: 'goal_01',
      name: 'MacBook Pro / Laptop',
      category: 'Device',
      target_amount: 50000.0,
      current_saved: 32000.0,
      target_date: '2027-06-30',
      created_date: '2026-06-30',
      monthly_contribution: 4167.0,
      current_avg_contribution: 3750.0,
      status: 'at_risk',
      icon: 'laptop_mac',
      color: 'primary',
      notes: 'Target for engineering and design workstation.'
    },
    {
      goal_id: 'goal_02',
      name: 'Emergency Shield Reserve',
      category: 'Emergency',
      target_amount: 30000.0,
      current_saved: 12000.0,
      target_date: '2027-12-31',
      created_date: '2026-01-01',
      monthly_contribution: 1200.0,
      current_avg_contribution: 1500.0,
      status: 'on_track',
      icon: 'shield',
      color: 'secondary',
      notes: 'Dedicated 6-month rainy day untouchable liquidity buffer.'
    },
    {
      goal_id: 'goal_03',
      name: 'Goa Vacation Trip',
      category: 'Travel',
      target_amount: 25000.0,
      current_saved: 15000.0,
      target_date: '2027-03-31',
      created_date: '2026-08-01',
      monthly_contribution: 1667.0,
      current_avg_contribution: 1800.0,
      status: 'ahead',
      icon: 'flight',
      color: 'tertiary',
      notes: 'Trip with university friends after semester exams.'
    }
  ],
  currentGoalId: 'goal_01',
  currentGoal: null,
  selectedGoalCategory: 'Device',
  livePlanCalculation: null,
  currentQuery: 'Can I buy a ₹40,000 laptop next month?',
  evaluationResult: null,
  selectedPlanType: 'recommended',
  selectedPlanText: 'Select "Wait & Pay in Full"',
  activeTxFilter: 'all',
  activeTxItem: null,
};

// Default Curated Financial Data
const defaultTxs = [
  { id: 'tx_01', merchant: 'Sri Lakshmi Stores', category: 'Food · Chai & Snacks', date: 'Today, 1:05 PM', amount: 30.0, direction: 'debit', type: 'Auto-detected (UPI)', icon: 'local_cafe' },
  { id: 'tx_02', merchant: 'Zepto Groceries', category: 'Food · Groceries', date: 'Today, 11:20 AM', amount: 341.0, direction: 'debit', type: 'Auto-detected (UPI)', icon: 'shopping_basket' },
  { id: 'tx_03', merchant: 'Monthly Salary Credit', category: 'Income · Tech Corp', date: 'Yesterday, 9:00 AM', amount: 35000.0, direction: 'credit', type: 'Salary Credit (NEFT)', icon: 'account_balance' },
  { id: 'tx_04', merchant: 'Airtel Broadband Fiber', category: 'Bills · Utilities', date: '2 days ago', amount: 999.0, direction: 'debit', type: 'Scheduled Mandate', icon: 'wifi' },
  { id: 'tx_05', merchant: 'Cult.Fit Gym Membership', category: 'Subscription · Fitness', date: '3 days ago', amount: 1500.0, direction: 'debit', type: 'Auto-debit', icon: 'fitness_center' },
  { id: 'tx_06', merchant: 'Uber Ride HSR to Indiranagar', category: 'Transport · Cab', date: '4 days ago', amount: 245.0, direction: 'debit', type: 'Auto-detected (UPI)', icon: 'directions_car' }
];

const defaultCommitments = [
  { id: 'com_01', title: 'Apartment Rent (HSR Layout)', due_date: 'Due in 4 days (Oct 1)', amount: 10000.0, category: 'Housing', icon: 'home' },
  { id: 'com_02', title: 'Bescom Electricity Bill', due_date: 'Due in 8 days (Oct 5)', amount: 1500.0, category: 'Utilities', icon: 'bolt' },
  { id: 'com_03', title: 'Broadband & Phone Bills', due_date: 'Due in 12 days (Oct 9)', amount: 999.0, category: 'Utilities', icon: 'wifi' }
];

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

  // Set default target date for goal create (12 months from today)
  const goalDateInput = document.getElementById('new-goal-date');
  if (goalDateInput) {
    const d = new Date();
    d.setFullYear(d.getFullYear() + 1);
    goalDateInput.value = d.toISOString().split('T')[0];
  }

  // Load saved local user settings if any
  const savedName = localStorage.getItem('afford_iq_user_name');
  if (savedName) state.profile.user_name = savedName;

  // Load backend or embedded data
  await loadDatasetUsers();
  await loadUserProfile(state.userId);
  await loadTransactions(state.userId);
  await loadCommitments(state.userId);
  await loadGoals();

  // Check if user has already signed in / configured profile
  const userSignedIn = localStorage.getItem('afford_iq_user_signed_in');
  if (userSignedIn === 'true') {
    navigateTo('home', false);
  } else {
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

  state.profile.user_name = name;
  state.profile.monthly_income = income;
  state.profile.minimum_balance_to_keep = buffer;

  // Save to backend if available
  try {
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_name: name, monthly_income: income, minimum_balance: buffer })
    });
  } catch (e) {
    // Local fallback
  }

  localStorage.setItem('afford_iq_user_signed_in', 'true');
  localStorage.setItem('afford_iq_user_name', name);

  renderHomeProfile();
  showToast(`Welcome, ${name}!`);
  navigateTo('home');
}

async function handleWelcomeGuest() {
  localStorage.setItem('afford_iq_user_signed_in', 'true');
  renderHomeProfile();
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

  // Screen-specific triggers
  if (screenId === 'goals') {
    renderGoalsDashboard();
  } else if (screenId === 'goal-create') {
    triggerLiveGoalCalculation();
  }

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
    case 'goals':
      if (backBtn) backBtn.classList.remove('hidden');
      if (title) title.textContent = 'Goal Accelerator';
      highlightBottomNav('nav-goals');
      break;
    case 'goal-create':
      if (backBtn) backBtn.classList.remove('hidden');
      if (title) title.textContent = 'Create Goal';
      highlightBottomNav('nav-goals');
      break;
    case 'goal-detail':
      if (backBtn) backBtn.classList.remove('hidden');
      if (title) title.textContent = 'Goal Strategy';
      highlightBottomNav('nav-goals');
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
 * Data Fetching APIs with Standalone Offline Fallback
 */
async function loadUserProfile(userId) {
  try {
    const res = await fetch(`/api/profile?user_id=${userId}`);
    if (res.ok) {
      state.profile = await res.json();
    }
  } catch (err) {
    // Keep embedded profile
  }
  renderHomeProfile();
}

async function loadTransactions(userId) {
  try {
    const res = await fetch(`/api/transactions?user_id=${userId}`);
    if (res.ok) {
      state.transactions = await res.json();
    } else {
      state.transactions = defaultTxs;
    }
  } catch (err) {
    state.transactions = defaultTxs;
  }
  renderHomeTransactions();
  renderActivityList();
}

async function loadCommitments(userId) {
  try {
    const res = await fetch(`/api/commitments?user_id=${userId}`);
    if (res.ok) {
      state.commitments = await res.json();
    } else {
      state.commitments = defaultCommitments;
    }
  } catch (err) {
    state.commitments = defaultCommitments;
  }
  renderHomeCommitments();
}

async function loadDatasetUsers() {
  try {
    const res = await fetch('/api/dataset_users');
    if (res.ok) {
      state.allUsers = await res.json();
    }
  } catch (err) {
    state.allUsers = [];
  }
  populateUserSwitcher();
}

async function loadGoals() {
  try {
    const res = await fetch('/api/goals');
    if (res.ok) {
      state.goals = await res.json();
    }
  } catch (err) {
    // Keep embedded goals
  }
  renderHomeGoalsPreview();
  renderGoalsDashboard();
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

function renderHomeGoalsPreview() {
  const container = document.getElementById('home-goals-preview-container');
  if (!container) return;

  if (!state.goals || state.goals.length === 0) {
    container.innerHTML = `
      <div class="p-4 rounded-2xl bg-surface-container-low border border-dashed border-outline-variant text-center space-y-2">
        <p class="font-body-sm text-on-surface-variant">No goals created yet. Turn your next purchase into a behavior-aware plan.</p>
        <button class="px-3.5 py-1.5 rounded-xl bg-primary text-on-primary font-label-sm font-semibold inline-flex items-center gap-1" onclick="navigateTo('goal-create')">
          <span class="material-symbols-outlined text-[16px]">add</span>
          <span>Set Financial Goal</span>
        </button>
      </div>
    `;
    return;
  }

  // Show top 2 active goals
  const topGoals = state.goals.slice(0, 2);
  container.innerHTML = topGoals.map(g => {
    const pct = Math.min(100, Math.round((g.current_saved / g.target_amount) * 100));
    const statusPill = getStatusPillHtml(g.status);
    return `
      <div class="p-3.5 rounded-2xl bg-surface-container-low border border-surface-container hover:border-primary/40 shadow-xs cursor-pointer active:scale-[0.99] transition-all" onclick="openGoalDetail('${g.goal_id}')">
        <div class="flex items-center justify-between gap-2 mb-2">
          <div class="flex items-center gap-2.5 min-w-0">
            <div class="w-8 h-8 rounded-xl bg-surface-container-highest flex items-center justify-center text-primary shrink-0">
              <span class="material-symbols-outlined text-[18px]">${g.icon || 'flag'}</span>
            </div>
            <div class="flex flex-col min-w-0">
              <span class="font-label-md text-label-md font-bold text-on-surface truncate">${g.name}</span>
              <span class="font-body-sm text-[11px] text-on-surface-variant truncate">Target: ${formatDateReadable(g.target_date)}</span>
            </div>
          </div>
          ${statusPill}
        </div>

        <!-- Progress Bar -->
        <div class="space-y-1">
          <div class="w-full h-2 bg-surface-container-high rounded-full overflow-hidden">
            <div class="h-full bg-primary rounded-full transition-all duration-300" style="width: ${pct}%"></div>
          </div>
          <div class="flex justify-between items-center text-xs text-on-surface-variant">
            <span><strong>${formatCurr(g.current_saved)}</strong> / ${formatCurr(g.target_amount)} (${pct}%)</span>
            <span class="text-primary font-semibold">${formatCurr(g.monthly_contribution)}/mo</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
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
 * Rendering: Goals Dashboard & Accelerator
 */
function renderGoalsDashboard() {
  const container = document.getElementById('goals-list-container');
  if (!container) return;

  let totalSaved = 0;
  let monthlyPace = 0;
  (state.goals || []).forEach(g => {
    totalSaved += Number(g.current_saved || 0);
    monthlyPace += Number(g.monthly_contribution || 0);
  });

  const totalSavedEl = document.getElementById('goals-total-saved');
  if (totalSavedEl) totalSavedEl.textContent = formatCurr(totalSaved);

  const activeCountEl = document.getElementById('goals-active-count');
  if (activeCountEl) activeCountEl.textContent = `${state.goals.length} ${state.goals.length === 1 ? 'Goal' : 'Goals'}`;

  const monthlyPaceEl = document.getElementById('goals-monthly-pace');
  if (monthlyPaceEl) monthlyPaceEl.textContent = formatCurr(monthlyPace);

  if (state.goals.length === 0) {
    container.innerHTML = `
      <div class="p-8 text-center bg-surface-container-lowest rounded-2xl border border-surface-container space-y-3">
        <span class="material-symbols-outlined text-4xl text-outline mb-1">flag</span>
        <h3 class="font-headline-sm text-on-surface">No goals currently active</h3>
        <p class="font-body-sm text-on-surface-variant max-w-[280px] mx-auto">Create your first financial target to get an intelligent, behavior-aware saving roadmap.</p>
        <button class="px-4 py-2.5 rounded-xl bg-primary text-on-primary font-label-md font-semibold inline-flex items-center gap-1.5 shadow-sm" onclick="navigateTo('goal-create')">
          <span class="material-symbols-outlined text-[18px]">add</span>
          <span>Create New Goal</span>
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = state.goals.map(g => {
    const pct = Math.min(100, Math.round((g.current_saved / g.target_amount) * 100));
    const statusPill = getStatusPillHtml(g.status);
    return `
      <div class="p-4 rounded-2xl bg-surface-container-lowest border border-surface-container shadow-xs space-y-3 hover:border-primary/50 transition-all cursor-pointer" onclick="openGoalDetail('${g.goal_id}')">
        <div class="flex items-start justify-between gap-2">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-10 h-10 rounded-xl bg-primary-container text-on-primary flex items-center justify-center shrink-0 shadow-xs">
              <span class="material-symbols-outlined text-[20px]">${g.icon || 'flag'}</span>
            </div>
            <div class="flex flex-col min-w-0">
              <span class="font-headline-sm text-label-lg font-bold text-on-surface truncate">${g.name}</span>
              <span class="font-body-sm text-xs text-on-surface-variant">${g.category || 'General'} · Target ${formatDateReadable(g.target_date)}</span>
            </div>
          </div>
          ${statusPill}
        </div>

        <!-- Progress Bar and Numbers -->
        <div class="space-y-1.5 pt-1">
          <div class="flex justify-between items-baseline">
            <div class="flex items-baseline gap-1">
              <span class="font-headline-sm text-label-lg font-bold text-on-surface">${formatCurr(g.current_saved)}</span>
              <span class="font-body-sm text-xs text-on-surface-variant">of ${formatCurr(g.target_amount)}</span>
            </div>
            <span class="font-label-md text-primary font-bold">${pct}% complete</span>
          </div>
          <div class="w-full h-2.5 bg-surface-container-high rounded-full overflow-hidden">
            <div class="h-full bg-primary rounded-full transition-all duration-500" style="width: ${pct}%"></div>
          </div>
        </div>

        <!-- Telemetry & Action Footer -->
        <div class="flex items-center justify-between pt-1 border-t border-surface-container-low text-xs text-on-surface-variant">
          <div class="flex items-center gap-1 font-medium">
            <span class="material-symbols-outlined text-[15px] text-primary">event_upcoming</span>
            <span>Required: <strong class="text-on-surface">${formatCurr(g.monthly_contribution)}/mo</strong></span>
          </div>
          <span class="text-primary font-semibold flex items-center gap-0.5">
            <span>Inspect Strategy</span>
            <span class="material-symbols-outlined text-[15px]">arrow_forward</span>
          </span>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Goal Detail & Dynamic Adjustment Controller
 */
function openGoalDetail(goalId) {
  state.currentGoalId = goalId;
  const goal = (state.goals || []).find(g => g.goal_id === goalId) || state.goals[0];
  if (!goal) return;
  state.currentGoal = goal;

  renderGoalDetailView(goal);
  navigateTo('goal-detail');
}

async function renderGoalDetailView(goal) {
  if (!goal) return;

  const titleEl = document.getElementById('goal-detail-title');
  if (titleEl) titleEl.textContent = goal.name;

  const categoryEl = document.getElementById('goal-detail-category');
  if (categoryEl) categoryEl.textContent = `${goal.category || 'General'} · Target: ${formatDateReadable(goal.target_date)}`;

  const iconEl = document.getElementById('goal-detail-icon');
  if (iconEl) iconEl.textContent = goal.icon || 'flag';

  const statusBadgeEl = document.getElementById('goal-detail-status-badge');
  if (statusBadgeEl) {
    if (goal.status === 'at_risk') {
      statusBadgeEl.className = 'px-2.5 py-1 rounded-full bg-error-container text-on-error-container font-label-sm text-label-sm font-bold uppercase tracking-wider';
      statusBadgeEl.textContent = 'AT RISK';
    } else if (goal.status === 'ahead') {
      statusBadgeEl.className = 'px-2.5 py-1 rounded-full bg-secondary-container text-on-secondary-container font-label-sm text-label-sm font-bold uppercase tracking-wider';
      statusBadgeEl.textContent = 'AHEAD OF PACE';
    } else {
      statusBadgeEl.className = 'px-2.5 py-1 rounded-full bg-secondary-container text-on-secondary-container font-label-sm text-label-sm font-bold uppercase tracking-wider';
      statusBadgeEl.textContent = 'ON TRACK';
    }
  }

  const savedEl = document.getElementById('goal-detail-saved');
  if (savedEl) savedEl.textContent = formatCurr(goal.current_saved);

  const targetEl = document.getElementById('goal-detail-target');
  if (targetEl) targetEl.textContent = `of ${formatCurr(goal.target_amount)}`;

  const pct = Math.min(100, Math.round((goal.current_saved / goal.target_amount) * 100));
  const pctEl = document.getElementById('goal-detail-percent');
  if (pctEl) pctEl.textContent = `${pct}%`;

  const barEl = document.getElementById('goal-detail-progress-bar');
  if (barEl) barEl.style.width = `${pct}%`;

  const remainingAmt = Math.max(0, goal.target_amount - goal.current_saved);
  const remainingTextEl = document.getElementById('goal-detail-remaining-text');
  if (remainingTextEl) remainingTextEl.textContent = `${formatCurr(remainingAmt)} remaining`;

  const reqPaceEl = document.getElementById('goal-detail-req-pace');
  if (reqPaceEl) reqPaceEl.textContent = `${formatCurr(goal.monthly_contribution)} / mo`;

  const curPaceEl = document.getElementById('goal-detail-current-pace');
  if (curPaceEl) {
    curPaceEl.textContent = `${formatCurr(goal.current_avg_contribution || goal.monthly_contribution)} / mo`;
    if (goal.status === 'at_risk') {
      curPaceEl.className = 'font-label-lg text-label-lg text-error font-bold mt-0.5';
    } else {
      curPaceEl.className = 'font-label-lg text-label-lg text-secondary font-bold mt-0.5';
    }
  }

  // Calculate Dynamic Adjustment
  const lagAmt = goal.status === 'at_risk' ? 1200.0 : 0.0;
  const adj = calculateDynamicAdjustmentClient(goal.target_amount, goal.current_saved, goal.target_date, lagAmt, goal.current_avg_contribution || goal.monthly_contribution);
  updateDynamicAdjustmentUI(adj, goal);

  // Generate Growth Scenarios
  const planData = calculateGoalPlanClient(goal.target_amount, goal.current_saved, goal.target_date);
  renderEducationalScenarios(planData.growth_scenarios || []);
}

function updateDynamicAdjustmentUI(adj, goal) {
  const bannerEl = document.getElementById('dynamic-pace-banner');
  const titleEl = document.getElementById('dynamic-pace-title');
  const subEl = document.getElementById('dynamic-pace-sub');
  const iconEl = document.getElementById('dynamic-pace-icon');

  if (goal.status === 'at_risk') {
    if (bannerEl) bannerEl.className = 'p-3 rounded-xl bg-tertiary-fixed/60 flex items-start gap-2.5';
    if (iconEl) {
      iconEl.className = 'material-symbols-outlined text-[20px] text-tertiary-fixed-variant mt-0.5 shrink-0';
      iconEl.textContent = 'warning';
    }
    if (titleEl) titleEl.textContent = "You're currently ₹1,200 behind your planned pace.";
    if (subEl) subEl.textContent = "Recent higher discretionary spends reduced monthly savings. Choose a calibrated course correction below:";
  } else {
    if (bannerEl) bannerEl.className = 'p-3 rounded-xl bg-secondary-container/50 flex items-start gap-2.5';
    if (iconEl) {
      iconEl.className = 'material-symbols-outlined text-[20px] text-secondary mt-0.5 shrink-0';
      iconEl.textContent = 'check_circle';
    }
    if (titleEl) titleEl.textContent = "Your goal pace is healthy & on schedule.";
    if (subEl) subEl.textContent = "You're saving safely without risking your ₹5,000 emergency shield or essential commitments.";
  }

  const opt1Title = document.getElementById('opt-increase-title');
  if (opt1Title && adj.option_increase_monthly) opt1Title.textContent = adj.option_increase_monthly.title;

  const opt1Diff = document.getElementById('opt-increase-diff');
  if (opt1Diff && adj.option_increase_monthly) opt1Diff.textContent = adj.option_increase_monthly.diff;

  const opt2Title = document.getElementById('opt-extend-title');
  if (opt2Title && adj.option_extend_date) opt2Title.textContent = adj.option_extend_date.title;

  const opt2Diff = document.getElementById('opt-extend-diff');
  if (opt2Diff && adj.option_extend_date) opt2Diff.textContent = adj.option_extend_date.diff;
}

function renderEducationalScenarios(scenarios) {
  const container = document.getElementById('goal-scenarios-container');
  if (!container) return;

  container.innerHTML = scenarios.map(s => `
    <div class="p-3.5 rounded-xl bg-surface-container-low border border-surface-container hover:border-primary/40 transition-all space-y-2">
      <div class="flex items-start justify-between">
        <div class="flex items-center gap-2 min-w-0">
          <div class="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center text-primary shrink-0">
            <span class="material-symbols-outlined text-[18px]">${s.icon || 'trending_up'}</span>
          </div>
          <div class="flex flex-col min-w-0">
            <span class="font-label-md text-label-md font-bold text-on-surface truncate">${s.name}</span>
            <span class="font-body-sm text-[11px] text-on-surface-variant">Assumed: ${s.assumed_annual_rate} p.a. · Risk: ${s.risk_level}</span>
          </div>
        </div>
        <span class="px-2 py-0.5 rounded-full ${s.timeline_fit === 'Best fit' ? 'bg-secondary-container text-on-secondary-container' : 'bg-surface-container text-on-surface-variant'} text-[11px] font-bold">
          ${s.timeline_fit}
        </span>
      </div>

      <p class="text-xs text-on-surface-variant leading-relaxed">${s.desc}</p>

      <div class="grid grid-cols-2 gap-2 pt-1 border-t border-surface-container-highest text-xs">
        <div>
          <span class="text-on-surface-variant">Monthly Contribution:</span>
          <p class="font-label-md font-bold text-primary">${formatCurr(s.monthly_contribution)}/mo</p>
        </div>
        <div>
          <span class="text-on-surface-variant">Estimated Compounded Gain:</span>
          <p class="font-label-md font-bold text-secondary">+${formatCurr(s.estimated_gain)}</p>
        </div>
      </div>
    </div>
  `).join('');
}

/**
 * Live Goal Creation Controller
 */
function triggerLiveGoalCalculation() {
  const nameInput = document.getElementById('new-goal-name');
  const amountInput = document.getElementById('new-goal-amount');
  const dateInput = document.getElementById('new-goal-date');
  const savedInput = document.getElementById('new-goal-saved');

  const amount = amountInput ? parseFloat(amountInput.value) || 50000 : 50000;
  const targetDate = dateInput ? dateInput.value || '2027-06-30' : '2027-06-30';
  const currentSaved = savedInput ? parseFloat(savedInput.value) || 0 : 0;

  const plan = calculateGoalPlanClient(amount, currentSaved, targetDate);
  state.livePlanCalculation = plan;

  const dailyEl = document.getElementById('create-plan-daily');
  if (dailyEl) dailyEl.textContent = `${formatCurr(plan.required_daily)} / day`;

  const weeklyEl = document.getElementById('create-plan-weekly');
  if (weeklyEl) weeklyEl.textContent = `${formatCurr(plan.required_weekly)} / wk`;

  const monthlyEl = document.getElementById('create-plan-monthly');
  if (monthlyEl) monthlyEl.textContent = `${formatCurr(plan.required_monthly)} / mo`;

  const badgeEl = document.getElementById('create-feasibility-badge');
  if (badgeEl) {
    badgeEl.textContent = plan.feasibility_badge;
    if (plan.feasibility === 'comfortable') {
      badgeEl.className = 'px-2.5 py-0.5 rounded-full bg-secondary-container text-on-secondary-container font-label-sm text-label-sm font-bold';
    } else if (plan.feasibility === 'moderate') {
      badgeEl.className = 'px-2.5 py-0.5 rounded-full bg-primary-fixed text-primary font-label-sm text-label-sm font-bold';
    } else {
      badgeEl.className = 'px-2.5 py-0.5 rounded-full bg-error-container text-on-error-container font-label-sm text-label-sm font-bold';
    }
  }

  const headEl = document.getElementById('create-feasibility-headline');
  if (headEl) headEl.textContent = plan.feasibility_headline;

  const subEl = document.getElementById('create-feasibility-sub');
  if (subEl) subEl.textContent = plan.feasibility_sub;

  renderCreatePlans(plan.plans || []);
}

function renderCreatePlans(plans) {
  const container = document.getElementById('create-plans-container');
  if (!container) return;

  container.innerHTML = plans.map((p, idx) => `
    <div class="p-3 rounded-xl bg-surface-container-low border ${p.is_recommended ? 'border-primary bg-primary/5' : 'border-outline-variant/30'} flex items-start justify-between gap-2 cursor-pointer transition-all">
      <div class="flex flex-col min-w-0">
        <div class="flex items-center gap-1.5">
          <span class="font-label-sm font-bold text-on-surface">${p.name}</span>
          <span class="px-1.5 py-0.2 rounded text-[10px] font-bold ${p.is_recommended ? 'bg-primary text-on-primary' : 'bg-surface-container text-on-surface-variant'}">${p.badge}</span>
        </div>
        <p class="text-xs text-on-surface-variant mt-0.5">${p.desc}</p>
      </div>
      <div class="text-right shrink-0">
        <span class="font-label-md font-bold text-primary">${formatCurr(p.monthly_amount)}/mo</span>
      </div>
    </div>
  `).join('');
}

function setGoalTemplate(name, amount, months, category) {
  const nameEl = document.getElementById('new-goal-name');
  if (nameEl) nameEl.value = name;

  const amtEl = document.getElementById('new-goal-amount');
  if (amtEl) amtEl.value = amount;

  const savedEl = document.getElementById('new-goal-saved');
  if (savedEl) savedEl.value = 0;

  const dateEl = document.getElementById('new-goal-date');
  if (dateEl) {
    const d = new Date();
    d.setMonth(d.getMonth() + months);
    dateEl.value = d.toISOString().split('T')[0];
  }

  state.selectedGoalCategory = category;
  const pills = document.querySelectorAll('#new-goal-category-container button');
  pills.forEach(btn => {
    if (btn.textContent.trim().toLowerCase() === category.toLowerCase()) {
      btn.className = 'px-3 py-1.5 rounded-full bg-primary text-on-primary font-label-sm text-label-sm shadow-xs flex-shrink-0';
    } else {
      btn.className = 'px-3 py-1.5 rounded-full bg-surface-container text-on-surface font-label-sm text-label-sm flex-shrink-0';
    }
  });

  triggerLiveGoalCalculation();
  showToast(`Loaded template for ${name}`);
}

function selectGoalCategory(category, btnEl) {
  state.selectedGoalCategory = category;
  const pills = document.querySelectorAll('#new-goal-category-container button');
  pills.forEach(b => {
    b.className = 'px-3 py-1.5 rounded-full bg-surface-container text-on-surface font-label-sm text-label-sm flex-shrink-0';
  });
  if (btnEl) {
    btnEl.className = 'px-3 py-1.5 rounded-full bg-primary text-on-primary font-label-sm text-label-sm shadow-xs flex-shrink-0';
  }
}

async function submitCreateGoal() {
  const nameInput = document.getElementById('new-goal-name');
  const amountInput = document.getElementById('new-goal-amount');
  const dateInput = document.getElementById('new-goal-date');
  const savedInput = document.getElementById('new-goal-saved');

  const name = nameInput ? nameInput.value.trim() || 'My Financial Goal' : 'My Financial Goal';
  const amount = amountInput ? parseFloat(amountInput.value) || 50000 : 50000;
  const targetDate = dateInput ? dateInput.value || '2027-06-30' : '2027-06-30';
  const saved = savedInput ? parseFloat(savedInput.value) || 0 : 0;

  const monthlyPace = state.livePlanCalculation ? state.livePlanCalculation.required_monthly : Math.round(amount / 12);

  const iconMap = {
    'Device': 'laptop_mac',
    'Emergency': 'shield',
    'Travel': 'flight',
    'Education': 'school',
    'Vehicle': 'directions_car',
    'Other': 'flag'
  };

  const newGoal = {
    goal_id: `goal_${Date.now()}`,
    name: name,
    category: state.selectedGoalCategory || 'Device',
    target_amount: amount,
    current_saved: saved,
    target_date: targetDate,
    created_date: new Date().toISOString().split('T')[0],
    monthly_contribution: monthlyPace,
    current_avg_contribution: monthlyPace,
    status: 'on_track',
    icon: iconMap[state.selectedGoalCategory] || 'flag'
  };

  state.goals.unshift(newGoal);
  renderHomeGoalsPreview();
  renderGoalsDashboard();
  showToast(`Goal "${name}" created successfully!`);
  openGoalDetail(newGoal.goal_id);
}

/**
 * Dynamic Adjustment Action Handlers & Simulations
 */
function simulateGoalBehavior(status, lagAmount) {
  if (!state.currentGoalId) return;
  const goal = state.goals.find(g => g.goal_id === state.currentGoalId);
  if (!goal) return;

  goal.status = status;
  if (status === 'at_risk') {
    goal.current_avg_contribution = Math.max(500, goal.monthly_contribution - (lagAmount / 4.0));
  } else {
    goal.current_avg_contribution = goal.monthly_contribution;
  }

  state.currentGoal = goal;
  renderGoalDetailView(goal);
  renderHomeGoalsPreview();
  renderGoalsDashboard();
  showToast(status === 'at_risk' ? 'Simulated: Behind pace by ₹1,200.' : 'Simulated: On track with planned pace.');
}

function applyGoalAdjustment(actionType) {
  if (!state.currentGoal) return;
  const goal = state.currentGoal;

  if (actionType === 'increase_pace') {
    const newPace = Math.round(goal.monthly_contribution * 1.12);
    goal.monthly_contribution = newPace;
    goal.current_avg_contribution = newPace;
    goal.status = 'on_track';
    showToast(`Applied new target pace of ${formatCurr(newPace)}/month.`);
  } else if (actionType === 'extend_date') {
    const d = new Date(goal.target_date);
    d.setDate(d.getDate() + 18);
    goal.target_date = d.toISOString().split('T')[0];
    goal.status = 'on_track';
    showToast(`Extended target date to ${formatDateReadable(goal.target_date)}.`);
  } else if (actionType === 'trim_spending') {
    goal.status = 'on_track';
    showToast('Committed ₹400/month spending trim. Goal returned to ON TRACK.');
  }

  renderGoalDetailView(goal);
  renderHomeGoalsPreview();
  renderGoalsDashboard();
}

function updateInteractiveGrowthScenario(customRate) {
  const rateLabel = document.getElementById('slider-rate-label');
  if (rateLabel) rateLabel.textContent = `${Number(customRate).toFixed(1)}% p.a.`;

  if (!state.currentGoal) return;
  const goal = state.currentGoal;
  const remaining = Math.max(0, goal.target_amount - goal.current_saved);
  const months = 12.0;

  const r = parseFloat(customRate) / 100.0;
  const i = r / 12.0;
  let factor = (((1.0 + i) ** months - 1.0) / i) * (1.0 + i);
  let monthly = remaining / (factor > 0 ? factor : months);

  const calcEl = document.getElementById('slider-calculated-monthly');
  if (calcEl) calcEl.textContent = `${formatCurr(Math.round(monthly))} / month`;
}

function exportSingleGoalData() {
  if (!state.currentGoal) return;
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state.currentGoal, null, 2));
  const dlAnchor = document.createElement('a');
  dlAnchor.setAttribute("href", dataStr);
  dlAnchor.setAttribute("download", `goal_${state.currentGoal.goal_id}.json`);
  document.body.appendChild(dlAnchor);
  dlAnchor.click();
  dlAnchor.remove();
  showToast('Goal data exported.');
}

function deleteCurrentGoal() {
  if (!state.currentGoalId) return;
  if (confirm('Delete this goal and remove from tracking?')) {
    state.goals = state.goals.filter(g => g.goal_id !== state.currentGoalId);
    renderHomeGoalsPreview();
    renderGoalsDashboard();
    showToast('Goal deleted.');
    navigateTo('goals');
  }
}

/**
 * Client-Side Mathematical Intelligence Engine (Offline / Static Web Compatible)
 */
function calculateGoalPlanClient(targetAmount, currentSaved, targetDateStr) {
  let targetD;
  try {
    targetD = new Date(targetDateStr);
  } catch (e) {
    targetD = new Date();
    targetD.setFullYear(targetD.getFullYear() + 1);
  }

  const now = new Date();
  const diffTime = Math.max(1, targetD - now);
  const daysDiff = Math.max(1, Math.round(diffTime / (1000 * 60 * 60 * 24)));
  const monthsDiff = Math.max(1.0, daysDiff / 30.4375);
  const weeksDiff = Math.max(1.0, daysDiff / 7.0);

  const remaining = Math.max(0, targetAmount - currentSaved);
  const reqDaily = Math.round(remaining / daysDiff);
  const reqWeekly = Math.round(remaining / weeksDiff);
  const reqMonthly = Math.round(remaining / monthsDiff);

  const income = state.profile.monthly_income || 35000;
  const essentials = state.profile.upcoming_commitments || 12499;
  const disposable = Math.max(1000, income - essentials);
  const ratio = reqMonthly / disposable;

  let feasibility, badge, color, headline, sub;
  if (ratio <= 0.50) {
    feasibility = 'comfortable';
    badge = 'Easily Achievable';
    headline = `Your current spending leaves plenty of room for ${formatCurr(reqMonthly)}/month.`;
    sub = `You will retain ~${formatCurr(disposable - reqMonthly)}/month for everyday flexible spending and unexpected events.`;
  } else if (ratio <= 0.85) {
    feasibility = 'moderate';
    badge = 'Achievable with Focus';
    headline = `${formatCurr(reqMonthly)}/month is achievable with moderate day-to-day flexibility.`;
    sub = `Leaves approximately ${formatCurr(disposable - reqMonthly)}/month free after essentials and your emergency buffer.`;
  } else {
    feasibility = 'tight';
    badge = 'Tight Margin';
    headline = `${formatCurr(reqMonthly)}/month takes up most of your disposable cash flow.`;
    sub = `Consider extending your target date or trimming flexible subscriptions to avoid cash stress.`;
  }

  const plans = [
    {
      id: 'plan_std',
      name: 'Plan A · Pure Savings Pace',
      badge: 'Standard',
      monthly_amount: reqMonthly,
      desc: `Save ${formatCurr(reqMonthly)}/mo (approx ${formatCurr(reqDaily)}/day) in your safe savings account.`,
      is_recommended: feasibility !== 'tight'
    },
    {
      id: 'plan_trim',
      name: 'Plan B · Optimized Spending Trim',
      badge: 'Balanced',
      monthly_amount: Math.round(reqMonthly * 0.90),
      desc: `Save ${formatCurr(reqMonthly * 0.90)}/mo + reduce discretionary dining/shopping by ${formatCurr(reqMonthly * 0.10)}/mo.`,
      is_recommended: feasibility === 'tight'
    },
    {
      id: 'plan_growth',
      name: 'Plan C · Smart Growth Scenario',
      badge: 'Compounding',
      monthly_amount: Math.round(calculateSipMonthlyClient(targetAmount, currentSaved, monthsDiff, 0.08)),
      desc: `Contribute ${formatCurr(calculateSipMonthlyClient(targetAmount, currentSaved, monthsDiff, 0.08))}/mo with illustrative 8% annual return compounding.`,
      is_recommended: false
    }
  ];

  const growthScenarios = [
    {
      name: 'Liquid Savings Account',
      assumed_annual_rate: '4%',
      risk_level: 'Very Low',
      icon: 'account_balance',
      desc: 'Capital fully protected. Ideal for emergency funds and short-term goals (< 6 months).',
      monthly_contribution: Math.round(calculateSipMonthlyClient(targetAmount, currentSaved, monthsDiff, 0.04)),
      estimated_gain: Math.round(calculateSipGainClient(targetAmount, currentSaved, monthsDiff, 0.04)),
      timeline_fit: monthsDiff < 12 ? 'Best fit' : 'Optional'
    },
    {
      name: 'Recurring Deposit / Fixed Income',
      assumed_annual_rate: '7%',
      risk_level: 'Low',
      icon: 'lock_clock',
      desc: 'Guaranteed fixed interest. Great for goals with fixed upcoming dates (6 - 24 months).',
      monthly_contribution: Math.round(calculateSipMonthlyClient(targetAmount, currentSaved, monthsDiff, 0.07)),
      estimated_gain: Math.round(calculateSipGainClient(targetAmount, currentSaved, monthsDiff, 0.07)),
      timeline_fit: (monthsDiff >= 6 && monthsDiff <= 24) ? 'Best fit' : 'Optional'
    },
    {
      name: 'Balanced / Index SIP',
      assumed_annual_rate: '10%',
      risk_level: 'Moderate',
      icon: 'trending_up',
      desc: 'Diversified basket of index equities and debt. Suitable for medium-term horizons (1 - 3 years).',
      monthly_contribution: Math.round(calculateSipMonthlyClient(targetAmount, currentSaved, monthsDiff, 0.10)),
      estimated_gain: Math.round(calculateSipGainClient(targetAmount, currentSaved, monthsDiff, 0.10)),
      timeline_fit: monthsDiff >= 12 ? 'Best fit' : 'Optional'
    },
    {
      name: 'Long-Term Growth Fund',
      assumed_annual_rate: '12%',
      risk_level: 'Higher',
      icon: 'insights',
      desc: 'Higher volatility with long-term compounding potential. Best for horizons > 3 years.',
      monthly_contribution: Math.round(calculateSipMonthlyClient(targetAmount, currentSaved, monthsDiff, 0.12)),
      estimated_gain: Math.round(calculateSipGainClient(targetAmount, currentSaved, monthsDiff, 0.12)),
      timeline_fit: monthsDiff >= 36 ? 'Best fit' : 'Optional'
    }
  ];

  return {
    target_amount: targetAmount,
    current_saved: currentSaved,
    required_daily: reqDaily,
    required_weekly: reqWeekly,
    required_monthly: reqMonthly,
    feasibility: feasibility,
    feasibility_badge: badge,
    feasibility_headline: headline,
    feasibility_sub: sub,
    plans: plans,
    growth_scenarios: growthScenarios
  };
}

function calculateDynamicAdjustmentClient(targetAmount, currentSaved, targetDateStr, behindAmount, currentPace) {
  const remaining = Math.max(0, targetAmount - currentSaved);
  const remainingMonths = 9.0;
  const newReqMonthly = Math.round(remaining / remainingMonths);

  return {
    behind_amount: behindAmount,
    option_increase_monthly: {
      title: `Option A · Increase Monthly Saving to ${formatCurr(newReqMonthly)}`,
      diff: `+${formatCurr(Math.max(0, newReqMonthly - currentPace))}/mo`
    },
    option_extend_date: {
      title: `Option B · Keep ${formatCurr(currentPace)}/mo & extend by 18 days`,
      diff: `+18 Days`
    }
  };
}

function calculateSipMonthlyClient(target, lump, months, annualRate) {
  if (months <= 0) return Math.max(0, target - lump);
  if (annualRate <= 0) return Math.max(0, target - lump) / months;
  const i = annualRate / 12.0;
  const fvLump = lump * Math.pow(1.0 + i, months);
  const needed = Math.max(0, target - fvLump);
  const factor = ((Math.pow(1.0 + i, months) - 1.0) / i) * (1.0 + i);
  return factor > 0 ? (needed / factor) : (needed / months);
}

function calculateSipGainClient(target, lump, months, annualRate) {
  const p = calculateSipMonthlyClient(target, lump, months, annualRate);
  const totalInvested = lump + (p * months);
  return Math.max(0, target - totalInvested);
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

  const amt = extractNumericAmount(queryText);

  try {
    const res = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: queryText, amount: amt, user_id: state.userId })
    });

    if (res.ok) {
      state.evaluationResult = await res.json();
    } else {
      throw new Error('API offline');
    }
  } catch (err) {
    // Client-side fallback evaluation
    state.evaluationResult = evaluateAffordabilityClient(queryText, amt);
  } finally {
    renderDecisionResult();
    renderWhyScreen();
    renderPlanScreen();
    navigateTo('result');

    if (submitBtn) {
      submitBtn.innerHTML = originalHtml;
      submitBtn.disabled = false;
    }
  }
}

function evaluateAffordabilityClient(queryText, amount) {
  const safeSpend = state.profile.safe_to_spend_today || 8450.0;
  const buffer = state.profile.minimum_balance_to_keep || 5000.0;

  if (amount <= safeSpend) {
    return {
      affordability_status: 'affordable_now',
      recommended_payment_method: 'full_payment',
      verdict_badge: 'AFFORDABLE NOW',
      verdict_color: 'secondary',
      verdict_headline: `You can comfortably afford ${formatCurr(amount)} today.`,
      verdict_sub: `Leaves your emergency buffer of ${formatCurr(buffer)} completely intact with surplus cash remaining.`,
      amount_safe_to_pay: amount,
      requested_amount: amount,
      earliest_date_for_full_payment: new Date().toISOString().split('T')[0],
      breakdown: { purchase_price: amount, safe_today: safeSpend, shortfall_today: 0 }
    };
  } else {
    const d = new Date();
    d.setDate(d.getDate() + 26);
    return {
      affordability_status: 'affordable_later',
      recommended_payment_method: 'wait',
      verdict_badge: 'WAIT',
      verdict_color: 'tertiary',
      verdict_headline: `Buying this today could reduce your safety buffer below ${formatCurr(buffer)}.`,
      verdict_sub: `Give your balance time until your upcoming commitments clear and salary arrives.`,
      amount_safe_to_pay: safeSpend,
      requested_amount: amount,
      earliest_date_for_full_payment: d.toISOString().split('T')[0],
      breakdown: { purchase_price: amount, safe_today: safeSpend, shortfall_today: amount - safeSpend }
    };
  }
}

/**
 * Rendering Decision Result
 */
function renderDecisionResult() {
  const r = state.evaluationResult || evaluateAffordabilityClient(state.currentQuery, 40000);

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
  } else {
    if (verdictCard) verdictCard.className = 'relative overflow-hidden rounded-2xl bg-tertiary-fixed p-5 shadow-sm';
    if (verdictTitle) verdictTitle.className = 'font-display-hero text-display-hero text-on-tertiary-fixed tracking-tight leading-none';
    if (verdictIcon) verdictIcon.textContent = 'hourglass_top';
  }

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
    } catch (e) {}
  }

  const b = r.breakdown || {};
  const pEl = document.getElementById('breakdown-price');
  const sEl = document.getElementById('breakdown-safe');
  if (pEl) pEl.textContent = formatCurr(b.purchase_price || 40000);
  if (sEl) sEl.textContent = formatCurr(b.safe_today || 8450);
}

function renderWhyScreen() {}
function renderPlanScreen() {}

function selectPlanCard(cardEl, btnText, planType) {
  state.selectedPlanType = planType;
  state.selectedPlanText = btnText;
  showToast(`Selected ${btnText}`);
}

function confirmSelectedPlan() {
  showToast(`Plan selected: ${state.selectedPlanText}`);
  setTimeout(() => navigateTo('home'), 800);
}

/**
 * Modals & Settings
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

function closeSettingsModal() {
  const modal = document.getElementById('settings-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  }
}

function populateUserSwitcher() {}

function switchUserProfile(newUserId) {
  state.userId = newUserId;
  loadUserProfile(newUserId);
  loadTransactions(newUserId);
  loadCommitments(newUserId);
  showToast(`Switched to profile: ${newUserId}`);
}

async function saveSettings() {
  const name = document.getElementById('settings-name-input').value.trim() || 'Rahul';
  const income = parseFloat(document.getElementById('settings-income-input').value) || 35000;
  const buffer = parseFloat(document.getElementById('settings-buffer-input').value) || 5000;

  state.profile.user_name = name;
  state.profile.monthly_income = income;
  state.profile.minimum_balance_to_keep = buffer;

  localStorage.setItem('afford_iq_user_name', name);
  renderHomeProfile();
  closeSettingsModal();
  showToast('Settings saved.');
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

    recognition.onerror = () => fallbackVoiceSimulation(inputEl, targetInputId);
  } else {
    fallbackVoiceSimulation(inputEl, targetInputId);
  }
}

function fallbackVoiceSimulation(inputEl, targetInputId) {
  showToast('Listening...');
  const samples = [
    'How much is safe to spend this weekend?',
    'Can I buy a ₹15,000 phone next month?',
    'Can I afford ₹2,500 on dinner tonight?'
  ];
  const chosen = samples[Math.floor(Math.random() * samples.length)];
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
  showToast(`Preference updated.`);
}

function exportUserData() {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify({
    profile: state.profile,
    goals: state.goals,
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
  if (confirm('Clear local data and restart setup?')) {
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

function getStatusPillHtml(status) {
  if (status === 'at_risk') {
    return `<span class="px-2.5 py-0.5 rounded-full bg-error-container text-on-error-container text-[11px] font-bold tracking-wide uppercase">AT RISK</span>`;
  } else if (status === 'ahead') {
    return `<span class="px-2.5 py-0.5 rounded-full bg-secondary-container text-on-secondary-container text-[11px] font-bold tracking-wide uppercase">AHEAD</span>`;
  } else {
    return `<span class="px-2.5 py-0.5 rounded-full bg-secondary-container text-on-secondary-container text-[11px] font-bold tracking-wide uppercase">ON TRACK</span>`;
  }
}

function formatDateReadable(dateStr) {
  if (!dateStr) return 'Target Date';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch (e) {
    return dateStr;
  }
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
