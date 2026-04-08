const apiBase = "/api/items";
const form = document.getElementById("item-form");
const itemIdInput = document.getElementById("item-id");
const nameInput = document.getElementById("name");
const descriptionInput = document.getElementById("description");
const statusField = document.getElementById("status-field");
const itemsNode = document.getElementById("items");
const statusNode = document.getElementById("status");
const titleNode = document.getElementById("form-title");
const cancelButton = document.getElementById("cancel-button");

function setStatus(message, isError = false) {
  statusNode.textContent = message;
  statusNode.style.color = isError ? "#b42318" : "#52606d";
}

function formatErrorDetail(detail) {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((entry) => entry.msg || JSON.stringify(entry)).join(" | ");
  }

  return "Erro desconhecido";
}

function resetForm() {
  itemIdInput.value = "";
  form.reset();
  statusField.value = "PENDENTE";
  titleNode.textContent = "Criar item";
}

function populateForm(item) {
  itemIdInput.value = item.id;
  nameInput.value = item.name;
  descriptionInput.value = item.description || "";
  statusField.value = item.status;
  titleNode.textContent = `Editar item ${item.id.slice(0, 8)}`;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: "Erro desconhecido" }));
    throw new Error(formatErrorDetail(errorBody.detail));
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function renderItems(items) {
  if (!items.length) {
    itemsNode.innerHTML = "<p>Nenhum item criado. Experimente criar para enxergar os traces chegando no Live Tail.</p>";
    return;
  }

  itemsNode.innerHTML = items
    .map(
      (item) => `
        <article class="item">
          <header>
            <div>
              <strong>${item.name}</strong>
              <div class="meta">ID ${item.id}</div>
            </div>
            <span class="pill">${item.status}</span>
          </header>
          <div>${item.description || "Nenhuma descrição."}</div>
          <div class="meta">Última atualização ${new Date(item.updated_at).toLocaleString()}</div>
          <div class="row">
            <button type="button" data-edit="${item.id}">Editar</button>
            <button type="button" class="danger" data-delete="${item.id}">Deletar</button>
          </div>
        </article>
      `
    )
    .join("");

  itemsNode.querySelectorAll("[data-edit]").forEach((button) => {
    button.addEventListener("click", async () => {
      const item = await request(`${apiBase}/${button.dataset.edit}`);
      populateForm(item);
    });
  });

  itemsNode.querySelectorAll("[data-delete]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await request(`${apiBase}/${button.dataset.delete}`, { method: "DELETE" });
        setStatus("Item deletedo. Cheque o trace DELETE e o span do consumer no Datadog.");
        await loadItems();
        if (itemIdInput.value === button.dataset.delete) {
          resetForm();
        }
      } catch (error) {
        setStatus(error.message, true);
      }
    });
  });
}

async function loadItems() {
  try {
    const items = await request(apiBase);
    renderItems(items);
  } catch (error) {
    setStatus(error.message, true);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    name: nameInput.value.trim(),
    description: descriptionInput.value.trim() || null,
    status: statusField.value,
  };

  try {
    const itemId = itemIdInput.value;
    if (itemId) {
      await request(`${apiBase}/${itemId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setStatus("Item atualizado.");
    } else {
      await request(apiBase, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setStatus("Item criado. Um create event foi publicado ao RabbitMQ.");
    }
    resetForm();
    await loadItems();
  } catch (error) {
    setStatus(error.message, true);
  }
});

cancelButton.addEventListener("click", resetForm);

loadItems();
