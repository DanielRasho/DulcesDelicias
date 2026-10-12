"""Configuration that is easier to do in Python than in XML.

`pre_init_hook` runs ONCE, before the data files of this module are loaded.
`post_init_hook` runs ONCE, right after they are loaded.
Everything here could also be done by hand in the web UI; the comments say
where.
"""


def pre_init_hook(env):
    """Create the chart of accounts before our data files need it.

    Odoo 18 normally creates the chart of accounts at the very END of the
    installation, but our data files (product categories, journals...)
    refer to its accounts. "generic_coa" is Odoo's generic chart of
    accounts. UI: Invoicing > Configuration > Settings > Fiscal Localization.
    """
    if not env.company.chart_template:
        env["account.chart.template"].try_loading("generic_coa", env.company)


def post_init_hook(env):
    _enable_features(env)
    _configure_warehouse(env)
    _configure_inventory_accounting(env)
    _configure_payment_journals(env)
    _remove_default_crm_stages(env)


def _enable_features(env):
    """Tick the same boxes you would tick in Settings.

    Many Odoo features are hidden until you enable them in
    Settings (Inventory / Manufacturing / Sales sections).
    """
    env["res.config.settings"].create({
        "group_uom": True,                         # Inventory > Units of Measure
        "group_stock_multi_locations": True,       # Inventory > Storage Locations
        "group_stock_adv_location": True,          # Inventory > Multi-Step Routes
        "group_stock_accounting_automatic": True,  # Inventory > Automatic Accounting
        "group_mrp_routings": True,                # Manufacturing > Work Orders
        "group_sale_delivery_address": True,       # Sales > Customer Addresses
    }).execute()


def _configure_warehouse(env):
    """Give the work-in-process location a meaningful name.

    data/04_warehouse.xml switches the warehouse to "Pick components, then
    manufacture" (2 steps). Odoo then uses a location called
    "Pre-Production" to hold the raw materials taken to the production
    floor: that is exactly our "Productos en Proceso" (WIP) area.
    UI: Inventory > Configuration > Warehouse Management > Locations.
    """
    warehouse = env.ref("stock.warehouse0")
    warehouse.pbm_loc_id.name = "Productos en Proceso"
    # Renaming the warehouse code (WH -> DD) only renames the Inventory
    # sequences; do it for all of them so manufacturing orders are DD/MO/...
    for field, sequence_values in warehouse._get_sequence_values().items():
        warehouse[field].sequence_id.write(sequence_values)


def _configure_inventory_accounting(env):
    """Choose the accounts used when stock appears or disappears.

    - Scrapped (damaged) goods are an expense: "Mermas y Pérdidas".
    - Inventory adjustments: the INITIAL inventory is the owner's
      contribution (Capital); quantities lost in a later count are an
      expense ("Mermas y Pérdidas").
    UI: Inventory > Configuration > Warehouse Management > Locations >
    (Scrap / Inventory adjustment), with the "Archived" filter if needed.
    """
    loss_account = env.ref("dulces_delicias.account_inventory_losses")
    capital_account = env.ref("account.1_capital")
    virtual_locations = env["stock.location"].search([
        ("usage", "=", "inventory"),
        ("company_id", "=", env.company.id),
    ])
    for location in virtual_locations:
        location.write({
            # goods going INTO this location = lost / scrapped
            "valuation_in_account_id": loss_account.id,
            # goods coming FROM this location = found / initial inventory
            "valuation_out_account_id": loss_account.id if location.scrap_location else capital_account.id,
        })


def _configure_payment_journals(env):
    """Make payments land directly in the bank/cash account of each journal.

    This way an invoice is shown as "Paid" as soon as the payment is
    registered (without a bank statement reconciliation, which needs the
    Enterprise Accounting app).
    UI: Invoicing > Configuration > Accounting > Journals > (journal) >
    tab Incoming Payments.
    """
    for xmlid in ("journal_bank_transfer", "journal_credit_card", "journal_cash_on_delivery"):
        journal = env.ref(f"dulces_delicias.{xmlid}")
        method_lines = journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids
        method_lines.payment_account_id = journal.default_account_id


def _remove_default_crm_stages(env):
    """Delete Odoo's default pipeline stages (New, Qualified, Proposition, Won).

    data/11_crm.xml creates ours (Prospecto, Negociación, Cierre). This is
    done here and not in the XML file because the XML is loaded again every
    time `odoo -i` runs on an existing database, and by then these stages
    (and their external IDs) are already gone.
    UI: CRM > Pipeline > gear icon on each column > Delete.
    """
    for xmlid in ("stage_lead1", "stage_lead2", "stage_lead3", "stage_lead4"):
        env.ref(f"crm.{xmlid}").unlink()
