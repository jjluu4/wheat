(function () {
    function formControls(form) {
        if (!form) return [];
        return Array.from(form.querySelectorAll('button, input, select, textarea'));
    }

    function submitControls(form) {
        if (!form) return [];
        return Array.from(
            form.querySelectorAll(
                'button[type="submit"], button:not([type]), input[type="submit"], input[type="image"]'
            )
        );
    }

    function markDisabled(control) {
        if (!control || control.disabled) return;
        control.dataset.pendingDisabledByScript = '1';
        control.disabled = true;
    }

    function clearDisabled(control) {
        if (!control) return;
        if (control.dataset.pendingDisabledByScript === '1') {
            control.disabled = false;
            delete control.dataset.pendingDisabledByScript;
        }
    }

    function beginPendingForm(form) {
        if (!form) return false;
        if (form.dataset.pending === '1') return false;

        form.dataset.pending = '1';
        submitControls(form).forEach(markDisabled);
        return true;
    }

    function endPendingForm(form) {
        if (!form) return;
        delete form.dataset.pending;
        formControls(form).forEach(clearDisabled);
    }

    function beginPendingButton(button) {
        if (!button) return false;
        if (button.dataset.pending === '1') return false;

        button.dataset.pending = '1';
        markDisabled(button);
        return true;
    }

    function endPendingButton(button) {
        if (!button) return;
        delete button.dataset.pending;
        clearDisabled(button);
    }

    document.addEventListener('submit', function (event) {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) return;
        if (!form.matches('form[data-pending-form]')) return;
        if (beginPendingForm(form)) return;
        event.preventDefault();
    });

    window.beginPendingForm = beginPendingForm;
    window.endPendingForm = endPendingForm;
    window.beginPendingButton = beginPendingButton;
    window.endPendingButton = endPendingButton;
})();
