const list = document.getElementById("list");
const form = document.getElementById("form");
const input = document.getElementById("title");

async function api(path, opts) {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  return r.status === 204 ? null : r.json();
}

async function render() {
  const todos = await api("/api/todos");
  list.replaceChildren(...todos.map((t) => {
    const li = document.createElement("li");
    if (t.done) li.className = "done";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = t.done;
    cb.onchange = async () => {
      await api(`/api/todos/${t.id}`, { method: "PATCH", body: JSON.stringify({ done: cb.checked }) });
      render();
    };
    const span = document.createElement("span");
    span.textContent = t.title; // textContent => no XSS
    const del = document.createElement("button");
    del.textContent = "✕";
    del.onclick = async () => {
      await api(`/api/todos/${t.id}`, { method: "DELETE" });
      render();
    };
    li.append(cb, span, del);
    return li;
  }));
}

form.onsubmit = async (e) => {
  e.preventDefault();
  await api("/api/todos", { method: "POST", body: JSON.stringify({ title: input.value }) });
  input.value = "";
  render();
};
render();
