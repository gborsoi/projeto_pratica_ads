import time
from secrets import token_urlsafe

from storage import (METHODS, ROLES, audit, authenticated, available_lots, calendar, change,
                     money, now, number, password_hash, receive)


def required(data, key):
    value = data.get(key, "").strip()
    if not value:
        raise ValueError("Preencha todos os campos obrigatórios.")
    return value


def record(db, table, identifier):
    row = db.execute(f"SELECT * FROM {table} WHERE id=?", (identifier,)).fetchone()
    if not row:
        raise ValueError("Registro não encontrado.")
    return row


def contact(db, identifier, kind):
    if identifier:
        row = record(db, "contacts", identifier)
        if row["kind"] != kind:
            raise ValueError("Selecione um cadastro do tipo correto.")
        return row["id"]
    return None


def open_till(db, user_id):
    return db.execute("SELECT * FROM tills WHERE user_id=? AND closed IS NULL", (user_id,)).fetchone()


def expected(db, till):
    totals = dict.fromkeys(METHODS, 0)
    totals["Dinheiro"] = till["initial"]
    for row in db.execute("""SELECT method, SUM(total) AS total FROM sales
                           WHERE till_id=? AND cancelled IS NULL GROUP BY method""", (till["id"],)):
        totals[row["method"]] += row["total"]
    return totals


def approval(db, user, data):
    if user["role"] in ("manager", "owner"):
        return user["id"]
    account = authenticated(db, data.get("approver", ""), data.get("authorization", ""))
    if not account or account["role"] not in ("manager", "owner"):
        raise ValueError("Informe as credenciais de um gerente ou proprietário.")
    return account["id"]


def discount(data, prefix, gross):
    mode = data.get(prefix + "_mode", "fixed")
    value = money(data.get(prefix, "") or "0")
    if mode == "percent":
        if value > 10000:
            raise ValueError("O percentual precisa estar entre 0 e 100.")
        return (gross * value + 5000) // 10000
    if value > gross:
        raise ValueError("O desconto excede o valor da compra ou do item.")
    return value


def sell(db, user, data):
    user_id = user["id"]
    key = required(data, "request")
    existing = db.execute("""SELECT s.id FROM sales s JOIN tills t ON t.id=s.till_id
                           WHERE s.request_key=? AND t.user_id=?""", (key, user_id)).fetchone()
    if existing:
        return existing["id"]
    till = open_till(db, user_id)
    if not till:
        raise ValueError("Abra o caixa antes de registrar vendas.")
    method = data.get("method")
    if method not in METHODS or data.get("confirmed") != "on":
        raise ValueError("Escolha uma forma de pagamento e confirme o recebimento.")
    selections = [(name[4:], value) for name, value in data.items() if name.startswith("qty_")]
    if not selections:
        raise ValueError("Adicione itens à venda.")
    gross = item_discounts = 0
    allocations = []
    selected_ids = set()
    for identifier, value in selections:
        product = record(db, "products", identifier)
        if product["id"] in selected_ids:
            raise ValueError("Cada produto deve aparecer uma única vez na venda.")
        selected_ids.add(product["id"])
        if not product["active"]:
            raise ValueError("A venda contém um produto inativo.")
        quantity = number(value, 1)
        subtotal = product["price"] * quantity
        reduction = discount(data, f"discount_{identifier}", subtotal)
        gross += subtotal
        item_discounts += reduction
        remaining = quantity
        allocated_discount = 0
        for lot in available_lots(db, product["id"]):
            take = min(remaining, lot["quantity"])
            remaining -= take
            cumulative = reduction * (quantity - remaining) // quantity
            allocations.append((lot["id"], product, take, cumulative - allocated_discount))
            allocated_discount = cumulative
            if not remaining:
                break
        if remaining:
            raise ValueError(f"Estoque vendável insuficiente para {product['name']}.")
    reduction = item_discounts + discount(data, "sale_discount", gross - item_discounts)
    limit = int(db.execute("SELECT value FROM config WHERE key='discount'").fetchone()[0])
    approver = approval(db, user, data) if reduction * 100 > gross * limit else None
    total = gross - reduction
    received = money(data.get("received", "")) if method == "Dinheiro" else total
    if received < total:
        raise ValueError("O valor recebido é menor que o total.")
    customer = contact(db, data.get("customer"), "customer")
    sale_id = db.execute("""INSERT INTO sales(till_id,happened,method,total,received,discount,
                          approver,customer,request_key) VALUES (?,?,?,?,?,?,?,?,?)""",
                         (till["id"], now(), method, total, received, reduction, approver,
                          customer, key)).lastrowid
    for lot, product, quantity, line_discount in allocations:
        change(db, lot, user_id, -quantity, f"Venda #{sale_id}")
        db.execute("""INSERT INTO sale_lines(sale_id,lot_id,name,category,quantity,price,cost,discount)
                      VALUES (?,?,?,?,?,?,?,?)""",
                   (sale_id, lot, product["name"], product["category"], quantity,
                    product["price"], product["cost"], line_discount))
    audit(db, user_id, "Venda", f"#{sale_id}")
    if reduction:
        audit(db, user_id, "Desconto", f"Venda #{sale_id} · {reduction} centavos · responsável #{approver or user_id}")
    return sale_id


def operate(db, user, action, data):
    uid = user["id"]
    owner = user["role"] == "owner"
    management = user["role"] in ("owner", "manager")
    if action in {"user", "permissions", "config"} and not owner:
        raise ValueError("Operação reservada ao proprietário.")
    if action in {"product", "stock", "contact", "purchase", "receive", "finance", "settle",
                  "fiscal", "reopen"} and not management:
        raise ValueError("Operação reservada à gerência.")
    if action == "open":
        till = db.execute("INSERT INTO tills(user_id,number,opened,initial) VALUES (?,?,?,?)",
                          (uid, required(data, "number"), now(), money(data.get("initial", "")))).lastrowid
        audit(db, uid, "Abertura de caixa", f"#{till}")
        return "pdv"
    if action == "sell":
        return f"receipt?id={sell(db, user, data)}"
    if action == "draft":
        audit(db, uid, "Cancelamento de " + ("item" if data.get("kind") == "item" else "venda em andamento"),
              required(data, "reason")[:250])
        return "pdv"
    if action == "cancel":
        if data.get("confirm") != "on":
            raise ValueError("Confirme o estorno antes de cancelar a venda.")
        sale = record(db, "sales", data.get("id"))
        till = record(db, "tills", sale["till_id"])
        if sale["cancelled"] or till["closed"] or (not management and till["user_id"] != uid):
            raise ValueError("Só é possível cancelar uma venda ativa em um caixa aberto com acesso autorizado.")
        reason = required(data, "reason")
        approver = approval(db, user, data)
        lines = db.execute("SELECT * FROM sale_lines WHERE sale_id=?", (sale["id"],)).fetchall()
        for line in lines:
            change(db, line["lot_id"], uid, line["quantity"], f"Estorno #{sale['id']}: {reason}")
        db.execute("""UPDATE sales SET cancelled=?,cancel_reason=?,cancel_approver=? WHERE id=?""",
                   (now(), reason, approver, sale["id"]))
        audit(db, uid, "Cancelamento de venda", f"#{sale['id']} · autorizado por #{approver} · {reason}")
        return f"receipt?id={sale['id']}"
    if action == "close":
        till = open_till(db, uid)
        if not till:
            raise ValueError("Nenhum caixa aberto.")
        for index, (method, total) in enumerate(expected(db, till).items()):
            counted = money(data.get(f"count_{index}", ""))
            db.execute("INSERT INTO counts VALUES (?,?,?,?)", (till["id"], method, total, counted))
        db.execute("UPDATE tills SET closed=? WHERE id=?", (now(), till["id"]))
        audit(db, uid, "Fechamento de caixa", f"#{till['id']}")
        return f"till?id={till['id']}"
    if action == "reopen":
        till = record(db, "tills", data.get("id"))
        if not till["closed"]:
            raise ValueError("Este caixa já está aberto.")
        previous = db.execute("SELECT * FROM counts WHERE till_id=?", (till["id"],)).fetchall()
        summary = ", ".join(f"{row['method']}: {row['counted'] - row['expected']:+d} centavos" for row in previous)
        db.execute("UPDATE tills SET closed=NULL WHERE id=?", (till["id"],))
        db.execute("DELETE FROM counts WHERE till_id=?", (till["id"],))
        audit(db, uid, "Reabertura de caixa", f"#{till['id']} · divergências anteriores: {summary}")
        return f"till?id={till['id']}"
    if action == "product":
        identifier = data.get("id")
        values = (required(data, "sku"), data.get("barcode") or None, required(data, "name"),
                  required(data, "category"), required(data, "unit"), money(data.get("cost", "")),
                  money(data.get("price", "")), number(data.get("minimum")),
                  contact(db, data.get("supplier"), "supplier"), data.get("tax"), int(data.get("active") == "on"))
        if identifier:
            old = record(db, "products", identifier)
            db.execute("""UPDATE products SET sku=?,barcode=?,name=?,category=?,unit=?,cost=?,price=?,
                          minimum=?,supplier=?,tax=?,active=? WHERE id=?""", (*values, identifier))
            if old["price"] != values[6]:
                audit(db, uid, "Alteração de preço", f"Produto #{identifier}: {old['price']} → {values[6]} centavos")
        else:
            identifier = db.execute("""INSERT INTO products(sku,barcode,name,category,unit,cost,price,minimum,
                                       supplier,tax,active) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", values).lastrowid
            quantity = number(data.get("initial") or "0")
            if quantity:
                receive(db, uid, identifier, required(data, "lot"), calendar(data.get("expiry")),
                        quantity, "Estoque inicial")
        audit(db, uid, "Cadastro de produto", f"#{identifier}")
        return "products"
    if action == "stock":
        kind = data.get("kind")
        quantity = number(data.get("quantity"), 0 if kind == "inventory" else 1)
        reason = required(data, "reason")
        if kind == "in":
            product = record(db, "products", data.get("product"))
            receive(db, uid, product["id"], required(data, "lot"), calendar(data.get("expiry")), quantity, reason)
        elif kind in ("out", "inventory"):
            lot = record(db, "lots", data.get("lot_id"))
            delta = -quantity if kind == "out" else quantity - lot["quantity"]
            change(db, lot["id"], uid, delta, reason)
        else:
            raise ValueError("Selecione o tipo de movimentação.")
        audit(db, uid, "Ajuste de estoque", reason)
        return "stock"
    if action == "contact":
        kind = data.get("kind")
        if kind not in ("customer", "supplier"):
            raise ValueError("Tipo de cadastro inválido.")
        values = (required(data, "name"), data.get("document"), data.get("phone"), data.get("email"),
                  data.get("address"), data.get("notes"))
        identifier = contact(db, data.get("id"), kind)
        if identifier:
            db.execute("""UPDATE contacts SET name=?,document=?,phone=?,email=?,address=?,notes=?
                          WHERE id=?""", (*values, identifier))
        else:
            identifier = db.execute("""INSERT INTO contacts(kind,name,document,phone,email,address,notes)
                                        VALUES (?,?,?,?,?,?,?)""", (kind, *values)).lastrowid
        audit(db, uid, "Cadastro de " + ("cliente" if kind == "customer" else "fornecedor"), f"#{identifier}")
        return "customers" if kind == "customer" else "suppliers"
    if action == "purchase":
        supplier = contact(db, required(data, "supplier"), "supplier")
        product = record(db, "products", data.get("product"))
        identifier = db.execute("""INSERT INTO purchases(supplier,product,quantity,cost,created)
                                   VALUES (?,?,?,?,?)""", (supplier, product["id"], number(data.get("quantity"), 1),
                                                           money(data.get("cost", "")), now())).lastrowid
        audit(db, uid, "Pedido de compra", f"#{identifier}")
        return "purchases"
    if action == "receive":
        purchase = record(db, "purchases", data.get("id"))
        if purchase["received"] or data.get("confirmed") != "on":
            raise ValueError("Confirme a conferência de um pedido em aberto.")
        quantity = number(data.get("quantity"))
        cost = money(data.get("cost", ""))
        notes = data.get("notes", "").strip()
        if (quantity != purchase["quantity"] or cost != purchase["cost"]) and not notes:
            raise ValueError("Descreva a divergência antes de confirmar.")
        if quantity:
            receive(db, uid, purchase["product"], required(data, "lot"), calendar(data.get("expiry")),
                    quantity, f"Recebimento do pedido #{purchase['id']}")
        db.execute("UPDATE purchases SET received=?,actual=?,actual_cost=?,notes=? WHERE id=?",
                   (now(), quantity, cost, notes, purchase["id"]))
        audit(db, uid, "Recebimento de compra", f"#{purchase['id']}")
        return "purchases"
    if action == "finance":
        kind = data.get("kind")
        if kind not in ("pay", "receive"):
            raise ValueError("Selecione o tipo de conta.")
        identifier = db.execute("INSERT INTO finance(kind,description,amount,due) VALUES (?,?,?,?)",
                                (kind, required(data, "description"), money(data.get("amount", "")),
                                 calendar(data.get("due")))).lastrowid
        audit(db, uid, "Lançamento financeiro", f"#{identifier}")
        return "finance"
    if action == "settle":
        entry = record(db, "finance", data.get("id"))
        if entry["settled"]:
            raise ValueError("Esta conta já foi baixada.")
        db.execute("UPDATE finance SET settled=? WHERE id=?", (now(), entry["id"]))
        audit(db, uid, "Baixa financeira", f"#{entry['id']}")
        return "finance"
    if action == "fiscal":
        sale = record(db, "sales", data.get("id"))
        db.execute("UPDATE sales SET fiscal=? WHERE id=?", (required(data, "reference"), sale["id"]))
        audit(db, uid, "Vínculo de referência fiscal", f"Venda #{sale['id']}")
        return f"receipt?id={sale['id']}"
    if action == "user":
        role = data.get("role")
        if role not in ROLES or len(data.get("password", "")) < 10:
            raise ValueError("Selecione um perfil e use pelo menos 10 caracteres na senha.")
        identifier = db.execute("INSERT INTO users(name,login,password,role) VALUES (?,?,?,?)",
                                (required(data, "name"), required(data, "login"),
                                 password_hash(data["password"]), role)).lastrowid
        audit(db, uid, "Usuário cadastrado", f"#{identifier}")
        return "users"
    if action == "permissions":
        account = record(db, "users", data.get("id"))
        role = data.get("role")
        if account["id"] == uid or role not in ROLES:
            raise ValueError("Selecione outro usuário e um perfil válido.")
        db.execute("UPDATE users SET role=?,active=? WHERE id=?",
                   (role, int(data.get("active") == "on"), account["id"]))
        db.execute("DELETE FROM sessions WHERE user_id=?", (account["id"],))
        audit(db, uid, "Alteração de acesso", f"Usuário #{account['id']}")
        return "users"
    if action == "password":
        if not authenticated(db, user["login"], data.get("current", "")) or len(data.get("password", "")) < 10:
            raise ValueError("Confira a senha atual e informe uma nova senha de pelo menos 10 caracteres.")
        db.execute("UPDATE users SET password=? WHERE id=?", (password_hash(data["password"]), uid))
        db.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
        audit(db, uid, "Alteração de senha")
        return "login"
    if action == "config":
        limit = number(data.get("discount"), 0, 100)
        db.execute("UPDATE config SET value=? WHERE key='discount'", (str(limit),))
        db.execute("UPDATE config SET value=? WHERE key='name'", (required(data, "name"),))
        audit(db, uid, "Alteração de configurações")
        return "settings"
    raise ValueError("Operação desconhecida.")


def login(db, data):
    account = authenticated(db, data.get("login", "").strip(), data.get("password", ""))
    if not account:
        raise ValueError("Usuário ou senha incorretos.")
    token = token_urlsafe(32)
    current = int(time.time())
    db.execute("DELETE FROM sessions WHERE expires<=?", (current,))
    db.execute("INSERT INTO sessions VALUES (?,?,?)", (token, account["id"], current + 43200))
    audit(db, account["id"], "Login")
    return token
