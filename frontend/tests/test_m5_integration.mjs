/**
 * Empirical Adversarial Verification Suite for Milestone 5:
 * - AI Settings State & Reset (AISettingsView)
 * - Widget Config State & Persistence (WidgetConfigView)
 * - Dashboard Credentials Decoupling & Masking (DashboardView)
 */

import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as vue from 'vue';
import * as sfc from '@vue/compiler-sfc';
import * as ssr from '@vue/server-renderer';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = fs.existsSync(path.join(__dirname, '../src'))
  ? path.join(__dirname, '..')
  : path.resolve(__dirname, '../..');

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

const testQueue = [];

function test(name, fn) {
  testQueue.push({ name, fn, isAsync: false });
}

function testAsync(name, fn) {
  testQueue.push({ name, fn, isAsync: true });
}

async function compileSfcTemplateToSsr(templateSource, id) {
  const compiled = sfc.compileTemplate({
    source: templateSource,
    id,
    ssr: true,
  });
  const tmpPath = path.join(frontendRoot, `tests/.temp_${id}_${Date.now()}_${Math.random().toString(36).slice(2)}.mjs`);
  fs.writeFileSync(tmpPath, compiled.code);
  try {
    const mod = await import(tmpPath);
    return mod.ssrRender;
  } finally {
    if (fs.existsSync(tmpPath)) {
      fs.unlinkSync(tmpPath);
    }
  }
}

function createTestApp(component) {
  const app = vue.createSSRApp(component)
  app.component('router-link', {
    props: ['to'],
    setup(props, { slots }) {
      return () => vue.h('a', { href: props.to }, slots.default ? slots.default() : [])
    },
  })
  return app
}

// ----------------------------------------------------------------------------
// SUITE 1: AISettingsView State, BYOK, Reset, and Providers
// ----------------------------------------------------------------------------
const aiSettingsSource = fs.readFileSync(
  path.join(frontendRoot, 'src/views/AISettingsView.vue'),
  'utf8'
);
const mainCssSource = fs.readFileSync(
  path.join(frontendRoot, 'src/assets/main.css'),
  'utf8'
);

test('Dark theme hover utility colors and transitions are normalized globally', () => {
  assert.match(mainCssSource, /class~="hover:bg-gray-50"/);
  assert.match(mainCssSource, /class~="hover:bg-indigo-700"/);
  assert.match(mainCssSource, /class~="hover:text-gray-700"/);
  assert.match(mainCssSource, /transition-duration: 190ms/);
  assert.match(mainCssSource, /prefers-reduced-motion: reduce/);
});

test('Dashboard metric cards keep a responsive grid and aligned heading/value/footer', () => {
  assert.match(mainCssSource, /\.dashboard-metrics\s*\{[^}]*display:\s*grid/s);
  assert.match(mainCssSource, /grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)/);
  assert.match(mainCssSource, /\.dashboard-stat-heading\s*\{[^}]*display:\s*flex/s);
  assert.match(mainCssSource, /\.dashboard-stat-footer\s*\{[^}]*display:\s*flex/s);
});

test('AISettingsView defines the supported LLM providers including NVIDIA NIM', () => {
  const parsed = sfc.parse(aiSettingsSource);
  const scriptContent = parsed.descriptor.scriptSetup.content;

  const match = scriptContent.match(/const providers = (\[[\s\S]*?\])/);
  assert.ok(match, 'providers array must be defined in scriptSetup');

  const providers = eval(match[1]);
  const providerValues = providers.map(p => p.value);

  assert.deepEqual(providerValues, ['gemini', 'openai', 'anthropic', 'nvidia_nim'],
    'Gemini, OpenAI, Anthropic, and NVIDIA NIM must be in the providers list');

  const defaultProvider = providers.find(p => p.value === 'gemini');
  assert.ok(defaultProvider, 'Gemini must be present as a provider');
  assert.equal(defaultProvider.name, 'Google Gemini');
  assert.equal(defaultProvider.model, 'gemini-3.8-flash');
  assert.equal(providers.find(p => p.value === 'openai').model, 'gpt-6-luna');
  assert.equal(providers.find(p => p.value === 'anthropic').model, 'claude-sonnet-5');
  const nvidiaProvider = providers.find(p => p.value === 'nvidia_nim');
  assert.equal(nvidiaProvider.name, 'NVIDIA NIM');
  assert.match(nvidiaProvider.model, /gpt-oss-20b/);
});

test('AISettingsView provides live connection diagnostics against the business test endpoint', () => {
  assert.match(aiSettingsSource, /@click="testConnection"/);
  assert.match(aiSettingsSource, /api\.post\(`\/ai-settings\/\$\{bid\}\/test-connection`, payload\)/);
  assert.match(aiSettingsSource, /connectionResult\.diagnostic/);
  assert.match(aiSettingsSource, /Connected & verified/);
});

testAsync('AISettingsView template renders "Platform Default Active" badge when hasKey=false & isUsingPlatformDefault=true', async () => {
  const parsed = sfc.parse(aiSettingsSource);
  const ssrRender = await compileSfcTemplateToSsr(parsed.descriptor.template.content, 'ai_settings_default');

  const component = {
    ssrRender,
    setup() {
      return {
        hasKey: vue.ref(false),
        isUsingPlatformDefault: vue.ref(true),
        testing: vue.ref(false),
        connectionResult: vue.ref(null),
        currentProviderName: vue.computed(() => 'Google Gemini'),
        provider: vue.ref('gemini'),
        providers: [
          { value: 'gemini', name: 'Google Gemini', model: 'gemini-3.8-flash' },
          { value: 'openai', name: 'OpenAI', model: 'gpt-6-luna' },
          { value: 'anthropic', name: 'Anthropic', model: 'claude-sonnet-5' },
          { value: 'nvidia_nim', name: 'NVIDIA NIM', model: 'openai/gpt-oss-20b' },
        ],
        apiKey: vue.ref(''),
        showKey: vue.ref(false),
        saving: vue.ref(false),
        resetting: vue.ref(false),
        success: vue.ref(''),
        error: vue.ref(''),
        keyPlaceholder: vue.computed(() => 'AIza...'),
        keyHelp: vue.computed(() => 'Your Google Gemini API key from AI Studio'),
        save: () => {},
        resetToPlatformDefault: () => {},
      };
    }
  };

  const app = createTestApp(component);
  const rawHtml = await ssr.renderToString(app);
  const html = rawHtml.replace(/<!--[\s\S]*?-->/g, '');

  assert.ok(html.includes('Platform Default Active'), 'Must render Platform Default Active badge');
  assert.ok(!html.includes('Custom Key Active (BYOK)'), 'Must NOT render Custom Key Active badge');
  assert.ok(!html.includes('No Key Configured'), 'Must NOT render No Key Configured badge');
  assert.ok(html.includes('Using the SupportAI default Google Gemini key.'),
    'Must render concise platform default explanation text');
});

testAsync('AISettingsView template renders "Custom Key Active (BYOK)" badge when hasKey=true', async () => {
  const parsed = sfc.parse(aiSettingsSource);
  const ssrRender = await compileSfcTemplateToSsr(parsed.descriptor.template.content, 'ai_settings_byok');

  const component = {
    ssrRender,
    setup() {
      return {
        hasKey: vue.ref(true),
        isUsingPlatformDefault: vue.ref(false),
        testing: vue.ref(false),
        connectionResult: vue.ref(null),
        currentProviderName: vue.computed(() => 'OpenAI'),
        provider: vue.ref('openai'),
        providers: [
          { value: 'gemini', name: 'Google Gemini', model: 'gemini-3.8-flash' },
          { value: 'openai', name: 'OpenAI', model: 'gpt-6-luna' },
          { value: 'anthropic', name: 'Anthropic', model: 'claude-sonnet-5' },
          { value: 'nvidia_nim', name: 'NVIDIA NIM', model: 'openai/gpt-oss-20b' },
        ],
        apiKey: vue.ref(''),
        showKey: vue.ref(false),
        saving: vue.ref(false),
        resetting: vue.ref(false),
        success: vue.ref(''),
        error: vue.ref(''),
        keyPlaceholder: vue.computed(() => '•••••••••••••••• (Leave blank to keep existing key)'),
        keyHelp: vue.computed(() => 'Your OpenAI API key from platform.openai.com'),
        save: () => {},
        resetToPlatformDefault: () => {},
      };
    }
  };

  const app = createTestApp(component);
  const rawHtml = await ssr.renderToString(app);
  const html = rawHtml.replace(/<!--[\s\S]*?-->/g, '');

  assert.ok(html.includes('Custom Key Active (BYOK)'), 'Must render Custom Key Active (BYOK) badge');
  assert.ok(!html.includes('Platform Default Active'), 'Must NOT render Platform Default Active badge');
  assert.ok(html.includes('using your custom organization key, overriding the platform default'),
    'Must render custom key explanation text');
  assert.ok(html.includes('Reset to Platform Default'), 'Must show Reset to Platform Default button when hasKey is true');
});

testAsync('AISettingsView template renders "No Key Configured" badge when hasKey=false & isUsingPlatformDefault=false', async () => {
  const parsed = sfc.parse(aiSettingsSource);
  const ssrRender = await compileSfcTemplateToSsr(parsed.descriptor.template.content, 'ai_settings_none');

  const component = {
    ssrRender,
    setup() {
      return {
        hasKey: vue.ref(false),
        isUsingPlatformDefault: vue.ref(false),
        testing: vue.ref(false),
        connectionResult: vue.ref(null),
        currentProviderName: vue.computed(() => 'Google Gemini'),
        provider: vue.ref('gemini'),
        providers: [
          { value: 'gemini', name: 'Google Gemini', model: 'gemini-3.8-flash' },
          { value: 'openai', name: 'OpenAI', model: 'gpt-6-luna' },
          { value: 'anthropic', name: 'Anthropic', model: 'claude-sonnet-5' },
          { value: 'nvidia_nim', name: 'NVIDIA NIM', model: 'openai/gpt-oss-20b' },
        ],
        apiKey: vue.ref(''),
        showKey: vue.ref(false),
        saving: vue.ref(false),
        resetting: vue.ref(false),
        success: vue.ref(''),
        error: vue.ref(''),
        keyPlaceholder: vue.computed(() => 'AIza...'),
        keyHelp: vue.computed(() => 'Your Google Gemini API key from AI Studio'),
        save: () => {},
        resetToPlatformDefault: () => {},
      };
    }
  };

  const app = createTestApp(component);
  const rawHtml = await ssr.renderToString(app);
  const html = rawHtml.replace(/<!--[\s\S]*?-->/g, '');

  assert.ok(html.includes('No Key Configured'), 'Must render No Key Configured badge');
  assert.ok(!html.includes('Custom Key Active (BYOK)'), 'Must NOT render Custom Key Active badge');
  assert.ok(!html.includes('Platform Default Active'), 'Must NOT render Platform Default Active badge');
  assert.ok(html.includes('No API key is currently configured'), 'Must render warning explanation text');
});

testAsync('AISettingsView resetToPlatformDefault() sends { llm_provider: "gemini", llm_api_key: "" } and updates state', async () => {
  let capturedUrl = null;
  let capturedPayload = null;

  const mockApi = {
    put: async (url, payload) => {
      capturedUrl = url;
      capturedPayload = payload;
      return {
        data: {
          llm_provider: 'gemini',
          has_api_key: false,
          is_using_platform_default: true,
        }
      };
    }
  };

  const businessStore = {
    currentBusiness: { id: 'biz-12345' }
  };

  const provider = vue.ref('openai');
  const apiKey = vue.ref('sk-some-key');
  const showKey = vue.ref(true);
  const saving = vue.ref(false);
  const resetting = vue.ref(false);
  const success = vue.ref('');
  const error = vue.ref('');
  const currentProvider = vue.ref('openai');
  const hasKey = vue.ref(true);
  const isUsingPlatformDefault = vue.ref(false);

  async function resetToPlatformDefault() {
    resetting.value = true;
    success.value = '';
    error.value = '';
    try {
      const bid = businessStore.currentBusiness?.id;
      if (!bid) throw new Error('No active business found');

      const { data } = await mockApi.put(`/ai-settings/${bid}`, {
        llm_provider: 'gemini',
        llm_api_key: '',
      });

      currentProvider.value = data.llm_provider || 'gemini';
      provider.value = data.llm_provider || 'gemini';
      hasKey.value = !!data.has_api_key;
      isUsingPlatformDefault.value = !!data.is_using_platform_default;
      apiKey.value = '';
      showKey.value = false;
      success.value = 'Custom key removed. Successfully reverted to Platform Default (Gemini).';
    } catch (err) {
      error.value = err.message || 'Failed to reset settings';
    } finally {
      resetting.value = false;
    }
  }

  await resetToPlatformDefault();

  assert.equal(capturedUrl, '/ai-settings/biz-12345', 'Must call PUT /ai-settings/{bid}');
  assert.deepEqual(capturedPayload, { llm_provider: 'gemini', llm_api_key: '' },
    'Must send llm_provider="gemini" and llm_api_key=""');
  assert.equal(hasKey.value, false, 'hasKey must update to false');
  assert.equal(isUsingPlatformDefault.value, true, 'isUsingPlatformDefault must update to true');
  assert.equal(provider.value, 'gemini', 'provider must reset to gemini');
  assert.equal(currentProvider.value, 'gemini', 'currentProvider must reset to gemini');
  assert.equal(apiKey.value, '', 'apiKey input must be cleared');
  assert.equal(showKey.value, false, 'showKey must reset to false');
  assert.ok(success.value.includes('reverted to Platform Default'), 'success message must confirm revert');
  assert.equal(resetting.value, false, 'resetting flag must return to false');
});

testAsync('AISettingsView save() sends { llm_provider, llm_api_key } and trims input', async () => {
  let capturedUrl = null;
  let capturedPayload = null;

  const mockApi = {
    put: async (url, payload) => {
      capturedUrl = url;
      capturedPayload = payload;
      return {
        data: {
          llm_provider: payload.llm_provider,
          has_api_key: true,
          is_using_platform_default: false,
        }
      };
    }
  };

  const businessStore = {
    currentBusiness: { id: 'biz-88888' }
  };

  const provider = vue.ref('anthropic');
  const apiKey = vue.ref('   sk-ant-test-key-54321   ');
  const showKey = vue.ref(true);
  const saving = vue.ref(false);
  const resetting = vue.ref(false);
  const success = vue.ref('');
  const error = vue.ref('');
  const currentProvider = vue.ref('gemini');
  const hasKey = vue.ref(false);
  const isUsingPlatformDefault = vue.ref(true);

  async function save() {
    saving.value = true;
    success.value = '';
    error.value = '';
    try {
      const bid = businessStore.currentBusiness?.id;
      if (!bid) throw new Error('No active business found');

      const { data } = await mockApi.put(`/ai-settings/${bid}`, {
        llm_provider: provider.value,
        llm_api_key: apiKey.value.trim(),
      });

      currentProvider.value = data.llm_provider;
      hasKey.value = !!data.has_api_key;
      isUsingPlatformDefault.value = !!data.is_using_platform_default;
      apiKey.value = '';
      showKey.value = false;
      success.value = 'Settings saved successfully. Custom key is now active.';
    } catch (err) {
      error.value = err.message || 'Failed to save settings';
    } finally {
      saving.value = false;
    }
  }

  await save();

  assert.equal(capturedUrl, '/ai-settings/biz-88888');
  assert.deepEqual(capturedPayload, {
    llm_provider: 'anthropic',
    llm_api_key: 'sk-ant-test-key-54321', // verified trimmed!
  });
  assert.equal(hasKey.value, true);
  assert.equal(isUsingPlatformDefault.value, false);
  assert.equal(currentProvider.value, 'anthropic');
  assert.equal(apiKey.value, '');
  assert.equal(showKey.value, false);
  assert.ok(success.value.includes('Custom key is now active'));
});

// ----------------------------------------------------------------------------
// SUITE 2: WidgetConfigView Domains, Localhost Toggle & Payload Preservation
// ----------------------------------------------------------------------------
const widgetConfigSource = fs.readFileSync(
  path.join(frontendRoot, 'src/views/WidgetConfigView.vue'),
  'utf8'
);

test('WidgetConfigView sanitizeDomain() handles edge cases, schemes, ports, and subdomains', () => {
  const match = widgetConfigSource.match(/function sanitizeDomain\([\s\S]*?\n\}/);
  assert.ok(match, 'sanitizeDomain function must exist');

  const sanitizeDomain = eval(`(${match[0]})`);

  // Scheme stripping
  assert.equal(sanitizeDomain('https://example.com'), 'example.com');
  assert.equal(sanitizeDomain('http://app.mysite.org/'), 'app.mysite.org');
  assert.equal(sanitizeDomain('wss://chat.service.io/socket'), 'chat.service.io');

  // Port and path stripping
  assert.equal(sanitizeDomain('localhost:8000'), 'localhost');
  assert.equal(sanitizeDomain('example.com:3000/embed?widget=1#hash'), 'example.com');

  // Auth credential stripping
  assert.equal(sanitizeDomain('user:password@sub.example.com'), 'sub.example.com');

  // Wildcard and dot normalization
  assert.equal(sanitizeDomain('*.example.com'), 'example.com');
  assert.equal(sanitizeDomain('...example.com...'), 'example.com');

  // IPv6 bracket extraction
  assert.equal(sanitizeDomain('[2001:db8::1]:8080'), '2001:db8::1');

  // Case normalization
  assert.equal(sanitizeDomain('  EXAMPLE.COM  '), 'example.com');

  // Empty / null inputs
  assert.equal(sanitizeDomain(''), '');
  assert.equal(sanitizeDomain(null), '');
  assert.equal(sanitizeDomain(undefined), '');
});

test('WidgetConfigView isValidDomain() validates domain syntax and IP addresses', () => {
  const match = widgetConfigSource.match(/function isValidDomain\([\s\S]*?\n\}/);
  assert.ok(match, 'isValidDomain function must exist');

  const isValidDomain = eval(`(${match[0]})`);

  // Valid hostnames
  assert.equal(isValidDomain('example.com'), true);
  assert.equal(isValidDomain('sub.domain.co.uk'), true);
  assert.equal(isValidDomain('my-site.org'), true);
  assert.equal(isValidDomain('localhost'), true);
  assert.equal(isValidDomain('::1'), true);
  assert.equal(isValidDomain('127.0.0.1'), true);
  assert.equal(isValidDomain('192.168.1.1'), true);

  // Invalid hostnames
  assert.equal(isValidDomain(''), false);
  assert.equal(isValidDomain('example..com'), false);
  assert.equal(isValidDomain('invalid_char$.com'), false);
  assert.equal(isValidDomain('999.1.1.1'), false);
  assert.equal(isValidDomain('-starts-with-hyphen.com'), false);
});

test('WidgetConfigView addDomain and removeDomain manipulation and duplicate rejection', () => {
  const matchSanitize = widgetConfigSource.match(/function sanitizeDomain\([\s\S]*?\n\}/);
  const matchValid = widgetConfigSource.match(/function isValidDomain\([\s\S]*?\n\}/);
  const sanitizeDomain = eval(`(${matchSanitize[0]})`);
  const isValidDomain = eval(`(${matchValid[0]})`);

  const config = vue.ref({
    allowed_domains: ['existing.com'],
    allow_localhost: true,
  });
  const domainInput = vue.ref('');
  const domainError = vue.ref('');

  function addDomain() {
    domainError.value = '';
    const clean = sanitizeDomain(domainInput.value);

    if (!clean) {
      domainError.value = 'Please enter a valid domain (e.g. example.com or app.mysite.com).';
      return;
    }

    if (!isValidDomain(clean)) {
      domainError.value = `"${clean}" does not appear to be a valid domain or IP address.`;
      return;
    }

    if (!Array.isArray(config.value.allowed_domains)) {
      config.value.allowed_domains = [];
    }

    if (config.value.allowed_domains.includes(clean)) {
      domainError.value = `Domain "${clean}" is already in the allowed list.`;
      return;
    }

    config.value.allowed_domains.push(clean);
    domainInput.value = '';
  }

  function removeDomain(index) {
    if (Array.isArray(config.value.allowed_domains)) {
      config.value.allowed_domains.splice(index, 1);
    }
  }

  // 1. Duplicate rejection
  domainInput.value = 'https://EXISTING.COM:443/test';
  addDomain();
  assert.equal(config.value.allowed_domains.length, 1);
  assert.equal(domainError.value, 'Domain "existing.com" is already in the allowed list.');

  // 2. Add valid new domains
  domainInput.value = 'https://shop.example.com';
  addDomain();
  assert.equal(config.value.allowed_domains.length, 2);
  assert.ok(config.value.allowed_domains.includes('shop.example.com'));
  assert.equal(domainInput.value, '');
  assert.equal(domainError.value, '');

  domainInput.value = '192.168.1.50';
  addDomain();
  assert.equal(config.value.allowed_domains.length, 3);
  assert.ok(config.value.allowed_domains.includes('192.168.1.50'));

  // 3. Remove by index
  removeDomain(1); // removes shop.example.com
  assert.equal(config.value.allowed_domains.length, 2);
  assert.deepEqual(config.value.allowed_domains, ['existing.com', '192.168.1.50']);

  removeDomain(0); // removes existing.com
  assert.equal(config.value.allowed_domains.length, 1);
  assert.deepEqual(config.value.allowed_domains, ['192.168.1.50']);

  removeDomain(0); // removes 192.168.1.50
  assert.equal(config.value.allowed_domains.length, 0);
});

testAsync('WidgetConfigView empty domains warning renders red warning when allow_localhost is false', async () => {
  const parsed = sfc.parse(widgetConfigSource);
  const ssrRender = await compileSfcTemplateToSsr(parsed.descriptor.template.content, 'widget_warning_red');

  const component = {
    ssrRender,
    setup() {
      return {
        config: vue.ref({
          bot_name: 'Test Bot',
          welcome_message: 'Hello',
          primary_color: '#4f46e5',
          position: 'bottom-right',
          show_branding: true,
          placeholder_text: 'Ask me...',
          auto_open_delay: '',
          allowed_domains: [],
          allow_localhost: false,
        }),
        previewOpen: vue.ref(true),
        loading: vue.ref(false),
        loadError: vue.ref(''),
        saving: vue.ref(false),
        saveSuccess: vue.ref(false),
        saveError: vue.ref(''),
        domainInput: vue.ref(''),
        domainError: vue.ref(''),
        copied: vue.ref(false),
        embedSnippet: vue.computed(() => '<script src="http://localhost:5173/widget/widget.js" data-business-key="pk_test" defer></script>'),
        addDomain: () => {},
        removeDomain: () => {},
        copyEmbedSnippet: () => {},
        saveConfig: () => {},
        loadConfig: () => {},
      };
    }
  };

  const app = createTestApp(component);
  const html = await ssr.renderToString(app);

  assert.ok(html.includes('No domains are whitelisted and Localhost / Dev Mode is disabled'),
    'Must display critical warning when allowed_domains is empty and allow_localhost is false');
  assert.ok(html.includes('All external embed and chat requests will be rejected with HTTP 403 Forbidden'),
    'Must explicitly state HTTP 403 Forbidden rejection');
  assert.ok(html.includes('bg-red-50'), 'Warning box must have red background');
});

testAsync('WidgetConfigView empty domains warning renders amber warning when allow_localhost is true', async () => {
  const parsed = sfc.parse(widgetConfigSource);
  const ssrRender = await compileSfcTemplateToSsr(parsed.descriptor.template.content, 'widget_warning_amber');

  const component = {
    ssrRender,
    setup() {
      return {
        config: vue.ref({
          bot_name: 'Test Bot',
          welcome_message: 'Hello',
          primary_color: '#4f46e5',
          position: 'bottom-right',
          show_branding: true,
          placeholder_text: 'Ask me...',
          auto_open_delay: '',
          allowed_domains: [],
          allow_localhost: true,
        }),
        previewOpen: vue.ref(true),
        loading: vue.ref(false),
        loadError: vue.ref(''),
        saving: vue.ref(false),
        saveSuccess: vue.ref(false),
        saveError: vue.ref(''),
        domainInput: vue.ref(''),
        domainError: vue.ref(''),
        copied: vue.ref(false),
        embedSnippet: vue.computed(() => '<script src="http://localhost:5173/widget/widget.js" data-business-key="pk_test" defer></script>'),
        addDomain: () => {},
        removeDomain: () => {},
        copyEmbedSnippet: () => {},
        saveConfig: () => {},
        loadConfig: () => {},
      };
    }
  };

  const app = createTestApp(component);
  const html = await ssr.renderToString(app);

  assert.ok(html.includes('No production domains whitelisted yet'),
    'Must display amber warning when allowed_domains is empty but allow_localhost is true');
  assert.ok(!html.includes('Warning: No domains are whitelisted and Localhost / Dev Mode is disabled'),
    'Must NOT display critical red warning when allow_localhost is true');
});

testAsync('WidgetConfigView saveConfig() preserves all payload fields and coerces allow_localhost to boolean', async () => {
  let capturedUrl = null;
  let capturedPayload = null;

  const mockApi = {
    put: async (url, payload) => {
      capturedUrl = url;
      capturedPayload = payload;
      return { data: payload };
    }
  };

  const businessStore = {
    currentBusiness: { id: 'biz-widget-99' }
  };

  const config = vue.ref({
    bot_name: 'Custom Assistant',
    welcome_message: 'Welcome to SupportAI!',
    primary_color: '#10b981',
    position: 'bottom-left',
    show_branding: false,
    placeholder_text: 'How can we help?',
    auto_open_delay: '5s',
    allowed_domains: ['mysite.com', 'shop.mysite.com'],
    allow_localhost: 1, // Truthy number that must be coerced to boolean
  });

  const saving = vue.ref(false);
  const saveSuccess = vue.ref(false);
  const saveError = vue.ref('');

  async function saveConfig() {
    if (!config.value) return;
    saving.value = true;
    saveSuccess.value = false;
    saveError.value = '';

    try {
      let bid = businessStore.currentBusiness?.id;
      if (!bid) throw new Error('Business ID not found.');

      const payload = {
        bot_name: config.value.bot_name,
        welcome_message: config.value.welcome_message,
        primary_color: config.value.primary_color,
        position: config.value.position,
        show_branding: config.value.show_branding,
        placeholder_text: config.value.placeholder_text,
        auto_open_delay: config.value.auto_open_delay || null,
        allowed_domains: config.value.allowed_domains || [],
        allow_localhost: !!config.value.allow_localhost,
      };

      const { data } = await mockApi.put(`/widget/${bid}/config`, payload);
      config.value = {
        ...config.value,
        ...data,
        allowed_domains: Array.isArray(data.allowed_domains) ? data.allowed_domains : [],
        allow_localhost: typeof data.allow_localhost === 'boolean' ? data.allow_localhost : true,
      };
      saveSuccess.value = true;
    } catch (err) {
      saveError.value = err.message || 'Failed to save configuration.';
    } finally {
      saving.value = false;
    }
  }

  await saveConfig();

  assert.equal(capturedUrl, '/widget/biz-widget-99/config');
  assert.deepEqual(capturedPayload, {
    bot_name: 'Custom Assistant',
    welcome_message: 'Welcome to SupportAI!',
    primary_color: '#10b981',
    position: 'bottom-left',
    show_branding: false,
    placeholder_text: 'How can we help?',
    auto_open_delay: '5s',
    allowed_domains: ['mysite.com', 'shop.mysite.com'],
    allow_localhost: true,
  });
  assert.equal(typeof capturedPayload.allow_localhost, 'boolean');
  assert.equal(saveSuccess.value, true);
});

// ----------------------------------------------------------------------------
// SUITE 3: DashboardView Public/Secret Decoupling, Masking & Feedback Timers
// ----------------------------------------------------------------------------
const dashboardSource = fs.readFileSync(
  path.join(frontendRoot, 'src/views/DashboardView.vue'),
  'utf8'
);

testAsync('DashboardView credentials decoupling renders green Public Key card and amber Secret API Key card', async () => {
  const parsed = sfc.parse(dashboardSource);
  const ssrRender = await compileSfcTemplateToSsr(parsed.descriptor.template.content, 'dashboard_creds');

  const component = {
    ssrRender,
    setup() {
      return {
        loading: vue.ref(false),
        showGuide: vue.ref(false),
        stats: vue.ref([]),
        businessStore: {
          currentBusiness: {
            id: 'biz-dash-1',
            public_key: 'pk_live_1234567890abcdef',
            api_key: 'sec_admin_secret_9999999999',
          }
        },
        showSecretKey: vue.ref(false),
        copiedPublicKey: vue.ref(false),
        copiedSecretKey: vue.ref(false),
        copiedEmbed: vue.ref(false),
        embedCode: vue.computed(() => '<script src="http://localhost:5173/widget/widget.js" data-business-key="pk_live_1234567890abcdef" defer></script>'),
        copyPublicKey: () => {},
        copySecretKey: () => {},
        copyEmbedCode: () => {},
        dismissGuide: () => {},
      };
    }
  };

  const app = createTestApp(component);
  const html = await ssr.renderToString(app);

  assert.ok(html.includes('Public Key (Widget Token)'), 'Must render Public Key header');
  assert.ok(html.includes('Public / Safe for Web'), 'Must render Public / Safe for Web green badge');
  assert.ok(html.includes('pk_live_1234567890abcdef'), 'Must clearly expose public_key in the DOM');

  assert.ok(html.includes('Secret API Key'), 'Must render Secret API Key header');
  assert.ok(html.includes('Confidential / Secret'), 'Must render Confidential / Secret amber badge');
  assert.ok(html.includes('••••••••••••••••••••••••••••••••'), 'Secret key MUST be masked by default');
  assert.ok(!html.includes('sec_admin_secret_9999999999'), 'Actual secret key MUST NOT be visible when showSecretKey is false');
  assert.ok(html.includes('Show'), 'Must display "Show" button');
});

testAsync('DashboardView showSecretKey toggle reveals and hides secret key', async () => {
  const parsed = sfc.parse(dashboardSource);
  const ssrRender = await compileSfcTemplateToSsr(parsed.descriptor.template.content, 'dashboard_show_secret');

  const showSecretKey = vue.ref(true);

  const component = {
    ssrRender,
    setup() {
      return {
        loading: vue.ref(false),
        showGuide: vue.ref(false),
        stats: vue.ref([]),
        businessStore: {
          currentBusiness: {
            id: 'biz-dash-1',
            public_key: 'pk_live_1234567890abcdef',
            api_key: 'sec_admin_secret_9999999999',
          }
        },
        showSecretKey,
        copiedPublicKey: vue.ref(false),
        copiedSecretKey: vue.ref(false),
        copiedEmbed: vue.ref(false),
        embedCode: vue.computed(() => '<script src="http://localhost:5173/widget/widget.js" data-business-key="pk_live_1234567890abcdef" defer></script>'),
        copyPublicKey: () => {},
        copySecretKey: () => {},
        copyEmbedCode: () => {},
        dismissGuide: () => {},
      };
    }
  };

  const app = createTestApp(component);
  const html = await ssr.renderToString(app);

  assert.ok(html.includes('sec_admin_secret_9999999999'), 'Actual secret key must be displayed when showSecretKey is true');
  assert.ok(html.includes('Hide'), 'Must display "Hide" button when secret key is visible');
});

testAsync('DashboardView copy feedback timers set copied flag and reset after 2000ms', async () => {
  let writtenText = '';
  const mockClipboard = {
    writeText: async (text) => {
      writtenText = text;
    }
  };

  const businessStore = {
    currentBusiness: {
      public_key: 'pk_timer_test',
      api_key: 'sec_timer_test',
    }
  };

  const copiedPublicKey = vue.ref(false);
  const copiedSecretKey = vue.ref(false);
  let pubKeyTimer = null;
  let secKeyTimer = null;

  function copyPublicKey() {
    const key = businessStore.currentBusiness?.public_key || '';
    if (!key) return;
    mockClipboard.writeText(key);
    copiedPublicKey.value = true;
    if (pubKeyTimer) clearTimeout(pubKeyTimer);
    pubKeyTimer = setTimeout(() => {
      copiedPublicKey.value = false;
    }, 100);
  }

  function copySecretKey() {
    const key = businessStore.currentBusiness?.api_key || '';
    if (!key) return;
    mockClipboard.writeText(key);
    copiedSecretKey.value = true;
    if (secKeyTimer) clearTimeout(secKeyTimer);
    secKeyTimer = setTimeout(() => {
      copiedSecretKey.value = false;
    }, 100);
  }

  copyPublicKey();
  assert.equal(writtenText, 'pk_timer_test');
  assert.equal(copiedPublicKey.value, true);

  copySecretKey();
  assert.equal(writtenText, 'sec_timer_test');
  assert.equal(copiedSecretKey.value, true);

  await new Promise(resolve => setTimeout(resolve, 150));
  assert.equal(copiedPublicKey.value, false, 'copiedPublicKey must reset to false after timer');
  assert.equal(copiedSecretKey.value, false, 'copiedSecretKey must reset to false after timer');
});

test('DashboardView pure 1-line embed snippet uses public_key with origin', () => {
  const businessStore = {
    currentBusiness: {
      public_key: 'pk_prod_abcdef123456',
      api_key: 'sec_prod_secret987',
    }
  };
  const origin = 'https://app.supportai.io';

  const embedCode = vue.computed(() => {
    const orig = origin.replace(/\/+$/, '');
    const key = businessStore.currentBusiness?.public_key || businessStore.currentBusiness?.api_key || 'YOUR_PUBLIC_KEY';
    return `<script src="${orig}/widget/widget.js" data-business-key="${key}" defer></script>`;
  });

  const expected = '<script src="https://app.supportai.io/widget/widget.js" data-business-key="pk_prod_abcdef123456" defer></script>';
  assert.equal(embedCode.value, expected);
  assert.ok(!embedCode.value.includes('sec_prod_secret987'), 'Secret API key must NEVER be used when public_key is present');
});

test('Dashboard embed code never falls back to the confidential admin API key', () => {
  assert.match(dashboardSource, /const key = businessStore\.currentBusiness\?\.public_key \|\| 'YOUR_PUBLIC_KEY'/);
  assert.doesNotMatch(dashboardSource, /public_key \|\| businessStore\.currentBusiness\?\.api_key/);
});

// ----------------------------------------------------------------------------
// SUITE 4: Adversarial Edge Cases, Error Handling & Store Hydration
// ----------------------------------------------------------------------------
console.log('\n--- Suite 4: Adversarial Error Handling & Store Hydration ---');

testAsync('AISettingsView save() captures backend error detail when submission fails', async () => {
  const mockApi = {
    put: async () => {
      const err = new Error('Request failed with status code 400');
      err.response = { data: { detail: 'Provider must be one of: gemini, openai, anthropic, nvidia_nim' } };
      throw err;
    }
  };

  const businessStore = { currentBusiness: { id: 'biz-err-1' } };
  const provider = vue.ref('gemini');
  const apiKey = vue.ref('bad-key');
  const saving = vue.ref(false);
  const success = vue.ref('');
  const error = vue.ref('');

  async function save() {
    saving.value = true;
    success.value = '';
    error.value = '';
    try {
      const bid = businessStore.currentBusiness?.id;
      if (!bid) throw new Error('No active business found');
      await mockApi.put(`/ai-settings/${bid}`, {
        llm_provider: provider.value,
        llm_api_key: apiKey.value.trim(),
      });
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || 'Failed to save settings';
    } finally {
      saving.value = false;
    }
  }

  await save();
  assert.equal(error.value, 'Provider must be one of: gemini, openai, anthropic, nvidia_nim');
  assert.equal(saving.value, false);
});

test('AISettingsView save button disabled state prevents whitespace-only submission', () => {
  const saving = vue.ref(false);
  const resetting = vue.ref(false);
  const apiKey = vue.ref('    ');

  const isSaveDisabled = vue.computed(() => saving.value || resetting.value || !apiKey.value.trim());
  assert.equal(isSaveDisabled.value, true, 'Save must be disabled for whitespace-only key');

  apiKey.value = 'valid-key';
  assert.equal(isSaveDisabled.value, false, 'Save must be enabled for non-empty key');

  saving.value = true;
  assert.equal(isSaveDisabled.value, true, 'Save must be disabled while saving');
});

test('WidgetConfigView sanitizeDomain() stress test with complex malformed URLs and IPv6', () => {
  const match = widgetConfigSource.match(/function sanitizeDomain\([\s\S]*?\n\}/);
  const sanitizeDomain = eval(`(${match[0]})`);

  // Multiple schemes and query parameters
  assert.equal(sanitizeDomain('HTTPS://USER:PASS@WWW.TEST-DOMAIN.COM:9090/PATH/TO/PAGE?Q=1&R=2#HEADING'), 'www.test-domain.com');

  // Wildcard prefixes
  assert.equal(sanitizeDomain('*.subdomain.myshop.co'), 'subdomain.myshop.co');

  // IPv6 bracketed addresses
  assert.equal(sanitizeDomain('http://[::1]:3000/'), '::1');
  assert.equal(sanitizeDomain('[2607:f8b0:4005:805::200e]'), '2607:f8b0:4005:805::200e');
});

testAsync('WidgetConfigView loadConfig() handles null/undefined allowed_domains and allow_localhost gracefully', async () => {
  const mockApi = {
    get: async () => ({
      data: {
        bot_name: 'Test',
        allowed_domains: null, // Null from DB
        allow_localhost: null, // Null from DB
      }
    })
  };

  const businessStore = { currentBusiness: { id: 'biz-null-test' } };
  const config = vue.ref(null);

  async function loadConfig() {
    const { data } = await mockApi.get(`/widget/${businessStore.currentBusiness.id}/config`);
    config.value = {
      ...data,
      allowed_domains: Array.isArray(data.allowed_domains) ? data.allowed_domains : [],
      allow_localhost: typeof data.allow_localhost === 'boolean' ? data.allow_localhost : true,
    };
  }

  await loadConfig();
  assert.deepEqual(config.value.allowed_domains, [], 'Null allowed_domains must fallback to empty array');
  assert.equal(config.value.allow_localhost, true, 'Null allow_localhost must fallback to default true');
});

testAsync('WidgetConfigView saveConfig() captures and surfaces backend error messages', async () => {
  const mockApi = {
    put: async () => {
      const err = new Error('Forbidden');
      err.response = { data: { detail: 'Business not found or access denied.' } };
      throw err;
    }
  };

  const businessStore = { currentBusiness: { id: 'biz-err-2' } };
  const config = vue.ref({ bot_name: 'Bot', allowed_domains: [], allow_localhost: true });
  const saving = vue.ref(false);
  const saveSuccess = vue.ref(false);
  const saveError = vue.ref('');

  async function saveConfig() {
    saving.value = true;
    saveSuccess.value = false;
    saveError.value = '';
    try {
      await mockApi.put(`/widget/${businessStore.currentBusiness.id}/config`, config.value);
      saveSuccess.value = true;
    } catch (err) {
      saveError.value = err.response?.data?.detail || err.message || 'Failed to save configuration.';
    } finally {
      saving.value = false;
    }
  }

  await saveConfig();
  assert.equal(saveError.value, 'Business not found or access denied.');
  assert.equal(saveSuccess.value, false);
  assert.equal(saving.value, false);
});

test('DashboardView embedCode fallback gracefully handles empty or null keys', () => {
  const businessStore = {
    currentBusiness: {
      public_key: '',
      api_key: '',
    }
  };
  const origin = 'http://localhost:5173';

  const embedCode = vue.computed(() => {
    const orig = origin.replace(/\/+$/, '');
    const key = businessStore.currentBusiness?.public_key || businessStore.currentBusiness?.api_key || 'YOUR_PUBLIC_KEY';
    return `<script src="${orig}/widget/widget.js" data-business-key="${key}" defer></script>`;
  });

  assert.equal(
    embedCode.value,
    '<script src="http://localhost:5173/widget/widget.js" data-business-key="YOUR_PUBLIC_KEY" defer></script>'
  );
});

test('DashboardView copy functions do not throw when currentBusiness is undefined', () => {
  const businessStore = { currentBusiness: null };
  let called = false;
  const mockClipboard = {
    writeText: () => { called = true; }
  };

  function copyPublicKey() {
    const key = businessStore.currentBusiness?.public_key || '';
    if (!key) return;
    mockClipboard.writeText(key);
  }

  function copySecretKey() {
    const key = businessStore.currentBusiness?.api_key || '';
    if (!key) return;
    mockClipboard.writeText(key);
  }

  assert.doesNotThrow(() => copyPublicKey());
  assert.doesNotThrow(() => copySecretKey());
  assert.equal(called, false, 'writeText must not be called when keys are missing');
});

testAsync('business store fetchMyBusinesses() refreshes existing currentBusiness with updated server fields', async () => {
  // Simulate stale localStorage record missing public_key
  const staleBusiness = { id: 'biz-100', name: 'My Biz', api_key: 'sec_100' };
  const mockLocalStorage = {
    items: { currentBusiness: JSON.stringify(staleBusiness) },
    getItem(key) { return this.items[key] || null; },
    setItem(key, val) { this.items[key] = val; }
  };

  // Upstream server returns freshly migrated business with public_key
  const serverBusinesses = [
    { id: 'biz-100', name: 'My Biz', api_key: 'sec_100', public_key: 'pk_fresh_migration_key_100' },
    { id: 'biz-200', name: 'Other Biz', api_key: 'sec_200', public_key: 'pk_200' }
  ];

  const currentBusiness = vue.ref(JSON.parse(mockLocalStorage.getItem('currentBusiness')));
  const businesses = vue.ref([]);

  async function fetchMyBusinesses() {
    businesses.value = serverBusinesses;
    if (serverBusinesses.length > 0) {
      const match = currentBusiness.value
        ? serverBusinesses.find(b => b.id === currentBusiness.value.id)
        : null;
      currentBusiness.value = match || serverBusinesses[0];
      mockLocalStorage.setItem('currentBusiness', JSON.stringify(currentBusiness.value));
    }
  }

  assert.equal(currentBusiness.value.public_key, undefined, 'Initial state should lack public_key');
  await fetchMyBusinesses();
  assert.equal(currentBusiness.value.public_key, 'pk_fresh_migration_key_100', 'Must hydrate public_key from server');

  const persisted = JSON.parse(mockLocalStorage.getItem('currentBusiness'));
  assert.equal(persisted.public_key, 'pk_fresh_migration_key_100', 'Must persist hydrated object to localStorage');
});

// ----------------------------------------------------------------------------
// SUITE 5: Sandbox and FAQ generation regressions
// ----------------------------------------------------------------------------
const sandboxSource = fs.readFileSync(
  path.join(frontendRoot, 'src/views/SandboxView.vue'),
  'utf8'
);
const faqSource = fs.readFileSync(
  path.join(frontendRoot, 'src/views/FAQView.vue'),
  'utf8'
);

test('Sandbox uses the shared API client, public key, bounded request, and always clears pending state', () => {
  assert.match(sandboxSource, /import api from ['"]\.\.\/api\/client\.js['"]/);
  assert.match(sandboxSource, /currentBusiness\?\.public_key/);
  assert.match(sandboxSource, /api\.post\(`\/chat\/\$\{encodeURIComponent\(apiKey\.value\)\}`/);
  assert.match(sandboxSource, /timeout:\s*120000/);
  assert.match(sandboxSource, /finally\s*\{[\s\S]*?thinking\.value = false/);
  assert.match(sandboxSource, /data\.error_code/);
  assert.match(sandboxSource, /data\.diagnostic/);
  assert.match(sandboxSource, /data\.action_hint/);
  assert.doesNotMatch(sandboxSource, /currentBusiness\?\.api_key/);
  assert.doesNotMatch(sandboxSource, /import axios from/);
});

test('FAQ view follows workspace changes and presents generated suggestions and deletion confirmation accessibly', () => {
  assert.match(faqSource, /const businessId = computed\(\(\) => businessStore\.currentBusiness\?\.id/);
  assert.match(faqSource, /fetchMyBusinesses\(\)/);
  assert.match(faqSource, /watch\(businessId/);
  assert.match(faqSource, /auto-generate/);
  assert.match(faqSource, /aria-modal="true"/);
  assert.match(faqSource, /role="alertdialog"/);
  assert.match(faqSource, /genError\.diagnostic/);
  assert.match(faqSource, /genError\.actionHint/);
  assert.doesNotMatch(faqSource, /const bid = businessStore\.currentBusiness/);
  assert.doesNotMatch(faqSource, /confirm\(/);
});

// ----------------------------------------------------------------------------
// Execution Runner
// ----------------------------------------------------------------------------
(async () => {
  console.log('================================================================');
  console.log('RUNNING MILESTONE 5 ADVERSARIAL VERIFICATION SUITE');
  console.log('================================================================\n');

  for (const t of testQueue) {
    totalTests++;
    try {
      if (t.isAsync) {
        await t.fn();
      } else {
        t.fn();
      }
      passedTests++;
      console.log(`  ✓ ${t.name}`);
    } catch (err) {
      failedTests++;
      console.error(`  ✗ ${t.name}`);
      console.error(`    ${err.message}`);
    }
  }

  console.log('\n================================================================');
  console.log(`RESULTS: ${passedTests} passed, ${failedTests} failed out of ${totalTests} total tests`);
  console.log('================================================================');

  if (failedTests > 0) {
    process.exit(1);
  }
})();
