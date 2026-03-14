import {
  redirectAuthenticated,
  requestPasswordReset,
  signInWithEmail,
  signUpWithEmail,
} from "../lib/auth.js";

const params = new URLSearchParams(window.location.search);
const nextPath = params.get("next") || "/";

const elements = {
  form: document.getElementById("auth-form"),
  email: document.getElementById("auth-email"),
  password: document.getElementById("auth-password"),
  loginButton: document.getElementById("login-button"),
  signupButton: document.getElementById("signup-button"),
  forgotPasswordButton: document.getElementById("forgot-password-button"),
  messageBox: document.getElementById("auth-message-box"),
};

function setMessage(type, text) {
  if (!text) {
    elements.messageBox.innerHTML = "";
    return;
  }

  elements.messageBox.innerHTML = `<div class="message ${type}">${text}</div>`;
}

function setLoadingState(isLoading) {
  elements.loginButton.disabled = isLoading;
  elements.signupButton.disabled = isLoading;
  elements.forgotPasswordButton.disabled = isLoading;
}

function getCredentials() {
  return {
    email: elements.email.value.trim(),
    password: elements.password.value,
  };
}

function redirectToApp() {
  window.location.replace(nextPath);
}

async function handleLogin(event) {
  event.preventDefault();
  const { email, password } = getCredentials();

  setLoadingState(true);
  setMessage("", "");

  try {
    await signInWithEmail(email, password);
    redirectToApp();
  } catch (error) {
    setMessage("error", error instanceof Error ? error.message : "Не удалось выполнить вход.");
  } finally {
    setLoadingState(false);
  }
}

async function handleSignup() {
  const { email, password } = getCredentials();

  setLoadingState(true);
  setMessage("", "");

  try {
    const result = await signUpWithEmail(email, password);
    const needsEmailConfirmation = !result.session;

    if (needsEmailConfirmation) {
      setMessage("info", "Регистрация выполнена. Подтвердите email и затем войдите в систему.");
      return;
    }

    redirectToApp();
  } catch (error) {
    setMessage(
      "error",
      error instanceof Error ? error.message : "Не удалось выполнить регистрацию."
    );
  } finally {
    setLoadingState(false);
  }
}

async function handleForgotPassword() {
  const email = elements.email.value.trim();

  if (!email) {
    setMessage("error", "Введите email, чтобы запросить восстановление пароля.");
    return;
  }

  setLoadingState(true);
  setMessage("", "");

  try {
    await requestPasswordReset(email);
    setMessage("info", "Письмо для восстановления пароля отправлено. Проверьте почту.");
  } catch (error) {
    setMessage(
      "error",
      error instanceof Error ? error.message : "Не удалось отправить письмо для восстановления."
    );
  } finally {
    setLoadingState(false);
  }
}

async function init() {
  await redirectAuthenticated({ redirectTo: nextPath });
  elements.form.addEventListener("submit", handleLogin);
  elements.signupButton.addEventListener("click", handleSignup);
  elements.forgotPasswordButton.addEventListener("click", handleForgotPassword);
}

init().catch((error) => {
  setMessage("error", error instanceof Error ? error.message : "Ошибка инициализации авторизации.");
});
