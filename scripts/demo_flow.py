"""
Dulces Delicias S.A. - simulation of one complete business cycle.

The module `dulces_delicias` only CONFIGURES the company (products, recipes,
warehouse, customers...). This script plays the role of the employees and
does, with code, the same clicks you would do in the web interface,
following the case study in order:

    1. Initial inventory (inventario inicial) ...... Inventory + Invoicing
    2. Purchase for low stock (compra) ............. Inventory + Purchase
    3. Production of one batch (producción) ........ Manufacturing
    4. Opportunities (oportunidades) ............... CRM
    5. Sales orders (pedidos de venta) ............. Sales
    6. Invoices and payments (facturación) ......... Invoicing
    7. Deliveries (entregas) ....................... Inventory
    8. After-sales case (atención postventa) ....... Helpdesk
    9. Reports (reportes) .......................... Dulces Delicias app

Run it with:   make demo
It runs inside "odoo shell", where the variable `env` gives access to every
model of the database:  env["sale.order"], env["res.partner"], ...
Every step prints where to look at the result in the web interface.
"""
from datetime import timedelta

from odoo import Command, fields


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def ref(xmlid):
    """Record created by our module, e.g. ref("product_candy")."""
    return env.ref(f"dulces_delicias.{xmlid}")


def title(text):
    print(f"\n{'=' * 72}\n {text}\n{'=' * 72}")


def info(text):
    print(f"   {text}")


def see(menu):
    print(f"   -> See it in Odoo: {menu}")


def validate_transfer(picking):
    """Same as opening a transfer and clicking "Validate" with everything done."""
    picking.action_assign()
    for move in picking.move_ids:
        move.quantity = move.product_uom_qty
        move.picked = True
    # skip_sms: do not ask "send an SMS to the customer?" (needs paid credits)
    result = picking.with_context(skip_sms=True).button_validate()
    if picking.state != "done":
        raise Exception(f"{picking.name} could not be validated: {result}")


def register_payment(invoice, journal, amount=None):
    """Same as the "Register Payment" button of an invoice or vendor bill."""
    values = {"journal_id": journal.id, "payment_date": today}
    if amount:
        values["amount"] = amount
    wizard = env["account.payment.register"].with_context(
        active_model="account.move", active_ids=invoice.ids,
    ).create(values)
    return wizard._create_payments()


def note(record, text):
    """Write an internal note in the chatter of a record."""
    record.message_post(body=text, subtype_xmlid="mail.mt_note")


# Work as the "admin" user (not the internal OdooBot), in English
admin = env.ref("base.user_admin")
env = env(user=admin, context=dict(env.context, lang="en_US"))
today = fields.Date.context_today(env.user)
money = lambda amount: f"{env.company.currency_id.symbol} {amount:,.2f}"


# --------------------------------------------------------------------------
# 1. INVENTARIO INICIAL
# --------------------------------------------------------------------------
# Quantities in the stock unit of each product. Sugar, cocoa and flour start
# BELOW their minimum (see the reordering rules) to simulate low stock.
INITIAL_STOCK = {
    "raw_sugar": 60,       # kg      (minimum 100)  -> low stock
    "raw_coloring": 5,     # L
    "raw_flavoring": 8,    # L
    "raw_cocoa": 8,        # kg      (minimum 20)   -> low stock
    "raw_milk": 30,        # L
    "raw_flour": 30,       # kg      (minimum 50)   -> low stock
    "raw_butter": 15,      # kg
    "raw_eggs": 150,       # units
}


OPENING_BANK_BALANCE = 10000


def step_1_initial_inventory():
    title("1. INITIAL INVENTORY OF RAW MATERIALS (and opening bank balance)")
    # The owners put money in the bank: a manual journal entry
    # Bank (debit) / Capital (credit). UI: Invoicing > Accounting > Journal Entries
    bank_account = ref("journal_bank_transfer").default_account_id
    opening = env["account.move"].create({
        "move_type": "entry",
        "journal_id": env.ref("account.1_general").id,
        "date": today,
        "ref": "Aporte inicial de capital",
        "line_ids": [
            Command.create({"account_id": bank_account.id, "debit": OPENING_BANK_BALANCE, "name": "Aporte inicial de capital"}),
            Command.create({"account_id": env.ref("account.1_capital").id, "credit": OPENING_BANK_BALANCE, "name": "Aporte inicial de capital"}),
        ],
    })
    opening.action_post()
    info(f"Opening balance in {bank_account.name}: {money(OPENING_BANK_BALANCE)} ({opening.name})")

    location = ref("location_raw_materials")
    # inventory_mode = we are COUNTING the stock (an inventory adjustment)
    Quant = env["stock.quant"].with_context(inventory_mode=True)
    quants = Quant.browse()
    for xmlid, quantity in INITIAL_STOCK.items():
        product = ref(xmlid)
        quants |= Quant.create({
            "product_id": product.id,
            "location_id": location.id,
            "inventory_quantity": quantity,
        })
        info(f"{product.name:25} {quantity:>6} {product.uom_id.name}")
    # "Apply" button: creates the stock moves from Inventory adjustment -> stock
    quants.with_context(inventory_name="Inventario inicial de materias primas").action_apply_inventory()
    see("Inventory > Operations > Physical Inventory  |  Inventory > Reporting > Stock")


# --------------------------------------------------------------------------
# 2. COMPRA DE INSUMOS POR BAJO STOCK
# --------------------------------------------------------------------------
def step_2_purchase():
    title("2. PURCHASE ORDER TO REPLENISH LOW-STOCK RAW MATERIALS")
    orderpoints = env["stock.warehouse.orderpoint"].search([
        ("product_id.categ_id", "=", ref("categ_raw_materials").id),
    ])
    low_stock = orderpoints.filtered(lambda op: op.qty_forecast < op.product_min_qty)
    for op in low_stock:
        info(f"Low stock: {op.product_id.name:16} {op.qty_forecast:g} {op.product_uom.name} "
             f"(min {op.product_min_qty:g}, max {op.product_max_qty:g}) -> order {op.qty_to_order:g}")
    # Button "Order Once" in Inventory > Operations > Replenishment.
    # Odoo creates a Request for Quotation (RFQ) for the vendor of each product.
    low_stock.action_replenish()

    purchase = env["purchase.order"].search([("state", "=", "draft")], order="id desc", limit=1)
    info(f"Request for Quotation {purchase.name} to {purchase.partner_id.name}:")
    for line in purchase.order_line:
        info(f"   {line.product_id.name:18} {line.product_qty:g} {line.product_uom.name:14} x {money(line.price_unit)}")

    purchase.button_confirm()                       # "Confirm Order": RFQ -> Purchase Order
    info(f"{purchase.name} confirmed. Total {money(purchase.amount_total)}")

    receipt = purchase.picking_ids
    validate_transfer(receipt)                      # goods arrive at the warehouse
    info(f"Receipt {receipt.name} validated -> goods stored in {ref('location_raw_materials').complete_name}")

    purchase.action_create_invoice()                # "Create Bill"
    bill = purchase.invoice_ids
    bill.write({"invoice_date": today, "ref": "FACT-PROV-2026-0815"})
    bill.action_post()
    register_payment(bill, ref("journal_bank_transfer"))
    info(f"Vendor bill {bill.name} posted and paid by bank transfer")
    see("Purchase > Orders > Purchase Orders  |  Inventory > Operations > Replenishment")


# --------------------------------------------------------------------------
# 3. PRODUCCIÓN: un lote (100 unidades) de cada producto
# --------------------------------------------------------------------------
# How long each work order REALLY took compared with the expected time
# (1.10 = it took 10 % longer). Makes the time reports more interesting.
REAL_TIME_FACTOR = {"bom_candy": 1.10, "bom_chocolate": 0.95, "bom_cookies": 1.05}


def step_3_manufacturing():
    title("3. PLANNING AND EXECUTING PRODUCTION (one batch of 100 of each product)")
    for bom_xmlid, factor in REAL_TIME_FACTOR.items():
        bom = ref(bom_xmlid)
        product = bom.product_tmpl_id.product_variant_id

        # a) Plan: create and confirm the manufacturing order (MO)
        production = env["mrp.production"].create({
            "product_id": product.id,
            "bom_id": bom.id,
            "product_qty": bom.product_qty,
        })
        production.action_confirm()
        info(f"{production.name}: {production.product_qty:g} x {product.name}")

        # b) Take the raw materials to the production floor ("Pick Components")
        for picking in production.picking_ids:
            validate_transfer(picking)
            info(f"   {picking.name}: raw materials -> {picking.location_dest_id.complete_name}")
        production.action_assign()

        # c) Execute the work orders: Start -> (time passes) -> Done
        for workorder in production.workorder_ids:
            workorder.button_start()
            workorder.duration = round(workorder.duration_expected * factor, 1)
            workorder.button_finish()
            info(f"   WO {workorder.name:24} {workorder.workcenter_id.name:20} "
                 f"expected {workorder.duration_expected:>4.0f} min | real {workorder.duration:>4.0f} min")

        # d) "Produce All": consumes the components, adds the finished goods
        production.button_mark_done()
        consumed = ", ".join(f"{m.product_id.name} {m.quantity:g} {m.product_uom.name}" for m in production.move_raw_ids)
        info(f"   Done. Consumed: {consumed}")
        info(f"   Unit cost of {product.name}: {money(product.standard_price)}")

    # Production consumed raw materials: the automatic reordering rules
    # (trigger "auto") already created RFQs for what fell below the minimum.
    for rfq in env["purchase.order"].search([("state", "=", "draft")]):
        products = ", ".join(rfq.order_line.product_id.mapped("name"))
        info(f"Automatic replenishment: draft RFQ {rfq.name} to {rfq.partner_id.name} for {products}")
    see("Manufacturing > Operations > Manufacturing Orders  |  Manufacturing > Reporting > Work Orders")


# --------------------------------------------------------------------------
# 4. CRM: oportunidades, etapas y seguimientos
# --------------------------------------------------------------------------
OPPORTUNITIES = [
    {
        "customer": "customer_la_dulzura",
        "contact": "contact_la_dulzura",
        "name": "Pedido semanal de caramelos y chocolates",
        "expected_revenue": 1500,
        "probability": 20,
        "tags": ["crm_tag_recurring"],
        "stages": ["crm_stage_prospect"],
        "note": "Primer contacto en la feria de confiteros. Pidió un pedido de prueba antes de comprometerse a pedidos semanales.",
        "activity": ("mail.mail_activity_data_call", 3, "Llamar para conocer su opinión del pedido de prueba"),
    },
    {
        "customer": "customer_supermercado",
        "contact": "contact_supermercado",
        "name": "Góndola anual de galletas y chocolates",
        "expected_revenue": 8000,
        "probability": 60,
        "tags": ["crm_tag_volume", "crm_tag_season"],
        "stages": ["crm_stage_prospect", "crm_stage_negotiation"],
        "note": "Interesados en un contrato anual para sus 5 tiendas. Piden 5 % de descuento por volumen; estamos negociando.",
        "activity": ("mail.mail_activity_data_meeting", 5, "Reunión con Carlos Méndez para negociar precios por volumen"),
    },
    {
        "customer": "customer_distribuidora",
        "contact": "contact_distribuidora",
        "name": "Distribución regional - primer pedido",
        "expected_revenue": 2500,
        "probability": 100,
        "tags": ["crm_tag_volume"],
        "stages": ["crm_stage_prospect", "crm_stage_negotiation", "crm_stage_closed"],
        "note": "Aceptó nuestras condiciones: pago contra entrega y entrega en su bodega del puerto.",
        "activity": ("mail.mail_activity_data_todo", 7, "Seguimiento postventa: confirmar satisfacción y próximo pedido"),
    },
]


def step_4_crm():
    title("4. CUSTOMER MANAGEMENT: OPPORTUNITIES IN THE CRM")
    leads = env["crm.lead"]
    for data in OPPORTUNITIES:
        customer = ref(data["customer"])
        lead = env["crm.lead"].create({
            "type": "opportunity",
            "name": data["name"],
            "partner_id": customer.id,
            "contact_name": ref(data["contact"]).name,
            "expected_revenue": data["expected_revenue"],
            "probability": data["probability"],
            "user_id": admin.id,
            "team_id": env.ref("sales_team.team_sales_department").id,
            "tag_ids": [Command.set([ref(tag).id for tag in data["tags"]])],
            "date_deadline": today + timedelta(days=30),
            "stage_id": ref(data["stages"][0]).id,
        })
        note(lead, data["note"])
        # Move the card through the pipeline (each change is logged in the chatter)
        for stage in data["stages"][1:]:
            lead.stage_id = ref(stage)
        # Follow-up / reminder: appears in the activity view and in the clock icon
        activity_type, days, summary = data["activity"]
        lead.activity_schedule(activity_type, date_deadline=today + timedelta(days=days),
                               summary=summary, user_id=admin.id)
        info(f"{customer.name:26} | stage: {lead.stage_id.name:15} | "
             f"follow-up in {days} days: {summary}")
        leads |= lead
    see("CRM > Sales > My Pipeline  |  CRM > Sales > My Activities")
    return leads


# --------------------------------------------------------------------------
# 5. PEDIDOS DE VENTA con términos de pago y condiciones de entrega
# --------------------------------------------------------------------------
SALES = [
    {
        "customer": "customer_la_dulzura",
        "client_order_ref": "LD-0457",
        "lines": {"product_candy": 20, "product_chocolate": 30, "product_cookies": 10},
        "payment_term": "account.account_payment_term_immediate",
        "picking_policy": "direct",          # deliver each product as soon as it is ready
        "incoterm": "account.incoterm_DAP",  # we deliver to the customer's door
        "days_to_deliver": 1,
        "conditions": "Entrega en tienda de 9:00 a 12:00. Pago inmediato con tarjeta de crédito.",
    },
    {
        "customer": "customer_supermercado",
        "shipping_address": "delivery_supermercado",
        "client_order_ref": "OC-SD-2026-1189",
        "lines": {"product_candy": 40, "product_chocolate": 40, "product_cookies": 50},
        "payment_term": "account.account_payment_term_30days",
        "picking_policy": "one",             # deliver everything together, no partial deliveries
        "incoterm": "account.incoterm_DAP",
        "days_to_deliver": 3,
        "conditions": "Entrega completa en Bodega Central (Carretera Norte Km 12), lunes a viernes de 7:00 a 13:00. "
                      "Anticipo del 50 % por transferencia, saldo a 30 días.",
    },
    {
        "customer": "customer_distribuidora",
        "client_order_ref": "DS-PED-031",
        "lines": {"product_candy": 25, "product_chocolate": 20, "product_cookies": 25},
        "payment_term": "payment_term_cash_on_delivery",
        "picking_policy": "direct",
        "incoterm": "account.incoterm_DAP",
        "days_to_deliver": 2,
        "conditions": "Entrega en bodega del puerto. Pago en efectivo contra entrega.",
    },
]


def xmlid_to_record(xmlid):
    return env.ref(xmlid) if "." in xmlid else ref(xmlid)


def step_5_sales(leads):
    title("5. SALES: ONE ORDER PER CUSTOMER")
    orders = env["sale.order"]
    for data, lead in zip(SALES, leads):
        customer = ref(data["customer"])
        order = env["sale.order"].create({
            "partner_id": customer.id,
            "partner_shipping_id": ref(data.get("shipping_address", data["customer"])).id,
            "opportunity_id": lead.id,
            "client_order_ref": data["client_order_ref"],
            "payment_term_id": xmlid_to_record(data["payment_term"]).id,
            "picking_policy": data["picking_policy"],
            "incoterm": env.ref(data["incoterm"]).id,
            "commitment_date": fields.Datetime.now() + timedelta(days=data["days_to_deliver"]),
            "note": f"<p><b>Condiciones de entrega:</b> {data['conditions']}</p>",
            "order_line": [
                Command.create({"product_id": ref(product).id, "product_uom_qty": quantity})
                for product, quantity in data["lines"].items()
            ],
        })
        # "Send by Email": the quotation PDF is emailed (see it in Mailpit)
        action = order.action_quotation_send()
        env["mail.compose.message"].with_context(**action["context"]).create({}).action_send_mail()
        # "Confirm": quotation -> sales order. Odoo creates the delivery order.
        order.action_confirm()
        products = ", ".join(f"{l.product_uom_qty:g} {l.product_id.name.split(' (')[0]}" for l in order.order_line)
        info(f"{order.name} {customer.name:28} {money(order.amount_total):>12} | {order.payment_term_id.name:20} | {products}")
        orders |= order
    see("Sales > Orders > Orders  |  the 'Orders' button of each CRM opportunity")
    return orders


# --------------------------------------------------------------------------
# 6. FACTURACIÓN Y PAGOS
# --------------------------------------------------------------------------
def step_6_invoicing(orders):
    title("6. INVOICING: INVOICES, SENDING AND PAYMENTS")
    invoices = env["account.move"]
    for order in orders:
        invoice = order._create_invoices()          # "Create Invoice"
        invoice.action_post()                       # "Confirm": draft -> posted
        # "Send": generates the PDF and emails it to the customer (Mailpit)
        env["account.move.send"]._generate_and_send_invoices(invoice, sending_methods={"email"})
        info(f"Invoice {invoice.name} sent to {invoice.partner_id.name:26} {money(invoice.amount_total):>10} "
             f"due {invoice.invoice_date_due}")
        invoices |= invoice

    la_dulzura, supermercado, _distribuidora = invoices
    register_payment(la_dulzura, ref("journal_credit_card"))
    info(f"{la_dulzura.name}: paid by CREDIT CARD")
    register_payment(supermercado, ref("journal_bank_transfer"), amount=round(supermercado.amount_total / 2, 2))
    info(f"{supermercado.name}: 50 % advance by BANK TRANSFER, the rest is due in 30 days")
    info(f"{_distribuidora.name}: will be paid CASH ON DELIVERY (step 7)")
    see("Invoicing > Customers > Invoices  |  sent emails: http://localhost:8025")
    return invoices


# --------------------------------------------------------------------------
# 7. ENTREGAS
# --------------------------------------------------------------------------
def step_7_deliveries(orders, invoices):
    title("7. DELIVERIES")
    for order, invoice in zip(orders, invoices):
        delivery = order.picking_ids.filtered(lambda p: p.picking_type_code == "outgoing")
        info(f"{delivery.name} scheduled for {fields.Datetime.to_string(delivery.scheduled_date)[:16]} "
             f"-> {delivery.partner_id.display_name}")
        validate_transfer(delivery)
        note(delivery, "Mercadería entregada y recibida conforme por el cliente.")
        info(f"   Delivered from {ref('location_finished_goods').complete_name}")
        if order.payment_term_id == ref("payment_term_cash_on_delivery"):
            register_payment(invoice, ref("journal_cash_on_delivery"))
            info(f"   {invoice.name}: paid in CASH on delivery")
    see("Inventory > Operations > Transfers > Deliveries")


# --------------------------------------------------------------------------
# 8. ATENCIÓN POSTVENTA
# --------------------------------------------------------------------------
def step_8_after_sales(orders):
    title("8. AFTER-SALES: COMPLAINT ABOUT DAMAGED PRODUCTS")
    order = orders[1]                               # Supermercado Delicias
    cookies = ref("product_cookies")
    contact = ref("contact_supermercado")
    delivery = order.picking_ids.filtered(lambda p: p.picking_type_code == "outgoing" and p.state == "done")

    # a) The customer calls: open a ticket linked to the order and the product
    ticket = env["helpdesk.ticket"].create({
        "name": f"5 paquetes de galletas llegaron rotos ({order.name})",
        "description": f"<p>{contact.name} (Jefe de Compras) llama para informar que 5 paquetes de "
                       f"<b>{cookies.name}</b> del pedido {order.name} (entrega {delivery.name}) llegaron "
                       f"rotos y no se pueden vender. Solicita su reposición.</p>",
        "partner_id": contact.id,
        "partner_name": contact.name,
        "partner_email": contact.email,
        "team_id": ref("helpdesk_team_after_sales").id,
        "user_id": admin.id,
        "category_id": ref("helpdesk_category_damaged").id,
        "tag_ids": [Command.link(ref("helpdesk_tag_complaint").id)],
        "channel_id": env.ref("helpdesk_mgmt.helpdesk_ticket_channel_phone").id,
        "priority": "2",
        "product_id": cookies.id,
        "sale_order_ids": [Command.link(order.id)],
    })
    info(f"Ticket {ticket.number} created: {ticket.name}")

    # b) Follow up: work on it and schedule a task
    ticket.stage_id = env.ref("helpdesk_mgmt.helpdesk_ticket_stage_in_progress")
    note(ticket, "Se revisaron las fotos enviadas por el cliente: el empaque se dañó durante el transporte. "
                 "Se aprueba la devolución y reposición de los 5 paquetes.")
    activity = ticket.activity_schedule("mail.mail_activity_data_todo", date_deadline=today,
                                        summary="Coordinar devolución y reposición", user_id=admin.id)
    info(f"   Stage: {ticket.stage_id.name}. Activity: {activity.summary}")

    # c) "Return" button on the delivery -> "Return for Exchange": Odoo creates
    #    the return (damaged goods come back) AND a new delivery (replacement)
    wizard = env["stock.return.picking"].with_context(
        active_id=delivery.id, active_model="stock.picking",
    ).create({"picking_id": delivery.id})
    for line in wizard.product_return_moves:
        line.quantity = 5 if line.product_id == cookies else 0
    wizard.action_create_exchanges()
    return_picking = env["stock.picking"].search([("return_id", "=", delivery.id)])
    validate_transfer(return_picking)
    info(f"   Return {return_picking.name}: the 5 damaged packs come back to the factory")

    # d) The damaged goods cannot be sold: scrap them (Inventory > Scrap)
    damaged_location = return_picking.move_ids.move_line_ids.location_dest_id
    scrap = env["stock.scrap"].create({
        "product_id": cookies.id,
        "scrap_qty": 5,
        "location_id": damaged_location.id,
        "picking_id": return_picking.id,
        "origin": ticket.number,
    })
    scrap.action_validate()
    info(f"   Scrap {scrap.name}: the 5 packs are thrown away (expense 'Mermas y Pérdidas de Inventario')")

    # e) Ship the replacement
    replacement = order.picking_ids.filtered(lambda p: p.picking_type_code == "outgoing" and p.state not in ("done", "cancel"))
    validate_transfer(replacement)
    info(f"   Replacement {replacement.name}: 5 new packs delivered")

    # f) Close the ticket (the customer is notified by email)
    activity.action_feedback(feedback="Devolución, baja y reposición completadas.")
    note(ticket, f"Resuelto: devolución {return_picking.name}, desecho {scrap.name} y reposición "
                 f"{replacement.name}. El cliente confirma que recibió los paquetes en buen estado.")
    ticket.stage_id = env.ref("helpdesk_mgmt.helpdesk_ticket_stage_done")
    info(f"Ticket {ticket.number} -> {ticket.stage_id.name} (solved)")
    see("Helpdesk > Tickets > All Tickets  |  Inventory > Operations > Adjustments > Scrap")


# --------------------------------------------------------------------------
# 9. REPORTES
# --------------------------------------------------------------------------
def step_9_reports():
    title("9. REPORTS")
    info("Inventory status:")
    quants = env["stock.quant"].search([("location_id.usage", "=", "internal"), ("quantity", "!=", 0)])
    for quant in quants.sorted(lambda q: (q.location_id.complete_name, q.product_id.default_code)):
        info(f"   {quant.location_id.complete_name:32} {quant.product_id.name:28} "
             f"{quant.quantity:>8g} {quant.product_uom_id.name}")

    wizard = env["dd.income.statement.wizard"].create({"period": "this_year"})
    data = wizard.get_report_values()
    sections = data["sections"]
    info(f"Income statement {wizard.date_from} to {wizard.date_to}:")
    info(f"   Sales revenue            {money(sections['income']['total']):>14}")
    info(f"   Cost of goods sold      -{money(sections['cost']['total']):>14}")
    info(f"   GROSS PROFIT             {money(data['gross_profit']):>14}")
    info(f"   Operating expenses      -{money(sections['expense']['total']):>14}")
    info(f"   NET PROFIT               {money(data['net_profit']):>14}")
    see("Dulces Delicias > Reportes")


# --------------------------------------------------------------------------
# Run everything (only once per database)
# --------------------------------------------------------------------------
def main():
    params = env["ir.config_parameter"].sudo()
    if params.get_param("dulces_delicias.demo_done"):
        print("\nThe simulation already ran on this database.")
        print("To start from scratch:  make reset   and then   make demo\n")
        return
    if not env.ref("dulces_delicias.product_candy", raise_if_not_found=False):
        print("\nThe dulces_delicias module is not installed. Run first:  make install\n")
        return

    step_1_initial_inventory()
    step_2_purchase()
    step_3_manufacturing()
    leads = step_4_crm()
    orders = step_5_sales(leads)
    invoices = step_6_invoicing(orders)
    step_7_deliveries(orders, invoices)
    step_8_after_sales(orders)
    step_9_reports()

    params.set_param("dulces_delicias.demo_done", fields.Datetime.now())
    env.cr.commit()   # save everything in the database (odoo shell does not do it by itself)
    print("\nDone. Open http://localhost:8069 (admin / admin) to see the results.\n")


main()
