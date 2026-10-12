"""
Add Spanish (Latin America) to Odoo, keeping English as the default.

Same as: Settings > Languages > Add Languages > "Spanish (Latin America)"
with "Overwrite Existing Terms" ticked. `make install` runs it for you.
Each user then chooses the language in: avatar (top right) > Preferences.
"""
spanish = env["res.lang"]._activate_lang("es_419")
env["base.language.install"].create({
    "lang_ids": [(6, 0, spanish.ids)],
    "overwrite": True,
}).lang_install()
# Our customers and vendors speak Spanish: the emails they receive
# (quotations, invoices...) will be written in Spanish.
partner_ids = env["ir.model.data"].search([
    ("module", "=", "dulces_delicias"), ("model", "=", "res.partner"),
]).mapped("res_id")
env["res.partner"].browse(partner_ids).write({"lang": "es_419"})
env.cr.commit()
print("Spanish (Latin America) is ready: avatar (top right) > Preferences > Language")
