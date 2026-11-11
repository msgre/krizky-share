/* krizky-share — progressive enhancement:
 * - Web Share API na mobilu (nahradí dropdown, klepnutí na "Sdílet" volá navigator.share).
 * - Kopírování odkazu do schránky (data-share-copy tlačítko v dropdownu).
 * - Zavírání dropdownu po klepnutí mimo / na Escape.
 */
(function () {
  'use strict';

  const nativeShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function';

  document.querySelectorAll('[data-share]').forEach(setupShare);

  function setupShare(root) {
    const url = root.dataset.shareUrl;
    const title = root.dataset.shareTitle || document.title;
    const details = root.querySelector('.share-mobile');
    const toggle = root.querySelector('.share-toggle');
    const menu = root.querySelector('.share-menu');
    const copyBtn = root.querySelector('[data-share-copy]');

    // Web Share API: intercept toggle click and call navigator.share().
    if (nativeShare && details && toggle) {
      toggle.addEventListener('click', (e) => {
        // Only on viewports where the mobile widget is actually visible.
        if (getComputedStyle(details).display === 'none') {
          return;
        }
        e.preventDefault();
        navigator.share({ title, url }).catch(() => {
          /* user dismissed */
        });
      });
    }

    // Copy link to clipboard.
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        copyToClipboard(url).then(() => {
          const label = copyBtn.querySelector('span');
          const original = label ? label.textContent : null;
          copyBtn.classList.add('is-copied');
          if (label) {
            label.textContent = 'Zkopírováno';
          }
          setTimeout(() => {
            copyBtn.classList.remove('is-copied');
            if (label && original !== null) {
              label.textContent = original;
            }
          }, 1600);
          // Close the dropdown so user gets feedback the action ran.
          if (details && details.open) {
            details.open = false;
          }
        });
      });
    }

    // Menu items (share links) — close dropdown after click.
    if (details && menu) {
      menu.querySelectorAll('a.share-menu-item').forEach((a) => {
        a.addEventListener('click', () => {
          details.open = false;
        });
      });
    }

    // Click outside → close.
    if (details) {
      document.addEventListener('click', (e) => {
        if (!details.open) {
          return;
        }
        if (!details.contains(e.target)) {
          details.open = false;
        }
      });
    }
  }

  // Escape closes any open dropdown.
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') {
      return;
    }
    document.querySelectorAll('.share-mobile[open]').forEach((d) => {
      d.open = false;
    });
  });

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    // Fallback for older browsers.
    return new Promise((resolve) => {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'absolute';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand('copy');
      } catch {
        /* ignore */
      }
      document.body.removeChild(ta);
      resolve();
    });
  }
})();
