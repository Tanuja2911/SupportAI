/**
 * Comprehensive Verification Test Suite for Milestone 2:
 * Ultra-Modern Embed Widget UI/UX Overhaul (widget/widget.js)
 *
 * Verifies Intercom/Crisp/Stripe design overhaul:
 * - Floating gradient launcher with SVG speech bubble <-> close icon morphing and entrance pulse
 * - Header with bot avatar, live glowing presence pulse dot ("Active now"), and crisp SVG action buttons
 * - Chat canvas with distinct AI/User/System styling, timestamps, and slide-in animations
 * - Zero-dependency lightweight markdown parser (bold, italic, inline code, code blocks, lists, safe links, XSS defense)
 * - Sleek 3-dot wave typing indicator (#supportai-typing-indicator)
 * - Rounded pill input capsule, keyboard shortcuts (Enter to send, Shift+Enter for newline), SVG send button
 * - Mobile sheet drawer (<480px) with iOS safe area insets and 16px font size
 * - Clean session reset ("New Chat") flow
 * - 100% preservation of all 25 contract tokens
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const widgetJsPath = path.resolve(__dirname, 'widget.js');
const widgetSource = fs.readFileSync(widgetJsPath, 'utf8');

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 25));

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
// MOCK DOM SIMULATOR FOR MODERN WIDGET TESTING
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

    // Parse paired child elements with id, class, title, style, and content
    const tagMatches = [...html.matchAll(/<([a-zA-Z0-9]+)([^>]*?id="([^"]+)"[^>]*?)>([\s\S]*?)<\/\1>/g)];
    for (const match of tagMatches) {
      const tag = match[1].toUpperCase();
      const attrsStr = match[2];
      const childId = match[3];
      const content = match[4];

      if (!this.querySelector('#' + childId)) {
        const childEl = new MockElement(tag, childId);
        childEl.textContent = content.replace(/<[^>]+>/g, '').trim();
        childEl._innerHTML = content;
        const classMatch = attrsStr.match(/class="([^"]+)"/);
        if (classMatch) childEl.className = classMatch[1];
        const titleMatch = attrsStr.match(/title="([^"]+)"/);
        if (titleMatch) childEl.title = titleMatch[1];
        this.appendChild(childEl);
      }
    }

    // Also fallback to match self-closing or empty elements with id
    const selfClosingMatches = [...html.matchAll(/<([a-zA-Z0-9]+)([^>]*?id="([^"]+)"[^>]*?)\/?>/g)];
    for (const match of selfClosingMatches) {
      const tag = match[1].toUpperCase();
      const attrsStr = match[2];
      const childId = match[3];

      if (!this.querySelector('#' + childId)) {
        const childEl = new MockElement(tag, childId);
        const classMatch = attrsStr.match(/class="([^"]+)"/);
        if (classMatch) childEl.className = classMatch[1];
        const titleMatch = attrsStr.match(/title="([^"]+)"/);
        if (titleMatch) childEl.title = titleMatch[1];
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
    function search(node) {
      if (selector.startsWith('#')) {
        if (node.id === selector.slice(1)) results.push(node);
      } else if (selector.startsWith('.')) {
        if (node.className && node.className.includes(selector.slice(1))) results.push(node);
      }
      for (const c of node.children) search(c);
    }
    search(this);
    return results;
  }

  addEventListener(event, fn) {
    if (!this.eventListeners[event]) this.eventListeners[event] = [];
    this.eventListeners[event].push(fn);
  }
}

function createModernTestEnvironment(options = {}) {
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
      origin: options.origin || 'https://client-store.com',
      href: (options.origin || 'https://client-store.com') + '/shop',
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

async function runModernWidgetTestSuite() {
  console.log('================================================================');
  console.log('STARTING ULTRA-MODERN EMBED WIDGET VERIFICATION SUITE');
  console.log('================================================================\n');

  // =========================================================================
  // CATEGORY 1: Floating Launcher & SVG Morphing Transitions
  // =========================================================================
  console.log('--- CATEGORY 1: Floating Launcher & SVG Morphing Transitions ---');

  // Test 1.1: Launcher SVG icons (bubble and close) present with morphing classes
  {
    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_launcher_test' },
      },
      isCurrentScript: true,
      fetch: async () => ({
        ok: true,
        status: 200,
        json: async () => ({
          bot_name: 'Modern Bot',
          primary_color: '#4f46e5',
        }),
      }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const btn = documentMock.getElementById('supportai-btn');
    let t1_1_passed = true;
    let t1_1_err = '';

    if (!btn) {
      t1_1_passed = false;
      t1_1_err += '#supportai-btn not found. ';
    } else {
      // Check for dual SVG icons inside launcher button
      if (!btn.innerHTML.includes('supportai-icon-bubble')) {
        t1_1_passed = false;
        t1_1_err += 'Missing .supportai-icon-bubble in launcher. ';
      }
      if (!btn.innerHTML.includes('supportai-icon-close')) {
        t1_1_passed = false;
        t1_1_err += 'Missing .supportai-icon-close in launcher. ';
      }
      // Check for gradient background styling
      if (!btn.style.background || !btn.style.background.includes('gradient')) {
        t1_1_passed = false;
        t1_1_err += 'Launcher button background lacks gradient styling. ';
      }
    }

    recordTest(
      'Launcher SVG dual-icon markup (speech bubble & close) with brand gradient',
      t1_1_passed,
      t1_1_err
    );
  }

  // Test 1.2: Launcher morphing state toggles on open() and close()
  {
    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_morph_test' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const btn = documentMock.getElementById('supportai-btn');
    let t1_2_passed = true;
    let t1_2_err = '';

    // Initially closed: not is-open
    if (btn.className.includes('is-open')) {
      t1_2_passed = false;
      t1_2_err += 'Launcher should not have is-open initially. ';
    }

    // Programmatically open widget
    windowMock.SupportAI.open();
    if (!btn.className.includes('is-open')) {
      t1_2_passed = false;
      t1_2_err += 'Launcher failed to gain is-open class on SupportAI.open(). ';
    }

    // Programmatically close widget
    windowMock.SupportAI.close();
    if (btn.className.includes('is-open')) {
      t1_2_passed = false;
      t1_2_err += 'Launcher failed to remove is-open class on SupportAI.close(). ';
    }

    // Toggle widget
    windowMock.SupportAI.toggle();
    if (!btn.className.includes('is-open')) {
      t1_2_passed = false;
      t1_2_err += 'Launcher failed to gain is-open class on SupportAI.toggle(). ';
    }

    recordTest(
      'Launcher SVG morphing transition class (.is-open) toggles correctly across open/close/toggle',
      t1_2_passed,
      t1_2_err
    );
  }

  // =========================================================================
  // CATEGORY 2: Modern Header with Avatar, Presence Dot, and Actions
  // =========================================================================
  console.log('\n--- CATEGORY 2: Modern Header, Avatar & Presence Dot ---');

  // Test 2.1: Header contains bot avatar, status dot with glow pulse, and subtitle
  {
    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_header_test' },
      },
      isCurrentScript: true,
      fetch: async () => ({
        ok: true,
        status: 200,
        json: async () => ({
          bot_name: 'Crisp Assistant',
          primary_color: '#0ea5e9',
        }),
      }),
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const header = documentMock.getElementById('supportai-header');
    const avatar = documentMock.getElementById('supportai-avatar');
    const dot = documentMock.getElementById('supportai-status-dot');
    const label = documentMock.getElementById('supportai-status-label');
    const botName = documentMock.getElementById('supportai-bot-name');

    let t2_1_passed = true;
    let t2_1_err = '';

    if (!header) {
      t2_1_passed = false;
      t2_1_err += '#supportai-header missing. ';
    }
    if (!avatar) {
      t2_1_passed = false;
      t2_1_err += '#supportai-avatar bot avatar element missing. ';
    }
    if (!dot) {
      t2_1_passed = false;
      t2_1_err += '#supportai-status-dot missing. ';
    } else {
      if (dot.className !== 'online') {
        t2_1_passed = false;
        t2_1_err += `Status dot class should be online, got: ${dot.className}. `;
      }
    }
    if (!label || label.textContent !== 'Active now') {
      t2_1_passed = false;
      t2_1_err += `Live presence label should be "Active now", got: "${label ? label.textContent : 'null'}". `;
    }
    if (!botName || botName.textContent !== 'Crisp Assistant') {
      t2_1_passed = false;
      t2_1_err += `Bot name should be "Crisp Assistant", got: "${botName ? botName.textContent : 'null'}". `;
    }

    recordTest(
      'Header layout includes bot avatar, live status dot (.online), and "Active now" presence indicator',
      t2_1_passed,
      t2_1_err
    );
  }

  // Test 2.2: Status changes dynamically update subtitle label
  {
    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_status_label_test' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const label = documentMock.getElementById('supportai-status-label');
    let t2_2_passed = true;
    let t2_2_err = '';

    windowMock.SupportAI.setStatus('connecting');
    if (label.textContent !== 'Connecting...') {
      t2_2_passed = false;
      t2_2_err += `Expected label Connecting..., got: ${label.textContent}. `;
    }

    windowMock.SupportAI.setStatus('error');
    if (label.textContent !== 'Offline') {
      t2_2_passed = false;
      t2_2_err += `Expected label Offline, got: ${label.textContent}. `;
    }

    windowMock.SupportAI.setStatus('forbidden');
    if (label.textContent !== 'Unauthorized') {
      t2_2_passed = false;
      t2_2_err += `Expected label Unauthorized, got: ${label.textContent}. `;
    }

    windowMock.SupportAI.setStatus('online');
    if (label.textContent !== 'Active now') {
      t2_2_passed = false;
      t2_2_err += `Expected label Active now, got: ${label.textContent}. `;
    }

    recordTest(
      'Presence subtitle updates reactively across all connection states',
      t2_2_passed,
      t2_2_err
    );
  }

  // Test 2.3: Action buttons have SVG icons and rotation animation on refresh
  {
    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_actions_test' },
      },
      isCurrentScript: true,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const refreshBtn = documentMock.getElementById('supportai-refresh');
    const closeBtn = documentMock.getElementById('supportai-close');

    let t2_3_passed = true;
    let t2_3_err = '';

    if (!refreshBtn || !refreshBtn.innerHTML.includes('<svg')) {
      t2_3_passed = false;
      t2_3_err += '#supportai-refresh missing crisp SVG icon. ';
    }
    if (!closeBtn || !closeBtn.innerHTML.includes('<svg')) {
      t2_3_passed = false;
      t2_3_err += '#supportai-close missing crisp SVG icon. ';
    }

    // Trigger refresh click to verify rotation animation class
    refreshBtn.onclick();
    if (!refreshBtn.className.includes('supportai-spinning')) {
      t2_3_passed = false;
      t2_3_err += 'Refresh button did not trigger spinning rotation animation class. ';
    }

    recordTest(
      'Action controls use crisp SVG icons with micro-interaction rotation on refresh',
      t2_3_passed,
      t2_3_err
    );
  }

  // =========================================================================
  // CATEGORY 3: Zero-Dependency Lightweight Markdown Engine & XSS Defense
  // =========================================================================
  console.log('\n--- CATEGORY 3: Safe Lightweight Markdown Engine & XSS Defense ---');

  // Test 3.1: Markdown formatting for bold, italic, inline code, and fenced code blocks
  {
    const mockChat = async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        conversation_id: 'conv_md_1',
        message: 'Here is **bold text**, *italic emphasis*, `inline code`, and:\n```javascript\nconst modern = true;\n```\nEnjoy!',
      }),
    });

    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_markdown_test' },
      },
      isCurrentScript: true,
      fetch: mockChat,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const msgs = documentMock.getElementById('supportai-messages');

    input.value = 'Show me formatting';
    sendBtn.onclick();
    await flushPromises();

    const aiRow = msgs.children[msgs.children.length - 1];
    const aiBubble = aiRow.children[0];

    let t3_1_passed = true;
    let t3_1_err = '';

    const html = aiBubble.innerHTML;
    if (!html.includes('<strong>bold text</strong>')) {
      t3_1_passed = false;
      t3_1_err += 'Bold markdown not rendered to <strong>. ';
    }
    if (!html.includes('<em>italic emphasis</em>')) {
      t3_1_passed = false;
      t3_1_err += 'Italic markdown not rendered to <em>. ';
    }
    if (!html.includes('<code class="supportai-inline-code">inline code</code>')) {
      t3_1_passed = false;
      t3_1_err += 'Inline code not rendered to <code class="supportai-inline-code">. ';
    }
    if (!html.includes('<pre class="supportai-code-block"><code>const modern = true;</code></pre>')) {
      t3_1_passed = false;
      t3_1_err += 'Fenced code block not rendered to <pre class="supportai-code-block">. ';
    }

    recordTest(
      'Markdown engine successfully parses bold, italic, inline code, and fenced code blocks',
      t3_1_passed,
      t3_1_err
    );
  }

  // Test 3.2: Markdown formatting for bullet lists and safe links
  {
    const mockChat = async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        conversation_id: 'conv_md_2',
        message: 'Features:\n- Fast response\n- 24/7 Support\n\nVisit [Documentation](https://supportai.com/docs) or [Email](mailto:help@supportai.com)',
      }),
    });

    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_md_lists_test' },
      },
      isCurrentScript: true,
      fetch: mockChat,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const msgs = documentMock.getElementById('supportai-messages');

    input.value = 'List features';
    sendBtn.onclick();
    await flushPromises();

    const aiRow = msgs.children[msgs.children.length - 1];
    const aiBubble = aiRow.children[0];

    let t3_2_passed = true;
    let t3_2_err = '';

    const html = aiBubble.innerHTML;
    if (!html.includes('<ul class="supportai-ul">') || !html.includes('<li class="supportai-li">Fast response</li>')) {
      t3_2_passed = false;
      t3_2_err += 'Unordered list not rendered properly. ';
    }
    if (!html.includes('<a href="https://supportai.com/docs" target="_blank" rel="noopener noreferrer" class="supportai-link">Documentation</a>')) {
      t3_2_passed = false;
      t3_2_err += 'Safe HTTPS link not rendered properly. ';
    }
    if (!html.includes('<a href="mailto:help@supportai.com" target="_blank" rel="noopener noreferrer" class="supportai-link">Email</a>')) {
      t3_2_passed = false;
      t3_2_err += 'Safe mailto link not rendered properly. ';
    }

    recordTest(
      'Markdown engine parses bullet lists and safe links (https:// and mailto:)',
      t3_2_passed,
      t3_2_err
    );
  }

  // Test 3.3: Strict XSS sanitization and JavaScript URL neutralization
  {
    const mockChat = async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        conversation_id: 'conv_md_3',
        message: '<script>alert(1)</script><img src=x onerror=alert(2)> [Malicious](javascript:alert(3))',
      }),
    });

    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_xss_defense_test' },
      },
      isCurrentScript: true,
      fetch: mockChat,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const msgs = documentMock.getElementById('supportai-messages');

    input.value = '<script>evil()</script>';
    sendBtn.onclick();
    await flushPromises();

    const aiRow = msgs.children[msgs.children.length - 1];
    const aiBubble = aiRow.children[0];

    let t3_3_passed = true;
    let t3_3_err = '';

    const html = aiBubble.innerHTML;
    // Must NOT contain raw unescaped script tags
    if (html.includes('<script>')) {
      t3_3_passed = false;
      t3_3_err += 'Raw <script> tag detected in HTML! ';
    }
    if (html.includes('<img src=x')) {
      t3_3_passed = false;
      t3_3_err += 'Raw <img> tag detected in HTML! ';
    }
    if (html.includes('href="javascript:')) {
      t3_3_passed = false;
      t3_3_err += 'javascript: URI allowed in href attribute! ';
    }
    // Must have escaped characters
    if (!html.includes('&lt;script&gt;') || !html.includes('&lt;img src=x')) {
      t3_3_passed = false;
      t3_3_err += 'HTML entities were not properly escaped. ';
    }

    recordTest(
      'Strict XSS defense: raw HTML tags escaped and javascript: URIs neutralized',
      t3_3_passed,
      t3_3_err
    );
  }

  // =========================================================================
  // CATEGORY 4: 3-Dot Wave Typing Indicator (#supportai-typing-indicator)
  // =========================================================================
  console.log('\n--- CATEGORY 4: 3-Dot Wave Typing Indicator ---');

  // Test 4.1: Typing indicator renders during in-flight fetch and removes on response
  {
    let resolveChat;
    const pendingPromise = new Promise((resolve) => {
      resolveChat = resolve;
    });

    const mockChat = async (url) => {
      if (url.includes('/api/chat/')) {
        return pendingPromise;
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_typing_test' },
      },
      isCurrentScript: true,
      fetch: mockChat,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const msgs = documentMock.getElementById('supportai-messages');

    input.value = 'Calculate answer...';
    sendBtn.onclick();

    let t4_1_passed = true;
    let t4_1_err = '';

    // While in-flight: #supportai-typing-indicator MUST be present in messages
    const indicator = documentMock.getElementById('supportai-typing-indicator');
    if (!indicator) {
      t4_1_passed = false;
      t4_1_err += '#supportai-typing-indicator not rendered during in-flight fetch. ';
    } else {
      if (!indicator.innerHTML.includes('supportai-typing-dots') || !indicator.innerHTML.includes('supportai-typing-dot')) {
        t4_1_passed = false;
        t4_1_err += 'Typing indicator lacks .supportai-typing-dots markup. ';
      }
    }

    // Resolve chat
    resolveChat({
      ok: true,
      status: 200,
      json: async () => ({
        conversation_id: 'conv_typing_1',
        message: '42 is the answer.',
      }),
    });
    await flushPromises();

    // After resolution: typing indicator MUST be removed
    const indicatorAfter = documentMock.getElementById('supportai-typing-indicator');
    if (indicatorAfter !== null) {
      t4_1_passed = false;
      t4_1_err += '#supportai-typing-indicator was not removed after response arrived. ';
    }

    recordTest(
      '3-Dot wave typing indicator mounts during in-flight request and unmounts upon completion',
      t4_1_passed,
      t4_1_err
    );
  }

  // Test 4.2: Typing indicator safely cleared on error or session reset
  {
    let resolveChat;
    const pendingPromise = new Promise((resolve) => {
      resolveChat = resolve;
    });

    const mockChat = async (url) => {
      if (url.includes('/api/chat/')) {
        return pendingPromise;
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };

    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_typing_reset_test' },
      },
      isCurrentScript: true,
      fetch: mockChat,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const refreshBtn = documentMock.getElementById('supportai-refresh');

    input.value = 'In-flight before reset';
    sendBtn.onclick();

    assert(documentMock.getElementById('supportai-typing-indicator'), 'Indicator present');

    // Trigger reset mid-flight
    refreshBtn.onclick();
    await flushPromises();

    let t4_2_passed = true;
    let t4_2_err = '';

    if (documentMock.getElementById('supportai-typing-indicator') !== null) {
      t4_2_passed = false;
      t4_2_err += 'Typing indicator remained after session reset! ';
    }

    recordTest(
      'Typing indicator safely purged when session reset is clicked during in-flight request',
      t4_2_passed,
      t4_2_err
    );
  }

  // =========================================================================
  // CATEGORY 5: Pill Input Capsule, Keyboard Ergonomics & Send Button
  // =========================================================================
  console.log('\n--- CATEGORY 5: Input Capsule, Keyboard Ergonomics & Send Button ---');

  // Test 5.1: Pill capsule structure, Enter shortcut, and Shift+Enter multiline behavior
  {
    let messageSent = 0;
    const mockChat = async (url) => {
      if (url.includes('/api/chat/')) {
        messageSent++;
      }
      return { ok: true, status: 200, json: async () => ({ conversation_id: 'conv_keys', message: 'Got it' }) };
    };

    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_input_capsule_test' },
      },
      isCurrentScript: true,
      fetch: mockChat,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');

    let t5_1_passed = true;
    let t5_1_err = '';

    // Verify SVG icon inside send button
    if (!sendBtn.innerHTML.includes('<svg') || !sendBtn.innerHTML.includes('supportai-send-icon')) {
      t5_1_passed = false;
      t5_1_err += 'Send button lacks SVG paper plane markup. ';
    }

    // Press Shift+Enter -> Should NOT send message
    input.value = 'Multiline line 1';
    input.onkeydown({ key: 'Enter', shiftKey: true, preventDefault: () => {} });
    await flushPromises();

    if (messageSent !== 0) {
      t5_1_passed = false;
      t5_1_err += 'Shift+Enter prematurely dispatched message! ';
    }

    // Press Enter without Shift -> MUST send message
    input.onkeydown({ key: 'Enter', shiftKey: false, preventDefault: () => {} });
    await flushPromises();

    if (messageSent !== 1) {
      t5_1_passed = false;
      t5_1_err += `Enter key failed to send message! Sent count: ${messageSent}. `;
    }

    recordTest(
      'Pill input capsule with Enter to send, Shift+Enter to newline, and SVG paper plane send button',
      t5_1_passed,
      t5_1_err
    );
  }

  // =========================================================================
  // CATEGORY 6: Chat Canvas Hierarchy, Bubbles & Timestamps
  // =========================================================================
  console.log('\n--- CATEGORY 6: Canvas Hierarchy, Bubbles & Timestamps ---');

  // Test 6.1: Discreet relative timestamps rendered underneath each message
  {
    const mockChat = async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        conversation_id: 'conv_ts',
        message: 'Timestamp verified.',
      }),
    });

    const { context, windowMock, documentMock } = createModernTestEnvironment({
      origin: 'https://client-store.com',
      scriptTag: {
        src: 'https://support.ai/widget/widget.js',
        attrs: { 'data-business-key': 'pk_timestamps_test' },
      },
      isCurrentScript: true,
      fetch: mockChat,
    });

    vm.runInContext(widgetSource, context);
    await flushPromises();

    const input = documentMock.getElementById('supportai-input');
    const sendBtn = documentMock.getElementById('supportai-send-btn');
    const msgs = documentMock.getElementById('supportai-messages');

    input.value = 'Check timestamp';
    sendBtn.onclick();
    await flushPromises();

    let t6_1_passed = true;
    let t6_1_err = '';

    // Verify all rows have bubble as children[0] and timestamp as children[1]
    for (let i = 0; i < msgs.children.length; i++) {
      const row = msgs.children[i];
      const bubble = row.children[0];
      const ts = row.children[1];

      if (!bubble || !bubble.className.includes('supportai-bubble')) {
        t6_1_passed = false;
        t6_1_err += `Row ${i} missing bubble at children[0]. `;
      }
      if (!ts || !ts.className.includes('supportai-timestamp')) {
        t6_1_passed = false;
        t6_1_err += `Row ${i} missing timestamp at children[1]. `;
      } else if (!ts.textContent || !ts.textContent.includes(':')) {
        t6_1_passed = false;
        t6_1_err += `Row ${i} timestamp text formatted unexpectedly: "${ts.textContent}". `;
      }
    }

    recordTest(
      'Discreet relative timestamps attached to all AI, User, and Welcome message bubbles',
      t6_1_passed,
      t6_1_err
    );
  }

  // =========================================================================
  // CATEGORY 7: Mobile Responsiveness & Contract Tokens
  // =========================================================================
  console.log('\n--- CATEGORY 7: Mobile Sheet (<480px) & 25 Contract Invariants ---');

  // Test 7.1: Mobile media query includes safe area insets and 16px font-size
  {
    let t7_1_passed = true;
    let t7_1_err = '';

    if (!widgetSource.includes('@media (max-width: 480px)')) {
      t7_1_passed = false;
      t7_1_err += '@media (max-width: 480px) missing. ';
    }
    if (!widgetSource.includes('calc(100vw - 24px) !important')) {
      t7_1_passed = false;
      t7_1_err += 'calc(100vw - 24px) !important missing. ';
    }
    if (!widgetSource.includes('calc(100vh - 96px) !important') && !widgetSource.includes('calc(100dvh - 96px) !important')) {
      t7_1_passed = false;
      t7_1_err += 'Mobile height calc missing. ';
    }
    if (!widgetSource.includes('16px !important')) {
      t7_1_passed = false;
      t7_1_err += '16px !important input zoom prevention missing. ';
    }
    if (!widgetSource.includes('env(safe-area-inset-bottom')) {
      t7_1_passed = false;
      t7_1_err += 'iOS safe-area-inset-bottom padding missing. ';
    }

    recordTest(
      'Mobile drawer rules conform to iOS safe areas and 16px auto-zoom prevention',
      t7_1_passed,
      t7_1_err
    );
  }

  // Test 7.2: Comprehensive Contract Tokens Verification (all 25 tokens strictly preserved)
  {
    const requiredContractTokens = [
      'scripts[i].src',
      'currentScript',
      'detectedServerUrl',
      'serverUrl',
      'window.SupportAI',
      '/api/widget/embed/',
      '/api/chat/',
      'primary_color',
      'primaryColor',
      'zIndex',
      'position',
      'data-business-key',
      'data-api-key',
      'id="supportai-styles"',
      '@media (max-width: 480px)',
      'calc(100vw - 24px) !important',
      'calc(100vh - 96px) !important',
      '16px !important',
      'supportai-status-dot',
      'supportai-domain-warning',
      'Domain not authorized',
      'supportai-refresh',
      'supportai-close',
      'supportai-messages',
      'supportai-input-area',
      'supportai-input',
      'supportai-send-btn',
      'supportai-branding',
      'supportai-pos-right',
      'supportai-pos-left',
      'online',
      'connecting',
      'error',
      'forbidden',
    ];

    let t7_2_passed = true;
    let missingTokens = [];

    for (const token of requiredContractTokens) {
      if (!widgetSource.includes(token)) {
        t7_2_passed = false;
        missingTokens.push(token);
      }
    }

    recordTest(
      'Preservation of all contract tokens for 100% backward compatibility',
      t7_2_passed,
      missingTokens.length ? `Missing tokens: ${missingTokens.join(', ')}` : ''
    );
  }

  console.log('\n================================================================');
  console.log(`MODERN WIDGET TEST SUITE COMPLETE: ${passCount} PASSED, ${failCount} FAILED out of ${passCount + failCount}`);
  console.log('================================================================');

  if (failCount > 0) {
    process.exit(1);
  }
}

runModernWidgetTestSuite().catch((err) => {
  console.error('Modern widget test suite uncaught exception:', err);
  process.exit(1);
});
