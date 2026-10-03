/**
 * Empirical Adversarial Test Harness for Milestone 4:
 * Pure 1-Line Self-Initializing Embed Widget & Mobile UI (widget/widget.js)
 *
 * Challenger: teamwork_preview_challenger_m4_2
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const widgetJsPath = path.resolve(__dirname, 'widget.js');
const widgetSource = fs.readFileSync(widgetJsPath, 'utf8');

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 30));

let passCount = 0;
let failCount = 0;
const testResults = [];

function recordTest(name, passed, details = '') {
  if (passed) {
    passCount++;
    testResults.push({ name, status: 'PASS', details });
    console.log(`  ✓ PASS: ${name}`);
  } else {
    failCount++;
    testResults.push({ name, status: 'FAIL', details });
    console.error(`  ✗ FAIL: ${name} — ${details}`);
  }
}

// =========================================================================
// MOCK DOM SIMULATOR FOR ADVERSARIAL TESTING
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
    this.scrollTop = 0;
    this.scrollHeight = 100;
  }

  get innerHTML() {
    return this._innerHTML;
  }

  set innerHTML(html) {
    this._innerHTML = html;
    this.children = [];

    // Parse all tags with id, class, title, style
    const idMatches = [...html.matchAll(/<([a-zA-Z0-9]+)([^>]*?id="([^"]+)"[^>]*?)>/g)];

    // Ensure all elements with ID are created and queryable
    for (const match of idMatches) {
      const tag = match[1].toUpperCase();
      const attrsStr = match[2];
      const childId = match[3];

      if (!this.querySelector('#' + childId)) {
        const childEl = new MockElement(tag, childId);
        const classMatch = attrsStr.match(/class="([^"]+)"/);
        if (classMatch) childEl.className = classMatch[1];
        const titleMatch = attrsStr.match(/title="([^"]+)"/);
        if (titleMatch) childEl.title = titleMatch[1];
        const styleMatch = attrsStr.match(/style="([^"]+)"/);
        if (styleMatch) {
          styleMatch[1].split(';').forEach(pair => {
            const [k, v] = pair.split(':');
            if (k && v) {
              const camelK = k.trim().replace(/-([a-z])/g, (_, c) => c.toUpperCase());
              childEl.style[camelK] = v.trim();
            }
          });
        }
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
    if (selector.startsWith('.')) {
      const targetClass = selector.slice(1);
      if (this.className && this.className.includes(targetClass)) return this;
      for (const child of this.children) {
        const found = child.querySelector(selector);
        if (found) return found;
      }
      return null;
    }
    return null;
  }

  querySelectorAll(selector) {
    const results = [];
    if (selector.startsWith('#')) {
      const targetId = selector.slice(1);
      if (this.id === targetId) results.push(this);
      for (const child of this.children) {
        results.push(...child.querySelectorAll(selector));
      }
    } else if (selector.startsWith('.')) {
      const targetClass = selector.slice(1);
      if (this.className && this.className.includes(targetClass)) results.push(this);
      for (const child of this.children) {
        results.push(...child.querySelectorAll(selector));
      }
    }
    return results;
  }

  addEventListener(event, fn) {
    if (!this.eventListeners[event]) this.eventListeners[event] = [];
    this.eventListeners[event].push(fn);
  }
}

function createEnvironment(options = {}) {
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
      if (sel.startsWith('#')) {
        const id = sel.slice(1);
        const match = this.getElementById(id);
        return match ? [match] : [];
      }
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

async function runAdversarialSuite() {
  console.log('================================================================');
  console.log('STARTING EMPIRICAL ADVERSARIAL STRESS TEST SUITE (M4)');
  console.log('================================================================');

  // -------------------------------------------------------------------------
  // CATEGORY 1: HTTP 403 Forbidden & Security Error Stress Testing
  // -------------------------------------------------------------------------
  console.log('\n--- CATEGORY 1: HTTP 403 Forbidden & Security Error Stress Testing ---');

  // Test 1.1: Consecutive 403 responses do NOT create duplicate warning banners
  {
    const fetchCalls = [];
    const mockFetch = async (url) => {
      fetchCalls.push(url);
      if (url.includes('/api/widget/embed/')) {
        return { ok: false, status: 403, json: async () => ({ detail: 'Origin not allowed' }) };
      }
      if (url.includes('/api/chat/')) {
        return { ok: false, status: 403, json: async () => ({ detail: 'Origin not allowed' }) };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'https://unauthorized-mall.com',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_live_adversarial_403' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    // Verify initial 403 state
    const dot = documentMock.getElementById('supportai-status-dot');
    const warningBannersInitial = documentMock.querySelectorAll('#supportai-domain-warning');
    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');

    let t1_1_passed = true;
    let t1_1_err = '';

    if (!dot || dot.style.backgroundColor !== '#ef4444' || dot.title !== 'Domain not authorized') {
      t1_1_passed = false;
      t1_1_err += `Status dot title/color incorrect on initial 403 (color: ${dot?.style?.backgroundColor}, title: ${dot?.title}). `;
    }
    if (warningBannersInitial.length !== 1) {
      t1_1_passed = false;
      t1_1_err += `Expected 1 initial warning banner, found ${warningBannersInitial.length}. `;
    }

    // Now trigger consecutive 403 calls: simulate chat message 403
    windowMock.SupportAI.handleDomainForbidden();
    windowMock.SupportAI.handleDomainForbidden();
    await flushPromises();

    const warningBannersAfter = documentMock.querySelectorAll('#supportai-domain-warning');
    if (warningBannersAfter.length !== 1) {
      t1_1_passed = false;
      t1_1_err += `Duplicate banners detected after consecutive 403s! Found: ${warningBannersAfter.length}. `;
    }

    recordTest(
      'Consecutive 403 responses: zero duplicate warning banners in DOM',
      t1_1_passed,
      t1_1_err
    );
  }

  // Test 1.2: Disabled input tampering & bypass resistance
  {
    let chatEndpointHit = false;
    const mockFetch = async (url) => {
      if (url.includes('/api/widget/embed/')) {
        return { ok: false, status: 403, json: async () => ({ detail: 'Origin not allowed' }) };
      }
      if (url.includes('/api/chat/')) {
        chatEndpointHit = true;
        return { ok: false, status: 403, json: async () => ({ detail: 'Origin not allowed' }) };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'https://attacker.com',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_attacker_key' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');

    let t1_2_passed = true;
    let t1_2_err = '';

    if (!input.disabled || !sendBtn.disabled) {
      t1_2_passed = false;
      t1_2_err += 'Input or send button not disabled after 403. ';
    }

    // Tamper attempt 1: Programmatically set value and call sendBtn.onclick() while disabled
    input.value = 'Malicious bypass payload';
    if (typeof sendBtn.onclick === 'function') {
      sendBtn.onclick();
    }
    await flushPromises();

    if (chatEndpointHit) {
      t1_2_passed = false;
      t1_2_err += 'Bypass vulnerability: chat fetch invoked while input disabled! ';
    }

    // Tamper attempt 2: Simulate Enter keypress while disabled
    if (typeof input.onkeydown === 'function') {
      input.onkeydown({ key: 'Enter' });
    }
    await flushPromises();

    if (chatEndpointHit) {
      t1_2_passed = false;
      t1_2_err += 'Bypass vulnerability: Enter key triggered fetch while input disabled! ';
    }

    // Tamper attempt 3: Attacker tampers in devtools and un-disables input
    input.disabled = false;
    sendBtn.disabled = false;
    input.value = 'Forced DevTools submission';
    sendBtn.onclick();
    await flushPromises();

    if (!chatEndpointHit) {
      t1_2_passed = false;
      t1_2_err += 'Expected chat endpoint to be reached when attacker force-enabled DOM. ';
    }

    // Verify widget reacted to 403 by immediately RE-DISABLING inputs
    if (!input.disabled || !sendBtn.disabled) {
      t1_2_passed = false;
      t1_2_err += 'Widget failed to re-lock inputs after 403 on chat submission. ';
    }
    const banners = documentMock.querySelectorAll('#supportai-domain-warning');
    if (banners.length !== 1) {
      t1_2_passed = false;
      t1_2_err += `Banner count after re-lock is ${banners.length}, expected 1. `;
    }

    recordTest(
      'Disabled input tampering: cannot submit requests while 403 active & auto-relocks on backend 403',
      t1_2_passed,
      t1_2_err
    );
  }

  // Test 1.3: Recovery flow (simulate domain becoming whitelisted & refresh clicked)
  {
    let domainWhitelisted = false;
    let chatCallCount = 0;

    const mockFetch = async (url) => {
      if (url.includes('/api/widget/embed/')) {
        if (!domainWhitelisted) {
          return { ok: false, status: 403, json: async () => ({ detail: 'Origin not allowed' }) };
        }
        return {
          ok: true,
          status: 200,
          json: async () => ({
            business_id: 1,
            bot_name: 'Recovered Bot',
            placeholder_text: 'Ask a recovered question...',
            welcome_message: 'Welcome back!',
          }),
        };
      }
      if (url.includes('/api/chat/')) {
        chatCallCount++;
        return {
          ok: true,
          status: 200,
          json: async () => ({
            conversation_id: 'conv_recovered_99',
            message: 'Domain is now authorized! How can I help?',
          }),
        };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'https://pending-whitelist.com',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_recovery_flow_key' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    // Verify in forbidden state initially
    const dot = documentMock.getElementById('supportai-status-dot');
    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    assert.strictEqual(dot.title, 'Domain not authorized');
    assert.strictEqual(input.disabled, true);

    // SIMULATE: Tenant whitelists domain in dashboard
    domainWhitelisted = true;

    // User clicks refresh button
    const refreshBtn = documentMock.getElementById('supportai-refresh');
    assert(refreshBtn, '#supportai-refresh button must exist');
    await refreshBtn.onclick();
    await flushPromises();

    let t1_3_passed = true;
    let t1_3_err = '';

    // Verify recovery to online
    if (dot.style.backgroundColor !== '#22c55e' || dot.title !== 'Online') {
      t1_3_passed = false;
      t1_3_err += `Status dot did not recover to online! Color: ${dot.style.backgroundColor}, Title: ${dot.title}. `;
    }
    if (documentMock.getElementById('supportai-domain-warning') !== null) {
      t1_3_passed = false;
      t1_3_err += 'Domain warning banner was not removed after recovery! ';
    }
    if (input.disabled !== false) {
      t1_3_passed = false;
      t1_3_err += 'Input remained disabled after recovery. ';
    }
    if (input.placeholder !== 'Ask a recovered question...') {
      t1_3_passed = false;
      t1_3_err += `Placeholder not restored, got: ${input.placeholder}. `;
    }
    if (sendBtn.disabled !== false) {
      t1_3_passed = false;
      t1_3_err += 'Send button remained disabled after recovery. ';
    }

    // Verify subsequent chat message sends cleanly
    input.value = 'Hello after recovery!';
    sendBtn.onclick();
    await flushPromises();

    if (chatCallCount !== 1) {
      t1_3_passed = false;
      t1_3_err += `Expected 1 chat call after recovery, got ${chatCallCount}. `;
    }
    if (dot.title !== 'Online') {
      t1_3_passed = false;
      t1_3_err += `Status dot should be Online after chat response, got: ${dot.title}. `;
    }

    recordTest(
      'Recovery flow: domain whitelisting + refresh restores online status, unlocks UI, and allows chat',
      t1_3_passed,
      t1_3_err
    );
  }

  // Test 1.4: Network failure vs 403 Forbidden strict distinction
  {
    let mode = '403'; // '403' or 'network_error'
    const mockFetch = async (url) => {
      if (mode === '403') {
        return { ok: false, status: 403, json: async () => ({ detail: 'Origin not allowed' }) };
      } else {
        throw new Error('Connection refused / TypeError: Failed to fetch');
      }
    };

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_distinction_key' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const dot = documentMock.getElementById('supportai-status-dot');
    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');

    let t1_4_passed = true;
    let t1_4_err = '';

    // Check 403 state
    if (dot.title !== 'Domain not authorized' || dot.style.backgroundColor !== '#ef4444') {
      t1_4_passed = false;
      t1_4_err += `403 title expected 'Domain not authorized', got '${dot.title}'. `;
    }
    if (!documentMock.getElementById('supportai-domain-warning')) {
      t1_4_passed = false;
      t1_4_err += 'Domain warning expected in 403 state. ';
    }

    // Now switch to network error mode during chat message
    mode = 'network_error';
    // Manually reset to online to test transient chat failure
    windowMock.SupportAI.isForbidden = false;
    windowMock.SupportAI.reset();
    await flushPromises();

    input.value = 'Transient network failure test';
    sendBtn.onclick();
    await flushPromises();

    // Check network failure state
    if (dot.title !== 'Offline / Error' || dot.style.backgroundColor !== '#ef4444') {
      t1_4_passed = false;
      t1_4_err += `Network error title expected 'Offline / Error', got '${dot.title}'. `;
    }
    if (documentMock.getElementById('supportai-domain-warning') !== null) {
      t1_4_passed = false;
      t1_4_err += 'Domain warning banner MUST NOT appear on transient network error! ';
    }
    if (input.disabled === true) {
      t1_4_passed = false;
      t1_4_err += 'Input should NOT be locked disabled on network error (allows retry). ';
    }
    if (sendBtn.disabled === true) {
      t1_4_passed = false;
      t1_4_err += 'Send button should NOT be locked disabled on network error (allows retry). ';
    }

    recordTest(
      'Network failure vs 403 Forbidden: strict distinction in title, banners, and retry ability',
      t1_4_passed,
      t1_4_err
    );
  }

  // -------------------------------------------------------------------------
  // CATEGORY 2: Mobile Responsive Styling Stress Testing
  // -------------------------------------------------------------------------
  console.log('\n--- CATEGORY 2: Mobile Responsive Styling Stress Testing ---');

  // Test 2.1: Scoped CSS rules for 320px, 360px, 375px, 414px, and 480px boundary
  {
    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_css_test' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const styleEl = documentMock.getElementById('supportai-styles');
    let t2_1_passed = true;
    let t2_1_err = '';

    if (!styleEl) {
      t2_1_passed = false;
      t2_1_err += 'Injected style tag #supportai-styles not found. ';
    } else {
      const css = styleEl.textContent;

      // Extract the @media (max-width: 480px) block
      const mediaMatch = css.match(/@media\s*\(\s*max-width\s*:\s*480px\s*\)\s*\{([\s\S]*?)\n\}/);
      if (!mediaMatch) {
        t2_1_passed = false;
        t2_1_err += '@media (max-width: 480px) query block missing in CSS. ';
      } else {
        const mediaRules = mediaMatch[1];

        // Verify rules covering compact viewports: 320px (iPhone SE), 360px (Android), 375px (iPhone standard), 414px (Plus)
        const requiredDeclarations = [
          { pattern: /width:\s*calc\(100vw\s*-\s*24px\)\s*!important/i, desc: 'width calc(100vw - 24px) !important' },
          { pattern: /height:\s*calc\((?:100vh|100dvh)\s*-\s*96px\)\s*!important/i, desc: 'height calc(100vh/100dvh - 96px) !important' },
          { pattern: /bottom:\s*80px\s*!important/i, desc: 'bottom: 80px !important' },
          { pattern: /left:\s*12px\s*!important/i, desc: 'left: 12px !important' },
          { pattern: /right:\s*12px\s*!important/i, desc: 'right: 12px !important' },
          { pattern: /max-width:\s*none\s*!important/i, desc: 'max-width: none !important' },
          { pattern: /border-radius:\s*12px\s*!important/i, desc: 'border-radius: 12px !important' },
        ];

        for (const req of requiredDeclarations) {
          if (!req.pattern.test(mediaRules)) {
            t2_1_passed = false;
            t2_1_err += `Missing mobile declaration: ${req.desc}. `;
          }
        }
      }
    }

    recordTest(
      'Mobile responsive scoped CSS rules: handles 320px, 360px, 375px, 414px, and 480px bounds',
      t2_1_passed,
      t2_1_err
    );
  }

  // Test 2.2: Input font-size: 16px !important strictly enforced to prevent iOS Safari auto-zoom
  {
    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_ios_zoom_test' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const styleEl = documentMock.getElementById('supportai-styles');
    let t2_2_passed = true;
    let t2_2_err = '';

    if (!styleEl) {
      t2_2_passed = false;
      t2_2_err += 'Style element missing. ';
    } else {
      const css = styleEl.textContent;
      const mediaMatch = css.match(/@media\s*\(\s*max-width\s*:\s*480px\s*\)\s*\{([\s\S]*?)\n\}/);
      if (!mediaMatch) {
        t2_2_passed = false;
        t2_2_err += 'Media query missing. ';
      } else {
        const mediaRules = mediaMatch[1];
        // Must specifically target #supportai-input with font-size: 16px !important
        const inputRuleMatch = mediaRules.match(/#supportai-input\s*\{([^}]+)\}/);
        if (!inputRuleMatch) {
          t2_2_passed = false;
          t2_2_err += '#supportai-input rule not declared within @media (max-width: 480px). ';
        } else {
          const inputProps = inputRuleMatch[1];
          if (!/font-size:\s*16px\s*!important/i.test(inputProps)) {
            t2_2_passed = false;
            t2_2_err += `#supportai-input lacks 'font-size: 16px !important'. Content: "${inputProps.trim()}". `;
          }
        }
      }
    }

    recordTest(
      'iOS Safari auto-zoom prevention: font-size 16px !important strictly declared for #supportai-input in mobile media query',
      t2_2_passed,
      t2_2_err
    );
  }

  // Test 2.3: Desktop layout styling (>= 481px)
  {
    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_desktop_css' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const styleEl = documentMock.getElementById('supportai-styles');
    const css = styleEl.textContent;

    let t2_3_passed = true;
    let t2_3_err = '';

    // Verify desktop declarations on #supportai-chat
    if (!css.includes('width: 380px;')) {
      t2_3_passed = false;
      t2_3_err += 'Desktop width: 380px missing. ';
    }
    if (!css.includes('height: 520px;')) {
      t2_3_passed = false;
      t2_3_err += 'Desktop height: 520px missing. ';
    }
    if (!css.includes('box-sizing: border-box !important')) {
      t2_3_passed = false;
      t2_3_err += 'Box sizing reset missing. ';
    }

    recordTest(
      'Desktop layout rules (>= 481px) properly specified: 380px width, 520px height, box-sizing reset',
      t2_3_passed,
      t2_3_err
    );
  }

  // -------------------------------------------------------------------------
  // CATEGORY 3: Chat Reset & Conversational Greetings
  // -------------------------------------------------------------------------
  console.log('\n--- CATEGORY 3: Chat Reset & Conversational Greetings ---');

  // Test 3.1: Clean initial greeting without false escalations
  {
    const mockFetch = async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        bot_name: 'Customer Hero',
        welcome_message: 'Hi there! What can I help you with today?',
      }),
    });

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_clean_welcome' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const messages = documentMock.getElementById('supportai-messages');
    let t3_1_passed = true;
    let t3_1_err = '';

    if (!messages) {
      t3_1_passed = false;
      t3_1_err += '#supportai-messages missing. ';
    } else {
      const rows = messages.children;
      if (rows.length !== 1) {
        t3_1_passed = false;
        t3_1_err += `Expected exactly 1 welcome bubble, found ${rows.length}. `;
      } else {
        const welcomeText = rows[0].children[0].textContent;
        if (welcomeText !== 'Hi there! What can I help you with today?') {
          t3_1_passed = false;
          t3_1_err += `Unexpected welcome text: "${welcomeText}". `;
        }
        // False escalation check
        const lower = welcomeText.toLowerCase();
        if (lower.includes('escalat') || lower.includes('human agent') || lower.includes('live agent')) {
          t3_1_passed = false;
          t3_1_err += 'False escalation prompt detected in initial greeting! ';
        }
      }
    }

    recordTest(
      'Clean initial greeting: renders configured welcome message with zero false escalations',
      t3_1_passed,
      t3_1_err
    );
  }

  // Test 3.2: Chat reset completely purges conversation state and restores initial greeting
  {
    const sentPayloads = [];
    const mockFetch = async (url, opts) => {
      if (url.includes('/api/widget/embed/')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            bot_name: 'Bot 1',
            welcome_message: 'Fresh Welcome Message',
            placeholder_text: 'Type here...',
          }),
        };
      }
      if (url.includes('/api/chat/')) {
        const body = JSON.parse(opts.body);
        sentPayloads.push(body);
        return {
          ok: true,
          status: 200,
          json: async () => ({
            conversation_id: 'conv_session_101',
            message: 'Response to: ' + body.message,
          }),
        };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_reset_lifecycle' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const messages = documentMock.getElementById('supportai-messages');

    // 1. Send first message
    input.value = 'Message 1';
    sendBtn.onclick();
    await flushPromises();

    // 2. Send second message (should reuse conv_session_101)
    input.value = 'Message 2';
    sendBtn.onclick();
    await flushPromises();

    assert.strictEqual(sentPayloads[0].conversation_id, null);
    assert.strictEqual(sentPayloads[1].conversation_id, 'conv_session_101');
    assert.strictEqual(messages.children.length, 5); // Welcome + (User1, AI1) + (User2, AI2)

    // 3. User clicks reset button
    const refreshBtn = documentMock.getElementById('supportai-refresh');
    refreshBtn.onclick();
    await flushPromises();

    let t3_2_passed = true;
    let t3_2_err = '';

    // Verify messages wiped and only 1 welcome bubble remains
    if (messages.children.length !== 1) {
      t3_2_passed = false;
      t3_2_err += `Messages not reset to 1 welcome bubble, found ${messages.children.length}. `;
    } else {
      const bubble = messages.children[0].children[0];
      if (!bubble || bubble.textContent !== 'Fresh Welcome Message') {
        t3_2_passed = false;
        t3_2_err += 'Welcome greeting not restored after reset. ';
      }
    }

    if (input.value !== '') {
      t3_2_passed = false;
      t3_2_err += 'Input value not cleared after reset. ';
    }

    // 4. Send message 3 (MUST have conversation_id = null to verify conversationId was wiped)
    input.value = 'Message 3 After Reset';
    sendBtn.onclick();
    await flushPromises();

    if (sentPayloads.length !== 3) {
      t3_2_passed = false;
      t3_2_err += `Expected 3 chat requests, found ${sentPayloads.length}. `;
    } else if (sentPayloads[2].conversation_id !== null) {
      t3_2_passed = false;
      t3_2_err += `conversation_id leaked across reset! Sent: ${sentPayloads[2].conversation_id}, expected null. `;
    }

    recordTest(
      'Chat reset: resets conversation ID to null, wipes chat history, restores welcome greeting without leakage',
      t3_2_passed,
      t3_2_err
    );
  }

  // -------------------------------------------------------------------------
  // CATEGORY 4: Edge Cases, Security Boundaries & Stress Harness
  // -------------------------------------------------------------------------
  console.log('\n--- CATEGORY 4: Edge Cases, Security Boundaries & Stress Harness ---');

  // Test 4.1: XSS / HTML Injection Defense in Messages
  {
    const mockFetch = async (url) => {
      if (url.includes('/api/chat/')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            conversation_id: 'conv_xss',
            message: '<img src=x onerror=alert("hacked")> <script>evil()</script>',
          }),
        };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_xss_test' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const messages = documentMock.getElementById('supportai-messages');

    input.value = '<script>window.attacker=1</script>';
    sendBtn.onclick();
    await flushPromises();

    let t4_1_passed = true;
    let t4_1_err = '';

    const rows = messages.children;
    const userRow = rows[1];
    const aiRow = rows[2];

    const userBubble = userRow.children[0];
    const aiBubble = aiRow.children[0];

    // Verify textContent is exact
    if (userBubble.textContent !== '<script>window.attacker=1</script>') {
      t4_1_passed = false;
      t4_1_err += 'User textContent altered unexpectedly. ';
    }
    if (!aiBubble.textContent.includes('<script>evil()</script>')) {
      t4_1_passed = false;
      t4_1_err += 'AI textContent not preserved. ';
    }

    recordTest(
      'XSS defense: uses textContent to render user and AI messages without script evaluation',
      t4_1_passed,
      t4_1_err
    );
  }

  // Test 4.2: Whitespace and empty inputs stress test
  {
    let fetchCalled = false;
    const mockFetch = async () => {
      fetchCalled = true;
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_whitespace_test' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');

    // Test empty string
    fetchCalled = false;
    input.value = '';
    sendBtn.onclick();
    await flushPromises();
    assert.strictEqual(fetchCalled, false, 'Empty string must not trigger fetch');

    // Test whitespace only
    input.value = '   \t\n   ';
    sendBtn.onclick();
    await flushPromises();
    assert.strictEqual(fetchCalled, false, 'Whitespace must not trigger fetch');

    recordTest(
      'Whitespace stress test: empty or whitespace-only messages rejected cleanly without network calls',
      true
    );
  }

  // Test 4.3: Server URL sanitization & trailing slash normalization
  {
    let fetchedUrl = null;
    const mockFetch = async (url) => {
      fetchedUrl = url;
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'https://api.mycompany.com///widget/widget.js',
        attrs: {
          'data-business-key': 'pk_slash_test',
          'data-server-url': 'https://custom-api.company.com///',
        },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    let t4_3_passed = true;
    let t4_3_err = '';

    if (!fetchedUrl || fetchedUrl.includes('///')) {
      t4_3_passed = false;
      t4_3_err += `URL not stripped of trailing slashes: ${fetchedUrl}. `;
    }
    if (fetchedUrl !== 'https://custom-api.company.com/api/widget/embed/pk_slash_test') {
      t4_3_passed = false;
      t4_3_err += `Unexpected fetched URL: ${fetchedUrl}. `;
    }

    recordTest(
      'Server URL normalization: strips extraneous trailing slashes from explicit and inferred origins',
      t4_3_passed,
      t4_3_err
    );
  }

  // Test 4.4: Rapid concurrent interactions (double-click on refresh during loadConfig)
  {
    let loadConfigCalls = 0;
    const mockFetch = async (url) => {
      if (url.includes('/api/widget/embed/')) {
        loadConfigCalls++;
        await new Promise((r) => setTimeout(r, 15));
        return { ok: true, status: 200, json: async () => ({}) };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_race_test' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const refreshBtn = documentMock.getElementById('supportai-refresh');
    // Trigger two rapid clicks
    const p1 = refreshBtn.onclick();
    const p2 = refreshBtn.onclick();
    await Promise.all([p1, p2]);
    await flushPromises();

    const dot = documentMock.getElementById('supportai-status-dot');
    let t4_4_passed = true;
    let t4_4_err = '';

    if (dot.title !== 'Online' || dot.style.backgroundColor !== '#22c55e') {
      t4_4_passed = false;
      t4_4_err += `Status dot inconsistent after rapid clicks: ${dot.title}. `;
    }

    recordTest(
      'Rapid concurrent interactions: rapid refresh clicks settle gracefully into consistent online state',
      t4_4_passed,
      t4_4_err
    );
  }

  // Test 4.5: Credential whitespace trimming & malformed key rejection
  {
    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': '   pk_whitespace_padded_key   ' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert.strictEqual(windowMock.SupportAI.config.apiKey, 'pk_whitespace_padded_key');

    recordTest(
      'Credential extraction: automatically trims leading/trailing whitespace from data-business-key',
      true
    );
  }

  // Test 4.6: Multi-element DOM cleanup upon SupportAI.destroy()
  {
    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_destroy_test' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    assert(documentMock.getElementById('supportai-btn'));
    assert(documentMock.getElementById('supportai-chat'));
    assert(documentMock.getElementById('supportai-styles'));

    windowMock.SupportAI.destroy();

    let t4_6_passed = true;
    let t4_6_err = '';

    if (documentMock.getElementById('supportai-btn') !== null) {
      t4_6_passed = false;
      t4_6_err += '#supportai-btn was not removed. ';
    }
    if (documentMock.getElementById('supportai-chat') !== null) {
      t4_6_passed = false;
      t4_6_err += '#supportai-chat was not removed. ';
    }
    if (documentMock.getElementById('supportai-styles') !== null) {
      t4_6_passed = false;
      t4_6_err += '#supportai-styles was not removed. ';
    }
    if (windowMock.SupportAI.isInitialized !== false) {
      t4_6_passed = false;
      t4_6_err += 'isInitialized was not reset to false. ';
    }

    recordTest(
      'Lifecycle destruction: SupportAI.destroy() purges all injected elements and resets internal state',
      t4_6_passed,
      t4_6_err
    );
  }

  // Test 4.7: Asynchronous race: open() called before loadConfig() finishes
  {
    let resolveConfig;
    const configPromise = new Promise((res) => { resolveConfig = res; });
    const mockFetch = async () => configPromise;

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_race_open' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    // Call open() immediately while loadConfig is pending
    windowMock.SupportAI.open();

    // Now resolve config
    resolveConfig({
      ok: true,
      status: 200,
      json: async () => ({ bot_name: 'RaceBot' }),
    });
    await flushPromises();

    const chat = documentMock.getElementById('supportai-chat');
    const isDisplayFlex = chat && chat.style.display === 'flex';
    recordTest(
      'Asynchronous race: open() called before config fetch completes maintains display: flex',
      isDisplayFlex,
      `Expected chat display: 'flex', got: '${chat ? chat.style.display : 'null'}'`
    );
  }

  // Test 4.8: Lifecycle race: destroy() called while loadConfig() is in-flight
  {
    let resolveConfig;
    const configPromise = new Promise((res) => { resolveConfig = res; });
    const mockFetch = async () => configPromise;

    const { context, windowMock, documentMock } = createEnvironment({
      origin: 'http://localhost:3000',
      scriptTag: {
        src: 'http://localhost:8000/widget/widget.js',
        attrs: { 'data-business-key': 'pk_race_destroy' },
      },
      isCurrentScript: true,
      fetch: mockFetch,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    // Caller destroys widget while config is in-flight
    windowMock.SupportAI.destroy();

    // Catch any unhandled rejections during this async operation
    let unhandledRejectionMsg = null;
    const rejectionHandler = (reason) => {
      unhandledRejectionMsg = reason ? (reason.message || String(reason)) : 'unhandled rejection';
    };
    process.on('unhandledRejection', rejectionHandler);

    // Now resolve config
    resolveConfig({
      ok: true,
      status: 200,
      json: async () => ({ bot_name: 'DestroyedBot' }),
    });
    await flushPromises();

    process.removeListener('unhandledRejection', rejectionHandler);

    const btnAfter = documentMock.getElementById('supportai-btn');
    const chatAfter = documentMock.getElementById('supportai-chat');
    const cleanAbort = !unhandledRejectionMsg && btnAfter === null && chatAfter === null;

    recordTest(
      'Lifecycle race: destroy() during in-flight loadConfig cleanly aborts without mounting DOM or throwing',
      cleanAbort,
      unhandledRejectionMsg ? `Uncaught rejection: ${unhandledRejectionMsg}` : (btnAfter || chatAfter ? 'Elements re-mounted into DOM after destroy()' : '')
    );
  }

  // =========================================================================
  // SUMMARY REPORT
  // =========================================================================
  console.log('\n================================================================');
  console.log(`ADVERSARIAL STRESS TEST SUITE COMPLETE`);
  console.log(`TOTAL TESTS: ${passCount + failCount}`);
  console.log(`PASSED: ${passCount}`);
  console.log(`FAILED: ${failCount}`);
  console.log(`VERDICT: ${failCount === 0 ? 'APPROVE' : 'REQUEST_CHANGES'}`);
  console.log('================================================================\n');

  // Challenger exits cleanly so runner can inspect structured output
}

runAdversarialSuite().catch((err) => {
  console.error('Adversarial Harness Error:', err);
  process.exit(1);
});
