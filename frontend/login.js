const API_BASE = "http://localhost:8000";

const form = document.getElementById("login-form");
const message = document.getElementById("message");
const btnSubmit = document.getElementById("btn-submit");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  message.className = "message";
  message.textContent = "";
  btnSubmit.classList.add("loading");

  const payload = {
    email: form.email.value.trim(),
    password: form.password.value,
  };

  try {
    const res = await fetch(`${API_BASE}/usuarios/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error al iniciar sesión");
    }

    const data = await res.json();
    message.className = "message success";
    message.textContent = `Bienvenido, ${data.nombre}. Redirigiendo...`;
    form.reset();

    setTimeout(() => {
      window.location.href = "index.html";
    }, 1500);
  } catch (err) {
    message.className = "message error";
    message.textContent = err.message;
  } finally {
    btnSubmit.classList.remove("loading");
  }
});
