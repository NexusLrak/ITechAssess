document.addEventListener('DOMContentLoaded', () => {
  const dateInput = document.querySelector('#date');
  if (dateInput && !dateInput.value) {
    const today = new Date().toISOString().slice(0, 10);
    dateInput.value = today;
  }
});


async function openModal(url) {
  const modalBody = document.getElementById('modal-body');
  const modalEl = document.getElementById('modal');
  const bsModal = new bootstrap.Modal(modalEl);

  const response = await fetch(url, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  });

  modalBody.innerHTML = await response.text();
  bsModal.show();

  bindModalForm(modalBody, bsModal);
}


function bindModalForm(container, bsModal) {
  const form = container.querySelector('form');
  if (!form) return;

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(form);

    const response = await fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    if (response.status === 204) {
      bsModal.hide();
      window.location.reload();
      return;
    }

    container.innerHTML = await response.text();
    bindModalForm(container, bsModal);
  });
}