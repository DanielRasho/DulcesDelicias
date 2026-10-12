# Dulces Delicias S.A. — Odoo 18 demo

A complete, reproducible Odoo setup for the case study **"Dulces Delicias S.A."**, a fictional
company that makes artisanal candy (caramelos, chocolates y galletas). It covers inventory,
purchasing, manufacturing, CRM, sales, invoicing, deliveries, after-sales service and reports.

Everything runs locally with Docker: one command creates the company already configured, a
second command simulates a full business cycle so every report has data.

- **This file:** how to run the project, the basics of Odoo, and how this repository is organized.
- **[docs/WALKTHROUGH.md](docs/WALKTHROUGH.md):** the case study step by step: what was
  configured, where to see it in Odoo, and how to do each operation yourself by clicking.

---

## Contents

1. [Quick start](#1-quick-start)
2. [Odoo basics](#2-odoo-basics)
3. [How the apps work together](#3-how-the-apps-work-together)
4. [What is in this repository](#4-what-is-in-this-repository)
5. [Case study map](#5-case-study-map)
6. [Working with the code](#6-working-with-the-code)
7. [Spanish interface](#7-spanish-interface)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Quick start

### What you need

| Tool | Why | Check |
|---|---|---|
| Docker + Docker Compose | runs Odoo, PostgreSQL and a fake mail server | `docker compose version` |
| git | downloads the community Helpdesk add-on (submodule) | `git --version` |
| make | short commands (`make install`, `make demo`...) | `make --version` |

All three are already installed on this machine. The first `make install` downloads about
1 GB of Docker images. Odoo needs about 1 GB of free RAM.

### Run it

```bash
make install   # ~2 min: creates the database and configures the company
make demo      # ~30 s: simulates purchases, production, sales, invoices, a complaint...
```

Then open:

| What | URL | Login |
|---|---|---|
| Odoo | <http://localhost:8069> | user `admin`, password `admin` |
| Emails sent by Odoo (Mailpit) | <http://localhost:8025> | – |

> **Two ways to use this project**
> - **See it done:** run `make install` + `make demo` and explore the results.
> - **Do it yourself:** run only `make install` (configuration, no operations) and follow
>   [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md) to create the orders by hand in the web interface.
>
> `make reset` deletes the database and starts again from zero, so you can practise as many times as you want.

### All commands

| Command | What it does |
|---|---|
| `make install` | Create the database `dulces_delicias` and install the case-study module |
| `make demo` | Run the business simulation ([scripts/demo_flow.py](scripts/demo_flow.py)); only once per database |
| `make start` / `make stop` | Start / stop the containers (data is kept) |
| `make update` | Reload the module after you edit its files |
| `make reset` | **Delete** the database and install everything again |
| `make logs` | Follow the Odoo server log |
| `make shell` | Interactive Python console connected to the database |
| `make clean` | Remove containers **and all data** |

---

## 2. Odoo basics

### 2.1 What is Odoo?

Odoo is an **ERP** (Enterprise Resource Planning): a single system where all the areas of a
company (sales, purchases, stock, production, accounting...) work on **one shared database**.
When the warehouse ships a box, the sales order knows it was delivered, the accounting gets the
cost of goods sold, and the stock report goes down, without anyone re-typing anything.

Odoo is organised in **apps** (CRM, Sales, Inventory, Manufacturing, Invoicing...). You install
only the ones you need.

There are two editions:

| | Community (this project) | Enterprise |
|---|---|---|
| Price | Free, open source (LGPL) | Paid subscription |
| Apps used here | CRM, Sales, Purchase, Inventory, Manufacturing, Invoicing | + Helpdesk, full Accounting reports, Studio... |
| What we did about the missing parts | **Helpdesk** → free module from the Odoo Community Association ([OCA](https://github.com/OCA/helpdesk)). **Income statement** → our own report (`Dulces Delicias > Reportes > Estado de Resultados`) | – |

### 2.2 How it is built

```
  Browser (you)  ──HTTP──▶  Odoo server (Python)  ──SQL──▶  PostgreSQL database
  localhost:8069            business logic + web UI          all the data
                                  │
                                  └──SMTP──▶ Mailpit (catches every email, localhost:8025)
```

- **Database:** one PostgreSQL database = one company setup (here `dulces_delicias`).
  The "filestore" (attachments, PDFs, images) lives next to it.
- **Odoo server:** Python program that contains all the apps and serves the web interface.
- **Module (= add-on):** a folder of code and data that adds features. Every app is a module,
  and **our own configuration is a module too**:
  [addons/dulces_delicias](addons/dulces_delicias).

### 2.3 Models, records and fields

Odoo stores everything as **records** of **models**. A model is like a table, a record is a
row, and a field is a column.

| Model (technical name) | What it is | Example in this project |
|---|---|---|
| `res.partner` | Contact: customer, vendor, person, address | Supermercado Delicias |
| `product.product` | Product | Azúcar, Caramelos (bolsa 500 g) |
| `uom.uom` | Unit of measure | kg, L, Units, Saco (50 kg) |
| `stock.warehouse` / `stock.location` | Warehouse / area inside it | DD/Stock/Materias Primas |
| `stock.picking` | Transfer: receipt, delivery, internal move | DD/IN/00001, DD/OUT/00001 |
| `stock.warehouse.orderpoint` | Reordering rule (min / max) | Azúcar: min 100 kg, max 400 kg |
| `mrp.bom` | Bill of materials (the recipe) | 1 lote de galletas |
| `mrp.production` / `mrp.workorder` | Manufacturing order / work order | DD/MO/00001 |
| `crm.lead` | Opportunity | "Góndola anual de galletas" |
| `sale.order` / `purchase.order` | Sales order / purchase order | S00001 / P00001 |
| `account.move` | Invoice, vendor bill or journal entry | INV/2026/00001 |
| `account.payment` | Payment | PTCR/2026/00001 |
| `helpdesk.ticket` | After-sales ticket | HT00001 |

Fields can point to other records: **many2one** (an order has *one* customer),
**one2many** (an order has *many* lines), **many2many** (a customer has *many* preferred
products, a product is preferred by *many* customers).

### 2.4 The screen, piece by piece

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ⋮⋮⋮ Sales   Orders  To Invoice  Products  Reporting  Configuration   💬 🕓 A │ ← app menu
├──────────────────────────────────────────────────────────────────────────┤
│ Orders / S00002            [Search... | Filters | Group By]   ☰ ▦ 📅 📊   │ ← control panel
│ [Create Invoice] [Send]                  Quotation ▸ Sent ▸ [Sales Order] │ ← buttons + status bar
│                     [Delivery 1] [Invoices 1]                             │ ← smart buttons
│  Customer: Supermercado Delicias    Payment Terms: 30 Days                │
│  Order Lines | Other Info                                                  │ ← tabs (notebook)
├──────────────────────────────────────────────────────────────────────────┤
│ Send message · Log note · Activities                                      │ ← chatter
│  Admin – Quotation confirmed                                               │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Home / apps menu (⋮⋮⋮):** every installed app, including our **Dulces Delicias** app with
  the reports.
- **Views:** the same records can be seen as a list ☰, kanban cards ▦, calendar 📅, pivot table
  or graph 📊. Switch with the buttons on the right.
- **Search bar:** type to search; use *Filters* and *Group By* to slice data (e.g. group the
  inventory by location). Filters can be saved as favourites.
- **Status bar:** the stage of a document (Draft → Confirmed → Done). Buttons move it forward.
- **Smart buttons:** shortcuts to related documents (the deliveries of an order, the sales of a
  customer...). They show how everything is connected.
- **Chatter:** the history of each record: emails sent, internal notes, and **activities**
  (to-dos, calls, meetings with a deadline: the reminders asked for in the case study).
  The 🕓 icon at the top shows your pending activities.
- **Settings:** many features are hidden until you enable them (*Settings* app, or
  *Configuration > Settings* in each app). This project already enabled units of measure,
  storage locations, multi-step routes, work orders and automatic stock accounting.
- **Developer mode:** add `?debug=1` to the URL (e.g. `http://localhost:8069/odoo?debug=1`).
  It shows technical names when you hover over a field, plus extra menus. Very useful to
  connect what you see on screen with the code.

### 2.5 Business concepts used in the case study

| Concept | Meaning |
|---|---|
| **Storable product** | A product whose quantity Odoo tracks (*Track Inventory* checkbox) |
| **Unit of measure (UoM)** | kg, L, Units... Stock can be counted in kg and bought in 50 kg sacks; Odoo converts between units of the same category |
| **Warehouse / Location** | A warehouse is a site. Locations are areas inside it (`DD/Stock/Materias Primas`) or virtual places (Vendors, Customers, Production, Scrap) |
| **Transfer** | Moves goods between locations: *Receipt* (vendor → stock), *Delivery* (stock → customer), *Pick Components* (stock → production floor) |
| **Route** | How a product is replenished: *Buy* (purchase order) or *Manufacture* (manufacturing order) |
| **Reordering rule** | Min / max stock. When the forecast drops under the minimum, Odoo proposes (or creates) an order up to the maximum |
| **Bill of materials (BoM)** | The recipe: components + quantities + operations to make N units |
| **Work center / operation / work order** | Where work happens (oven, packaging line), each step of the recipe, and that step for one specific production, with a timer |
| **Manufacturing order (MO)** | "Make 100 Galletas": consumes components, produces finished goods |
| **Lead / opportunity / pipeline** | A potential deal, shown as a card that moves through stages (Prospecto → Negociación → Cierre) |
| **Quotation → sales order** | A quotation becomes a sales order when the customer confirms it |
| **Payment term** | *When* the customer pays (immediately, 30 days, on delivery) |
| **Journal** | Where entries are recorded. Bank/cash journals = *how* money arrives (bank transfer, credit card, cash) |
| **Chart of accounts / journal entry** | Accounts (Sales, Cost of Goods Sold, Stock...). Every operation with money creates a journal entry (debits = credits) |
| **Inventory valuation (AVCO, automated)** | Stock has a money value (average cost). Every move of goods creates its accounting entry automatically |
| **Return / scrap** | Goods coming back from a customer / goods thrown away (damaged) |
| **Ticket** | A customer complaint or question, handled by a helpdesk team through stages |

---

## 3. How the apps work together

This is the "integration" the case study wants you to understand: each step **creates the next
document automatically** and posts its **accounting entry** without retyping anything.

```
 PURCHASING                    MANUFACTURING                    SALES
 ──────────                    ─────────────                    ─────
 Reordering rule (min/max)                                      CRM opportunity
   │ stock < minimum                                              │ "New Quotation"
   ▼                                                              ▼
 Request for Quotation (RFQ)                                    Quotation ──email──▶ customer
   │ Confirm                                                      │ Confirm
   ▼                                                              ▼
 Purchase Order                                                 Sales Order
   │ creates                                                      │ creates            │ Create invoice
   ▼                                                              ▼                    ▼
 Receipt ──▶ DD/Stock/Materias Primas                          Delivery            Invoice ──email──▶ customer
   │                     │                                        ▲    │                 │ Pay
   ▼                     │ Manufacturing Order (BoM)              │    ▼                 ▼
 Vendor Bill ──▶ Payment │   1. Pick Components ─▶ Productos en Proceso      Payment (card / transfer / cash)
                         │   2. Work orders (time × cost/hour)    │
                         └─▶ 3. Produce ─▶ DD/Stock/Productos Terminados
                                                                   │
 AFTER-SALES:  Ticket ─▶ Return (damaged goods back) ─▶ Scrap ─▶ Replacement delivery ─▶ Ticket done
```

The journal entries that Odoo created during `make demo` (Invoicing > Accounting > Journal Entries):

| Operation | Journal entry created automatically (Dr = debit, Cr = credit) |
|---|---|
| Initial inventory count | Dr Stock Valuation / Cr Capital |
| Receipt of the purchase | Dr Stock Valuation / Cr Stock Interim (Received) |
| Vendor bill | Dr Stock Interim (Received) + Tax Paid / Cr Account Payable |
| Payment to vendor | Dr Account Payable / Cr Bank (Transferencia Bancaria) |
| Manufacturing order | Dr Stock Valuation (finished candy) / Cr Stock Valuation (raw materials) + Cr Salary Payable (labour: work-order minutes × work-center cost per hour) |
| Customer invoice | Dr Account Receivable / Cr Product Sales + Tax Received, **and** Dr Cost of Goods Sold / Cr Stock Interim (Delivered) |
| Delivery | Dr Stock Interim (Delivered) / Cr Stock Valuation |
| Customer payment | Dr Bank, Credit Card or Cash journal / Cr Account Receivable |
| Scrap of damaged goods | Dr Mermas y Pérdidas de Inventario (expense) / Cr Stock Valuation |

The **income statement** (Estado de Resultados) simply adds up the income and expense accounts
for the chosen period: Sales − Cost of Goods Sold − Expenses = Net profit.

---

## 4. What is in this repository

```
.
├── README.md                    ← you are here
├── docs/WALKTHROUGH.md          ← the case study, step by step
├── Makefile                     ← the `make ...` shortcuts
├── docker-compose.yml           ← the 3 containers: db, odoo, mailpit
├── config/odoo.conf             ← Odoo server settings (database, add-ons path, mail)
├── scripts/
│   ├── demo_flow.py             ← simulates the business operations (make demo)
│   └── install_spanish.py       ← adds the Spanish (Latin America) language
├── third_party/oca-helpdesk/    ← OCA Helpdesk modules (git submodule, not our code)
└── addons/dulces_delicias/      ← OUR MODULE: the whole company configuration
    ├── __manifest__.py          ← module "ID card": name, dependencies, files to load in order
    ├── hooks.py                 ← Python run once at install (settings, accounts, warehouse)
    ├── data/                    ← master data, one file per topic, in case-study order
    │   ├── 01_company.xml           company name, address, logo
    │   ├── 02_units_of_measure.xml  "Saco (50 kg)"
    │   ├── 03_product_categories.xml  Materias Primas / Productos Terminados + valuation
    │   ├── 04_warehouse.xml         warehouse, the 3 storage areas, putaway rules
    │   ├── 05_vendors.xml           3 vendors
    │   ├── 06_raw_materials.xml     8 raw materials + vendor prices + min/max rules
    │   ├── 07_finished_products.xml caramelos, chocolates, galletas
    │   ├── 08_manufacturing.xml     work centers + the 3 recipes (BoMs) with operations
    │   ├── 09_sales_and_invoicing.xml  payment terms, payment methods (journals)
    │   ├── 10_customers.xml         the 3 customers with contacts and preferences
    │   ├── 11_crm.xml               pipeline stages, sales team, tags
    │   └── 12_helpdesk.xml          after-sales team, ticket categories and tags
    ├── models/res_partner.py    ← adds "customer type" and "preferred products" to contacts
    ├── views/                   ← screens: customer profile tab, Dulces Delicias menu
    ├── wizard/                  ← the income statement pop-up (pick a period)
    ├── report/                  ← printable reports: income statement, customer/vendor lists
    ├── security/                ← access rights for our new model
    └── static/description/icon.png
```

**Module vs. script:** the module holds *configuration and master data* (things that exist
before the company starts working). The script holds *operations* (things employees do every
day). That is why `make install` gives you a clean company ready to operate, and `make demo`
fills it with one complete business cycle.

### Reading an XML data file

```xml
<record id="product_candy" model="product.product">   <!-- create a record of model product.product -->
    <field name="name">Caramelos (bolsa 500 g)</field> <!-- a simple value -->
    <field name="list_price">4.00</field>
    <field name="categ_id" ref="categ_finished_goods"/>  <!-- link to another record by its XML ID -->
</record>
```

The `id` (**XML ID**) is a permanent name for the record, so other files, the scripts and
updates can find it. `ref="..."` links to another record by its XML ID; `module.name` (like
`uom.product_uom_kgm`) points to a record created by another module.

---

## 5. Case study map

| # | Case study requirement | Done by | Where to see it in Odoo |
|---|---|---|---|
| 1 | 3 products and their raw materials, units, min/max stock | module (`06`, `07`, `02`) | Inventory > Products > Products · Inventory > Operations > Procurement > Replenishment |
| 2 | Initial inventory | demo, step 1 | Inventory > Operations > Adjustments > Physical Inventory |
| 2 | Warehouses: raw materials, work in process, finished goods | module (`04`) | Inventory > Configuration > Warehouse Management > Locations |
| 2 | Purchase order for low stock | demo, step 2 | Purchase > Orders > Purchase Orders |
| 3 | Plan and produce one batch of each product, work orders and times | module (`08`) + demo, step 3 | Manufacturing > Operations > Manufacturing Orders · Manufacturing > Reporting > Work Orders |
| 4 | 3 customer profiles (type, contacts, history, preferences) | module (`10`) | Dulces Delicias > Reportes > Listado de Clientes (tab *Perfil comercial*) |
| 4 | Opportunities with stages and follow-ups | module (`11`) + demo, step 4 | CRM > Sales > My Pipeline · CRM > Sales > My Activities |
| 5 | A sales order per customer with payment terms and delivery conditions | demo, step 5 | Sales > Orders > Orders (tab *Other Info*) |
| 6 | Invoices sent; transfer / credit card / cash on delivery payments | module (`09`) + demo, step 6 | Invoicing > Customers > Invoices · Mailpit |
| 7 | Plan and complete deliveries | demo, step 7 | Inventory > Operations > Transfers > Deliveries |
| 8 | After-sales case for an order (damaged product), solved | module (`12`) + demo, step 8 | Helpdesk > Tickets > All Tickets |
| 9 | Reports: inventory, customers, vendors, income statement for a period | module (`views`, `report`, `wizard`) | **Dulces Delicias > Reportes** |

Step-by-step instructions for each line: **[docs/WALKTHROUGH.md](docs/WALKTHROUGH.md)**.

---

## 6. Working with the code

**Change the configuration** (prices, quantities, a new product...): edit the XML in
`addons/dulces_delicias/data/`, then run `make update`. The data in these files is reapplied
on every update, so if you change one of these records in the web interface, the next
`make update` restores the XML value. Change it in the XML to make it permanent.

**Add a new data file:** create it in `data/` and add it to the `data` list in
`__manifest__.py` (order matters: a record must exist before another file can `ref` it).

**Play with the ORM** (the Python API that every Odoo module uses):

```bash
make shell
```
```python
>>> env["res.partner"].search([("customer_rank", ">", 0)]).mapped("name")
['Confitería La Dulzura', 'Distribuidora Dulce Sabor', 'Supermercado Delicias']
>>> product = env.ref("dulces_delicias.product_candy")
>>> product.qty_available, product.standard_price
(15.0, 1.4720833333333332)
>>> env["sale.order"].search([]).mapped(lambda o: (o.name, o.amount_total))
[('S00003', 258.75), ('S00002', 471.5), ('S00001', 212.75)]
>>> env.cr.commit()   # only needed if you CHANGE data and want to keep it
```

**Read the demo script:** [scripts/demo_flow.py](scripts/demo_flow.py) is organised in
functions named after the case-study steps (`step_2_purchase`, `step_8_after_sales`...). Each
line has the name of the button it replaces (`button_confirm()` = *Confirm Order*).

**Useful official documentation:** <https://www.odoo.com/documentation/18.0/> (user guides
per app, and the developer tutorial "Server framework 101").

---

## 7. Spanish interface

The interface is in English by default (most tutorials and documentation are in English), and
Spanish (Latin America) is already installed. To switch: **click your avatar (top right) >
Preferences > Language > Spanish (Latin America) / Español (América Latina)**. Customers and vendors already have Spanish as their
language, so the quotations and invoices they receive by email are in Spanish.

| English | Español |
|---|---|
| Inventory | Inventario |
| Manufacturing | Manufactura |
| Purchase | Compras |
| Sales | Ventas |
| Invoicing | Facturación |
| Helpdesk | Servicio de asistencia |
| Bills of Materials | Listas de materiales |
| Work Orders | Órdenes de trabajo |
| Replenishment | Reabastecimiento |

The case-study data (product names, customers, stages, the Dulces Delicias reports) is in
Spanish in both interfaces.

---

## 8. Troubleshooting

| Problem | Solution |
|---|---|
| `make install` prints `(ERROR/3) Unexpected indentation` or `Warn: Can't find .pfb for face 'Courier'` | Harmless messages (a module description and the PDF engine). Ignore them |
| Port 8069 or 8025 already in use | Stop the other program, or change the left number in `ports:` in `docker-compose.yml` (e.g. `"8070:8069"`) |
| `make demo` says *"The simulation already ran"* | It only runs once per database. `make reset` then `make demo` |
| `make demo` fails with *"service odoo is not running"* | `make start`, wait a few seconds, try again |
| Error `module helpdesk_mgmt not found` | The submodule was not downloaded: `make setup` (or clone with `git clone --recursive`) |
| Manufacturing orders list looks empty | Remove the *To Do* filter in the search bar: finished orders are hidden by default |
| A screen does not show a field mentioned in the docs | Activate developer mode (`?debug=1`) or check the feature is enabled in Settings |
| `permission denied` talking to Docker | Your user must be in the `docker` group (`sudo usermod -aG docker $USER`, then log out and in) |
| I want to start completely fresh | `make clean` (removes all data), then `make install` |
