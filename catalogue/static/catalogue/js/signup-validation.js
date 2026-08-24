(() => {
    const form = document.querySelector('[data-signup-form]');
    if (!form) return;
    const submit = form.querySelector('[data-signup-submit]');
    const fields = ['username', 'email'];
    const state = {username: false, email: false, password: false, confirmation: false};
    const timers = {};
    const controllers = {};

    const updateSubmit = () => {
        submit.disabled = !Object.values(state).every(Boolean);
    };
    const showStatus = (field, available, message, pending = false) => {
        const input = form.elements[field];
        const output = form.querySelector(`[data-availability-message="${field}"]`);
        state[field] = available && !pending;
        output.textContent = message;
        output.classList.toggle('is-available', available && !pending);
        output.classList.toggle('is-unavailable', !available && !pending);
        output.classList.toggle('is-pending', pending);
        input.setAttribute('aria-invalid', String(!available && !pending));
        updateSubmit();
    };
    const checkAvailability = async (field) => {
        const value = form.elements[field].value.trim();
        if (!value) {
            showStatus(field, false, 'Ce champ est obligatoire.');
            return;
        }
        controllers[field]?.abort();
        controllers[field] = new AbortController();
        showStatus(field, false, 'Vérification…', true);
        const params = new URLSearchParams({field, value});
        try {
            const response = await fetch(`${form.dataset.availabilityUrl}?${params}`, {
                headers: {'X-Requested-With': 'XMLHttpRequest'},
                signal: controllers[field].signal,
            });
            const result = await response.json();
            showStatus(field, response.ok && result.available, result.message);
        } catch (error) {
            if (error.name !== 'AbortError') showStatus(field, false, 'Vérification impossible. Réessayez.');
        }
    };
    fields.forEach((field) => {
        const input = form.elements[field];
        input.addEventListener('input', () => {
            state[field] = false;
            updateSubmit();
            clearTimeout(timers[field]);
            timers[field] = setTimeout(() => checkAvailability(field), 350);
        });
        if (input.value.trim()) checkAvailability(field);
    });

    const password = form.elements.password1;
    const confirmation = form.elements.password2;
    const passwordStatus = form.querySelector('[data-password-status]');
    const matchStatus = form.querySelector('[data-password-match]');

    const validatePasswords = () => {
        const value = password.value;
        const missingRules = [];
        if (value.length < 8) missingRules.push('8 caractères minimum');
        if (!/[A-ZÀ-ÖØ-Þ]/.test(value)) missingRules.push('une majuscule');
        if (!/[^\p{L}\p{N}\s]/u.test(value)) missingRules.push('un caractère spécial');

        state.password = missingRules.length === 0;
        passwordStatus.textContent = state.password
            ? 'Le mot de passe respecte les règles.'
            : `Requis : ${missingRules.join(', ')}.`;
        passwordStatus.classList.toggle('is-valid', state.password);
        passwordStatus.classList.toggle('is-invalid', !state.password && value.length > 0);
        password.setAttribute('aria-invalid', String(!state.password && value.length > 0));

        state.confirmation = confirmation.value.length > 0 && confirmation.value === value;
        matchStatus.textContent = confirmation.value.length === 0
            ? ''
            : state.confirmation ? 'Les mots de passe correspondent.' : 'Les mots de passe ne correspondent pas.';
        matchStatus.classList.toggle('is-valid', state.confirmation);
        matchStatus.classList.toggle('is-invalid', !state.confirmation && confirmation.value.length > 0);
        confirmation.setAttribute('aria-invalid', String(!state.confirmation && confirmation.value.length > 0));
        updateSubmit();
    };

    password.addEventListener('input', validatePasswords);
    confirmation.addEventListener('input', validatePasswords);
    validatePasswords();
})();
