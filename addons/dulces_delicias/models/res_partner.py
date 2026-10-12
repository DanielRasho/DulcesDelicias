from odoo import fields, models


class ResPartner(models.Model):
    """Extend Odoo's contacts with the customer profile asked by the case study.

    `_inherit` does NOT create a new table: it adds these columns to the
    existing `res.partner` model (contacts). Our fields start with `dd_`
    (Dulces Delicias) so it is obvious they come from this module.
    """
    _inherit = "res.partner"

    dd_customer_type = fields.Selection(
        selection=[
            ("retail", "Minorista / Confitería"),
            ("supermarket", "Supermercado / Cadena"),
            ("distributor", "Distribuidor"),
        ],
        string="Tipo de cliente",
    )
    dd_preferred_product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Productos preferidos",
        domain=[("sale_ok", "=", True)],
    )
    dd_preferences = fields.Text(string="Preferencias y notas comerciales")

    # Helpers used by the printable customer / vendor lists (report/)
    def _dd_sold_amount(self):
        """Total of the confirmed sales orders of this customer."""
        orders = self.env["sale.order"].search([
            ("partner_id", "child_of", self.id),
            ("state", "=", "sale"),
        ])
        return sum(orders.mapped("amount_total"))

    def _dd_purchased_amount(self):
        """Total of the confirmed purchase orders sent to this vendor."""
        orders = self.env["purchase.order"].search([
            ("partner_id", "child_of", self.id),
            ("state", "in", ("purchase", "done")),
        ])
        return sum(orders.mapped("amount_total"))

    def _dd_supplied_products(self):
        """Products that list this vendor in their Purchase tab."""
        return self.env["product.supplierinfo"].search([
            ("partner_id", "=", self.id),
        ]).product_tmpl_id
