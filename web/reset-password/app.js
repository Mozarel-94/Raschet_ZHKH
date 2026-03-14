import {
  getCurrentSession,
  onAuthStateChange,
  updateCurrentUserPassword,
} from "../lib/auth.js";

const elements = {
  form: document.getElementById("reset-password-form"),
  newPassword: document.getElementById("new-password"),
  confirmPassword: document.getElementById("confirm-password"),
  submitButton: document.getElementById("reset-password-button"),
  messageBox: document.getElementById("reset-message-box"),
};

function setMessage(type, text) {
  if (!text) {
    elements.messageBox.innerHTML = "";
    return;
  }

  elements.messageBox.innerHTML = `<div class="message ${type}">${text}</div>`;
}

function setLoadingState(isLoading) {
  elements.submitButton.disabled = isLoading;
}

function passwordsMatch() {
  return elements.newPassword.value === elements.confirmPassword.value;
}

async function ensureRecoverySession() {
  const session = await getCurrentSession();
  if (session) {
    return true;
  }

  return new Promise((resolve) => {
    let resolved = false;

    onAuthStateChange((nextSession) => {
      if (resolved || !nextSession) {
        return;
      }

      resolved = true;
      resolve(true);
    }).catch(() => {
      if (!resolved) {
        resolved = true;
        resolve(false);
      }
    });

    window.setTimeout(() => {
      if (!resolved) {
        resolved = true;
        resolve(false);
      }
    }, 2000);
  });
}

async function handleSubmit(event) {
  event.preventDefault();

  if (!passwordsMatch()) {
    setMessage("error", "Пароли не совпадают.");
    return;
  }

  setLoadingState(true);
  setMessage("", "");

  try {
    await updateCurrentUserPassword(elements.newPassword.value);
    setMessage("info", "Пароль обновлён. Теперь можно войти с новым паролем.");
    window.setTimeout(() => {
      window.location.replace("/login");
    }, 1200);
  } catch (error) {
    setMessage(
      "error",
      error instanceof Error ? error.message : "Не удалось обновить пароль."
    );
  } finally {
    setLoadingState(false);
  }
}

async function init() {
  const hasRecoverySession = await ensureRecoverySession();

  if (!hasRecoverySession) {
    setMessage(
      "error",
      "Ссылка для восстановления недействительна или истекла. Запросите новую на странице входа."
    );
  }

  elements.form.addEventListener("submit", handleSubmit);
}

init().catch((error) => {
  setMessage(
    "error",
    error instanceof Error ? error.message : "Ошибка инициализации восстановления пароля."
  );
});
