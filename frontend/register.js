const API_BASE = "http://localhost:8000";

const form = document.getElementById("register-form");
const message = document.getElementById("message");
const btnSubmit = document.getElementById("btn-submit");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  message.className = "message";
  message.textContent = "";
  btnSubmit.classList.add("loading");

  const payload = {
    nombre: form.nombre.value.trim(),
    email: form.email.value.trim(),
    password: form.password.value,
    rol: form.rol.value,
  };

  try {
    const res = await fetch(`${API_BASE}/usuarios/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error al registrar usuario");
    }

    const usuario = await res.json();
    message.className = "message success";
    message.textContent = `Usuario "${usuario.nombre}" creado con éxito. Redirigiendo...`;
    form.reset();

    setTimeout(() => {
      window.location.href = "index.html";
    }, 2000);
  } catch (err) {
    message.className = "message error";
    message.textContent = err.message;
  } finally {
    btnSubmit.classList.remove("loading");
  }
});
