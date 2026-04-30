const endpoints = [
  {
    method: "GET",
    path: "/health",
    description: "Verifica que la API esté viva.",
  },
  {
    method: "GET",
    path: "/usuarios",
    description: "Listado de usuarios del sistema.",
  },
  {
    method: "GET",
    path: "/propiedades",
    description: "Listado de propiedades con filtros.",
  },
  {
    method: "GET",
    path: "/reservas",
    description: "Listado de reservas con filtros.",
  },
];

const endpointList = document.querySelector("#endpoint-list");

endpointList.innerHTML = endpoints
  .map(
    (endpoint) => `
      <article class="endpoint-item">
        <div>
          <code>${endpoint.method} ${endpoint.path}</code>
          <p>${endpoint.description}</p>
        </div>
      </article>
    `,
  )
  .join("");
