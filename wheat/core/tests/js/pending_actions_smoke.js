const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

class HTMLFormElement {}

class FakeControl {
    constructor(tagName, { type, name, disabled = false } = {}) {
        this.tagName = tagName.toUpperCase();
        this.type = type;
        this.name = name || '';
        this.disabled = disabled;
        this.dataset = {};
    }
}

class FakeForm extends HTMLFormElement {
    constructor(controls) {
        super();
        this._controls = controls;
        this.dataset = {};
    }

    querySelectorAll(selector) {
        return this._controls.filter((control) => selectorMatches(control, selector));
    }
}

function selectorMatches(control, selector) {
    return selector.split(',').some((part) => singleSelectorMatches(control, part.trim()));
}

function singleSelectorMatches(control, selector) {
    switch (selector) {
        case 'button':
            return control.tagName === 'BUTTON';
        case 'input':
            return control.tagName === 'INPUT';
        case 'select':
            return control.tagName === 'SELECT';
        case 'textarea':
            return control.tagName === 'TEXTAREA';
        case 'button[type="submit"]':
            return control.tagName === 'BUTTON' && control.type === 'submit';
        case 'button:not([type])':
            return control.tagName === 'BUTTON' && (control.type === undefined || control.type === null || control.type === '');
        case 'input[type="submit"]':
            return control.tagName === 'INPUT' && control.type === 'submit';
        case 'input[type="image"]':
            return control.tagName === 'INPUT' && control.type === 'image';
        default:
            throw new Error(`Unhandled selector in smoke test: ${selector}`);
    }
}

global.window = {};
global.document = { addEventListener() {} };
global.HTMLFormElement = HTMLFormElement;

const scriptPath = path.resolve(__dirname, '../../static/js/pending-actions.js');
const source = fs.readFileSync(scriptPath, 'utf8');
vm.runInThisContext(source, { filename: scriptPath });

const submitButton = new FakeControl('button', { type: 'submit' });
const implicitSubmitButton = new FakeControl('button');
const submitInput = new FakeControl('input', { type: 'submit' });
const imageInput = new FakeControl('input', { type: 'image' });
const disabledSubmitInput = new FakeControl('input', { type: 'submit', disabled: true });
const textInput = new FakeControl('input', { type: 'text', name: 'title' });
const passwordInput = new FakeControl('input', { type: 'password', name: 'password' });
const hiddenInput = new FakeControl('input', { type: 'hidden', name: 'csrfmiddlewaretoken' });
const fileInput = new FakeControl('input', { type: 'file', name: 'uploaded_image' });
const checkboxInput = new FakeControl('input', { type: 'checkbox', name: 'is_active' });
const selectInput = new FakeControl('select', { name: 'visibility' });
const textarea = new FakeControl('textarea', { name: 'content' });

const form = new FakeForm([
    submitButton,
    implicitSubmitButton,
    submitInput,
    imageInput,
    disabledSubmitInput,
    textInput,
    passwordInput,
    hiddenInput,
    fileInput,
    checkboxInput,
    selectInput,
    textarea,
]);

assert.strictEqual(window.beginPendingForm(form), true, 'first submit should lock the form');
assert.strictEqual(window.beginPendingForm(form), false, 'second submit should be blocked while pending');

assert.strictEqual(submitButton.disabled, true);
assert.strictEqual(implicitSubmitButton.disabled, true);
assert.strictEqual(submitInput.disabled, true);
assert.strictEqual(imageInput.disabled, true);

assert.strictEqual(textInput.disabled, false);
assert.strictEqual(passwordInput.disabled, false);
assert.strictEqual(hiddenInput.disabled, false);
assert.strictEqual(fileInput.disabled, false);
assert.strictEqual(checkboxInput.disabled, false);
assert.strictEqual(selectInput.disabled, false);
assert.strictEqual(textarea.disabled, false);

window.endPendingForm(form);

assert.strictEqual(submitButton.disabled, false);
assert.strictEqual(implicitSubmitButton.disabled, false);
assert.strictEqual(submitInput.disabled, false);
assert.strictEqual(imageInput.disabled, false);
assert.strictEqual(disabledSubmitInput.disabled, true, 'pre-disabled controls stay disabled');
assert.strictEqual(textInput.disabled, false);
assert.strictEqual(selectInput.disabled, false);
assert.strictEqual(textarea.disabled, false);
