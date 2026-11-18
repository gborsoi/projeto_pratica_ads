import json
from datetime import date, timedelta
from html import escape
from secrets import token_urlsafe

from operations import expected, open_till, record
from storage import METHODS, ROLES, today

PAGES = {
    "home": ("⌂", "Visão geral"), "pdv": ("▤", "PDV / Caixa"), "tills": ("▣", "Caixas"),
    "products": ("◇", "Produtos"), "stock": ("▥", "Estoque"), "purchases": ("↙", "Compras"),
    "suppliers": ("□", "Fornecedores"), "customers": ("♙", "Clientes"), "finance": ("◈", "Financeiro"),
    "reports": ("▧", "Relatórios"), "users": ("♧", "Usuários"), "audit": ("≡", "Auditoria"),
    "settings": ("⚙", "Configurações"), "account": ("◎", "Minha conta"),
    "receipt": ("", "Comprovante"), "till": ("", "Conferência de caixa"),
}


def e(value):
    return escape(str(value if value is not None else ""), quote=True)


def br(value):
    amount = f"{abs(value or 0) // 100:,}".replace(",", ".")
    return f"{'−' if (value or 0) < 0 else ''}R$ {amount},{abs(value or 0) % 100:02}"


def decimal(value):
    return f"{value // 100}.{value % 100:02}"


def stamp(value):
    if not value:
        return "—"
    raw_date, _, hour = value.partition("T")
    return "/".join(reversed(raw_date.split("-"))) + (f" às {hour[:5]}" if hour else "")


def field(label, name, type="text", value="", required=True, extra=""):
    return (f'<label>{e(label)}<input name="{name}" type="{type}" value="{e(value)}" '
            f'{"required" if required else ""} {extra}></label>')


def check(label, name, checked=False, required=False):
    return (f'<label class="check"><input type="checkbox" name="{name}" '
            f'{"checked" if checked else ""} {"required" if required else ""}>{e(label)}</label>')


def select(label, name, options, value="", optional=False, extra=""):
    placeholder = "Sem vínculo" if optional else "Selecione"
    choices = f'<option value="">{placeholder}</option>'
    for key, title in options:
        choices += f'<option value="{e(key)}" {"selected" if str(key) == str(value) else ""}>{e(title)}</option>'
    return f'<label>{e(label)}<select name="{name}" {"" if optional else "required"} {extra}>{choices}</select></label>'


def button(label, secondary=False):
    return f'<button class="{"secondary" if secondary else "primary"}">{e(label)}</button>'


def link(page, label):
    return f'<a class="secondary button" href="/{e(page)}">{e(label)}</a>'


def hidden(name, value):
    return f'<input type="hidden" name="{name}" value="{e(value)}">'


def form(csrf, action, body, label, back="", extra=""):
    return (f'<form method="post" action="/{action}" {extra}>{hidden("csrf", csrf)}'
            f'{hidden("back", back)}{body}{button(label) if label else ""}</form>')


def table(headers, rows):
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    if not body:
        return '<div class="empty">Nenhum registro encontrado.</div>'
    head = "".join(f'<th scope="col">{e(title)}</th>' for title in headers)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def panel(title, body):
    return f'<section class="panel"><h2>{e(title)}</h2>{body}</section>'


def metrics(items):
    return '<div class="metrics">' + "".join(
        f'<article><span>{e(label)}</span><strong>{e(value)}</strong></article>' for label, value in items
    ) + "</div>"


def expandable(title, body, opened=False):
    return f'<details {"open" if opened else ""}><summary>{e(title)}</summary>{body}</details>'


def contact_options(db, kind):
    return [(row["id"], row["name"]) for row in db.execute(
        "SELECT id,name FROM contacts WHERE kind=? ORDER BY name", (kind,))]


def products(db):
    return db.execute("""SELECT p.*, COALESCE(SUM(l.quantity),0) AS physical,
                     COALESCE(SUM(CASE WHEN l.expiry>=? THEN l.quantity ELSE 0 END),0) AS balance
                     FROM products p LEFT JOIN lots l ON l.product_id=p.id
                     GROUP BY p.id ORDER BY p.name""", (today(),)).fetchall()


def allowed(user, page):
    if page in {"home", "pdv", "receipt", "till", "account"}:
        return True
    if user["role"] == "cashier":
        return False
    return page in PAGES and (page not in {"users", "settings", "audit"} or user["role"] == "owner")


def document(title, body, name="Mercado Central"):
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{e(title)} · {e(name)}</title><link rel="stylesheet" href="/style.css">
    <script src="/app.js" defer></script></head>{body}</html>"""


def login_page(csrf, error="", first=False):
    fields = field("Nome", "name") if first else ""
    fields += field("Usuário", "login", extra='autocomplete="username" autofocus')
    fields += field("Senha", "password", "password", extra=(
        'autocomplete="new-password" minlength="10"' if first else 'autocomplete="current-password"'))
    title = "Crie sua conta de proprietário" if first else "Acesse sua conta"
    action = "setup" if first else "login"
    return document(title, f"""<body class="login"><aside class="login-brand">
    <div class="wordmark"><b>▰</b><span>Mercado Central</span></div>
    <p class="login-display">Seu mercado<br>em ordem.</p>
    <p>Conecte a rotina do caixa ao controle de estoque e à gestão da loja.</p>
    </aside><main class="login-content"><div><p class="eyebrow">Gestão de supermercado</p><h1>{title}</h1>
    {f'<p class="error" role="alert">{e(error)}</p>' if error else ''}
    {form(csrf, action, fields, "Criar proprietário" if first else "Entrar")}</div></main></body>""")


def layout(db, user, page, csrf, body):
    name = db.execute("SELECT value FROM config WHERE key='name'").fetchone()[0]
    title = PAGES[page][1]
    groups = (("Operação", ("home", "pdv", "tills", "products", "stock")),
              ("Gestão", ("purchases", "suppliers", "customers", "finance", "reports")),
              ("Administração", ("users", "audit", "settings", "account")))
    navigation = ""
    for group, keys in groups:
        links = ""
        for key in keys:
            if allowed(user, key):
                icon, label = PAGES[key]
                current = 'aria-current="page"' if page == key else ""
                links += f'<a href="/{key}" {current}><span aria-hidden="true">{icon}</span>{label}</a>'
        if links:
            navigation += f'<div class="nav-group"><p>{group}</p>{links}</div>'
    return document(title, f"""<body><aside class="sidebar">
    <a class="wordmark" href="/home"><b>▰</b><span>{e(name)}</span></a>
    <nav aria-label="Menu principal">{navigation}</nav>
    <div class="sidebar-bottom">{form(csrf, 'logout', '', 'Sair')}</div></aside>
    <div class="workspace"><header class="top"><span>Área de trabalho</span>
    <span class="identity"><b>{e(user['name'])}</b><small>{ROLES[user['role']]}</small></span></header>
    <main class="content"><div class="page-head"><div><p class="eyebrow">{e(stamp(today()))}</p>
    <h1>{e(title)}</h1></div></div>{body}</main></div></body>""", name)


def dashboard(db, user):
    if user["role"] == "cashier":
        till = open_till(db, user["id"])
        state = f"Caixa {till['number']} aberto" if till else "Nenhum caixa aberto"
        return metrics([("Situação do turno", state)]) + panel("Ponto de venda", link("pdv", "Acessar o caixa"))
    sales = db.execute("""SELECT COUNT(*) n,COALESCE(SUM(total),0) total,COALESCE(SUM(discount),0) discounts
                           FROM sales WHERE cancelled IS NULL AND substr(happened,1,10)=?""", (today(),)).fetchone()
    catalog = [p for p in products(db) if p["active"]]
    low = [p for p in catalog if p["balance"] <= p["minimum"]]
    open_count = db.execute("SELECT COUNT(*) FROM tills WHERE closed IS NULL").fetchone()[0]
    cutoff = (date.today() + timedelta(days=30)).isoformat()
    expiry = db.execute("""SELECT p.name,l.code,l.expiry,l.quantity FROM lots l JOIN products p ON p.id=l.product_id
                           WHERE l.expiry<=? AND l.quantity>0 ORDER BY l.expiry""", (cutoff,)).fetchall()
    payments = db.execute("""SELECT method, SUM(total) total FROM sales WHERE cancelled IS NULL
                              AND substr(happened,1,10)=? GROUP BY method ORDER BY total DESC""", (today(),))
    return (metrics([("Vendas de hoje", br(sales["total"])), ("Vendas concluídas", sales["n"]),
                     ("Ticket médio", br(sales["total"] // sales["n"] if sales["n"] else 0)),
                     ("Caixas abertos", open_count)]) +
            '<div class="split">' +
            panel("Faturamento por pagamento", table(["Forma", "Total"], [(e(r["method"]), br(r["total"])) for r in payments])) +
            panel("Estoque baixo", table(["Produto", "Disponível", "Mínimo"],
                                        [(e(r["name"]), r["balance"], r["minimum"]) for r in low])) +
            "</div>" + panel("Validade · próximos 30 dias ou vencidos",
                              table(["Produto", "Lote", "Validade", "Saldo"], [
                                  (e(r["name"]), e(r["code"]), e(stamp(r["expiry"])), r["quantity"]) for r in expiry])))


def catalog_view(db, csrf, query):
    identifier = query.get("id")
    product = dict(record(db, "products", identifier)) if identifier else {"active": 1}
    fields = [field("Nome", "name", value=product.get("name", "")),
              field("Código (SKU)", "sku", value=product.get("sku", "")),
              field("Código de barras", "barcode", value=product.get("barcode"), required=False),
              field("Categoria", "category", value=product.get("category", "")),
              field("Unidade", "unit", value=product.get("unit", "un")),
              field("Custo (R$)", "cost", value=decimal(product.get("cost", 0))),
              field("Preço de venda (R$)", "price", value=decimal(product.get("price", 0))),
              field("Estoque mínimo", "minimum", "number", product.get("minimum", 0), extra='min="0"'),
              select("Fornecedor", "supplier", contact_options(db, "supplier"), product.get("supplier"), True),
              field("Tributação", "tax", value=product.get("tax"), required=False),
              check("Produto ativo", "active", product["active"])]
    if not identifier:
        fields.extend([field("Estoque inicial", "initial", "number", 0, extra='min="0"'),
                       field("Lote inicial", "lot", required=False),
                       field("Validade inicial", "expiry", "date", required=False)])
    fields_html = '<div class="fields">' + "".join(fields) + "</div>"
    rows = [(e(p["name"]), e(p["sku"]), e(p["category"]), br(p["price"]), p["balance"],
             "Ativo" if p["active"] else "Inativo", link(f"products?id={p['id']}", "Editar"))
            for p in products(db)]
    return (panel("Catálogo", table(["Produto", "SKU", "Categoria", "Preço", "Disponível", "Situação", ""], rows)) +
            panel("Cadastro", expandable("Editar produto" if identifier else "Novo produto",
                  form(csrf, "product", hidden("id", identifier or "") + fields_html, "Salvar", "products"), bool(identifier))))


def stock_view(db, csrf):
    catalog = products(db)
    lots = db.execute("""SELECT l.*,p.name FROM lots l JOIN products p ON p.id=l.product_id
                         ORDER BY l.expiry,p.name""").fetchall()
    fields = '<div class="fields">' + (
        select("Tipo", "kind", [("in", "Entrada"), ("out", "Saída / perda"), ("inventory", "Inventário")],
               "in", extra='id="stock-kind"') +
        select("Produto", "product", [(p["id"], p["name"]) for p in catalog], optional=True, extra='data-stock="entry"') +
        field("Código do lote", "lot", required=False, extra='data-stock="entry"') +
        field("Validade", "expiry", "date", required=False, extra='data-stock="entry"') +
        select("Lote existente", "lot_id", [(r["id"], f"{r['name']} · {r['code']}") for r in lots],
               optional=True, extra='data-stock="adjust"') +
        field("Quantidade", "quantity", "number", extra='min="0"') + field("Motivo", "reason")) + "</div>"
    history = db.execute("""SELECT m.*, p.name,l.code,u.name AS employee FROM movements m
                            JOIN lots l ON l.id=m.lot_id JOIN products p ON p.id=l.product_id
                            JOIN users u ON u.id=m.user_id ORDER BY m.id DESC LIMIT 100""").fetchall()
    return (panel("Saldos por produto", table(["Produto", "Físico", "Disponível", "Mínimo", "Situação"],
                 [(e(p["name"]), p["physical"], p["balance"], p["minimum"],
                   "Em falta" if not p["balance"] else "Estoque baixo" if p["balance"] <= p["minimum"] else "Regular")
                  for p in catalog])) +
            panel("Lotes", table(["Produto", "Lote", "Entrada", "Validade", "Saldo", "Situação"],
                  [(e(r["name"]), e(r["code"]), stamp(r["received"]), stamp(r["expiry"]), r["quantity"],
                    "Vencido" if r["expiry"] < today() else "Validade próxima" if r["expiry"] <=
                    (date.today() + timedelta(days=30)).isoformat() else "Em dia") for r in lots])) +
            panel("Movimentar estoque", form(csrf, "stock", fields, "Registrar ajuste", "stock")) +
            panel("Movimentações recentes", table(["Data", "Produto", "Lote", "Quantidade", "Motivo", "Usuário"],
                  [(stamp(r["happened"]), e(r["name"]), e(r["code"]), f'{r["delta"]:+d}', e(r["reason"]), e(r["employee"]))
                   for r in history])))


def sale_rows(rows):
    return [(link(f"receipt?id={r['id']}", f"#{r['id']}"), stamp(r["happened"]), e(r["method"]),
             br(r["total"]), "Cancelada" if r["cancelled"] else "Concluída") for r in rows]


def pdv(db, user, csrf):
    till = open_till(db, user["id"])
    if not till:
        fields = '<div class="fields">' + field("Número do caixa", "number", value="01") + field(
            "Valor inicial em dinheiro (R$)", "initial", value="0.00") + "</div>"
        history = db.execute("SELECT * FROM tills WHERE user_id=? ORDER BY id DESC LIMIT 10", (user["id"],))
        return (panel("Abertura de caixa", form(csrf, "open", fields, "Abrir caixa", "pdv")) +
                panel("Turnos recentes", table(["Caixa", "Abertura", "Fechamento", ""],
                      [(e(r["number"]), stamp(r["opened"]), stamp(r["closed"]), link(f"till?id={r['id']}", "Conferir"))
                       for r in history])))
    catalog = [{k: p[k] for k in ("id", "name", "sku", "barcode", "price", "balance")}
               for p in products(db) if p["active"]]
    payload = e(json.dumps(catalog, ensure_ascii=False))
    approval = field("Usuário do gerente", "approver", required=False, extra='autocomplete="off"') + field(
        "Senha de autorização", "authorization", "password", required=False, extra='autocomplete="off"')
    sale_fields = f"""
    {hidden("request", token_urlsafe(18))}
    <div class="pos-grid" data-catalog="{payload}">
      <section class="panel">
        <h2>Itens da venda</h2>
        <div class="scan">
          {field("Produto por código ou nome", "search", required=False, extra='id="search" list="search-options" autocomplete="off"')}
          <datalist id="search-options"></datalist>
          {field("Quantidade", "scan_quantity", "number", 1, False, 'id="scan-quantity" min="1" max="1000000"')}
          <button type="button" class="secondary" id="add-item">Adicionar</button>
        </div>
        <p class="notice" id="pos-notice" role="status"></p>
        <div class="table-wrap"><table><thead><tr><th>Produto</th><th>Qtd.</th><th>Preço</th><th>Desconto</th>
        <th>Subtotal</th><th><span class="sr-only">Remover</span></th></tr></thead><tbody id="cart"></tbody></table></div>
        <p id="empty-cart" class="empty">Passe o código de barras ou procure um produto.</p>
        <button type="button" class="secondary" id="clear-sale">Cancelar venda em andamento</button>
      </section>
      <section class="panel payment">
        <h2>Pagamento</h2><span class="total-label">Total da venda</span><strong id="pos-total" class="pos-total">R$ 0,00</strong>
        {select("Cliente", "customer", contact_options(db, "customer"), optional=True, extra='id="customer"')}
        <div class="discount-fields">
        {field("Desconto na venda", "sale_discount", required=False, extra='id="sale-discount"')}
        {select("Tipo", "sale_discount_mode", [("fixed", "R$"), ("percent", "%")], "fixed", extra='id="sale-discount-mode"')}
        </div>
        {select("Forma de pagamento", "method", [(m, m) for m in METHODS], "Dinheiro", extra='id="method"')}
        {field("Valor recebido (R$)", "received", required=False, extra='id="received"')}
        <p id="change" class="notice"></p>
        {expandable("Autorização gerencial", approval) if user["role"] == "cashier" else ""}
        {check("Confirmei o recebimento", "confirmed", required=True)}
        <button class="primary" id="finish-sale">Concluir venda</button>
        <button type="button" class="secondary" id="pos-help">Atalhos do PDV</button>
      </section>
    </div>"""
    totals = expected(db, till)
    close = '<div class="fields">' + "".join(
        field(f"{method} · esperado {br(total)}", f"count_{index}", extra='inputmode="decimal"')
        for index, (method, total) in enumerate(totals.items())) + "</div>"
    sales = db.execute("SELECT * FROM sales WHERE till_id=? ORDER BY id DESC", (till["id"],))
    return (f'<div class="status-bar"><span class="dot"></span> Caixa {e(till["number"])} aberto'
            f' <span>desde {e(stamp(till["opened"]))}</span></div>' +
            form(csrf, "sell", sale_fields, "", "pdv", 'id="sale-form"') +
            panel("Vendas do turno", table(["Venda", "Data", "Pagamento", "Total", "Situação"], sale_rows(sales))) +
            panel("Fechamento", expandable("Conferir valores do turno",
                  form(csrf, "close", close, "Confirmar fechamento", "pdv", 'id="close-form"'))))


def receipt(db, user, csrf, identifier):
    sale = record(db, "sales", identifier)
    till = record(db, "tills", sale["till_id"])
    manages = user["role"] != "cashier"
    if not manages and till["user_id"] != user["id"]:
        raise ValueError("Você não tem acesso a esta venda.")
    lines = db.execute("""SELECT s.*,l.code FROM sale_lines s JOIN lots l ON l.id=s.lot_id
                          WHERE sale_id=?""", (identifier,))
    rows = [(e(r["name"]), e(r["code"]), r["quantity"], br(r["price"]), br(r["discount"])) for r in lines]
    state = "Cancelada" if sale["cancelled"] else "Concluída"
    context = f'<p>{stamp(sale["happened"])} · Caixa {e(till["number"])} · {e(sale["method"])} · {state}</p>'
    if sale["cancelled"]:
        approver = record(db, "users", sale["cancel_approver"])
        context += f'<p>Motivo: {e(sale["cancel_reason"])}. Autorização: {e(approver["name"])}.</p>'
    body = panel(f"Comprovante de venda #{sale['id']}", context +
                 table(["Produto", "Lote", "Qtd.", "Preço unitário", "Desconto do item"], rows) +
                 metrics([("Descontos", br(sale["discount"])), ("Total", br(sale["total"])),
                          ("Recebido", br(sale["received"])), ("Troco", br(sale["received"] - sale["total"]))]) +
                 '<button type="button" class="secondary no-print" data-print>Imprimir comprovante</button>')
    back = f"receipt?id={sale['id']}"
    if manages:
        body += panel("Conciliação fiscal", form(csrf, "fiscal", hidden("id", sale["id"]) +
                      field("Referência da nota emitida externamente", "reference", value=sale["fiscal"]),
                      "Vincular referência", back))
    if not till["closed"] and not sale["cancelled"]:
        authorization = "" if manages else field("Usuário autorizador", "approver") + field(
            "Senha de autorização", "authorization", "password")
        body += panel("Cancelamento", expandable("Estornar venda", form(csrf, "cancel",
                      hidden("id", sale["id"]) + field("Motivo", "reason") + authorization +
                      check("Confirmo o estorno dos itens", "confirm", required=True), "Confirmar cancelamento", back)))
    return body + link("pdv", "Voltar ao PDV")


def till_view(db, user, csrf, identifier=None):
    if identifier:
        till = record(db, "tills", identifier)
        if user["role"] == "cashier" and till["user_id"] != user["id"]:
            raise ValueError("Você não tem acesso a este caixa.")
        counts = db.execute("SELECT * FROM counts WHERE till_id=?", (identifier,))
        rows = [(e(r["method"]), br(r["expected"]), br(r["counted"]),
                 br(r["counted"] - r["expected"])) for r in counts] if till["closed"] else [
            (e(method), br(value), "—", "—") for method, value in expected(db, till).items()]
        sales = db.execute("SELECT * FROM sales WHERE till_id=? ORDER BY id DESC", (identifier,))
        body = panel(f"Caixa {till['number']}", f'<p>Abertura {stamp(till["opened"])} · '
                     f'Fechamento {stamp(till["closed"])}</p>' +
                     table(["Pagamento", "Esperado", "Informado", "Diferença"], rows) +
                     '<button type="button" class="secondary no-print" data-print>Imprimir conferência</button>')
        if till["closed"] and user["role"] != "cashier":
            body += panel("Reabertura", expandable("Reabrir turno", form(csrf, "reopen",
                          hidden("id", till["id"]), "Confirmar reabertura", f"till?id={till['id']}")))
        return body + panel("Vendas", table(["Venda", "Data", "Pagamento", "Total", "Situação"], sale_rows(sales)))
    tills = db.execute("""SELECT t.*,u.name,(SELECT COALESCE(SUM(total),0) FROM sales
                          WHERE till_id=t.id AND cancelled IS NULL) AS total FROM tills t
                          JOIN users u ON u.id=t.user_id ORDER BY t.id DESC""")
    return panel("Turnos", table(["Caixa", "Operador", "Abertura", "Fundo", "Vendas", "Situação", ""],
                 [(e(r["number"]), e(r["name"]), stamp(r["opened"]), br(r["initial"]), br(r["total"]),
                   "Fechado" if r["closed"] else "Aberto", link(f"till?id={r['id']}", "Conferir")) for r in tills]))


def contacts_view(db, csrf, kind, query):
    page = "customers" if kind == "customer" else "suppliers"
    entry = dict(record(db, "contacts", query["id"])) if query.get("id") else {}
    if entry and entry["kind"] != kind:
        raise ValueError("Cadastro não encontrado.")
    rows = db.execute("SELECT * FROM contacts WHERE kind=? ORDER BY name", (kind,))
    fields = [("Nome / razão social", "name"), ("CPF / CNPJ", "document"), ("Telefone", "phone"),
              ("E-mail", "email"), ("Endereço", "address"), ("Observações", "notes")]
    edit = hidden("kind", kind) + hidden("id", entry.get("id", "")) + '<div class="fields">' + "".join(
        field(label, key, "email" if key == "email" else "text", entry.get(key, ""), key == "name")
        for label, key in fields) + "</div>"
    body = panel("Cadastros", table(["Nome", "Documento", "Telefone", "E-mail", ""],
                 [(e(r["name"]), e(r["document"]), e(r["phone"]), e(r["email"]),
                   link(f"{page}?id={r['id']}", "Editar / histórico")) for r in rows]))
    body += panel("Cadastro", expandable("Editar cadastro" if entry else "Novo cadastro",
                  form(csrf, "contact", edit, "Salvar", page), bool(entry)))
    if entry and kind == "customer":
        body += panel("Histórico", table(["Venda", "Data", "Pagamento", "Total", "Situação"], sale_rows(
            db.execute("SELECT * FROM sales WHERE customer=? ORDER BY id DESC", (entry["id"],)))))
    if entry and kind == "supplier":
        history = db.execute("""SELECT c.*,p.name FROM purchases c JOIN products p ON p.id=c.product
                                WHERE c.supplier=? ORDER BY c.id DESC""", (entry["id"],))
        body += panel("Histórico de pedidos", table(["Pedido", "Produto", "Quantidade", "Recebimento"],
                     [(r["id"], e(r["name"]), r["quantity"], stamp(r["received"])) for r in history]))
    return body


def purchases_view(db, csrf, query):
    items = db.execute("""SELECT c.*,s.name AS supplier_name,p.name AS product_name FROM purchases c
                          JOIN contacts s ON s.id=c.supplier JOIN products p ON p.id=c.product
                          ORDER BY c.id DESC""")
    fields = select("Fornecedor", "supplier", contact_options(db, "supplier")) + select(
        "Produto", "product", [(p["id"], p["name"]) for p in products(db) if p["active"]]) + field(
        "Quantidade pedida", "quantity", "number", extra='min="1"') + field("Custo unitário (R$)", "cost")
    body = panel("Pedidos", table(["Pedido", "Fornecedor", "Produto", "Quantidade", "Custo unitário", "Situação"],
                 [(f"#{r['id']}", e(r["supplier_name"]), e(r["product_name"]), r["quantity"], br(r["cost"]),
                   f'Recebido: {r["actual"]} a {br(r["actual_cost"])} · {e(r["notes"])}' if r["received"] else
                   link(f"purchases?id={r['id']}", "Conferir recebimento")) for r in items]))
    body += panel("Novo pedido", expandable("Registrar pedido de compra",
                  form(csrf, "purchase", f'<div class="fields">{fields}</div>', "Registrar", "purchases")))
    if query.get("id"):
        entry = record(db, "purchases", query["id"])
        if not entry["received"]:
            fields = (field("Quantidade recebida", "quantity", "number", entry["quantity"], extra='min="0"') +
                      field("Custo unitário conferido (R$)", "cost", value=decimal(entry["cost"])) +
                      field("Lote", "lot", required=False) + field("Validade", "expiry", "date", required=False) +
                      field("Divergências", "notes", required=False))
            body += panel(f"Conferência do pedido #{entry['id']}", form(csrf, "receive",
                          hidden("id", entry["id"]) + f'<div class="fields">{fields}</div>' +
                          check("Conferi produto, quantidade e custo", "confirmed", required=True),
                          "Confirmar entrada", f"purchases?id={entry['id']}"))
    return body


def finance_view(db, csrf):
    entries = db.execute("SELECT * FROM finance ORDER BY settled IS NOT NULL,due,id").fetchall()
    payable = sum(r["amount"] for r in entries if r["kind"] == "pay" and not r["settled"])
    receivable = sum(r["amount"] for r in entries if r["kind"] == "receive" and not r["settled"])
    rows = [(e(r["description"]), "A pagar" if r["kind"] == "pay" else "A receber", br(r["amount"]),
             stamp(r["due"]), stamp(r["settled"]) if r["settled"] else form(
                 csrf, "settle", hidden("id", r["id"]), "Dar baixa", "finance")) for r in entries]
    fields = select("Tipo", "kind", [("pay", "A pagar"), ("receive", "A receber")]) + field(
        "Descrição", "description") + field("Valor (R$)", "amount") + field("Vencimento", "due", "date")
    return (metrics([("Contas a pagar em aberto", br(payable)), ("Contas a receber em aberto", br(receivable))]) +
            panel("Lançamentos", table(["Descrição", "Tipo", "Valor", "Vencimento", "Baixa"], rows)) +
            panel("Nova conta", form(csrf, "finance", f'<div class="fields">{fields}</div>', "Registrar", "finance")))


def reports(db, query):
    start = date.fromisoformat(query.get("start", today()[:8] + "01")).isoformat()
    end = date.fromisoformat(query.get("end", today())).isoformat()
    if start > end:
        raise ValueError("O início do período deve anteceder ou coincidir com o fim.")
    period = (start, end)
    sales = db.execute("""SELECT s.*,u.name AS employee,t.number,
                          COALESCE((SELECT SUM(cost*quantity) FROM sale_lines WHERE sale_id=s.id),0) AS cost
                          FROM sales s JOIN tills t ON t.id=s.till_id JOIN users u ON u.id=t.user_id
                          WHERE substr(s.happened,1,10) BETWEEN ? AND ? ORDER BY s.id DESC""", period).fetchall()
    confirmed = [r for r in sales if not r["cancelled"]]
    gross = sum(r["total"] for r in confirmed)
    cost = sum(r["cost"] for r in confirmed)
    breakdown = {}
    for sale in confirmed:
        key = (sale["employee"], sale["number"], sale["method"])
        breakdown[key] = breakdown.get(key, 0) + sale["total"]
    finance = db.execute("SELECT * FROM finance WHERE substr(settled,1,10) BETWEEN ? AND ?", period).fetchall()
    net = sum(r["amount"] if r["kind"] == "receive" else -r["amount"] for r in finance)
    moves = db.execute("""SELECT m.*,p.name,l.code FROM movements m JOIN lots l ON l.id=m.lot_id
                          JOIN products p ON p.id=l.product_id
                          WHERE substr(m.happened,1,10) BETWEEN ? AND ? ORDER BY m.id DESC""", period)
    lines = db.execute("""SELECT l.name,l.category,SUM(l.quantity) quantity,SUM(l.price*l.quantity-l.discount) total
                          FROM sale_lines l JOIN sales s ON s.id=l.sale_id WHERE s.cancelled IS NULL
                          AND substr(s.happened,1,10) BETWEEN ? AND ? GROUP BY l.name,l.category
                          ORDER BY quantity DESC""", period)
    return (panel("Período", f'<form method="get" class="fields">{field("De", "start", "date", start)}'
                  f'{field("Até", "end", "date", end)}{button("Filtrar")}'
                  '<button type="button" class="secondary no-print" data-print>Imprimir / salvar PDF</button></form>') +
            metrics([("Faturamento", br(gross)), ("Vendas concluídas", len(confirmed)),
                     ("Ticket médio", br(gross // len(confirmed) if confirmed else 0)),
                     ("Custo das vendas", br(cost)), ("Margem bruta", br(gross - cost)),
                     ("Fluxo registrado", br(gross + net)), ("Cancelamentos", len(sales) - len(confirmed)),
                     ("Descontos", br(sum(r["discount"] for r in confirmed))),
                     ("Vendas sem referência fiscal", sum(not r["fiscal"] for r in confirmed))]) +
            panel("Vendas e conciliação fiscal", table(["Venda", "Data", "Operador", "Caixa", "Pagamento", "Total",
                  "Situação", "Referência fiscal"], [
                  (link(f"receipt?id={r['id']}", f"#{r['id']}"), stamp(r["happened"]), e(r["employee"]),
                   e(r["number"]), e(r["method"]), br(r["total"]), "Cancelada" if r["cancelled"] else "Concluída",
                   e(r["fiscal"]) if r["fiscal"] else "Pendente") for r in sales])) +
            panel("Totais por operador, caixa e pagamento", table(["Operador", "Caixa", "Forma", "Total"],
                  [(*map(e, key), br(value)) for key, value in sorted(breakdown.items())])) +
            panel("Vendas por produto e categoria", table(["Produto", "Categoria", "Unidades", "Subtotal dos itens"],
                  [(e(r["name"]), e(r["category"]), r["quantity"], br(r["total"])) for r in lines])) +
            panel("Movimentações de estoque", table(["Data", "Produto", "Lote", "Quantidade", "Motivo"],
                  [(stamp(r["happened"]), e(r["name"]), e(r["code"]), f'{r["delta"]:+d}', e(r["reason"])) for r in moves])) +
            panel("Contas baixadas", table(["Descrição", "Tipo", "Valor", "Baixa"],
                  [(e(r["description"]), "Saída" if r["kind"] == "pay" else "Entrada", br(r["amount"]),
                    stamp(r["settled"])) for r in finance])))


def administration(db, user, csrf, page, query):
    if page == "account":
        return panel("Alterar senha", form(csrf, "password", field("Senha atual", "current", "password") +
                     field("Nova senha", "password", "password", extra='minlength="10"'), "Salvar senha", "account"))
    if page == "settings":
        config = dict(db.execute("SELECT key,value FROM config"))
        return panel("Preferências da loja", form(csrf, "config", field("Nome", "name", value=config["name"]) +
                     field("Limite de desconto sem autorização (%)", "discount", "number", config["discount"],
                           extra='min="0" max="100"'), "Salvar configurações", "settings"))
    if page == "audit":
        rows = db.execute("""SELECT a.*,u.name FROM audit a JOIN users u ON u.id=a.user_id
                             ORDER BY a.id DESC LIMIT 300""")
        return panel("Operações recentes", table(["Data", "Usuário", "Operação", "Detalhe"],
                     [(stamp(r["happened"]), e(r["name"]), e(r["action"]), e(r["detail"])) for r in rows]))
    accounts = db.execute("SELECT * FROM users ORDER BY name")
    fields = field("Nome", "name") + field("Usuário", "login") + select("Perfil", "role", ROLES.items()) + field(
        "Senha inicial", "password", "password", extra='minlength="10"')
    body = panel("Equipe", table(["Nome", "Usuário", "Perfil", "Situação", ""], [
        (e(r["name"]), e(r["login"]), ROLES[r["role"]], "Ativo" if r["active"] else "Inativo",
         link(f"users?id={r['id']}", "Editar acesso") if r["id"] != user["id"] else "") for r in accounts]))
    body += panel("Novo usuário", expandable("Cadastrar usuário",
                  form(csrf, "user", f'<div class="fields">{fields}</div>', "Cadastrar", "users")))
    if query.get("id"):
        account = record(db, "users", query["id"])
        body += panel(f"Acesso de {account['name']}", form(csrf, "permissions", hidden("id", account["id"]) +
                      select("Perfil", "role", ROLES.items(), account["role"]) +
                      check("Acesso ativo", "active", account["active"]), "Salvar acesso", "users"))
    return body


def render(db, user, csrf, page, query):
    if not allowed(user, page):
        raise ValueError("Você não tem acesso a esta área.")
    views = {
        "home": lambda: dashboard(db, user), "pdv": lambda: pdv(db, user, csrf),
        "products": lambda: catalog_view(db, csrf, query), "stock": lambda: stock_view(db, csrf),
        "tills": lambda: till_view(db, user, csrf), "till": lambda: till_view(db, user, csrf, query.get("id") or "0"),
        "receipt": lambda: receipt(db, user, csrf, query.get("id")),
        "customers": lambda: contacts_view(db, csrf, "customer", query),
        "suppliers": lambda: contacts_view(db, csrf, "supplier", query),
        "purchases": lambda: purchases_view(db, csrf, query), "finance": lambda: finance_view(db, csrf),
        "reports": lambda: reports(db, query),
    }
    view = views.get(page)
    return layout(db, user, page, csrf, view() if view else administration(db, user, csrf, page, query))
