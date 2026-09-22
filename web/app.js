/**
 * Afford IQ · Financial Decision Assistant
 * Frontend Application Controller
 * Handles SPA navigation, real financial engine integration, user sign-in flow,
 * transaction activities, natural language queries, Goal Accelerator, and payment plan selection.
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
  goals: [],
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

  // Load backend data
  await loadDatasetUsers();
  await loadUserProfile(state.userId);
  await loadTransactions(state.userId);
  await loadCommitments(state.userId);
  await loadGoals();

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

async function loadGoals() {
  try {
    const res = await fetch('/api/goals');
    if (res.ok) {
      state.goals = await res.json();
      renderHomeGoalsPreview();
      renderGoalsDashboard();
    }
  } catch (err) {
    console.warn('Goals fetch error:', err);
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

  // Calculate Aggregates
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

  // Header Elements
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

  // Hero Stats
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

  // Fetch Dynamic Adjustment Recalculation from Backend
  try {
    const lagAmt = goal.status === 'at_risk' ? 1200.0 : 0.0;
    const res = await fetch('/api/goals/adjust', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_amount: goal.target_amount,
        current_saved: goal.current_saved,
        target_date: goal.target_date,
        behind_amount: lagAmt,
        current_pace: goal.current_avg_contribution || goal.monthly_contribution
      })
    });
    if (res.ok) {
      const adj = await res.json();
      updateDynamicAdjustmentUI(adj, goal);
    }
  } catch (err) {
    console.warn('Adjustment fetch error:', err);
  }

  // Fetch Educational Growth Scenarios
  try {
    const planRes = await fetch('/api/goals/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_amount: goal.target_amount,
        current_saved: goal.current_saved,
        target_date: goal.target_date
      })
    });
    if (planRes.ok) {
      const planData = await planRes.json();
      renderEducationalScenarios(planData.growth_scenarios || []);
    }
  } catch (err) {
    console.warn('Growth calculation error:', err);
  }
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

  // Option 1 Elements
  const opt1Title = document.getElementById('opt-increase-title');
  if (opt1Title && adj.option_increase_monthly) opt1Title.textContent = adj.option_increase_monthly.title;

  const opt1Diff = document.getElementById('opt-increase-diff');
  if (opt1Diff && adj.option_increase_monthly) opt1Diff.textContent = adj.option_increase_monthly.diff;

  // Option 2 Elements
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
async function triggerLiveGoalCalculation() {
  const nameInput = document.getElementById('new-goal-name');
  const amountInput = document.getElementById('new-goal-amount');
  const dateInput = document.getElementById('new-goal-date');
  const savedInput = document.getElementById('new-goal-saved');

  const name = nameInput ? nameInput.value.trim() || 'New Goal' : 'New Goal';
  const amount = amountInput ? parseFloat(amountInput.value) || 50000 : 50000;
  const targetDate = dateInput ? dateInput.value || '2027-06-30' : '2027-06-30';
  const currentSaved = savedInput ? parseFloat(savedInput.value) || 0 : 0;

  try {
    const res = await fetch('/api/goals/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_amount: amount,
        current_saved: currentSaved,
        target_date: targetDate
      })
    });

    if (res.ok) {
      const plan = await res.json();
      state.livePlanCalculation = plan;

      // Update Breakdown Tiles
      const dailyEl = document.getElementById('create-plan-daily');
      if (dailyEl) dailyEl.textContent = `${formatCurr(plan.required_daily)} / day`;

      const weeklyEl = document.getElementById('create-plan-weekly');
      if (weeklyEl) weeklyEl.textContent = `${formatCurr(plan.required_weekly)} / wk`;

      const monthlyEl = document.getElementById('create-plan-monthly');
      if (monthlyEl) monthlyEl.textContent = `${formatCurr(plan.required_monthly)} / mo`;

      // Update Feasibility Badges
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

      // Render 3 Plans
      renderCreatePlans(plan.plans || []);
    }
  } catch (err) {
    console.warn('Live calculation error:', err);
  }
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

  const payload = {
    name: name,
    category: state.selectedGoalCategory || 'Device',
    target_amount: amount,
    current_saved: saved,
    target_date: targetDate,
    monthly_contribution: monthlyPace,
    current_avg_contribution: monthlyPace,
    status: 'on_track',
    icon: iconMap[state.selectedGoalCategory] || 'flag'
  };

  try {
    const res = await fetch('/api/goals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      await loadGoals();
      showToast(`Goal "${name}" created successfully!`);
      if (data.goal && data.goal.goal_id) {
        openGoalDetail(data.goal.goal_id);
      } else {
        navigateTo('goals');
      }
    }
  } catch (err) {
    console.error('Goal creation failed:', err);
    showToast('Goal creation failed. Please check inputs.');
  }
}

/**
 * Dynamic Adjustment Action Handlers & Simulations
 */
async function simulateGoalBehavior(status, lagAmount) {
  if (!state.currentGoalId) return;
  try {
    const res = await fetch('/api/goals/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        goal_id: state.currentGoalId,
        status: status,
        lag_amount: lagAmount
      })
    });

    if (res.ok) {
      const data = await res.json();
      state.currentGoal = data.goal;
      // Update goal in local state
      const idx = state.goals.findIndex(g => g.goal_id === state.currentGoalId);
      if (idx !== -1) state.goals[idx] = data.goal;

      await renderGoalDetailView(data.goal);
      renderHomeGoalsPreview();
      renderGoalsDashboard();
      showToast(status === 'at_risk' ? 'Simulated: Behind pace by ₹1,200.' : 'Simulated: On track with planned pace.');
    }
  } catch (err) {
    console.warn('Simulation error:', err);
  }
}

async function applyGoalAdjustment(actionType) {
  if (!state.currentGoal) return;
  const goal = state.currentGoal;

  if (actionType === 'increase_pace') {
    // Increase monthly pace to ₹4,650
    const newPace = Math.round(goal.monthly_contribution * 1.12);
    goal.monthly_contribution = newPace;
    goal.current_avg_contribution = newPace;
    goal.status = 'on_track';
    showToast(`Applied new target pace of ${formatCurr(newPace)}/month.`);
  } else if (actionType === 'extend_date') {
    // Extend target date by 18 days
    const d = new Date(goal.target_date);
    d.setDate(d.getDate() + 18);
    goal.target_date = d.toISOString().split('T')[0];
    goal.status = 'on_track';
    showToast(`Extended target date to ${formatDateReadable(goal.target_date)}.`);
  } else if (actionType === 'trim_spending') {
    goal.status = 'on_track';
    showToast('Committed ₹400/month spending trim. Goal returned to ON TRACK.');
  }

  // Update backend
  try {
    await fetch('/api/goals', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(goal)
    });
    await loadGoals();
    renderGoalDetailView(goal);
  } catch (err) {
    console.warn('Update goal error:', err);
  }
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

async function deleteCurrentGoal() {
  if (!state.currentGoalId) return;
  if (confirm('Delete this goal and remove from tracking?')) {
    try {
      const res = await fetch(`/api/goals?goal_id=${state.currentGoalId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        await loadGoals();
        showToast('Goal deleted.');
        navigateTo('goals');
      }
    } catch (err) {
      console.warn('Delete goal error:', err);
    }
  }
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
