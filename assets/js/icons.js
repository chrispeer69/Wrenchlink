/* ============================================================
   WRENCHLINK — inline SVG icon set (replaces emoji)
   Stroke-based, 1.5 weight, inherits currentColor.
   Usage: icon('wrench')  ->  <span class="ic">…</span>
   ============================================================ */
const ICONS = {
  wrench: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.2l-6 6a1.5 1.5 0 0 0 2.1 2.1l6-6a4 4 0 0 0 5.2-5.4l-2.3 2.3-2.1-.5-.5-2.1 2.3-2.3z"/>',
  building: '<path d="M3 21h18M5 21V5a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v16M15 9h3a1 1 0 0 1 1 1v11"/><path d="M8 7h2M8 11h2M8 15h2"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  bolt: '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/>',
  badge: '<circle cx="12" cy="9" r="5"/><path d="M9 13.5 8 22l4-2 4 2-1-8.5"/>',
  map: '<path d="m9 4-6 2v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/>',
  chat: '<path d="M21 12a8 8 0 0 1-11.4 7.2L3 21l1.8-6.6A8 8 0 1 1 21 12z"/>',
  chart: '<path d="M3 3v18h18"/><path d="M7 15l3-4 3 2 4-6"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  dollar: '<path d="M12 2v20M17 6.5C17 4.6 14.8 3.5 12 3.5S7 4.8 7 6.8s2 2.7 5 3.2 5 1.2 5 3.2-2.2 3.3-5 3.3-5-1.1-5-3"/>',
  pin: '<path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  heart: '<path d="M12 20s-7-4.5-9.5-9A5 5 0 0 1 12 6a5 5 0 0 1 9.5 5c-2.5 4.5-9.5 9-9.5 9z"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-2.7-1.1l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1.1-2.7H3a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.1-2.7l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3 1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8 1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z"/>',
  briefcase: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12h18"/>',
  card: '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
  shield: '<path d="M12 3l8 3v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3z"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>',
  send: '<path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z"/>',
  signal: '<path d="M4 20v-4M9 20v-8M14 20v-12M19 20V4"/>',
  star: '<path d="M12 3l2.7 5.5 6 .9-4.3 4.2 1 6-5.4-2.8L6.6 19.6l1-6L3.3 9.4l6-.9L12 3z"/>',
  arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
};

function iconSvg(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ''}</svg>`;
}
function icon(name, cls) {
  return `<span class="ic ${cls || ''}">${iconSvg(name)}</span>`;
}
// Fill any <span data-ic="name"></span> placeholders in static markup.
function applyIcons(root) {
  (root || document).querySelectorAll('[data-ic]').forEach(el => {
    el.classList.add('ic');
    el.innerHTML = iconSvg(el.getAttribute('data-ic'));
    el.removeAttribute('data-ic');
  });
}
document.addEventListener('DOMContentLoaded', function () { applyIcons(); });
