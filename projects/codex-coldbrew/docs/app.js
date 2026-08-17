document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
    const value = button.getAttribute('data-copy') || '';
    try {
      await navigator.clipboard.writeText(value);
      button.textContent = '已复制';
    } catch (_error) {
      button.textContent = value;
    }
  });
});
