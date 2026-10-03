(function () {
  'use strict';

  // 1. Capture executing script reference synchronously at top-level evaluation
  const activeScript = typeof document !== 'undefined' ? document.currentScript : null;

  // 2. Helper to find the widget script element across all environments
  function getWidgetScript() {
    if (activeScript && activeScript.tagName === 'SCRIPT') {
      if (
        activeScript.hasAttribute('data-business-key') ||
        activeScript.hasAttribute('data-api-key') ||
        (activeScript.src && activeScript.src.includes('widget.js'))
      ) {
        return activeScript;
      }
    }
    return (
      (typeof document !== 'undefined' && (
        document.querySelector('script[data-business-key]') ||
        document.querySelector('script[data-api-key]') ||
        document.querySelector('script[src*="/widget/widget.js"], script[src*="widget.js"]')
      )) || null
    );
  }

  // 3. Helper to extract credentials (data-business-key or data-api-key)
  function extractCredentials(scriptEl) {
    if (!scriptEl) return null;
    const businessKey = scriptEl.getAttribute('data-business-key') || (scriptEl.dataset && scriptEl.dataset.businessKey);
    if (businessKey && businessKey.trim()) return businessKey.trim();

    const apiKey = scriptEl.getAttribute('data-api-key') || (scriptEl.dataset && scriptEl.dataset.apiKey);
    if (apiKey && apiKey.trim()) return apiKey.trim();

    return null;
  }

  // 4. Helper to resolve backend server origin
  function extractServerUrl(scriptEl, explicitUrl) {
    if (explicitUrl) return explicitUrl.replace(/\/+$/, '');

    if (scriptEl) {
      const explicitAttr = scriptEl.getAttribute('data-server-url') || (scriptEl.dataset && scriptEl.dataset.serverUrl);
      if (explicitAttr) return explicitAttr.replace(/\/+$/, '');

      if (scriptEl.src) {
        try {
          const parsed = new URL(scriptEl.src, window.location.href);
          if (parsed.origin && parsed.origin !== 'null' && parsed.origin !== 'file://') {
            if (parsed.port === '5173') {
              return `${parsed.protocol}//${parsed.hostname}:8000`;
            }
            return parsed.origin;
          }
        } catch (e) {}
      }
    }

    // Fallback search through scripts (for backward compatibility and tests)
    let detectedServerUrl = '';
    try {
      const scripts = document.getElementsByTagName('script');
      for (let i = scripts.length - 1; i >= 0; i--) {
        if (scripts[i].src && (scripts[i].src.includes('/widget/widget.js') || scripts[i].src.includes('widget.js'))) {
          detectedServerUrl = new URL(scripts[i].src, window.location.href).origin;
          break;
        }
      }
    } catch (err) {}

    if (detectedServerUrl && detectedServerUrl !== 'null' && detectedServerUrl !== 'file://') {
      if (detectedServerUrl.includes(':5173')) {
        return detectedServerUrl.replace(':5173', ':8000');
      }
      return detectedServerUrl;
    }

    if (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin !== 'null' && window.location.origin !== 'file://') {
      if (window.location.port === '5173') {
        return `${window.location.protocol}//${window.location.hostname}:8000`;
      }
      return window.location.origin;
    }

    return 'http://localhost:8000';
  }

  // 5. Helper for DOM Ready execution
  function onDOMReady(fn) {
    if (typeof document === 'undefined') return;
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn, { once: true });
    } else {
      fn();
    }
  }

  // Helper to safely manipulate class names in both real DOM and mock DOMs
  function addClass(el, cls) {
    if (!el) return;
    if (el.classList && typeof el.classList.add === 'function') {
      el.classList.add(cls);
    } else {
      const cur = el.className || '';
      if (!cur.split(/\s+/).includes(cls)) {
        el.className = (cur + ' ' + cls).trim();
      }
    }
  }

  function removeClass(el, cls) {
    if (!el) return;
    if (el.classList && typeof el.classList.remove === 'function') {
      el.classList.remove(cls);
    } else {
      const cur = el.className || '';
      el.className = cur
        .split(/\s+/)
        .filter((c) => c && c !== cls)
        .join(' ');
    }
  }

  // Helper to compute a darker color shade for gradients
  function darkenColor(hex, percent) {
    if (!hex || typeof hex !== 'string' || !hex.startsWith('#')) return hex || '#4f46e5';
    let cleanHex = hex.slice(1);
    if (cleanHex.length === 3) {
      cleanHex = cleanHex.split('').map((c) => c + c).join('');
    }
    if (cleanHex.length !== 6) return hex;
    const num = parseInt(cleanHex, 16);
    let r = (num >> 16) - Math.round(255 * (percent / 100));
    let g = ((num >> 8) & 0x00ff) - Math.round(255 * (percent / 100));
    let b = (num & 0x0000ff) - Math.round(255 * (percent / 100));
    r = Math.max(0, Math.min(255, r));
    g = Math.max(0, Math.min(255, g));
    b = Math.max(0, Math.min(255, b));
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  }

  // Helper to format discreet timestamps
  function formatTimestamp(date = new Date()) {
    try {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      const h = String(date.getHours()).padStart(2, '0');
      const m = String(date.getMinutes()).padStart(2, '0');
      return `${h}:${m}`;
    }
  }

  // 6. Safe zero-dependency lightweight markdown parser with strict XSS sanitization
  function formatMarkdown(rawText) {
    if (!rawText) return '';

    // Step 1: Strict HTML entity escaping to eliminate raw script injection & XSS
    let text = String(rawText)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');

    // Step 2: Fenced code blocks (```language\ncode\n``` or ```code```)
    text = text.replace(/```(?:[a-zA-Z0-9_\-]+)?\n?([\s\S]*?)```/g, (match, code) => {
      return `<pre class="supportai-code-block"><code>${code.trim()}</code></pre>`;
    });

    // Step 3: Inline code (`code`)
    text = text.replace(/`([^`\n]+)`/g, '<code class="supportai-inline-code">$1</code>');

    // Step 4: Bold (**text** or __text__)
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/__(.+?)__/g, '<strong>$1</strong>');

    // Step 5: Italic (*text* or _text_)
    text = text.replace(/(^|[^\*])\*([^\*\n]+)\*([^\*]|$)/g, '$1<em>$2</em>$3');
    text = text.replace(/(^|[^_])_([^_\n]+)_([^_]|$)/g, '$1<em>$2</em>$3');

    // Step 6: Safe Links ([label](url)) - strictly allow only http://, https://, and mailto:
    text = text.replace(/\[([^\]]+)\]\(((?:https?:\/\/|mailto:)[^\s)]+)\)/g, (match, label, url) => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="supportai-link">${label}</a>`;
    });

    // Step 7: Unordered bullet lists (- item or * item)
    text = text.replace(/(?:^|\n)[*-] +([^\n]+)/g, '<li class="supportai-li">$1</li>');
    text = text.replace(/(<li class="supportai-li">[\s\S]+?<\/li>(?:\s*<li class="supportai-li">[\s\S]+?<\/li>)*)/g, '<ul class="supportai-ul">$1</ul>');

    // Step 8: Preserve linebreaks outside <pre>
    const parts = text.split(/(<pre[\s\S]*?<\/pre>)/);
    for (let i = 0; i < parts.length; i++) {
      if (!parts[i].startsWith('<pre')) {
        parts[i] = parts[i].replace(/\n/g, '<br>');
      }
    }
    return parts.join('');
  }

  // 7. Injected scoped stylesheet
  function injectStyles() {
    if (typeof document === 'undefined') return;
    if (document.getElementById('supportai-styles')) return;

    // Injected <style id="supportai-styles">
    const style = document.createElement('style');
    style.id = 'supportai-styles';
    style.setAttribute('id', 'supportai-styles');
    style.textContent = `
/* Box sizing reset & host style isolation */
#supportai-chat,
#supportai-chat *,
#supportai-btn,
#supportai-btn * {
  box-sizing: border-box !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Ambient Launcher Entrance Pulse Ring */
@keyframes supportai-launcher-pulse {
  0% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.45); }
  70% { box-shadow: 0 0 0 14px rgba(99, 102, 241, 0); }
  100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }
}

/* Floating Launcher Button */
#supportai-btn {
  position: fixed;
  bottom: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16), 0 2px 6px rgba(0, 0, 0, 0.08);
  z-index: 99999;
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.25s ease, background 0.3s ease;
  user-select: none;
  animation: supportai-launcher-pulse 3s infinite ease-out;
}

#supportai-btn:hover {
  transform: scale(1.08) translateY(-2px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
}

#supportai-btn:active {
  transform: scale(0.94);
}

#supportai-btn.supportai-pos-right {
  right: 24px;
  left: auto;
}

#supportai-btn.supportai-pos-left {
  left: 24px;
  right: auto;
}

/* Launcher SVG Morphing Transitions */
#supportai-btn .supportai-icon-bubble,
#supportai-btn .supportai-icon-close {
  position: absolute;
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.2s ease;
}

#supportai-btn .supportai-icon-bubble {
  opacity: 1;
  transform: scale(1) rotate(0deg);
}

#supportai-btn .supportai-icon-close {
  opacity: 0;
  transform: scale(0.5) rotate(-90deg);
}

#supportai-btn.is-open .supportai-icon-bubble {
  opacity: 0;
  transform: scale(0.5) rotate(90deg);
}

#supportai-btn.is-open .supportai-icon-close {
  opacity: 1;
  transform: scale(1) rotate(0deg);
}

/* Chat Window - Desktop (>= 481px) */
#supportai-chat {
  position: fixed;
  bottom: 96px;
  width: 380px;
  height: 520px;
  max-width: calc(100vw - 32px);
  max-height: calc(100vh - 120px);
  max-height: calc(100dvh - 120px);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.16), 0 3px 10px rgba(0, 0, 0, 0.08);
  z-index: 99998;
  display: none;
  flex-direction: column;
  background-color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

#supportai-chat.supportai-pos-right {
  right: 24px;
  left: auto;
}

#supportai-chat.supportai-pos-left {
  left: 24px;
  right: auto;
}

/* Modern Header */
#supportai-header {
  padding: 14px 16px;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  user-select: none;
  flex-shrink: 0;
  position: relative;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.supportai-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.supportai-avatar-wrapper {
  position: relative;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.supportai-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  border: 1.5px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.supportai-header-text {
  display: flex;
  flex-direction: column;
}

#supportai-bot-name {
  font-size: 14.5px;
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: -0.01em;
}

.supportai-status-subtext {
  font-size: 11px;
  opacity: 0.9;
  margin-top: 1px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.supportai-status-label {
  font-weight: 400;
}

/* Dynamic Live Status Dot & Pulse */
@keyframes supportai-glow-pulse {
  0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.65); }
  70% { box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
  100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}

#supportai-status-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
  background-color: #22c55e;
  position: absolute;
  bottom: -1px;
  right: -1px;
  border: 2px solid #ffffff;
  transition: background-color 0.25s ease, box-shadow 0.25s ease;
}

#supportai-status-dot.online {
  background-color: #22c55e;
  animation: supportai-glow-pulse 2s infinite;
}

#supportai-status-dot.connecting {
  background-color: #f59e0b;
  animation: none;
}

#supportai-status-dot.offline,
#supportai-status-dot.error,
#supportai-status-dot.forbidden {
  background-color: #ef4444;
  animation: none;
}

/* Header Action Controls */
.supportai-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.supportai-header-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #ffffff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0.85;
  transition: opacity 0.15s ease, background-color 0.15s ease, transform 0.2s ease;
  user-select: none;
  padding: 0;
}

.supportai-header-btn:hover {
  opacity: 1;
  background-color: rgba(255, 255, 255, 0.18);
}

.supportai-header-btn:active {
  transform: scale(0.92);
}

#supportai-refresh.supportai-spinning svg {
  transform: rotate(360deg);
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

#supportai-refresh {
  font-size: 16px;
}

#supportai-close {
  font-size: 18px;
}

/* Messages area */
#supportai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background-color: #f8fafc;
  display: flex;
  flex-direction: column;
}

#supportai-messages::-webkit-scrollbar {
  width: 5px;
}

#supportai-messages::-webkit-scrollbar-track {
  background: transparent;
}

#supportai-messages::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

/* Message Rows & Entrance Animation */
@keyframes supportai-msg-slide {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.supportai-msg-row {
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  animation: supportai-msg-slide 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.supportai-msg-row.user {
  align-items: flex-end;
}

.supportai-msg-row.ai {
  align-items: flex-start;
}

.supportai-bubble {
  max-width: 82%;
  padding: 10px 14px;
  font-size: 13.5px;
  line-height: 1.5;
  word-break: break-word;
}

.supportai-bubble.ai {
  border-radius: 18px 18px 18px 4px;
  background-color: #ffffff;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
}

.supportai-bubble.user {
  border-radius: 18px 18px 4px 18px;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Discreet Message Timestamps */
.supportai-timestamp {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 4px;
  padding: 0 4px;
  user-select: none;
}

/* Markdown Formatting */
.supportai-bubble strong {
  font-weight: 600;
}

.supportai-bubble em {
  font-style: italic;
}

.supportai-inline-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 5px;
  border-radius: 4px;
}

.supportai-bubble.user .supportai-inline-code {
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.supportai-code-block {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  background: #0f172a;
  color: #f8fafc;
  padding: 10px 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
  border: 1px solid #1e293b;
}

.supportai-code-block code {
  background: transparent;
  padding: 0;
  color: inherit;
}

.supportai-link {
  color: #2563eb;
  text-decoration: underline;
  word-break: break-all;
}

.supportai-bubble.user .supportai-link {
  color: #ffffff;
  text-decoration: underline;
}

.supportai-ul {
  margin: 6px 0;
  padding-left: 20px;
  list-style-type: disc;
}

.supportai-li {
  margin-bottom: 3px;
}

/* Sleek 3-Dot Wave Typing Indicator */
@keyframes supportai-dot-bounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.35;
  }
  30% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

.supportai-typing-bubble {
  padding: 8px 14px !important;
  display: inline-flex;
  align-items: center;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 18px 18px 18px 4px;
}

.supportai-typing-dots {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 16px;
}

.supportai-typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #64748b;
  display: inline-block;
  animation: supportai-dot-bounce 1.3s infinite ease-in-out;
}

.supportai-typing-dot:nth-child(1) {
  animation-delay: 0s;
}

.supportai-typing-dot:nth-child(2) {
  animation-delay: 0.18s;
}

.supportai-typing-dot:nth-child(3) {
  animation-delay: 0.36s;
}

/* Modern Input Area & Pill Capsule */
#supportai-input-area {
  padding: 10px 12px;
  border-top: 1px solid #f1f5f9;
  background-color: #ffffff;
  flex-shrink: 0;
}

.supportai-input-capsule {
  display: flex;
  align-items: center;
  gap: 6px;
  background-color: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 24px;
  padding: 4px 6px 4px 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}

.supportai-input-capsule.is-focused {
  background-color: #ffffff;
}

#supportai-input {
  flex: 1;
  padding: 6px 0;
  border: none !important;
  background: transparent !important;
  font-size: 13px;
  outline: none !important;
  font-family: inherit;
  color: #1e293b;
}

#supportai-input::placeholder {
  color: #94a3b8;
}

#supportai-input:disabled {
  background-color: transparent !important;
  color: #9ca3af;
  cursor: not-allowed;
}

#supportai-send-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease, background-color 0.15s ease;
  flex-shrink: 0;
  color: #ffffff;
  padding: 0;
}

#supportai-send-btn:hover:not(:disabled) {
  transform: scale(1.08) translateY(-1px);
}

#supportai-send-btn:active:not(:disabled) {
  transform: scale(0.92);
}

#supportai-send-btn:disabled {
  opacity: 0.45 !important;
  cursor: not-allowed;
}

#supportai-branding {
  text-align: center;
  padding: 6px;
  font-size: 10px;
  color: #94a3b8;
  border-top: 1px solid #f8fafc;
  background-color: #ffffff;
  flex-shrink: 0;
}

/* =========================================================================
   MOBILE RESPONSIVE MEDIA QUERY (<= 480px)
   ========================================================================= */
@media (max-width: 480px) {
  #supportai-chat {
    width: calc(100vw - 24px) !important;
    height: calc(100vh - 96px) !important;
    height: calc(100dvh - 96px) !important;
    bottom: 80px !important;
    left: 12px !important;
    right: 12px !important;
    max-width: none !important;
    max-height: none !important;
    border-radius: 12px !important;
    padding-bottom: env(safe-area-inset-bottom, 0px) !important;
  }

  #supportai-btn {
    bottom: 16px !important;
    width: 50px !important;
    height: 50px !important;
  }

  #supportai-btn.supportai-pos-right {
    right: 16px !important;
    left: auto !important;
  }

  #supportai-btn.supportai-pos-left {
    left: 16px !important;
    right: auto !important;
  }

  /* CRITICAL: 16px font-size prevents iOS Safari WebKit automatic viewport zoom */
  #supportai-input {
    font-size: 16px !important;
    padding: 10px 12px !important;
  }

  #supportai-send-btn {
    font-size: 14px !important;
    padding: 10px 16px !important;
  }
}
    `.trim();

    (document.head || document.documentElement || document.body).appendChild(style);
  }

  // 8. Status configuration
  const STATUS_CONFIG = {
    online: { color: '#22c55e', title: 'Online', className: 'online', label: 'Active now' },
    connecting: { color: '#f59e0b', title: 'Connecting...', className: 'connecting', label: 'Connecting...' },
    error: { color: '#ef4444', title: 'Offline / Error', className: 'error', label: 'Offline' },
    forbidden: { color: '#ef4444', title: 'Domain not authorized', className: 'forbidden', label: 'Unauthorized' },
  };

  // 9. Core SupportAI object
  const SupportAI = {
    config: null,
    container: null,
    iframe: null,
    isOpen: false,
    isInitialized: false,
    _initializing: false,
    isForbidden: false,
    currentStatus: 'online',
    currentTitle: 'Online',
    resetChat: null,
    autoOpenTimer: null,

    setStatus(state, customTitle) {
      this.currentStatus = state;
      const cfg = STATUS_CONFIG[state] || STATUS_CONFIG.online;
      const title = customTitle || cfg.title;
      this.currentTitle = title;

      if (typeof document !== 'undefined') {
        const dot = document.getElementById('supportai-status-dot');
        if (dot) {
          dot.style.backgroundColor = cfg.color;
          dot.title = title;
          dot.className = cfg.className;
        }
        const label = document.getElementById('supportai-status-label');
        if (label) {
          label.textContent = cfg.label;
        }
      }
    },

    handleDomainForbidden(msgs, input, sendBtn) {
      this.isForbidden = true;
      this.setStatus('forbidden');

      if (typeof document !== 'undefined') {
        const indicator = document.getElementById('supportai-typing-indicator');
        if (indicator) indicator.remove();

        const messagesContainer = msgs || document.getElementById('supportai-messages');
        if (messagesContainer && !document.getElementById('supportai-domain-warning')) {
          const banner = document.createElement('div');
          banner.id = 'supportai-domain-warning';
          Object.assign(banner.style, {
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '12px',
            padding: '12px 14px',
            fontSize: '13px',
            lineHeight: '1.4',
            color: '#991b1b',
            marginBottom: '12px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px',
            boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)',
          });
          banner.innerHTML = `
            <span style="font-size:16px;line-height:1;flex-shrink:0;">⚠️</span>
            <div>
              <strong style="display:block;margin-bottom:2px;font-weight:600;">Domain not authorized</strong>
              <span>Please whitelist this domain in your SupportAI Widget Configuration.</span>
            </div>
          `;
          messagesContainer.appendChild(banner);
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        const inputEl = input || document.getElementById('supportai-input');
        if (inputEl) {
          inputEl.disabled = true;
          inputEl.placeholder = 'Chat disabled: unauthorized domain';
          inputEl.style.backgroundColor = '#f3f4f6';
          inputEl.style.cursor = 'not-allowed';
          inputEl.style.borderColor = '#e5e7eb';
        }

        const btnEl = sendBtn || document.getElementById('supportai-send-btn');
        if (btnEl) {
          btnEl.disabled = true;
          btnEl.style.opacity = '0.5';
          btnEl.style.cursor = 'not-allowed';
        }
      }
    },

    init(options = {}) {
      const key = options.apiKey || options.businessKey || options.publicKey;
      if (!key) {
        console.error('SupportAI: apiKey is required');
        return;
      }

      // Idempotency check: if already initialized or currently initializing, do not duplicate
      if (this.isInitialized || this._initializing) {
        console.warn('SupportAI: Already initialized or initialization in progress.');
        return;
      }

      if (typeof document !== 'undefined' && (document.getElementById('supportai-btn') || document.getElementById('supportai-chat'))) {
        console.warn('SupportAI: Widget elements already present in DOM.');
        this.isInitialized = true;
        return;
      }

      this._initializing = true;

      const scriptEl = getWidgetScript();
      const serverUrl = extractServerUrl(scriptEl, options.serverUrl);
      const position = options.position || (scriptEl && (scriptEl.getAttribute('data-position') || (scriptEl.dataset && scriptEl.dataset.position))) || 'bottom-right';

      this.config = {
        apiKey: key,
        serverUrl: serverUrl,
        position: position,
        zIndex: 99999,
      };

      injectStyles();

      onDOMReady(() => {
        this.loadConfig()
          .then(() => {
            if (!this._initializing || !this.config) return;
            this.createWidget();
            this.isInitialized = true;
            this._initializing = false;
          })
          .catch((err) => {
            if (!this._initializing || !this.config) return;
            console.error('SupportAI: Failed to load configuration', err);
            this.createWidget();
            this.isInitialized = true;
            this._initializing = false;
          });
      });
    },

    async loadConfig() {
      if (!this.config) return { cancelled: true };
      try {
        this.setStatus('connecting');
        const res = await fetch(`${this.config.serverUrl}/api/widget/embed/${this.config.apiKey}`);
        if (!this.config) return { cancelled: true };
        if (res.status === 403) {
          this.isForbidden = true;
          this.setStatus('forbidden');
          this.handleDomainForbidden();
          return { forbidden: true };
        }
        if (res.ok) {
          const data = await res.json();
          if (this.config) {
            Object.assign(this.config, data);
          }
          this.isForbidden = false;
          this.setStatus('online');
          return { ok: true };
        }
        this.setStatus('error');
        return { error: true, status: res.status };
      } catch (e) {
        if (!this.config) return { cancelled: true };
        console.error('SupportAI: Failed to load config', e);
        this.setStatus('error');
        return { error: true };
      }
    },

    createWidget() {
      if (typeof document === 'undefined') return;
      if (!this.config) return;
      if (!document.body) {
        onDOMReady(() => this.createWidget());
        return;
      }

      // Prevent duplicate DOM element creation
      if (document.getElementById('supportai-btn') || document.getElementById('supportai-chat')) {
        return;
      }

      injectStyles();

      const primaryColor = this.config.primary_color || this.config.primaryColor || '#6366f1';
      const darkColor = darkenColor(primaryColor, 14);
      const position = this.config.position || 'bottom-right';
      const isRight = position === 'bottom-right';
      const posClass = isRight ? 'supportai-pos-right' : 'supportai-pos-left';

      // Floating launcher button with morphing SVG transition
      const btn = document.createElement('div');
      btn.id = 'supportai-btn';
      btn.className = posClass;
      btn.style.backgroundColor = primaryColor;
      btn.style.background = `linear-gradient(135deg, ${primaryColor} 0%, ${darkColor} 100%)`;
      btn.setAttribute('role', 'button');
      btn.setAttribute('aria-label', 'Open support chat');
      btn.innerHTML = `
        <svg class="supportai-icon-bubble" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
        </svg>
        <svg class="supportai-icon-close" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      `;
      btn.onclick = () => this.toggle();
      document.body.appendChild(btn);

      // Chat container window
      const chat = document.createElement('div');
      chat.id = 'supportai-chat';
      chat.className = posClass;
      chat.style.display = this.isOpen ? 'flex' : 'none';

      let conversationId = null;
      let activeRequestId = 0;

      // Modern Header with Avatar, Status Dot, Subtitle, and Crisp SVG Actions
      const header = document.createElement('div');
      header.id = 'supportai-header';
      header.style.backgroundColor = primaryColor;
      header.style.background = `linear-gradient(135deg, ${primaryColor} 0%, ${darkColor} 100%)`;

      const initialStatus = this.currentStatus || 'online';
      const initialCfg = STATUS_CONFIG[initialStatus] || STATUS_CONFIG.online;
      const initialColor = initialCfg.color;
      const initialTitle = this.currentTitle || initialCfg.title;
      const initialClass = initialCfg.className;
      const initialLabel = initialCfg.label || 'Active now';

      header.innerHTML = `
        <div class="supportai-header-left">
          <div class="supportai-avatar-wrapper">
            <div id="supportai-avatar" class="supportai-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="3"></rect>
                <circle cx="12" cy="5" r="2"></circle>
                <path d="M12 7v4"></path>
                <line x1="8" y1="16" x2="8" y2="16.01"></line>
                <line x1="16" y1="16" x2="16" y2="16.01"></line>
              </svg>
            </div>
            <div id="supportai-status-dot" class="${initialClass}" title="${initialTitle}" style="background-color:${initialColor};"></div>
          </div>
          <div class="supportai-header-text">
            <span id="supportai-bot-name">${this.config.bot_name || 'Support Assistant'}</span>
            <div class="supportai-status-subtext">
              <span id="supportai-status-label" class="supportai-status-label">${initialLabel}</span>
            </div>
          </div>
        </div>
        <div class="supportai-header-actions">
          <button id="supportai-refresh" class="supportai-header-btn" title="Start new chat" role="button" aria-label="Start new chat">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
            </svg>
          </button>
          <button id="supportai-close" class="supportai-header-btn" title="Close" role="button" aria-label="Close chat">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
        </div>
      `;
      chat.appendChild(header);

      // Messages area
      const msgs = document.createElement('div');
      msgs.id = 'supportai-messages';

      const showWelcome = () => {
        msgs.innerHTML = '';
        if (Array.isArray(msgs.children)) msgs.children = [];
        const row = document.createElement('div');
        row.className = 'supportai-msg-row ai';

        const welcome = document.createElement('div');
        welcome.className = 'supportai-bubble ai';
        const welcomeText = this.config.welcome_message || 'Hi! How can I help you today?';
        welcome.textContent = welcomeText;
        welcome.innerHTML = formatMarkdown(welcomeText);

        row.appendChild(welcome);

        const ts = document.createElement('span');
        ts.className = 'supportai-timestamp';
        ts.textContent = formatTimestamp(new Date());
        row.appendChild(ts);

        msgs.appendChild(row);
        msgs.scrollTop = msgs.scrollHeight;
      };
      showWelcome();
      chat.appendChild(msgs);

      // Input area with rounded pill capsule
      const inputArea = document.createElement('div');
      inputArea.id = 'supportai-input-area';

      const capsule = document.createElement('div');
      capsule.className = 'supportai-input-capsule';

      const input = document.createElement('input');
      input.id = 'supportai-input';
      input.placeholder = this.config.placeholder_text || 'Type your question...';

      input.onfocus = () => {
        if (!input.disabled) {
          input.style.borderColor = primaryColor;
          addClass(capsule, 'is-focused');
          capsule.style.borderColor = primaryColor;
          capsule.style.boxShadow = `0 0 0 3px rgba(99, 102, 241, 0.15)`;
        }
      };
      input.onblur = () => {
        if (!input.disabled) {
          input.style.borderColor = '#d1d5db';
          removeClass(capsule, 'is-focused');
          capsule.style.borderColor = '#e2e8f0';
          capsule.style.boxShadow = 'none';
        }
      };

      const sendBtn = document.createElement('button');
      sendBtn.id = 'supportai-send-btn';
      sendBtn.style.backgroundColor = primaryColor;
      sendBtn.style.background = `linear-gradient(135deg, ${primaryColor} 0%, ${darkColor} 100%)`;
      sendBtn.setAttribute('aria-label', 'Send message');
      sendBtn.setAttribute('title', 'Send message');
      sendBtn.innerHTML = `
        <svg class="supportai-send-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      `;

      const sendMessage = async () => {
        const text = input.value.trim();
        if (!text || input.disabled) return;

        this.addMessage(msgs, text, 'user', primaryColor);
        input.value = '';

        this.setStatus('connecting');
        sendBtn.disabled = true;

        // Render sleek 3-dot wave typing indicator
        const typingRow = document.createElement('div');
        typingRow.id = 'supportai-typing-indicator';
        typingRow.className = 'supportai-msg-row ai';
        typingRow.innerHTML = `
          <div class="supportai-bubble ai supportai-typing-bubble">
            <div class="supportai-typing-dots">
              <span class="supportai-typing-dot"></span>
              <span class="supportai-typing-dot"></span>
              <span class="supportai-typing-dot"></span>
            </div>
          </div>
        `;
        msgs.appendChild(typingRow);
        msgs.scrollTop = msgs.scrollHeight;

        const removeTyping = () => {
          const el = document.getElementById('supportai-typing-indicator');
          if (el) el.remove();
        };

        const currentRequestId = ++activeRequestId;

        try {
          const res = await fetch(`${this.config.serverUrl}/api/chat/${this.config.apiKey}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: text,
              conversation_id: conversationId,
            }),
          });

          if (currentRequestId !== activeRequestId) {
            removeTyping();
            return;
          }

          if (res.status === 403) {
            removeTyping();
            this.handleDomainForbidden(msgs, input, sendBtn);
            return;
          }

          const data = await res.json();
          if (currentRequestId !== activeRequestId) {
            removeTyping();
            return;
          }

          removeTyping();

          if (!res.ok) {
            this.setStatus('error');
            this.addMessage(msgs, data.detail || 'Error: Could not get a response from AI agent.', 'ai', primaryColor);
            sendBtn.disabled = false;
            return;
          }

          this.setStatus(data.error_code ? 'error' : 'online');
          conversationId = data.conversation_id;
          const assistantReply = [
            data.message || 'I could not complete that request. Please try again.',
            data.action_hint,
          ].filter(Boolean).join('\n\n');
          this.addMessage(msgs, assistantReply, 'ai', primaryColor);
          sendBtn.disabled = false;
        } catch (e) {
          if (currentRequestId !== activeRequestId) {
            removeTyping();
            return;
          }
          removeTyping();
          console.error('SupportAI widget error:', e);
          this.setStatus('error');
          this.addMessage(
            msgs,
            'Connection error: Could not connect to SupportAI server at ' +
              this.config.serverUrl +
              '. Please check that the server is running and CORS is enabled.',
            'ai',
            primaryColor
          );
          sendBtn.disabled = false;
        }
      };

      sendBtn.onclick = sendMessage;
      input.onkeydown = (e) => {
        if (e && e.key === 'Enter' && !e.shiftKey) {
          if (typeof e.preventDefault === 'function') e.preventDefault();
          sendMessage();
        }
      };

      capsule.appendChild(input);
      capsule.appendChild(sendBtn);
      inputArea.appendChild(capsule);
      chat.appendChild(inputArea);

      // Branding
      if (this.config.show_branding !== false) {
        const brand = document.createElement('div');
        brand.id = 'supportai-branding';
        brand.textContent = 'Powered by SupportAI';
        chat.appendChild(brand);
      }

      // Close & Reset actions
      header.querySelector('#supportai-close').onclick = () => this.toggle();

      const resetAction = async () => {
        activeRequestId++;
        conversationId = null;
        input.value = '';

        // Spin animation on refresh icon
        const refreshEl = header.querySelector('#supportai-refresh');
        if (refreshEl) {
          addClass(refreshEl, 'supportai-spinning');
          setTimeout(() => removeClass(refreshEl, 'supportai-spinning'), 600);
        }

        // Remove typing indicator if present
        const indicator = document.getElementById('supportai-typing-indicator');
        if (indicator) indicator.remove();

        // If previously forbidden, re-check config in case domain was whitelisted
        if (this.isForbidden) {
          this.setStatus('connecting');
          const result = await this.loadConfig();
          if (result && result.forbidden) {
            this.handleDomainForbidden(msgs, input, sendBtn);
            return;
          }
        }

        // Restore input states
        input.disabled = false;
        input.placeholder = this.config.placeholder_text || 'Type your question...';
        input.style.backgroundColor = '';
        input.style.cursor = '';
        input.style.borderColor = '#d1d5db';

        // Restore send button state
        sendBtn.disabled = false;
        sendBtn.style.opacity = '1';
        sendBtn.style.cursor = 'pointer';

        // Remove domain warning banner if present
        const warning = document.getElementById('supportai-domain-warning');
        if (warning) warning.remove();

        // Restore online status
        this.setStatus('online');

        // Clear messages and re-render welcome greeting
        showWelcome();
      };

      header.querySelector('#supportai-refresh').onclick = resetAction;
      this.resetChat = resetAction;

      document.body.appendChild(chat);
      this.container = chat;

      // If forbidden was already flagged during loadConfig, apply UI state immediately
      if (this.isForbidden) {
        this.handleDomainForbidden(msgs, input, sendBtn);
      } else {
        this.setStatus(initialStatus, initialTitle);
        const delay = this.getAutoOpenDelay();
        if (delay > 0) {
          this.autoOpenTimer = setTimeout(() => {
            this.autoOpenTimer = null;
            if (this.isInitialized && !this.isForbidden && !this.isOpen) this.open();
          }, delay);
        }
      }
    },

    getAutoOpenDelay() {
      const value = this.config && this.config.auto_open_delay;
      if (value === null || value === undefined || value === '') return 0;
      const match = String(value).trim().match(/^(\d+(?:\.\d+)?)\s*(ms|s)?$/i);
      if (!match) return 0;
      const amount = Number(match[1]);
      if (!Number.isFinite(amount) || amount <= 0) return 0;
      const milliseconds = (match[2] && match[2].toLowerCase() === 'ms') ? amount : amount * 1000;
      return Math.min(milliseconds, 60000);
    },

    addMessage(container, text, role, primaryColor) {
      if (!container) return;

      const isUser = role === 'user';
      const row = document.createElement('div');
      row.className = 'supportai-msg-row ' + (isUser ? 'user' : 'ai');

      const bubble = document.createElement('div');
      bubble.className = 'supportai-bubble ' + (isUser ? 'user' : 'ai');
      if (isUser) {
        const darkColor = darkenColor(primaryColor, 14);
        bubble.style.backgroundColor = primaryColor;
        bubble.style.background = `linear-gradient(135deg, ${primaryColor} 0%, ${darkColor} 100%)`;
      }
      bubble.textContent = text;
      bubble.innerHTML = formatMarkdown(text);

      row.appendChild(bubble);

      const ts = document.createElement('span');
      ts.className = 'supportai-timestamp';
      ts.textContent = formatTimestamp(new Date());
      row.appendChild(ts);

      container.appendChild(row);
      container.scrollTop = container.scrollHeight;
    },

    open() {
      if (this.autoOpenTimer) {
        clearTimeout(this.autoOpenTimer);
        this.autoOpenTimer = null;
      }
      this.isOpen = true;
      if (this.container) {
        this.container.style.display = 'flex';
      }
      const btn = typeof document !== 'undefined' ? document.getElementById('supportai-btn') : null;
      if (btn) {
        addClass(btn, 'is-open');
        btn.setAttribute('aria-label', 'Close support chat');
      }
    },

    close() {
      if (this.autoOpenTimer) {
        clearTimeout(this.autoOpenTimer);
        this.autoOpenTimer = null;
      }
      this.isOpen = false;
      if (this.container) {
        this.container.style.display = 'none';
      }
      const btn = typeof document !== 'undefined' ? document.getElementById('supportai-btn') : null;
      if (btn) {
        removeClass(btn, 'is-open');
        btn.setAttribute('aria-label', 'Open support chat');
      }
    },

    toggle() {
      if (this.isOpen) {
        this.close();
      } else {
        this.open();
      }
    },

    reset() {
      if (typeof this.resetChat === 'function') {
        this.resetChat();
      }
    },

    destroy() {
      if (this.autoOpenTimer) {
        clearTimeout(this.autoOpenTimer);
        this.autoOpenTimer = null;
      }
      if (typeof document !== 'undefined') {
        const btn = document.getElementById('supportai-btn');
        if (btn) btn.remove();
        const chat = document.getElementById('supportai-chat');
        if (chat) chat.remove();
        const styles = document.getElementById('supportai-styles');
        if (styles) styles.remove();
      }
      this.container = null;
      this.config = null;
      this.isOpen = false;
      this.isInitialized = false;
      this._initializing = false;
      this.isForbidden = false;
      this.currentStatus = 'online';
      this.currentTitle = 'Online';
      this.resetChat = null;
      this.autoOpenTimer = null;
    },
  };

  // 10. Auto-initialization entry point
  function autoInit() {
    const scriptEl = getWidgetScript();
    const credentials = extractCredentials(scriptEl);
    if (!credentials) {
      // No credentials on script tag; gracefully await manual SupportAI.init()
      return;
    }

    SupportAI.init({
      apiKey: credentials,
    });
  }

  // Expose global SupportAI namespace
  if (typeof window !== 'undefined') {
    window.SupportAI = SupportAI;
  }

  // Run autoInit on DOM ready
  onDOMReady(autoInit);
})();
