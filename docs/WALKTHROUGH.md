# Case study walkthrough — Dulces Delicias S.A.

This guide follows the case study section by section. For each one it shows:

- **Configured:** what `make install` already set up (from `addons/dulces_delicias/data/`).
- **Do it yourself:** the clicks to perform the operation in the web interface.
  `make demo` performs exactly these steps automatically
  ([scripts/demo_flow.py](../scripts/demo_flow.py)).
- **Check:** where to look at the result.

Menu paths are written for the English interface (`App > Menu > Submenu`). Log in at
<http://localhost:8069> with `admin` / `admin`.

> To practise by hand: run `make reset` (configured company, no operations) and follow this
> guide. To look at a finished example: run `make reset` and then `make demo`.

---

## 1. Products and raw materials

### Configured

**Finished products** (`07_finished_products.xml`), sold by unit and made in batches of 100:

| Code | Product | Sales price | Route |
|---|---|---|---|
| PT-001 | Caramelos (bolsa 500 g) | $4.00 | Manufacture |
| PT-002 | Chocolates (barra 100 g) | $2.50 | Manufacture |
| PT-003 | Galletas (paquete 250 g) | $3.00 | Manufacture |

**Raw materials** (`06_raw_materials.xml`), all with route *Buy*:

| Code | Raw material | Stock unit | Purchase unit | Cost | Vendor | Min | Max |
|---|---|---|---|---|---|---|---|
| MP-001 | Azúcar | kg | Saco (50 kg) | $1.00/kg | Distribuidora de Insumos Reposteros | 100 kg | 400 kg |
| MP-002 | Colorantes alimentarios | L | L | $15.00/L | Aromas y Colores Industriales | 2 L | 10 L |
| MP-003 | Saborizantes | L | L | $20.00/L | Aromas y Colores Industriales | 3 L | 15 L |
| MP-004 | Cacao | kg | kg | $8.00/kg | Distribuidora de Insumos Reposteros | 20 kg | 80 kg |
| MP-005 | Leche | L | L | $1.20/L | Lácteos y Granja La Pradera | 20 L | 60 L |
| MP-006 | Harina de trigo | kg | Saco (50 kg) | $0.90/kg | Distribuidora de Insumos Reposteros | 50 kg | 250 kg |
| MP-007 | Mantequilla | kg | kg | $7.00/kg | Lácteos y Granja La Pradera | 10 kg | 40 kg |
| MP-008 | Huevos | Units | Dozens | $0.15/unit | Lácteos y Granja La Pradera | 120 | 480 |

**Recipes (bills of materials)**, one batch = 100 units (`08_manufacturing.xml`):

| Product | Components per batch | Operations (work center, minutes) |
|---|---|---|
| Caramelos | Azúcar 45 kg, Colorantes 0.5 L, Saborizantes 1 L | Cocción del jarabe (Cocina, 60) → Moldeado y enfriado (Cocina, 45) → Empaque (Empaque, 30) |
| Chocolates | Cacao 5 kg, Leche 4 L, Azúcar 2 kg | Mezcla y conchado (Línea de Chocolate, 60) → Templado y moldeado (40) → Empaque (20) |
| Galletas | Harina 12 kg, Azúcar 5 kg, Mantequilla 6 kg, Huevos 60 | Preparación de la masa (Panadería y Horno, 30) → Horneado (35) → Empaque (25) |

### Where to see it

| What | Menu |
|---|---|
| Products (filter by category *Materias Primas* / *Productos Terminados*) | Inventory > Products > Products |
| Units of measure, including *Saco (50 kg)* in *Weight* | Inventory > Configuration > Units of Measures > UoM Categories |
| Min / max of every raw material | Open a raw material > smart button **Min: … Max: …**, or Inventory > Operations > Procurement > Replenishment (remove the filters) |
| Recipes | Manufacturing > Products > Bills of Materials |
| Work centers and their cost per hour | Manufacturing > Configuration > Work Centers |

### Do it yourself (example: a new raw material)

1. Inventory > Products > Products > **New**.
2. *Product Type*: Goods, tick **Track Inventory**, *Category*: Materias Primas.
3. *Unit of Measure*: kg; *Purchase Unit*: Saco (50 kg); *Cost*.
4. Tab **Purchase**: add the vendor and its price (per purchase unit).
5. Tab **Inventory**: *Routes* = Buy.
6. Save, then click the **Replenishment** smart button (it shows *Min / Max* once a rule exists) >
   **New**: minimum and maximum quantity.

---

## 2. Inventory management

### Configured

The factory is one warehouse, **Planta Dulces Delicias** (code `DD`), with three storage areas
(`04_warehouse.xml`):

| Case study | Location in Odoo | Used for |
|---|---|---|
| Almacén de materias primas | `DD/Stock/Materias Primas` | raw materials received from vendors |
| Almacén de productos en proceso | `DD/Productos en Proceso` | raw materials taken to the production floor (work in process) |
| Almacén de productos terminados | `DD/Stock/Productos Terminados` | finished candy ready to sell |

- **Putaway rules** send goods to the right area automatically: everything of category
  *Materias Primas* that enters `DD/Stock` is stored in *Materias Primas*, and finished goods
  in *Productos Terminados*.
- The warehouse manufactures in **2 steps** ("Pick components, then manufacture"): first a
  transfer takes the components to *Productos en Proceso*, then the production consumes them.

> In Odoo a *warehouse* is a physical site and *locations* are the areas inside it. Modelling
> the three "almacenes" as three locations of the same plant is the standard approach.

**Menus:** Inventory > Configuration > Warehouse Management > Warehouses / Locations / Putaway Rules.

### 2.1 Initial inventory

| Raw material | Initial quantity | vs. minimum |
|---|---|---|
| Azúcar | 60 kg | **below** min 100 |
| Colorantes alimentarios | 5 L | ok |
| Saborizantes | 8 L | ok |
| Cacao | 8 kg | **below** min 20 |
| Leche | 30 L | ok |
| Harina de trigo | 30 kg | **below** min 50 |
| Mantequilla | 15 kg | ok |
| Huevos | 150 | ok |

**Do it yourself:** Inventory > Operations > Adjustments > **Physical Inventory** > **New** →
product, location `DD/Stock/Materias Primas`, *Counted Quantity* → **Apply** on each line (or
**Apply All**).

**Check:** Inventory > Reporting > Stock, or **Dulces Delicias > Reportes > Estado de Inventario**.
The value of the stock appears in Invoicing > Accounting > Journal Entries (Stock Valuation / Capital).

### 2.2 Purchase order for low stock

**Do it yourself:**

1. Inventory > Operations > Procurement > **Replenishment**. Odoo lists the raw materials whose
   forecast is below the minimum and proposes the quantity to reach the maximum (rounded to
   whole sacks): Azúcar 300 kg, Cacao 70 kg, Harina 200 kg.
2. Select them > **Order**. Odoo creates one *Request for Quotation* per vendor
   (all three come from *Distribuidora de Insumos Reposteros*). Quantities are converted to the
   purchase unit: 6 sacos de azúcar, 4 sacos de harina.
3. Purchase > Orders > Requests for Quotation > open it > **Confirm Order**.
4. **Receive Products** > **Validate**: the goods go to `DD/Stock/Materias Primas`.
5. Back on the order: **Create Bill** > set the *Bill Date* > **Confirm** > **Pay** with
   journal *Transferencia Bancaria*.

> The reordering rules are *automatic*: when production later consumes butter and eggs below
> their minimum, Odoo creates a draft RFQ to *Lácteos y Granja La Pradera* by itself
> (Purchase > Orders > Requests for Quotation).

---

## 3. Production planning and execution

**Do it yourself** (repeat for the three products):

1. Manufacturing > Operations > Manufacturing Orders > **New**: *Product* = Caramelos,
   *Quantity* = 100. The bill of materials, components and work orders are filled in.
2. **Confirm**. A *Pick Components* transfer is created (smart button **Transfers**).
3. Open it > **Validate**: components move to `DD/Productos en Proceso`.
4. Back on the order, tab **Work Orders**: press **▶ Start** on each operation, and **✓ Done**
   when it is finished. The real duration is recorded (you can also type it).
5. **Produce All**: components are consumed and 100 units enter `DD/Stock/Productos Terminados`.

**Check:**

| What | Where |
|---|---|
| The finished orders | Manufacturing > Operations > Manufacturing Orders (remove the *To Do* filter) |
| Expected vs. real minutes per operation | Manufacturing > Reporting > Work Orders, or the *Work Orders* tab |
| Stock decrease / increase | Dulces Delicias > Reportes > Estado de Inventario |
| Unit cost of each product (materials + labour) | the product form, field *Cost* (e.g. Caramelos ≈ $1.47) |

Production cost = components (average cost) + work-order minutes × work-center cost per hour.

---

## 4. Customer management (CRM)

### Configured: customer profiles (`10_customers.xml`)

| Customer | Type | Contact | Payment terms | Preferences |
|---|---|---|---|---|
| Confitería La Dulzura | Minorista / Confitería | Lucía Fernández (Propietaria) | Immediate Payment | Caramelos, Chocolates; small weekly orders; pays by card |
| Supermercado Delicias | Supermercado / Cadena | Carlos Méndez (Jefe de Compras) | 30 Days | Galletas, Chocolates; full deliveries to *Bodega Central* |
| Distribuidora Dulce Sabor | Distribuidor | Ana Ruiz (Gerente Comercial) | Pago contra entrega | All three; volume prices; pays cash on delivery |

Open a customer: tab **Perfil comercial** (customer type, preferred products, notes; fields
added by this module). The **purchase history** is in the smart buttons at the top
(*Sales*, *Invoiced*, *Opportunities*).

**Pipeline stages** (`11_crm.xml`): **Prospecto → Negociación → Cierre (Ganado)**. They replace
Odoo's default stages. Edit them with the ⚙ icon on each column of the pipeline.

### Opportunities created by the demo

| Opportunity | Customer | Stage | Follow-up (activity) |
|---|---|---|---|
| Pedido semanal de caramelos y chocolates | Confitería La Dulzura | Prospecto | Call in 3 days |
| Góndola anual de galletas y chocolates | Supermercado Delicias | Negociación | Meeting in 5 days |
| Distribución regional - primer pedido | Distribuidora Dulce Sabor | Cierre (Ganado) | To-do in 7 days |

**Do it yourself:**

1. CRM > Sales > My Pipeline > **New**: name, customer, expected revenue > **Add**.
2. Open the card: probability, tags, internal notes (**Log note**).
3. Drag the card to another column to change the stage (the change is logged in the chatter).
4. Follow-ups / reminders: the 🕓 icon on the card, or **Activities** in the chatter: choose
   *Call*, *Meeting* or *To-Do*, a due date and a summary. They appear in CRM > Sales >
   My Activities and in the 🕓 icon of the top bar.
5. When the customer accepts: **Won**.

---

## 5. Sales management

### Orders created by the demo

| Order | Customer | Caramelos | Chocolates | Galletas | Total | Payment terms | Delivery conditions |
|---|---|---|---|---|---|---|---|
| S00001 | Confitería La Dulzura | 20 | 30 | 10 | $212.75 | Immediate Payment | As soon as possible, tomorrow, to the shop |
| S00002 | Supermercado Delicias | 40 | 40 | 50 | $471.50 | 30 Days | **All products at once**, in 3 days, to *Bodega Central* |
| S00003 | Distribuidora Dulce Sabor | 25 | 20 | 25 | $258.75 | Pago contra entrega | As soon as possible, in 2 days |

Prices include 15% tax. Each order is linked to its CRM opportunity.

**Do it yourself:**

1. From the opportunity: **New Quotation** (or Sales > Orders > Quotations > **New**).
2. Customer; *Delivery Address* (Supermercado → *Bodega Central*); *Payment Terms*.
3. Order lines: product and quantity.
4. Tab **Other Info**: *Shipping Policy* ("As soon as possible" or "When all products are
   ready"), *Delivery Date*, *Incoterm* (DAP = we deliver to the customer).
5. Delivery conditions as text at the bottom (terms and conditions).
6. **Send by Email** (check it in Mailpit, <http://localhost:8025>) > **Confirm**.

**Track the orders:** Sales > Orders > Orders shows the invoice status, and on each order the
smart buttons **Delivery** and **Invoices** show what was shipped and billed.
Sales > Reporting > Sales gives the analysis (pivot / graph).

---

## 6. Invoicing and payments

### Configured: payment methods (`09_sales_and_invoicing.xml`)

| Payment method (case study) | Journal in Odoo | Code |
|---|---|---|
| Transferencia bancaria | Transferencia Bancaria (bank) | TRF |
| Tarjeta de crédito | Tarjeta de Crédito (bank) | TCR |
| Pago contra entrega | Pago Contra Entrega (Efectivo) (cash) | PCE |

Plus the payment term **Pago contra entrega**. See them in Invoicing > Configuration >
Accounting > Journals and Invoicing > Configuration > Invoicing > Payment Terms.

### What the demo did

| Invoice | Customer | Paid with | Status |
|---|---|---|---|
| INV/2026/00001 | Confitería La Dulzura | Tarjeta de Crédito | Paid |
| INV/2026/00002 | Supermercado Delicias | Transferencia Bancaria, 50% advance | Partially paid, rest due in 30 days |
| INV/2026/00003 | Distribuidora Dulce Sabor | Efectivo, at delivery | Paid |

**Do it yourself:**

1. On the sales order: **Create Invoice** > **Create Draft** > **Confirm**.
2. **Send**: the PDF invoice is emailed to the customer (look in Mailpit).
3. **Pay**: choose the *Journal* (payment method), the amount (less than the total = partial
   payment) > **Create Payment**.

**Check:** Invoicing > Customers > Invoices (ribbon *Paid* / *Partial*), Invoicing > Customers >
Payments, and the receivable per customer in **Dulces Delicias > Reportes > Listado de Clientes**
(column *Por cobrar*).

---

## 7. Delivery management

**Do it yourself:**

1. Inventory > **Overview** (card *Delivery Orders*) or Inventory > Operations > Transfers >
   **Deliveries**. Each confirmed sales order created one, with the *Scheduled Date* taken from
   the order's delivery date.
2. Open it: the products are reserved from `DD/Stock/Productos Terminados`.
3. When the goods reach the customer: **Validate**. The delivery is *Done*, the sales order
   shows it as delivered, and stock goes down.
4. Cash-on-delivery customer: register the payment of the invoice now (journal
   *Pago Contra Entrega (Efectivo)*).

> Optional: Inventory > Configuration > Settings > **Signature** lets the customer sign the
> delivery order as proof of delivery.

---

## 8. After-sales service

### Configured (`12_helpdesk.xml`)

- Team **Atención Postventa**.
- Categories: *Producto en mal estado*, *Retraso en la entrega*, *Error en facturación*,
  *Consulta general*. Tags: *Reclamo*, *Consulta*.
- Stages (from the Helpdesk module): New → In Progress → Awaiting → Done.

Menus: Helpdesk > Configuration > Teams / Categories / Stages.

### The case: Supermercado Delicias received 5 broken cookie packs (order S00002)

| Step | In Odoo | Document |
|---|---|---|
| 1. The customer calls | Helpdesk > Tickets > **New**: title, contact *Carlos Méndez*, category *Producto en mal estado*, product *Galletas*, sales order *S00002*, priority, channel *Phone* | HT00001 |
| 2. Follow-up | Stage **In Progress**, a **Log note** with the analysis, an **Activity** "Coordinar devolución y reposición" | – |
| 3. Take back the damaged goods | Open delivery DD/OUT/00002 > **Return** > 5 Galletas (0 for the others) > **Return for Exchange**. Odoo creates the return *and* a new delivery for the replacement | DD/IN/00002 + DD/OUT/00004 |
| 4. Receive the return | Open the return > **Validate** | DD/IN/00002 |
| 5. Throw away the damaged packs | Inventory > Operations > Adjustments > **Scrap** > **New**: Galletas, 5, source `DD/Stock/Productos Terminados` > **Validate** | SP/00001 |
| 6. Send the replacement | Open DD/OUT/00004 > **Validate** | DD/OUT/00004 |
| 7. Close the case | Mark the activity as done, log the resolution, stage **Done**. The customer receives an email: "El ticket HT00001 ha sido cerrado" | HT00001 |

**Check:** the ticket (chatter with the full history and the *Sale Orders* smart button), the
scrap in Inventory > Operations > Adjustments > Scrap, and the expense *Mermas y Pérdidas de
Inventario* in the income statement.

---

## 9. Reports

All in the **Dulces Delicias** app > **Reportes**:

| Report | What it shows | How |
|---|---|---|
| **Estado de Inventario** | Stock per location (raw materials / finished goods), quantity, unit and value | List grouped by location; switch to the pivot view for a matrix |
| **Valoración de Inventario** | Every stock movement with its value | Odoo's standard valuation report |
| **Listado de Clientes** | Customers with type, preferred products, contact, payment terms, orders, receivable | Select the customers > **Print** > *Listado de Clientes (PDF)* |
| **Listado de Proveedores** | Vendors with contact, products they supply, purchases, payable | Select the vendors > **Print** > *Listado de Proveedores (PDF)* |
| **Estado de Resultados** | Income statement for a period | Choose *Este mes / Mes anterior / Este año / Personalizado* > **Ver en pantalla** or **Descargar PDF**. **Ver apuntes contables** shows the journal items behind the numbers |

And under **Dulces Delicias > Análisis**: sales, purchases, invoicing and work-order analysis
(Odoo's pivot / graph reports).

### Income statement after `make demo`

| | |
|---|---:|
| Ingresos por ventas (Product Sales) | $820.00 |
| Costo de ventas (Cost of Goods Sold) | −$345.95 |
| **Utilidad bruta** | **$474.05** |
| Gastos de operación (Mermas y Pérdidas de Inventario) | −$6.49 |
| **Utilidad neta del periodo** | **$467.56** |

Where the numbers come from:

- **Sales** = untaxed total of the three invoices: 185.00 + 410.00 + 225.00.
- **Cost of goods sold** = units sold × unit production cost (materials + labour), posted
  automatically with each customer invoice.
- **Mermas** = the 5 scrapped cookie packs × $1.30.

How it is computed: [wizard/income_statement_wizard.py](../addons/dulces_delicias/wizard/income_statement_wizard.py)
groups the posted journal items of the period by account type (income, cost of revenue,
expenses). Odoo Community has no income statement of its own (it is part of the paid
Accounting app), which is why this project includes one.
