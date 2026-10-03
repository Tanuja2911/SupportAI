/**
 * Automated Verification Test Suite for Milestone 4:
 * Pure 1-Line Self-Initializing Embed Widget & Mobile UI (widget/widget.js)
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const widgetJsPath = path.resolve(__dirname, 'widget.js');
const widgetSource = fs.readFileSync(widgetJsPath, 'utf8');

console.log('--- STARTING WIDGET AUTOMATED VERIFICATION ---');

// Helper to flush asynchronous microtasks and timers
const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 10));

// =========================================================================
// TEST 1: Static Code Inspection & Required Token Signatures
// =========================================================================
console.log('Test 1: Static Code Inspection & Required Token Signatures');

// Tier 1 & Tier 4 backend assertions compatibility
assert(
  widgetSource.includes('scripts[i].src') || widgetSource.includes('currentScript'),
  'Must include scripts[i].src or currentScript'
);
assert(
  widgetSource.includes('detectedServerUrl') || widgetSource.includes('serverUrl'),
  'Must include detectedServerUrl or serverUrl'
);
assert(widgetSource.includes('window.SupportAI'), 'Must expose window.SupportAI');
assert(widgetSource.includes('/api/widget/embed/'), 'Must call /api/widget/embed/');
assert(widgetSource.includes('/api/chat/'), 'Must call /api/chat/');
assert(widgetSource.includes('primary_color') || widgetSource.includes('primaryColor'), 'Must reference primary color');
assert(widgetSource.includes('data-business-key'), 'Must support data-business-key');
assert(widgetSource.includes('data-api-key'), 'Must support data-api-key fallback');

// Scoped styles & responsive media query
assert(widgetSource.includes('id="supportai-styles"'), 'Must define style tag with id supportai-styles');
assert(widgetSource.includes('@media (max-width: 480px)'), 'Must define mobile media query (max-width: 480px)');
assert(widgetSource.includes('calc(100vw - 24px) !important'), 'Must define mobile width calc(100vw - 24px)');
assert(
  widgetSource.includes('calc(100vh - 96px) !important') || widgetSource.includes('calc(100dvh - 96px) !important'),
  'Must define mobile height'
);
assert(widgetSource.includes('16px !important'), 'Must define 16px input font size to prevent iOS Safari auto-zoom');
assert(widgetSource.includes('supportai-status-dot'), 'Must define status dot element id');
assert(widgetSource.includes('supportai-domain-warning'), 'Must define domain warning banner id');
assert(widgetSource.includes('Domain not authorized'), 'Must define domain unauthorized message');
assert(widgetSource.includes('supportai-refresh'), 'Must define refresh button id');

console.log('  ✓ Test 1 Passed: All required tokens and static signatures present.');

// =========================================================================
// MOCK DOM HARNESS
// =========================================================================
class MockElement {
  constructor(tagName, id = '') {
    this.tagName = tagName.toUpperCase();
    this.id = id;
    this.style = {};
    this.dataset = {};
    this.attributes = {};
    this.children = [];
    this.parentNode = null;
    this.textContent = '';
    this._innerHTML = '';
    this.className = '';
    this.title = '';
    this.disabled = false;
    this.placeholder = '';
    this.value = '';
    this.eventListeners = {};
  }

  get innerHTML() {
    return this._innerHTML;
  }

  set innerHTML(html) {
    this._innerHTML = html;
    // Simple child parser for IDs
    const idMatches = [...html.matchAll(/id="([^"]+)"/g)];
    for (const match of idMatches) {
      const childId = match[1];
      if (!this.querySelector('#' + childId)) {
        const childEl = new MockElement('DIV', childId);
        this.appendChild(childEl);
      }
    }
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name.startsWith('data-')) {
      const camelKey = name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      this.dataset[camelKey] = String(value);
    }
    if (name === 'id') this.id = String(value);
    if (name === 'class') this.className = String(value);
  }

  getAttribute(name) {
    return this.attributes[name] || null;
  }

  hasAttribute(name) {
    return name in this.attributes;
  }

  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }

  remove() {
    if (this.parentNode) {
      const idx = this.parentNode.children.indexOf(this);
      if (idx !== -1) {
        this.parentNode.children.splice(idx, 1);
      }
      this.parentNode = null;
    }
  }

  querySelector(selector) {
    if (selector.startsWith('#')) {
      const targetId = selector.slice(1);
      if (this.id === targetId) return this;
      for (const child of this.children) {
        const found = child.querySelector(selector);
        if (found) return found;
      }
      return null;
    }
    return null;
  }

  addEventListener(event, fn) {
    if (!this.eventListeners[event]) this.eventListeners[event] = [];
    this.eventListeners[event].push(fn);
  }
}

function createMockEnvironment(options = {}) {
  const head = new MockElement('HEAD', 'head');
  const body = new MockElement('BODY', 'body');
  const root = new MockElement('HTML', 'html');
  root.appendChild(head);
  root.appendChild(body);

  const scripts = [];

  const documentMock = {
    readyState: options.readyState || 'complete',
    head: head,
    body: body,
    documentElement: root,
    currentScript: null,
    createElement(tag) {
      return new MockElement(tag);
    },
    getElementById(id) {
      function search(node) {
        if (node.id === id) return node;
        for (const child of node.children) {
          const res = search(child);
          if (res) return res;
        }
        return null;
      }
      return search(root);
    },
    getElementsByTagName(tag) {
      tag = tag.toUpperCase();
      const results = [];
      function search(node) {
        if (node.tagName === tag) results.push(node);
        for (const child of node.children) search(child);
      }
      search(root);
      return results;
    },
    querySelector(sel) {
      if (sel.startsWith('#')) return this.getElementById(sel.slice(1));
      if (sel.includes('data-business-key')) {
        for (const s of scripts) {
          if (s.hasAttribute('data-business-key')) return s;
        }
      }
      if (sel.includes('data-api-key')) {
        for (const s of scripts) {
          if (s.hasAttribute('data-api-key')) return s;
        }
      }
      if (sel.includes('widget.js')) {
        for (const s of scripts) {
          if (s.src && s.src.includes('widget.js')) return s;
        }
      }
      return null;
    },
    querySelectorAll(sel) {
      const match = this.querySelector(sel);
      return match ? [match] : [];
    },
    addEventListener(event, fn) {
      if (!this._listeners) this._listeners = {};
      if (!this._listeners[event]) this._listeners[event] = [];
      this._listeners[event].push(fn);
    },
    trigger(event) {
      if (this._listeners && this._listeners[event]) {
        for (const fn of this._listeners[event]) fn();
      }
    },
  };

  const mockFetch = options.fetch || (async () => ({ ok: true, status: 200, json: async () => ({}) }));

  const windowMock = {
    location: {
      origin: options.origin || 'http://localhost:3000',
      href: (options.origin || 'http://localhost:3000') + '/index.html',
    },
    fetch: mockFetch,
  };

  windowMock.document = documentMock;

  if (options.scriptTag) {
    const s = new MockElement('SCRIPT');
    if (options.scriptTag.src) s.src = options.scriptTag.src;
    for (const [k, v] of Object.entries(options.scriptTag.attrs || {})) {
      s.setAttribute(k, v);
    }
    scripts.push(s);
    head.appendChild(s);
    if (options.isCurrentScript) {
      documentMock.currentScript = s;
    }
  }

  const context = vm.createContext({
    window: windowMock,
    document: documentMock,
    fetch: mockFetch,
    URL: URL,
    console: console,
    setTimeout: setTimeout,
  });

  return { context, windowMock, documentMock };
}

async function runTests() {
  // =========================================================================
  // TEST 2: Pure 1-Line Self-Initialization via document.currentScript
  // =========================================================================
  console.log('Test 2: Pure 1-Line Self-Initialization via document.currentScript');
  {
    let configFetchedUrl = null;
    const mockFetch = async (url) => {
      configFetchedUrl = url;
      return {
        ok: true,
        status: 200,
        json: async () => ({
          business_id: 1,
          bot_name: 'AI Support Robot',
          primary_color: '#10b981',
          welcome_message: 'Welcome to automated test!',
        }),
      };
    };

    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'https://myshop.com',
      scriptTag: {
        src: 'https://support.mycompany.io/widget/widget.js',
        attrs: { 'data-business-key': 'pk_live_abcd1234efgh' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    // Assert global namespace
    assert(windowMock.SupportAI, 'window.SupportAI must be defined');
    assert.strictEqual(windowMock.SupportAI.config.apiKey, 'pk_live_abcd1234efgh');
    assert.strictEqual(windowMock.SupportAI.config.serverUrl, 'https://support.mycompany.io');

    // Assert DOM elements injected
    const styleEl = documentMock.getElementById('supportai-styles');
    assert(styleEl, '#supportai-styles should be injected');
    assert(styleEl.textContent.includes('@media (max-width: 480px)'));
    assert(styleEl.textContent.includes('16px !important'));

    const btnEl = documentMock.getElementById('supportai-btn');
    assert(btnEl, '#supportai-btn should be injected');

    const chatEl = documentMock.getElementById('supportai-chat');
    assert(chatEl, '#supportai-chat should be injected');

    console.log('  ✓ Test 2 Passed: Pure 1-line self-init successfully mounted widget with server origin and styles.');
  }

  // =========================================================================
  // TEST 3: Fallback Credential Extraction (data-api-key)
  // =========================================================================
  console.log('Test 3: Fallback Credential Extraction (data-api-key)');
  {
    const { context, windowMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-api-key': 'pk_fallback_key_999' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert(windowMock.SupportAI);
    assert.strictEqual(windowMock.SupportAI.config.apiKey, 'pk_fallback_key_999');
    assert.strictEqual(windowMock.SupportAI.config.serverUrl, 'http://localhost:8000');

    console.log('  ✓ Test 3 Passed: Successfully extracted credentials from data-api-key fallback.');
  }

  // =========================================================================
  // TEST 4: Graceful Standby without Script Attributes & Manual SupportAI.init()
  // =========================================================================
  console.log('Test 4: Graceful Standby & Manual SupportAI.init() Backward Compatibility');
  {
    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: {}, // No credentials
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    // Widget should NOT auto-init without credentials
    assert(windowMock.SupportAI, 'window.SupportAI must be defined');
    assert.strictEqual(windowMock.SupportAI.isInitialized, false);
    assert.strictEqual(documentMock.getElementById('supportai-btn'), null);

    // Manual init (as in WidgetTestView.vue)
    windowMock.SupportAI.init({
      apiKey: 'pk_manual_view_key',
      serverUrl: 'http://custom-api:9000',
    });
    await flushPromises();

    assert.strictEqual(windowMock.SupportAI.config.apiKey, 'pk_manual_view_key');
    assert.strictEqual(windowMock.SupportAI.config.serverUrl, 'http://custom-api:9000');
    assert(documentMock.getElementById('supportai-btn'), '#supportai-btn injected after manual init');

    console.log('  ✓ Test 4 Passed: Gracefully stood by, then initialized via manual SupportAI.init().');
  }

  // =========================================================================
  // TEST 5: Robust Idempotency Protection
  // =========================================================================
  console.log('Test 5: Idempotency Protection Against Duplicate Calls');
  {
    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_idempotent_123' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const initialBtn = documentMock.getElementById('supportai-btn');
    const initialChat = documentMock.getElementById('supportai-chat');
    assert(initialBtn);

    // Call init again with different parameters
    windowMock.SupportAI.init({ apiKey: 'pk_attempt_duplicate' });
    await flushPromises();

    // Element references should NOT have been re-created or duplicated
    assert.strictEqual(documentMock.getElementById('supportai-btn'), initialBtn);
    assert.strictEqual(documentMock.getElementById('supportai-chat'), initialChat);
    assert.strictEqual(windowMock.SupportAI.config.apiKey, 'pk_idempotent_123');

    console.log('  ✓ Test 5 Passed: Idempotency guards prevented duplicate element creation.');
  }

  // =========================================================================
  // TEST 6: Connection Status Dot Transitions
  // =========================================================================
  console.log('Test 6: Connection Status Dot Transitions');
  {
    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_status_test' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const dot = documentMock.getElementById('supportai-status-dot');
    assert(dot, 'Status dot #supportai-status-dot must exist in header');

    // Initial is online
    assert.strictEqual(dot.style.backgroundColor, '#22c55e');
    assert.strictEqual(dot.title, 'Online');

    // Change to connecting
    windowMock.SupportAI.setStatus('connecting');
    assert.strictEqual(dot.style.backgroundColor, '#f59e0b');
    assert.strictEqual(dot.title, 'Connecting...');

    // Change to error
    windowMock.SupportAI.setStatus('error');
    assert.strictEqual(dot.style.backgroundColor, '#ef4444');
    assert.strictEqual(dot.title, 'Offline / Error');

    // Change to forbidden
    windowMock.SupportAI.setStatus('forbidden');
    assert.strictEqual(dot.style.backgroundColor, '#ef4444');
    assert.strictEqual(dot.title, 'Domain not authorized');

    console.log('  ✓ Test 6 Passed: Status dot transitioned smoothly across all 4 operational states.');
  }

  // =========================================================================
  // TEST 7: HTTP 403 Forbidden Origin Guard Handling
  // =========================================================================
  console.log('Test 7: HTTP 403 Forbidden Origin Guard Handling');
  {
    const mock403Fetch = async (url) => {
      return {
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Origin not allowed' }),
      };
    };

    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'https://unauthorized-domain.com',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_blocked_test' },
      },
      isCurrentScript: true,
      fetch: mock403Fetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    // Status dot should be red with 'Domain not authorized'
    const dot = documentMock.getElementById('supportai-status-dot');
    assert.strictEqual(dot.style.backgroundColor, '#ef4444');
    assert.strictEqual(dot.title, 'Domain not authorized');

    // Warning banner must be present
    const warning = documentMock.getElementById('supportai-domain-warning');
    assert(warning, '#supportai-domain-warning banner should be rendered');
    assert(warning.innerHTML.includes('Domain not authorized'));
    assert(warning.innerHTML.includes('Please whitelist this domain in your SupportAI Widget Configuration.'));

    // Input and button disabled
    const input = documentMock.getElementById('supportai-input');
    assert.strictEqual(input.disabled, true);
    assert.strictEqual(input.placeholder, 'Chat disabled: unauthorized domain');

    const sendBtn = documentMock.getElementById('supportai-send-btn');
    assert.strictEqual(sendBtn.disabled, true);

    console.log('  ✓ Test 7 Passed: 403 Forbidden correctly triggered red dot, warning banner, and disabled inputs.');
  }

  // =========================================================================
  // TEST 8: Chat Reset & Lifecycle Restoration
  // =========================================================================
  console.log('Test 8: Chat Reset & Lifecycle Restoration');
  {
    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_reset_test' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    // Trigger forbidden state
    windowMock.SupportAI.handleDomainForbidden();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const dot = documentMock.getElementById('supportai-status-dot');

    assert.strictEqual(input.disabled, true);
    assert.strictEqual(dot.style.backgroundColor, '#ef4444');

    // Trigger Reset
    windowMock.SupportAI.reset();
    await flushPromises();

    assert.strictEqual(input.disabled, false);
    assert.strictEqual(sendBtn.disabled, false);
    assert.strictEqual(dot.style.backgroundColor, '#22c55e');
    assert.strictEqual(dot.title, 'Online');
    assert.strictEqual(documentMock.getElementById('supportai-domain-warning'), null, 'Warning banner removed');

    console.log('  ✓ Test 8 Passed: Reset successfully restored input, send button, status dot, and removed warning.');
  }

  // =========================================================================
  // TEST 9: Programmatic API (open, close, toggle, destroy)
  // =========================================================================
  console.log('Test 9: Programmatic API (open, close, toggle, destroy)');
  {
    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_api_test' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const chat = documentMock.getElementById('supportai-chat');
    assert.strictEqual(chat.style.display, 'none');

    windowMock.SupportAI.open();
    assert.strictEqual(chat.style.display, 'flex');

    windowMock.SupportAI.close();
    assert.strictEqual(chat.style.display, 'none');

    windowMock.SupportAI.toggle();
    assert.strictEqual(chat.style.display, 'flex');

    windowMock.SupportAI.destroy();
    assert.strictEqual(documentMock.getElementById('supportai-btn'), null);
    assert.strictEqual(documentMock.getElementById('supportai-chat'), null);
    assert.strictEqual(documentMock.getElementById('supportai-styles'), null);
    assert.strictEqual(windowMock.SupportAI.isInitialized, false);

    console.log('  ✓ Test 9 Passed: Programmatic API methods open/close/toggle/destroy all functioned as expected.');
  }

  // =========================================================================
  // TEST 10: In-flight Connecting Status during sendMessage & Success Online
  // =========================================================================
  console.log('Test 10: In-flight Connecting Status during sendMessage & Success Online');
  {
    let resolveChat;
    const pendingChatPromise = new Promise((resolve) => {
      resolveChat = resolve;
    });

    const mockChatFetch = async (url, opts) => {
      if (url.includes('/api/chat/')) {
        return pendingChatPromise;
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_chat_test' },
      },
      isCurrentScript: true,
      fetch: mockChatFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const dot = documentMock.getElementById('supportai-status-dot');

    input.value = 'Hello support!';
    // Trigger click on sendBtn
    sendBtn.onclick();

    // While request is in-flight:
    assert.strictEqual(dot.style.backgroundColor, '#f59e0b', 'Status dot is amber while sending');
    assert.strictEqual(dot.title, 'Connecting...', 'Status dot title is Connecting...');
    assert.strictEqual(sendBtn.disabled, true, 'Send button is disabled while in flight');

    // Resolve chat response
    resolveChat({
      ok: true,
      status: 200,
      json: async () => ({
        conversation_id: 'conv_12345',
        message: 'Hello! How can I assist you?',
      }),
    });
    await flushPromises();

    // After response succeeds:
    assert.strictEqual(dot.style.backgroundColor, '#22c55e', 'Status dot returns to green Online');
    assert.strictEqual(dot.title, 'Online', 'Status dot title is Online');
    assert.strictEqual(sendBtn.disabled, false, 'Send button is re-enabled');

    console.log('  ✓ Test 10 Passed: Status transitions to connecting in flight and returns to online on success.');
  }

  // =========================================================================
  // TEST 11: 403 Forbidden Received during sendMessage
  // =========================================================================
  console.log('Test 11: 403 Forbidden Received during sendMessage');
  {
    const mockChat403 = async (url) => {
      if (url.includes('/api/chat/')) {
        return {
          ok: false,
          status: 403,
          json: async () => ({ detail: 'Origin not allowed' }),
        };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_chat_403' },
      },
      isCurrentScript: true,
      fetch: mockChat403,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const dot = documentMock.getElementById('supportai-status-dot');

    input.value = 'Testing 403 chat';
    sendBtn.onclick();
    await flushPromises();

    assert.strictEqual(dot.style.backgroundColor, '#ef4444');
    assert.strictEqual(dot.title, 'Domain not authorized');
    assert.strictEqual(input.disabled, true);
    assert.strictEqual(sendBtn.disabled, true);
    assert(documentMock.getElementById('supportai-domain-warning'));

    console.log('  ✓ Test 11 Passed: 403 Forbidden during sendMessage disabled inputs and set domain warning.');
  }

  // =========================================================================
  // TEST 12: Network Error during sendMessage transitions to error state
  // =========================================================================
  console.log('Test 12: Network Error during sendMessage transitions to error state');
  {
    const mockChatErr = async (url) => {
      if (url.includes('/api/chat/')) {
        throw new Error('Network failed');
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_net_err' },
      },
      isCurrentScript: true,
      fetch: mockChatErr,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const dot = documentMock.getElementById('supportai-status-dot');

    input.value = 'Network test';
    sendBtn.onclick();
    await flushPromises();

    assert.strictEqual(dot.style.backgroundColor, '#ef4444');
    assert.strictEqual(dot.title, 'Offline / Error');
    assert.strictEqual(sendBtn.disabled, false);

    console.log('  ✓ Test 12 Passed: Network error transitions status to error and re-enables send button for retry.');
  }

  // =========================================================================
  // TEST 13: Positioning Classes (supportai-pos-left vs supportai-pos-right)
  // =========================================================================
  console.log('Test 13: Positioning Classes');
  {
    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_left_test', 'data-position': 'bottom-left' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const btn = documentMock.getElementById('supportai-btn');
    const chat = documentMock.getElementById('supportai-chat');

    assert.strictEqual(btn.className, 'supportai-pos-left');
    assert.strictEqual(chat.className, 'supportai-pos-left');

    console.log('  ✓ Test 13 Passed: Position classes applied correctly based on data-position.');
  }

  // =========================================================================
  // TEST 14: DOM Ready Timing Guard (document.readyState === 'loading')
  // =========================================================================
  console.log('Test 14: DOM Ready Timing Guard (document.readyState === "loading")');
  {
    const { context, windowMock, documentMock } = createMockEnvironment({
      origin: 'http://localhost:3000',
      readyState: 'loading',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_dom_ready_test' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    // Widget should not yet have attached to body because readyState is loading
    assert.strictEqual(documentMock.getElementById('supportai-btn'), null);

    // Trigger DOMContentLoaded
    documentMock.readyState = 'interactive';
    documentMock.trigger('DOMContentLoaded');
    await flushPromises();

    assert(documentMock.getElementById('supportai-btn'), 'Widget created once DOMContentLoaded fires');

    console.log('  ✓ Test 14 Passed: Deferred initialization properly awaited DOMContentLoaded.');
  }

  console.log('--- ALL 14 AUTOMATED VERIFICATION TESTS PASSED SUCCESSFULLY! ---');
}

runTests().catch((err) => {
  console.error('Test Suite Failed:', err);
  process.exit(1);
});
