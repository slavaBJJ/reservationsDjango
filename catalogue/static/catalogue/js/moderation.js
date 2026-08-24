(() => {
    const csrfInput = document.querySelector('[data-moderation-csrf] input[name="csrfmiddlewaretoken"]');
    const message = document.querySelector('[data-moderation-message]');
    if (!csrfInput || !message) return;

    document.querySelectorAll('[data-moderation-action]').forEach((button) => {
        button.addEventListener('click', async () => {
            const item = button.closest('[data-moderation-item]');
            const itemButtons = item.querySelectorAll('[data-moderation-action]');
            itemButtons.forEach((itemButton) => { itemButton.disabled = true; });
            try {
                const response = await fetch(button.dataset.url, {
                    method: 'POST',
                    headers: {'X-CSRFToken': csrfInput.value, 'Content-Type': 'application/x-www-form-urlencoded'},
                    body: new URLSearchParams({action: button.dataset.action}).toString(),
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'La modération a échoué.');
                item.remove();
                message.textContent = `Élément ${data.status_label.toLowerCase()}.`;
                message.className = 'moderation-message alert alert-success';
            } catch (error) {
                message.textContent = error.message;
                message.className = 'moderation-message alert alert-danger';
                itemButtons.forEach((itemButton) => { itemButton.disabled = false; });
            }
        });
    });
})();
