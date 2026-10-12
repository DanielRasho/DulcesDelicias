# The manifest is the "ID card" of an Odoo module: its name, which other
# modules it needs (depends) and which data files it loads, IN ORDER.
{
    "name": "Dulces Delicias S.A.",
    "summary": "Case study: candy factory configured end to end "
               "(inventory, manufacturing, CRM, sales, invoicing, after-sales)",
    "version": "18.0.1.0.0",
    "category": "Manufacturing",
    "author": "Dulces Delicias demo",
    "license": "LGPL-3",
    "application": True,
    "depends": [
        # Odoo apps used by the case study
        "contacts",          # Contacts app (customers & vendors)
        "crm",               # CRM: opportunities and pipeline
        "sale_management",   # Sales app (quotations, sales orders)
        "purchase",          # Purchase app (RFQs, purchase orders)
        "stock",             # Inventory app (warehouses, transfers)
        "mrp",               # Manufacturing app (BoMs, work orders)
        "account",           # Invoicing app (invoices, payments, journals)
        # "Bridge" modules that connect the apps above with each other
        "sale_crm",          # opportunity  -> quotation
        "sale_stock",        # sales order  -> delivery order
        "purchase_stock",    # purchase     -> receipt + reordering rules
        "stock_account",     # stock moves  -> accounting entries (valuation)
        "mrp_account",       # production   -> product cost
        # Helpdesk from the Odoo Community Association (OCA): the official
        # Helpdesk app only exists in the paid Enterprise edition
        "helpdesk_mgmt",
        "helpdesk_mgmt_sale",  # link tickets to sales orders
        "helpdesk_product",    # link tickets to products
    ],
    "data": [
        # 1. Security: who can use our new models
        "security/ir.model.access.csv",
        # 2. Master data and configuration, in the order of the case study
        "data/01_company.xml",
        "data/02_units_of_measure.xml",
        "data/03_product_categories.xml",
        "data/04_warehouse.xml",
        "data/05_vendors.xml",
        "data/06_raw_materials.xml",
        "data/07_finished_products.xml",
        "data/08_manufacturing.xml",
        "data/09_sales_and_invoicing.xml",
        "data/10_customers.xml",
        "data/11_crm.xml",
        "data/12_helpdesk.xml",
        # 3. Screens, reports and menus
        "views/res_partner_views.xml",
        "wizard/income_statement_wizard_views.xml",
        "report/income_statement_report.xml",
        "report/partner_list_report.xml",
        "views/menus.xml",
    ],
    # Python code that runs once, before / after the data files are loaded
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}
