/* ============================================================
   WRENCHLINK — shared app logic
   nav state, auth modal, toast, route guards
   ============================================================ */

/* ---------- TOAST ---------- */
function showToast(msg, isError) {
  let t = document.getElementById('toast');
  if (!t) {
    t = document.createElement('div');
    t.className = 'toast';
    t.id = 'toast';
    t.innerHTML = '<span id="toast-icon"></span><span id="toast-msg"></span>';
    document.body.appendChild(t);
  }
  document.getElementById('toast-msg').textContent = msg;
  document.getElementById('toast-icon').innerHTML = isError ? icon('bolt') : icon('check');
  t.classList.toggle('error', !!isError);
  t.classList.add('show');
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => t.classList.remove('show'), 3500);
}

/* ---------- MODAL (auth) ---------- */
function ensureModal() {
  if (document.getElementById('modal-overlay')) return;
  const html = `
  <div class="modal-overlay" id="modal-overlay" onclick="closeModalOutside(event)">
    <div class="modal">
      <div class="modal-header">
        <h3 id="modal-title">Sign In</h3>
        <button class="modal-close" onclick="closeModal()">✕</button>
      </div>
      <div class="modal-body">
        <div class="modal-tabs" id="modal-tabs">
          <button class="modal-tab active" data-t="login" onclick="setModalType('login', this)">Sign In</button>
          <button class="modal-tab" data-t="register-tech" onclick="setModalType('register-tech', this)">${icon('wrench')} Tech</button>
          <button class="modal-tab" data-t="employer" onclick="setModalType('employer', this)">${icon('building')} Employer</button>
        </div>

        <form id="modal-login" onsubmit="return wlLogin(event)">
          <div class="form-group"><label class="form-label">Email</label><input class="form-input" name="email" type="email" placeholder="you@example.com" required></div>
          <div class="form-group"><label class="form-label">Password</label><input class="form-input" name="password" type="password" placeholder="••••••••" required></div>
          <div class="form-group" style="flex-direction:row;gap:0.5rem;align-items:center;">
            <span class="form-label" style="margin:0;">Sign in as:</span>
            <label class="form-label" style="color:var(--chrome);"><input type="radio" name="role" value="tech" checked> Technician</label>
            <label class="form-label" style="color:var(--chrome);"><input type="radio" name="role" value="employer"> Employer</label>
          </div>
          <button class="btn-submit" type="submit">Sign In →</button>
          <div class="modal-switch">Don't have an account? <a onclick="setModalType('register-tech', document.querySelector('[data-t=register-tech]'))">Create one free</a></div>
        </form>

        <form id="modal-register-tech" style="display:none;" onsubmit="return wlRegisterTech(event)">
          <div class="form-row">
            <div class="form-group"><label class="form-label">First Name</label><input class="form-input" name="first" type="text" placeholder="Marcus" required></div>
            <div class="form-group"><label class="form-label">Last Name</label><input class="form-input" name="last" type="text" placeholder="Thompson" required></div>
          </div>
          <div class="form-group"><label class="form-label">Email</label><input class="form-input" name="email" type="email" placeholder="you@example.com" required></div>
          <div class="form-group"><label class="form-label">Password</label><input class="form-input" name="password" type="password" placeholder="Choose a password" required></div>
          <div class="form-group"><label class="form-label">Specialty</label>
            <select class="form-select" name="specialty">
              <option>Auto Repair Technician</option><option>Auto Body / Collision Tech</option>
              <option>EV / Hybrid Specialist</option><option>Estimator</option><option>Paint Technician</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Your City Pool</label>
            <select class="form-select" name="metro" id="reg-tech-metro"></select>
          </div>
          <button class="btn-submit" type="submit">Create Free Profile →</button>
        </form>

        <form id="modal-employer" style="display:none;" onsubmit="return wlRegisterEmployer(event)">
          <div class="form-group"><label class="form-label">Shop / Company Name</label><input class="form-input" name="company" type="text" placeholder="Apex Body & Auto" required></div>
          <div class="form-group"><label class="form-label">Shop Type</label>
            <select class="form-select" name="shoptype">
              <option>Auto Repair Shop</option><option>Auto Body / Collision Shop</option>
              <option>Dealership Service Dept.</option><option>Fleet Maintenance</option><option>Multi-Location Group</option>
            </select>
          </div>
          <div class="form-group"><label class="form-label">Your Email</label><input class="form-input" name="email" type="email" placeholder="hiring@yourshop.com" required></div>
          <div class="form-group"><label class="form-label">Password</label><input class="form-input" name="password" type="password" placeholder="Choose a password" required></div>
          <div class="form-group"><label class="form-label">City Pool</label><select class="form-select" name="metro" id="reg-emp-metro"></select></div>
          <button class="btn-submit" type="submit">Get Started →</button>
        </form>
      </div>
    </div>
  </div>`;
  document.body.insertAdjacentHTML('beforeend', html);

  // populate metro selects
  const opts = WL.cities().map(c => `<option>${c.name}</option>`).join('');
  const a = document.getElementById('reg-tech-metro'); if (a) a.innerHTML = opts;
  const b = document.getElementById('reg-emp-metro'); if (b) b.innerHTML = opts;
}

function openModal(type) {
  ensureModal();
  document.getElementById('modal-overlay').classList.add('open');
  const tabMap = { login: 'login', register: 'register-tech', 'register-tech': 'register-tech', employer: 'employer' };
  const t = tabMap[type] || 'login';
  setModalType(t, document.querySelector(`[data-t="${t}"]`));
}
function closeModal() { const o = document.getElementById('modal-overlay'); if (o) o.classList.remove('open'); }
function closeModalOutside(e) { if (e.target === document.getElementById('modal-overlay')) closeModal(); }

function setModalType(type, btn) {
  ['login','register-tech','employer'].forEach(t => {
    const el = document.getElementById('modal-' + t);
    if (el) el.style.display = 'none';
  });
  const target = document.getElementById('modal-' + type);
  if (target) target.style.display = 'block';
  const titles = { login: 'Sign In', 'register-tech': 'Join as a Technician', employer: 'Join as an Employer' };
  document.getElementById('modal-title').textContent = titles[type] || 'Sign In';
  document.querySelectorAll('.modal-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
}

/* ---------- AUTH ---------- */
function wlLogin(e) {
  e.preventDefault();
  const f = e.target;
  const role = f.role.value;
  // Admin shortcut
  if (f.email.value.trim().toLowerCase() === 'admin@wrenchlink.io') {
    WL.set({ user: { type: 'admin', name: 'Platform Admin', email: f.email.value } });
    closeModal(); window.location.href = 'admin.html'; return false;
  }
  if (role === 'employer') {
    WL.set({ user: { type: 'employer', name: WL.get().user?.company || 'Your Shop', company: WL.get().user?.company || 'Your Shop', email: f.email.value, metro: WL.get().user?.metro || 'Columbus', plan: WL.get().user?.plan || 'Pro' } });
    closeModal(); window.location.href = 'employer.html'; return false;
  }
  WL.set({ user: { type: 'tech', name: WL.get().user?.name || 'Marcus Thompson', email: f.email.value, metro: WL.get().user?.metro || 'Columbus', specialty: WL.get().user?.specialty || 'Master Auto Technician' } });
  closeModal(); window.location.href = 'vault.html'; return false;
}

function wlRegisterTech(e) {
  e.preventDefault();
  const f = e.target;
  WL.set({ user: {
    type: 'tech',
    name: `${f.first.value} ${f.last.value}`.trim(),
    email: f.email.value,
    specialty: f.specialty.value,
    metro: f.metro.value,
    joined: new Date().toISOString().slice(0,10),
    plan: 'Solo',
    price: 9.95,
  }});
  closeModal();
  showToast('Profile created! Welcome to WrenchLink.');
  setTimeout(() => window.location.href = 'vault.html', 700);
  return false;
}

function wlRegisterEmployer(e) {
  e.preventDefault();
  const f = e.target;
  WL.set({ user: {
    type: 'employer',
    name: f.company.value,
    company: f.company.value,
    shoptype: f.shoptype.value,
    email: f.email.value,
    metro: f.metro.value,
    joined: new Date().toISOString().slice(0,10),
    plan: 'Pro',
  }});
  closeModal();
  showToast('Employer account created! Set up your shop.');
  setTimeout(() => window.location.href = 'employer.html', 700);
  return false;
}

function wlLogout() {
  WL.logout();
  showToast('Signed out.');
  setTimeout(() => window.location.href = 'index.html', 500);
}

/* ---------- NAV (shared) ---------- */
function renderNav(active) {
  const user = WL.get().user;
  let ctas;
  if (user) {
    const initials = (user.name || 'U').split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase();
    let home = user.type === 'employer' ? 'employer.html' : user.type === 'admin' ? 'admin.html' : 'vault.html';
    let homeLabel = user.type === 'employer' ? 'Dashboard' : user.type === 'admin' ? 'Admin' : 'My Vault';
    ctas = `
      <a href="${home}" class="btn-nav-outline">${homeLabel}</a>
      <div class="nav-user show">
        <div class="nav-user-avatar">${initials}</div>
        <span class="nav-user-name">${user.name}</span>
        <a href="#" class="btn-nav-fill" onclick="wlLogout();return false;">Sign Out</a>
      </div>`;
  } else {
    ctas = `
      <a href="#" class="btn-nav-outline" onclick="openModal('login');return false;">Sign In</a>
      <a href="#" class="btn-nav-fill" onclick="openModal('register');return false;">Get Started</a>`;
  }

  const links = [
    { href: 'jobs.html', label: 'Find Jobs', key: 'jobs' },
    { href: 'city-pools.html', label: 'City Pools', key: 'city' },
    { href: 'index.html#how-it-works', label: 'How It Works', key: 'how' },
    { href: 'pricing.html', label: 'Pricing', key: 'pricing' },
  ];
  const linkHtml = links.map(l => `<a href="${l.href}" class="${active===l.key?'active':''}">${l.label}</a>`).join('');

  const nav = document.createElement('nav');
  nav.innerHTML = `
    <a href="index.html" class="logo">WRENCH<span>LINK</span></a>
    <button class="nav-toggle" onclick="document.querySelector('.nav-links').classList.toggle('mobile-open')">☰</button>
    <div class="nav-links">${linkHtml}</div>
    <div class="nav-ctas">${ctas}</div>`;
  const existing = document.querySelector('nav');
  if (existing) existing.replaceWith(nav); else document.body.prepend(nav);
}

/* ---------- ROUTE GUARD ---------- */
function requireRole(role) {
  const user = WL.get().user;
  if (!user) { showToast('Please sign in to continue.', true); setTimeout(() => { ensureModal(); openModal('login'); }, 300); return false; }
  if (role && user.type !== role && user.type !== 'admin') {
    showToast('That area is for ' + role + ' accounts.', true);
    setTimeout(() => window.location.href = 'index.html', 900);
    return false;
  }
  return true;
}

/* ---------- helpers ---------- */
function stars(r) {
  const full = Math.round(r);
  return '★★★★★'.slice(0, full) + '☆☆☆☆☆'.slice(0, 5 - full);
}
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function statusColor(s) { return s === 'active' ? 'var(--green)' : s === 'passive' ? 'var(--accent2)' : 'var(--red)'; }
function statusLabel(s) { return s === 'active' ? 'Actively Looking' : s === 'passive' ? 'Passively Open' : 'Not Looking'; }
