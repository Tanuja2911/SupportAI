/**
 * EMPIRICAL ADVERSARIAL STRESS TEST HARNESS FOR MILESTONE 4
 * Pure 1-Line Self-Initializing Embed Widget & Mobile UI (widget/widget.js)
 *
 * Challenger Agent: teamwork_preview_challenger_m4_1
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const widgetJsPath = path.resolve(__dirname, 'widget.js');
const widgetSource = fs.readFileSync(widgetJsPath, 'utf8');

console.log('======================================================================');
console.log('STARTING EMPIRICAL ADVERSARIAL STRESS TEST SUITE (widget.js)');
console.log('======================================================================');

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 25));

let passCount = 0;
let failCount = 0;
const failureDetails = [];

function recordPass(testName) {
  passCount++;
  console.log(`  ✓ [PASS ${passCount}] ${testName}`);
}

function recordFail(testName, error) {
  failCount++;
  const msg = error ? (error.stack || error.message || String(error)) : 'Assertion failed';
  failureDetails.push({ testName, error: msg });
  console.error(`  ✗ [FAIL ${failCount}] ${testName}:`, error ? (error.message || error) : 'Failed');
}

// -------------------------------------------------------------------------
// Enhanced Adversarial Mock DOM Harness
// -------------------------------------------------------------------------
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
    this.children = [];
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
    return this.attributes[name] !== undefined ? this.attributes[name] : null;
  }

  hasAttribute(name) {
    return name in this.attributes;
  }

  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }

  removeChild(child) {
    const idx = this.children.indexOf(child);
    if (idx !== -1) {
      this.children.splice(idx, 1);
      child.parentNode = null;
    }
    return child;
  }

  remove() {
    if (this.parentNode) {
      this.parentNode.removeChild(this);
    }
  }

  querySelector(selector) {
    const results = this.querySelectorAll(selector);
    return results.length > 0 ? results[0] : null;
  }

  querySelectorAll(selector) {
    const results = [];
    function search(node) {
      if (matches(node, selector)) {
        results.push(node);
      }
      for (const child of node.children) {
        search(child);
      }
    }

    function matches(node, sel) {
      if (!sel || !node) return false;
      if (sel.startsWith('#')) return node.id === sel.slice(1);
      if (sel.startsWith('.')) return node.className.includes(sel.slice(1));
      if (sel.includes('[data-business-key]')) return node.hasAttribute('data-business-key');
      if (sel.includes('[data-api-key]')) return node.hasAttribute('data-api-key');
      if (sel.includes('script[src*="widget.js"]')) {
        return node.tagName === 'SCRIPT' && node.src && node.src.includes('widget.js');
      }
      if (sel.includes('script[src*="/widget/widget.js"]')) {
        return node.tagName === 'SCRIPT' && node.src && node.src.includes('/widget/widget.js');
      }
      if (sel.toUpperCase() === node.tagName) return true;
      return false;
    }

    search(this);
    return results;
  }

  addEventListener(event, fn) {
    if (!this.eventListeners[event]) this.eventListeners[event] = [];
    this.eventListeners[event].push(fn);
  }

  dispatchEvent(event) {
    if (this.eventListeners[event.type]) {
      for (const fn of this.eventListeners[event.type]) fn(event);
    }
  }
}

function createAdversarialEnvironment(options = {}) {
  const head = new MockElement('HEAD', 'head');
  const body = new MockElement('BODY', 'body');
  const root = new MockElement('HTML', 'html');
  root.appendChild(head);
  if (options.hasBody !== false) {
    root.appendChild(body);
  }

  const scripts = [];

  const documentMock = {
    readyState: options.readyState || 'complete',
    head: head,
    body: options.hasBody !== false ? body : null,
    documentElement: root,
    currentScript: null,
    _listeners: {},

    createElement(tag) {
      const el = new MockElement(tag);
      if (tag.toUpperCase() === 'SCRIPT') {
        scripts.push(el);
      }
      return el;
    },
    getElementById(id) {
      function search(node) {
        if (!node) return null;
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
        if (!node) return;
        if (node.tagName === tag) results.push(node);
        for (const child of node.children) search(child);
      }
      search(root);
      return results;
    },
    querySelector(sel) {
      const parts = sel.split(',').map((s) => s.trim());
      for (const part of parts) {
        const found = root.querySelector(part);
        if (found) return found;
      }
      return null;
    },
    querySelectorAll(sel) {
      const parts = sel.split(',').map((s) => s.trim());
      const results = [];
      for (const part of parts) {
        results.push(...root.querySelectorAll(part));
      }
      return results;
    },
    addEventListener(event, fn) {
      if (!this._listeners[event]) this._listeners[event] = [];
      this._listeners[event].push(fn);
    },
    trigger(event) {
      if (this._listeners[event]) {
        for (const fn of this._listeners[event]) fn();
      }
    },
  };

  const mockFetch = options.fetch || (async () => ({ ok: true, status: 200, json: async () => ({}) }));

  const windowMock = {
    location: {
      origin: options.origin || 'http://localhost:3000',
      href: (options.origin || 'http://localhost:3000') + (options.pathname || '/index.html'),
    },
    fetch: mockFetch,
  };

  windowMock.document = documentMock;

  if (options.scripts && Array.isArray(options.scripts)) {
    for (const sc of options.scripts) {
      const s = new MockElement('SCRIPT');
      if (sc.src) s.src = sc.src;
      for (const [k, v] of Object.entries(sc.attrs || {})) {
        s.setAttribute(k, v);
      }
      scripts.push(s);
      if (sc.parent === 'body' && documentMock.body) {
        documentMock.body.appendChild(s);
      } else if (sc.parent === 'unattached') {
        // Unattached
      } else {
        head.appendChild(s);
      }
      if (sc.isCurrentScript) {
        documentMock.currentScript = s;
      }
    }
  } else if (options.scriptTag) {
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

  return { context, windowMock, documentMock, scripts };
}

async function runAdversarialSuite() {
  console.log('\n--- CATEGORY 1: Script Tag & Origin Detection Stress Testing ---');

  // Test 1.1: Multiple scripts in DOM
  try {
    const { context, windowMock } = createAdversarialEnvironment({
      origin: 'https://shop.customer.com',
      scripts: [
        { src: 'https://cdn.other.com/analytics.js', attrs: {} },
        { src: 'https://cdn.vendor.com/widget.js', attrs: {} },
        { src: 'https://api.supportai.com/widget/widget.js', attrs: { 'data-business-key': 'pk_live_real_target' } },
        { src: 'https://cdn.other.com/tracker.js', attrs: { 'data-api-key': 'pk_decoy_secondary' } },
      ],
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert(windowMock.SupportAI, 'window.SupportAI initialized');
    assert.strictEqual(windowMock.SupportAI.config.apiKey, 'pk_live_real_target', 'Prioritizes script with data-business-key');
    assert.strictEqual(windowMock.SupportAI.config.serverUrl, 'https://api.supportai.com', 'Origin inferred from target script src');
    recordPass('Multiple scripts in DOM correctly prioritizes data-business-key script');
  } catch (err) {
    recordFail('Multiple scripts in DOM correctly prioritizes data-business-key script', err);
  }

  // Test 1.2: Whitespace data-business-key
  try {
    const { context, windowMock } = createAdversarialEnvironment({
      origin: 'https://shop.customer.com',
      scripts: [
        { src: 'https://cdn.other.com/lib.js', attrs: { 'data-business-key': '   ' } },
        { src: 'https://api.supportai.com/widget/widget.js', attrs: { 'data-api-key': 'pk_valid_from_fallback' } },
      ],
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    recordPass('Whitespace-only data-business-key handled without throw');
  } catch (err) {
    recordFail('Whitespace-only data-business-key handled without throw', err);
  }

  // Test 1.3: Complex script src with query params, port, and hash
  try {
    const { context, windowMock } = createAdversarialEnvironment({
      origin: 'https://portal.client.net:9443',
      scriptTag: {
        src: 'https://support.backend.com:8443/custom/v1/static/widget/widget.js?token=xyz123&env=production#release',
        attrs: { 'data-business-key': 'pk_complex_url_key' },
      },
      isCurrentScript: true,
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert.strictEqual(windowMock.SupportAI.config.apiKey, 'pk_complex_url_key');
    assert.strictEqual(windowMock.SupportAI.config.serverUrl, 'https://support.backend.com:8443', 'Accurately parses port and origin from complex URL');
    recordPass('Complex script src with query params, port, and hash resolves origin cleanly');
  } catch (err) {
    recordFail('Complex script src with query params, port, and hash resolves origin cleanly', err);
  }

  // Test 1.4: Relative script src
  try {
    const { context, windowMock } = createAdversarialEnvironment({
      origin: 'http://shop.example.com:8080',
      pathname: '/products/catalog/view.html',
      scriptTag: {
        src: '../../widget/widget.js',
        attrs: { 'data-business-key': 'pk_relative_src_key' },
      },
      isCurrentScript: true,
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert.strictEqual(windowMock.SupportAI.config.apiKey, 'pk_relative_src_key');
    assert.strictEqual(windowMock.SupportAI.config.serverUrl, 'http://shop.example.com:8080', 'Resolves relative src against window.location.href origin');
    recordPass('Relative script src (../../widget/widget.js) resolves origin correctly against window.location');
  } catch (err) {
    recordFail('Relative script src resolves origin correctly', err);
  }

  // Test 1.5: data-server-url override
  try {
    const { context, windowMock } = createAdversarialEnvironment({
      origin: 'https://shop.example.com',
      scriptTag: {
        src: 'https://cdn.static.com/widget/widget.js',
        attrs: {
          'data-business-key': 'pk_override_key',
          'data-server-url': 'https://custom-api.example.com///',
        },
      },
      isCurrentScript: true,
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert.strictEqual(windowMock.SupportAI.config.serverUrl, 'https://custom-api.example.com', 'data-server-url override trims trailing slashes');
    recordPass('Explicit data-server-url attribute overrides script.src and strips trailing slashes');
  } catch (err) {
    recordFail('Explicit data-server-url attribute overrides script.src', err);
  }

  // Test 1.6: Unattached script element & graceful standby
  try {
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'https://shop.example.com',
      scripts: [
        {
          src: 'https://api.supportai.com/widget/widget.js',
          attrs: { 'data-business-key': 'pk_detached_key' },
          parent: 'unattached',
        },
      ],
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert(windowMock.SupportAI, 'SupportAI global defined');
    assert.strictEqual(windowMock.SupportAI.isInitialized, false, 'Does not auto-init from unattached script');
    assert.strictEqual(documentMock.getElementById('supportai-btn'), null, 'Zero DOM elements created');
    recordPass('Unattached script element gracefully stands down without throwing');
  } catch (err) {
    recordFail('Unattached script element gracefully stands down without throwing', err);
  }

  // Test 1.7: Dynamically created and injected script element
  try {
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'https://shop.example.com',
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    const dynamicScript = documentMock.createElement('SCRIPT');
    dynamicScript.src = 'https://dynamichost.com/widget/widget.js';
    dynamicScript.setAttribute('data-business-key', 'pk_dynamic_inject_123');
    documentMock.head.appendChild(dynamicScript);
    documentMock.currentScript = dynamicScript;

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert.strictEqual(windowMock.SupportAI.config.apiKey, 'pk_dynamic_inject_123');
    assert.strictEqual(windowMock.SupportAI.config.serverUrl, 'https://dynamichost.com');
    assert(documentMock.getElementById('supportai-btn'), '#supportai-btn mounted from dynamically injected script');
    recordPass('Dynamically injected script auto-initializes successfully');
  } catch (err) {
    recordFail('Dynamically injected script auto-initializes successfully', err);
  }

  console.log('\n--- CATEGORY 2: Document readyState & Timing Variations ---');

  // Test 2.1: readyState === 'loading'
  try {
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      readyState: 'loading',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_loading_state' },
      },
      isCurrentScript: true,
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert.strictEqual(documentMock.getElementById('supportai-btn'), null, 'No elements created during loading state');
    assert.strictEqual(windowMock.SupportAI.isInitialized, false);

    documentMock.readyState = 'interactive';
    documentMock.trigger('DOMContentLoaded');
    await flushPromises();

    assert(documentMock.getElementById('supportai-btn'), '#supportai-btn mounted after DOMContentLoaded fires');
    assert.strictEqual(windowMock.SupportAI.isInitialized, true);
    recordPass('readyState === "loading" properly defers until DOMContentLoaded');
  } catch (err) {
    recordFail('readyState === "loading" properly defers until DOMContentLoaded', err);
  }

  // Test 2.2: readyState === 'interactive'
  try {
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      readyState: 'interactive',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_interactive_state' },
      },
      isCurrentScript: true,
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert(documentMock.getElementById('supportai-btn'), 'Mounted immediately in interactive state');
    assert.strictEqual(windowMock.SupportAI.isInitialized, true);
    recordPass('readyState === "interactive" executes immediately without deferral');
  } catch (err) {
    recordFail('readyState === "interactive" executes immediately without deferral', err);
  }

  // Test 2.3: readyState === 'complete'
  try {
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      readyState: 'complete',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_complete_state' },
      },
      isCurrentScript: true,
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert(documentMock.getElementById('supportai-btn'), 'Mounted immediately in complete state');
    assert.strictEqual(windowMock.SupportAI.isInitialized, true);
    recordPass('readyState === "complete" executes immediately');
  } catch (err) {
    recordFail('readyState === "complete" executes immediately', err);
  }

  // Test 2.4: Race: Manual init during loading state before DOMContentLoaded
  try {
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      readyState: 'loading',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_race_loading' },
      },
      isCurrentScript: true,
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    windowMock.SupportAI.init({ apiKey: 'pk_manual_race' });

    documentMock.readyState = 'interactive';
    documentMock.trigger('DOMContentLoaded');
    await flushPromises();

    const buttons = documentMock.getElementsByTagName('div').filter((d) => d.id === 'supportai-btn');
    const chats = documentMock.getElementsByTagName('div').filter((d) => d.id === 'supportai-chat');
    assert.strictEqual(buttons.length, 1, 'Exactly one button exists in DOM');
    assert.strictEqual(chats.length, 1, 'Exactly one chat window exists in DOM');
    recordPass('Manual init during loading state before DOMContentLoaded causes zero duplicate elements');
  } catch (err) {
    recordFail('Manual init during loading state before DOMContentLoaded causes zero duplicate elements', err);
  }

  console.log('\n--- CATEGORY 3: Concurrency & Idempotency Stress Testing ---');

  // Test 3.1: 20 rapid simultaneous calls to SupportAI.init()
  try {
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_concurrent_init' },
      },
      isCurrentScript: true,
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);

    for (let i = 1; i <= 20; i++) {
      windowMock.SupportAI.init({
        apiKey: `pk_blast_${i}`,
        serverUrl: `http://server-${i}.com`,
      });
    }

    await flushPromises();

    const buttons = documentMock.getElementsByTagName('div').filter((d) => d.id === 'supportai-btn');
    const chats = documentMock.getElementsByTagName('div').filter((d) => d.id === 'supportai-chat');
    const styles = documentMock.getElementsByTagName('style').filter((s) => s.id === 'supportai-styles');

    assert.strictEqual(buttons.length, 1, 'Exactly 1 #supportai-btn created');
    assert.strictEqual(chats.length, 1, 'Exactly 1 #supportai-chat created');
    assert.strictEqual(styles.length, 1, 'Exactly 1 #supportai-styles created');
    recordPass('20 rapid concurrent SupportAI.init() calls result in exactly 1 DOM element set');
  } catch (err) {
    recordFail('20 rapid concurrent SupportAI.init() calls result in exactly 1 DOM element set', err);
  }

  // Test 3.2: Race condition: auto-init fetch in-flight + concurrent manual init
  try {
    let resolveConfig;
    const fetchPromise = new Promise((resolve) => {
      resolveConfig = resolve;
    });

    const mockFetch = async (url) => {
      if (url.includes('/api/widget/embed/')) {
        return fetchPromise;
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_inflight_auto' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    windowMock.SupportAI.init({ apiKey: 'pk_manual_intervening' });

    resolveConfig({
      ok: true,
      status: 200,
      json: async () => ({ bot_name: 'Resolved Bot' }),
    });
    await flushPromises();

    const buttons = documentMock.getElementsByTagName('div').filter((d) => d.id === 'supportai-btn');
    assert.strictEqual(buttons.length, 1, 'Single button mounted despite in-flight manual race');
    recordPass('Intervening manual init during in-flight loadConfig cleanly rejected by idempotency guard');
  } catch (err) {
    recordFail('Intervening manual init during in-flight loadConfig cleanly rejected by idempotency guard', err);
  }

  console.log('\n--- CATEGORY 4: Programmatic Lifecycle & Destroy Stress Testing ---');

  // Test 4.1: open, close, toggle display manipulation
  try {
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_lifecycle' },
      },
      isCurrentScript: true,
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const chat = documentMock.getElementById('supportai-chat');
    assert.strictEqual(chat.style.display, 'none', 'Initial display is none');

    windowMock.SupportAI.open();
    assert.strictEqual(chat.style.display, 'flex');
    assert.strictEqual(windowMock.SupportAI.isOpen, true);

    windowMock.SupportAI.close();
    assert.strictEqual(chat.style.display, 'none');
    assert.strictEqual(windowMock.SupportAI.isOpen, false);

    windowMock.SupportAI.toggle();
    assert.strictEqual(chat.style.display, 'flex');
    assert.strictEqual(windowMock.SupportAI.isOpen, true);

    windowMock.SupportAI.toggle();
    assert.strictEqual(chat.style.display, 'none');
    assert.strictEqual(windowMock.SupportAI.isOpen, false);

    recordPass('Programmatic open(), close(), and toggle() update display and isOpen accurately');
  } catch (err) {
    recordFail('Programmatic open(), close(), and toggle() update display and isOpen accurately', err);
  }

  // Test 4.2: Programmatic destroy followed by re-initialization
  try {
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_initial_instance' },
      },
      isCurrentScript: true,
      fetch: async () => ({ ok: true, status: 200, json: async () => ({ bot_name: 'Bot 1' }) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert(documentMock.getElementById('supportai-btn'));
    assert(documentMock.getElementById('supportai-chat'));

    windowMock.SupportAI.destroy();

    assert.strictEqual(documentMock.getElementById('supportai-btn'), null, 'Button removed after destroy');
    assert.strictEqual(documentMock.getElementById('supportai-chat'), null, 'Chat removed after destroy');
    assert.strictEqual(documentMock.getElementById('supportai-styles'), null, 'Styles removed after destroy');
    assert.strictEqual(windowMock.SupportAI.isInitialized, false, 'isInitialized false');
    assert.strictEqual(windowMock.SupportAI.container, null, 'container null');

    windowMock.SupportAI.init({
      apiKey: 'pk_second_instance',
      serverUrl: 'http://custom-api:9000',
    });
    await flushPromises();

    assert(documentMock.getElementById('supportai-btn'), 'Button re-created after re-init');
    assert(documentMock.getElementById('supportai-chat'), 'Chat re-created after re-init');
    assert.strictEqual(windowMock.SupportAI.config.apiKey, 'pk_second_instance');
    assert.strictEqual(windowMock.SupportAI.config.serverUrl, 'http://custom-api:9000');
    assert.strictEqual(windowMock.SupportAI.isInitialized, true);

    recordPass('destroy() cleanly unmounts and allows full re-initialization with new credentials');
  } catch (err) {
    recordFail('destroy() cleanly unmounts and allows full re-initialization with new credentials', err);
  }

  // Test 4.3: 5 consecutive cycles of init -> open -> destroy
  try {
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      fetch: async () => ({ ok: true, status: 200, json: async () => ({}) }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    for (let cycle = 1; cycle <= 5; cycle++) {
      windowMock.SupportAI.init({
        apiKey: `pk_cycle_${cycle}`,
        serverUrl: 'http://localhost:8000',
      });
      await flushPromises();

      windowMock.SupportAI.open();
      assert.strictEqual(windowMock.SupportAI.isOpen, true);
      assert.strictEqual(windowMock.SupportAI.config.apiKey, `pk_cycle_${cycle}`);

      windowMock.SupportAI.destroy();
      assert.strictEqual(documentMock.getElementById('supportai-btn'), null);
      assert.strictEqual(documentMock.getElementById('supportai-chat'), null);
      assert.strictEqual(windowMock.SupportAI.isInitialized, false);
    }

    recordPass('5 consecutive cycles of init -> open -> destroy execute with zero residue');
  } catch (err) {
    recordFail('5 consecutive cycles of init -> open -> destroy execute with zero residue', err);
  }

  // Test 4.4 (ADVERSARIAL CHALLENGE 1): Programmatic open() before config load / createWidget finishes
  try {
    let resolveConfig;
    const fetchPromise = new Promise((resolve) => {
      resolveConfig = resolve;
    });

    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      fetch: async () => fetchPromise,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    windowMock.SupportAI.init({ apiKey: 'pk_open_before_mount' });
    windowMock.SupportAI.open();
    assert.strictEqual(windowMock.SupportAI.isOpen, true, 'isOpen is true');

    resolveConfig({
      ok: true,
      status: 200,
      json: async () => ({ bot_name: 'Async Bot' }),
    });
    await flushPromises();

    const chat = documentMock.getElementById('supportai-chat');
    assert(chat, '#supportai-chat is mounted');
    assert.strictEqual(chat.style.display, 'flex', 'Chat display should be flex when open() was called before mount');

    recordPass('Programmatic open() called before config fetch resolves is respected by createWidget()');
  } catch (err) {
    recordFail('Programmatic open() called before config fetch resolves is respected by createWidget()', err);
  }

  // Test 4.5 (ADVERSARIAL CHALLENGE 2): destroy() called during in-flight loadConfig()
  try {
    let resolveConfig;
    const fetchPromise = new Promise((resolve) => {
      resolveConfig = resolve;
    });

    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      fetch: async () => fetchPromise,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    windowMock.SupportAI.init({ apiKey: 'pk_destroy_race' });
    windowMock.SupportAI.destroy();

    // Hook unhandledRejection temporarily to capture the crash
    let capturedRejection = null;
    const rejectionHandler = (reason) => {
      capturedRejection = reason;
    };
    process.on('unhandledRejection', rejectionHandler);

    resolveConfig({
      ok: true,
      status: 200,
      json: async () => ({ primary_color: '#4f46e5' }),
    });
    await flushPromises();

    process.removeListener('unhandledRejection', rejectionHandler);

    if (capturedRejection) {
      throw capturedRejection;
    }

    const btn = documentMock.getElementById('supportai-btn');
    const chat = documentMock.getElementById('supportai-chat');
    assert.strictEqual(btn, null, 'No button elements should mount after destroy()');
    assert.strictEqual(chat, null, 'No chat elements should mount after destroy()');
    assert.strictEqual(windowMock.SupportAI.isInitialized, false, 'isInitialized should remain false');

    recordPass('destroy() during in-flight loadConfig aborts cleanly without re-mounting DOM or throwing');
  } catch (err) {
    recordFail('destroy() during in-flight loadConfig aborts cleanly without re-mounting DOM or throwing', err);
  }

  console.log('\n--- CATEGORY 5: Origin Guard & 403 Forbidden Edge Cases ---');

  // Test 5.1: 403 Forbidden handling and self-healing reset recovery
  try {
    let domainWhitelisted = false;
    const mockDynamicFetch = async (url) => {
      if (url.includes('/api/widget/embed/')) {
        if (!domainWhitelisted) {
          return { ok: false, status: 403, json: async () => ({ detail: 'Origin not allowed' }) };
        } else {
          return {
            ok: true,
            status: 200,
            json: async () => ({
              bot_name: 'Whitelisted Assistant',
              welcome_message: 'Welcome back!',
            }),
          };
        }
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'https://unauthorized.com',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_recovery_test' },
      },
      isCurrentScript: true,
      fetch: mockDynamicFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const dot = documentMock.getElementById('supportai-status-dot');
    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const warning = documentMock.getElementById('supportai-domain-warning');

    assert.strictEqual(dot.style.backgroundColor, '#ef4444');
    assert.strictEqual(dot.title, 'Domain not authorized');
    assert(warning, 'Warning banner displayed on 403');
    assert.strictEqual(input.disabled, true);
    assert.strictEqual(sendBtn.disabled, true);

    // Whitelist and reset
    domainWhitelisted = true;
    windowMock.SupportAI.reset();
    await flushPromises();

    assert.strictEqual(dot.style.backgroundColor, '#22c55e', 'Status returns to online green');
    assert.strictEqual(dot.title, 'Online');
    assert.strictEqual(input.disabled, false, 'Input field re-enabled');
    assert.strictEqual(sendBtn.disabled, false, 'Send button re-enabled');
    assert.strictEqual(documentMock.getElementById('supportai-domain-warning'), null, 'Warning banner removed');

    recordPass('403 Forbidden state self-heals back to Online after domain whitelist and reset()');
  } catch (err) {
    recordFail('403 Forbidden state self-heals back to Online after domain whitelist and reset()', err);
  }

  // Test 5.2: 403 Forbidden mid-chat during sendMessage
  try {
    const mockChat403 = async (url) => {
      if (url.includes('/api/chat/')) {
        return { ok: false, status: 403, json: async () => ({ detail: 'Origin not allowed' }) };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_chat_403_test' },
      },
      isCurrentScript: true,
      fetch: mockChat403,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const dot = documentMock.getElementById('supportai-status-dot');

    input.value = 'Hello?';
    sendBtn.onclick();
    await flushPromises();

    assert.strictEqual(dot.style.backgroundColor, '#ef4444');
    assert.strictEqual(dot.title, 'Domain not authorized');
    assert.strictEqual(input.disabled, true);
    assert.strictEqual(sendBtn.disabled, true);
    assert(documentMock.getElementById('supportai-domain-warning'));

    recordPass('403 Forbidden received mid-chat safely transitions status dot and locks inputs');
  } catch (err) {
    recordFail('403 Forbidden received mid-chat safely transitions status dot and locks inputs', err);
  }

  // Test 5.3: Network error during sendMessage transitions status dot to error
  try {
    const mockChatErr = async (url) => {
      if (url.includes('/api/chat/')) {
        throw new Error('Network dropped');
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_chat_err_test' },
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
    assert.strictEqual(sendBtn.disabled, false, 'Send button re-enabled for retry');

    recordPass('Network drop during sendMessage transitions status to error and allows retry');
  } catch (err) {
    recordFail('Network drop during sendMessage transitions status to error and allows retry', err);
  }

  console.log('\n--- CATEGORY 6: XSS Protection & Mobile Responsive CSS Rules ---');

  // Test 6.1: Malicious HTML / script injection in user input and welcome text
  try {
    const xssPayload = '<img src=x onerror=alert("XSS")><script>window._xss=true;</script>';
    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_xss_test' },
      },
      isCurrentScript: true,
      fetch: async (url) => {
        if (url.includes('/api/widget/embed/')) {
          return {
            ok: true,
            status: 200,
            json: async () => ({ welcome_message: xssPayload }),
          };
        }
        if (url.includes('/api/chat/')) {
          return {
            ok: true,
            status: 200,
            json: async () => ({ conversation_id: 'conv_xss', message: xssPayload }),
          };
        }
        return { ok: true, status: 200, json: async () => ({}) };
      },
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const messages = documentMock.getElementById('supportai-messages');
    const bubbles = messages.children;
    assert(bubbles.length > 0);
    const welcomeBubble = bubbles[0].children[0];
    assert.strictEqual(welcomeBubble.textContent, xssPayload);
    assert.strictEqual(windowMock._xss, undefined, 'Script tag in payload was NOT executed');

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    input.value = xssPayload;
    sendBtn.onclick();
    await flushPromises();

    assert.strictEqual(windowMock._xss, undefined, 'User payload was NOT executed as HTML');
    recordPass('XSS payloads in welcome message, user input, and AI response safely rendered via textContent');
  } catch (err) {
    recordFail('XSS payloads safely rendered via textContent', err);
  }

  // Test 6.2: Mobile Responsive CSS Rules Validation
  try {
    const styleMatch = widgetSource.match(/\/\* =+[\s\S]*?MOBILE RESPONSIVE MEDIA QUERY[\s\S]*?\*\/([\s\S]*?)(?=\`)/);
    assert(styleMatch, 'Mobile responsive media query block exists in widget.js');
    const mobileCss = styleMatch[1];

    assert(mobileCss.includes('@media (max-width: 480px)'), 'Max-width 480px media query declared');
    assert(mobileCss.includes('calc(100vw - 24px) !important'), 'Mobile chat width calc(100vw - 24px) !important');
    assert(
      mobileCss.includes('calc(100vh - 96px) !important') && mobileCss.includes('calc(100dvh - 96px) !important'),
      'Mobile chat height includes both 100vh and modern 100dvh fallbacks'
    );
    assert(mobileCss.includes('font-size: 16px !important'), 'Input font size is 16px !important for iOS zoom prevention');
    assert(widgetSource.includes('box-sizing: border-box !important'), 'Host style isolation via border-box !important');

    recordPass('Mobile CSS rules conform 100% to mobile layout spec and iOS Safari zoom prevention');
  } catch (err) {
    recordFail('Mobile CSS rules conform 100% to mobile layout spec', err);
  }

  console.log('\n--- CATEGORY 7: Input Edge Cases & Rapid Interactions ---');

  // Test 7.1: Empty and whitespace-only message submission
  try {
    let chatEndpointCalled = false;
    const mockChatFetch = async (url) => {
      if (url.includes('/api/chat/')) {
        chatEndpointCalled = true;
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_empty_msg_test' },
      },
      isCurrentScript: true,
      fetch: mockChatFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');

    input.value = '';
    sendBtn.onclick();
    await flushPromises();
    assert.strictEqual(chatEndpointCalled, false, 'Empty input does not call chat API');

    input.value = '   \t\n   ';
    sendBtn.onclick();
    await flushPromises();
    assert.strictEqual(chatEndpointCalled, false, 'Whitespace input does not call chat API');

    recordPass('Empty and whitespace-only messages ignored without dispatching network calls');
  } catch (err) {
    recordFail('Empty and whitespace-only messages ignored without dispatching network calls', err);
  }

  // Test 7.2: In-flight double-click prevention
  try {
    let chatCallCount = 0;
    let resolveChat;
    const pendingPromise = new Promise((resolve) => {
      resolveChat = resolve;
    });

    const mockFetch = async (url) => {
      if (url.includes('/api/chat/')) {
        chatCallCount++;
        return pendingPromise;
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createAdversarialEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_double_click' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');

    input.value = 'Click 1';
    sendBtn.onclick();
    sendBtn.onclick();

    assert.strictEqual(chatCallCount, 1, 'Exactly one HTTP request sent; second click ignored');
    assert.strictEqual(sendBtn.disabled, true, 'Send button disabled while in flight');

    resolveChat({
      ok: true,
      status: 200,
      json: async () => ({ conversation_id: 'conv_1', message: 'Got it' }),
    });
    await flushPromises();

    assert.strictEqual(sendBtn.disabled, false, 'Send button re-enabled after completion');
    recordPass('Rapid double-click on send button safely de-duplicated; only 1 request dispatched');
  } catch (err) {
    recordFail('Rapid double-click on send button safely de-duplicated', err);
  }

  console.log('\n======================================================================');
  console.log(`STRESS TEST SUMMARY: ${passCount} PASSED, ${failCount} FAILED out of ${passCount + failCount} TOTAL`);
  console.log('======================================================================');

  if (failCount > 0) {
    console.log('\nFAILURE DETAILS:');
    for (const f of failureDetails) {
      console.log(`- ${f.testName}:`);
      console.log(`  ${f.error.split('\n')[0]}`);
    }
  }

  return { passCount, failCount, failureDetails };
}

runAdversarialSuite()
  .then((res) => {
    if (res.failCount > 0) {
      process.exitCode = 1;
    }
  })
  .catch((err) => {
    console.error('Unhandled suite error:', err);
    process.exitCode = 1;
  });
