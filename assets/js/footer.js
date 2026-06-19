/* shared footer */
function renderFooter() {
  const el = document.getElementById('footer');
  if (!el) return;
  el.outerHTML = `
  <footer>
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="index.html" class="logo">WRENCH<span>LINK</span></a>
        <p>Where automotive talent meets opportunity. The trade deserves a platform built for the trade.</p>
      </div>
      <div class="footer-col">
        <h5>For Technicians</h5>
        <a href="vault.html">My Vault</a>
        <a href="jobs.html">Browse Jobs</a>
        <a href="city-pools.html">Join City Pool</a>
        <a href="pricing.html">Salary Guide</a>
      </div>
      <div class="footer-col">
        <h5>For Employers</h5>
        <a href="employer.html">Post a Job</a>
        <a href="employer.html#candidates">Search Candidates</a>
        <a href="city-pools.html">City Pool Access</a>
        <a href="pricing.html">Pricing</a>
      </div>
      <div class="footer-col">
        <h5>Company</h5>
        <a href="index.html#how-it-works">How It Works</a>
        <a href="pricing.html">Pricing</a>
        <a href="legal.html#terms">Terms of Service</a>
        <a href="legal.html#privacy">Privacy Policy</a>
        <a href="admin.html">Admin Console</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2026 WrenchLink, Inc. All rights reserved.</p>
      <div style="display:flex;gap:1.25rem;flex-wrap:wrap;">
        <a href="legal.html#terms" style="font-size:0.8rem;color:var(--muted);text-decoration:none;">Terms</a>
        <a href="legal.html#privacy" style="font-size:0.8rem;color:var(--muted);text-decoration:none;">Privacy</a>
        <a href="legal.html#cookies" style="font-size:0.8rem;color:var(--muted);text-decoration:none;">Cookies</a>
        <a href="legal.html#billing" style="font-size:0.8rem;color:var(--muted);text-decoration:none;">Billing</a>
      </div>
    </div>
  </footer>`;
}
