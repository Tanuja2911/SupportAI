const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const context = vm.createContext({
  window: {},
  document: {
    currentScript: null,
    readyState: 'loading',
    addEventListener() {},
    getElementById() { return null; },
  },
  URL,
  console,
  setTimeout,
  clearTimeout,
});

vm.runInContext(fs.readFileSync('widget.js', 'utf8'), context);
const widget = context.window.SupportAI;

for (const [value, expected] of [
  ['5s', 5000],
  ['250ms', 250],
  ['1.5', 1500],
  ['', 0],
  ['invalid', 0],
  ['0s', 0],
  ['90s', 60000],
]) {
  widget.config = { auto_open_delay: value };
  assert.equal(widget.getAutoOpenDelay(), expected, `delay ${JSON.stringify(value)}`);
}

widget.config = { auto_open_delay: '5s' };
widget.autoOpenTimer = setTimeout(() => {}, 60000);
widget.close();
assert.equal(widget.autoOpenTimer, null, 'closing clears the pending auto-open timer');
widget.destroy();
console.log('Auto-open delay tests passed.');
