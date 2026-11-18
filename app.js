"use strict";

const byId = (id) => document.getElementById(id);
document.querySelectorAll("[data-print]").forEach((button) => {
  button.addEventListener("click", () => window.print());
});
document.querySelector("[data-back]")?.addEventListener("click", () => history.back());

const stockKind = byId("stock-kind");
if (stockKind) {
  function showStockFields() {
    document.querySelectorAll("[data-stock]").forEach((field) => {
      const show = field.dataset.stock === (stockKind.value === "in" ? "entry" : "adjust");
      field.closest("label").hidden = !show;
      field.disabled = !show;
      field.required = show;
    });
  }
  stockKind.addEventListener("change", showStockFields);
  showStockFields();
}

function setupPos(form) {
  const catalog = JSON.parse(form.querySelector("[data-catalog]").dataset.catalog);
  const search = byId("search");
  const quantity = byId("scan-quantity");
  const cart = byId("cart");
  const method = byId("method");
  const received = byId("received");
  const notice = byId("pos-notice");
  const currency = new Intl.NumberFormat("pt-BR", {style: "currency", currency: "BRL"});
  const format = (cents) => currency.format(cents / 100);
  const normalize = (value) => value?.trim().toLocaleLowerCase("pt-BR");
  const label = (product) => product.name + " · " + product.sku;
  function cents(value) {
    const text = value.trim().replace(",", ".");
    if (!text) return 0;
    return /^\d{1,7}(\.\d{0,2})?$/.test(text) ? Math.round(Number(text) * 100) : NaN;
  }
  function discount(value, mode, gross) {
    const amount = cents(value);
    if (mode === "percent") return amount <= 10000 ? Math.round(gross * amount / 10000) : NaN;
    return amount <= gross ? amount : NaN;
  }
  for (const product of catalog) {
    const option = document.createElement("option");
    option.value = label(product);
    byId("search-options").append(option);
  }
  function match() {
    const needle = normalize(search.value);
    if (!needle) return null;
    const exact = catalog.find((p) => [p.sku, p.barcode, label(p)].some((value) => normalize(value) === needle));
    if (exact) return exact;
    const matches = catalog.filter((p) => normalize(p.name).includes(needle));
    return matches.length === 1 ? matches[0] : null;
  }
  function update() {
    let subtotal = 0;
    for (const row of cart.rows) {
      const gross = Number(row.dataset.price) * Number(row.querySelector("[data-qty]").value);
      const net = gross - discount(row.querySelector("[data-discount]").value,
        row.querySelector("select").value, gross);
      row.querySelector("[data-subtotal]").textContent = Number.isFinite(net) ? format(net) : "Inválido";
      subtotal += net;
    }
    const total = subtotal - discount(byId("sale-discount").value, byId("sale-discount-mode").value, subtotal);
    byId("pos-total").textContent = Number.isFinite(total) ? format(total) : "Desconto inválido";
    byId("empty-cart").hidden = cart.rows.length > 0;
    const cash = method.value === "Dinheiro";
    received.closest("label").hidden = !cash;
    received.disabled = !cash;
    received.required = cash;
    const change = cents(received.value) - total;
    byId("change").textContent = cash && received.value
      ? Number.isFinite(change) && change >= 0 ? "Troco " + format(change) : "Confira o valor recebido."
      : "";
    return total;
  }
  async function cancel(kind, detail, remove) {
    const reason = window.prompt("Informe o motivo do cancelamento.");
    if (!reason?.trim() || !window.confirm("Confirmar cancelamento?")) return;
    try {
      const response = await fetch("/draft", {
        method: "POST",
        body: new URLSearchParams({csrf: form.elements.csrf.value, kind, reason: detail + " · " + reason})
      });
      if (!response.ok) throw new Error();
      remove();
      update();
    } catch {
      notice.textContent = "Não foi possível registrar o cancelamento.";
    }
  }
  function createRow(product, count) {
    const row = cart.insertRow();
    row.id = "item-" + product.id;
    row.dataset.price = product.price;
    row.insertCell().textContent = product.name;
    const input = document.createElement("input");
    input.type = "number";
    input.min = "1";
    input.max = Math.min(product.balance, 1000000);
    input.required = true;
    input.name = "qty_" + product.id;
    input.value = count;
    input.dataset.qty = "";
    input.setAttribute("aria-label", "Quantidade de " + product.name);
    row.insertCell().append(input);
    row.insertCell().textContent = format(product.price);
    const amount = document.createElement("input");
    amount.name = "discount_" + product.id;
    amount.dataset.discount = "";
    amount.inputMode = "decimal";
    amount.setAttribute("aria-label", "Desconto de " + product.name);
    const mode = document.createElement("select");
    mode.name = amount.name + "_mode";
    mode.setAttribute("aria-label", "Tipo de desconto de " + product.name);
    mode.add(new Option("R$", "fixed"));
    mode.add(new Option("%", "percent"));
    row.insertCell().append(amount, mode);
    row.insertCell().dataset.subtotal = "";
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "secondary";
    remove.textContent = "Remover";
    remove.setAttribute("aria-label", "Remover " + product.name);
    remove.addEventListener("click", async () => {
      remove.disabled = true;
      await cancel("item", product.name, () => row.remove());
      remove.disabled = false;
    });
    row.insertCell().append(remove);
  }
  function add() {
    const product = match();
    if (!product) {
      notice.textContent = "Produto não encontrado ou busca ambígua. Confira o nome ou código.";
      return;
    }
    const count = Number(quantity.value);
    const existing = byId("item-" + product.id)?.querySelector("[data-qty]");
    const total = count + Number(existing?.value || 0);
    if (!Number.isInteger(count) || count <= 0 || total > Math.min(product.balance, 1000000)) {
      notice.textContent = "Quantidade inválida. Estoque vendável de " + product.name + ": " + product.balance + ".";
      return;
    }
    if (existing) existing.value = total;
    else createRow(product, count);
    notice.textContent = product.name + " adicionado à venda.";
    search.value = "";
    quantity.value = "1";
    search.focus();
    update();
  }
  byId("add-item").addEventListener("click", add);
  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      add();
    }
  });
  byId("clear-sale").addEventListener("click", async (event) => {
    if (!cart.rows.length) return;
    const button = event.currentTarget;
    button.disabled = true;
    await cancel("sale", "Venda em andamento", () => {
      cart.replaceChildren();
      form.reset();
      search.focus();
    });
    button.disabled = false;
  });
  form.addEventListener("input", update);
  form.addEventListener("submit", (event) => {
    const total = update();
    if (!cart.rows.length || !Number.isFinite(total) || (method.value === "Dinheiro" &&
        (!Number.isFinite(cents(received.value)) || cents(received.value) < total))) {
      event.preventDefault();
      notice.textContent = "Revise os itens, descontos e valor recebido.";
    } else {
      byId("finish-sale").disabled = true;
    }
  });
  window.addEventListener("pageshow", () => { byId("finish-sale").disabled = false; });
  byId("close-form").addEventListener("submit", (event) => {
    if (cart.rows.length || !window.confirm("Confirmar o fechamento do turno?")) {
      event.preventDefault();
      if (cart.rows.length) {
        notice.textContent = "Conclua ou cancele a venda antes de fechar o caixa.";
        notice.scrollIntoView({block: "center"});
      }
    }
  });
  byId("pos-help").addEventListener("click", () => {
    notice.textContent = "F1 Ajuda · F2 Buscar · F3 Cliente · F4 Desconto · F5 Cancelar item · F6 Cancelar venda em andamento · F7 Pagamento · F8 Consultar preço · F9 Concluir · Esc Voltar à busca";
  });
  const shortcuts = {
    F1: () => byId("pos-help").click(),
    F2: () => search.focus(),
    F3: () => byId("customer").focus(),
    F4: () => byId("sale-discount").focus(),
    F5: () => (document.activeElement.closest("tr") || cart.rows[cart.rows.length - 1])?.querySelector("button")?.click(),
    F6: () => byId("clear-sale").click(),
    F7: () => method.focus(),
    F8: () => {
      const product = match();
      notice.textContent = product ? product.name + " · " + format(product.price) + " · Estoque " + product.balance
        : "Informe o nome ou código do produto para consultar o preço.";
      search.focus();
    },
    F9: () => form.requestSubmit(),
    Escape: () => search.focus()
  };
  document.addEventListener("keydown", (event) => {
    if (shortcuts[event.key] && !event.ctrlKey && !event.altKey && !event.metaKey) {
      event.preventDefault();
      shortcuts[event.key]();
    }
  });
  update();
}

const salesForm = byId("sale-form");
if (salesForm) setupPos(salesForm);
