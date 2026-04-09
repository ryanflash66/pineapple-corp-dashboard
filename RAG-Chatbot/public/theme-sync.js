/**
 * Theme sync — receives postMessage from the parent dashboard
 * and toggles Chainlit's built-in theme toggle to keep them in sync.
 */

window.addEventListener('message', function (event) {
  if (!event.data || event.data.type !== 'theme-change') return;

  var desired = event.data.theme; // "light" or "dark"

  // Detect Chainlit's current theme from the html element
  var html = document.documentElement;
  var current =
    html.getAttribute('data-theme') ||
    html.getAttribute('data-color-mode') ||
    html.style.colorScheme ||
    (html.classList.contains('dark') ? 'dark' : 'light');

  if (current === desired) return;

  // Try to find and click Chainlit's native theme toggle button
  var btn =
    document.querySelector('button[id*="theme"]') ||
    document.querySelector('button[aria-label*="heme"]') ||
    document.querySelector('header button svg[data-testid*="Brightness"]')?.closest('button');

  if (btn) {
    btn.click();
  }
});
