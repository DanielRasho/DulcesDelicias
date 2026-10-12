from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

# The income statement (Estado de Resultados) groups the accounts of the
# chart of accounts by their "account type":
#   (section key, title, account types, sign)
# Odoo stores balance = debit - credit. Income accounts normally have a
# CREDIT balance (negative), so we multiply them by -1 to show positive sales.
SECTIONS = [
    ("income", "Ingresos por ventas", ["income"], -1),
    ("cost", "Costo de ventas", ["expense_direct_cost"], 1),
    ("expense", "Gastos de operación", ["expense", "expense_depreciation"], 1),
    ("other_income", "Otros ingresos", ["income_other"], -1),
]
PROFIT_AND_LOSS_TYPES = [t for _key, _title, types, _sign in SECTIONS for t in types]


class IncomeStatementWizard(models.TransientModel):
    """Small pop-up window that asks for a period and shows the income statement.

    A TransientModel is a temporary model: its records are deleted
    automatically after a while. It is the usual way to build "wizards".
    Odoo Community has no income statement report (it is part of the paid
    Accounting app), so we compute it from the journal items ourselves.
    """
    _name = "dd.income.statement.wizard"
    _description = "Estado de Resultados"

    company_id = fields.Many2one(
        "res.company", string="Empresa", required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    period = fields.Selection(
        selection=[
            ("this_month", "Este mes"),
            ("last_month", "Mes anterior"),
            ("this_year", "Este año"),
            ("custom", "Personalizado"),
        ],
        string="Periodo", default="this_year", required=True,
    )
    # Computed from the period, but editable when the period is "custom"
    date_from = fields.Date(
        string="Desde", required=True,
        compute="_compute_dates", store=True, readonly=False, precompute=True,
    )
    date_to = fields.Date(
        string="Hasta", required=True,
        compute="_compute_dates", store=True, readonly=False, precompute=True,
    )

    @api.depends("period")
    def _compute_dates(self):
        today = fields.Date.context_today(self)
        for wizard in self:
            if wizard.period == "this_month":
                wizard.date_from = today.replace(day=1)
                wizard.date_to = today.replace(day=1) + relativedelta(months=1, days=-1)
            elif wizard.period == "last_month":
                wizard.date_from = today.replace(day=1) - relativedelta(months=1)
                wizard.date_to = today.replace(day=1) - relativedelta(days=1)
            elif wizard.period == "this_year":
                wizard.date_from = today.replace(month=1, day=1)
                wizard.date_to = today.replace(month=12, day=31)
            elif not wizard.date_from or not wizard.date_to:
                wizard.date_from = today.replace(day=1)
                wizard.date_to = today

    def _get_domain(self):
        """Posted journal items of the period on income / expense accounts."""
        self.ensure_one()
        return [
            ("company_id", "=", self.company_id.id),
            ("parent_state", "=", "posted"),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("account_id.account_type", "in", PROFIT_AND_LOSS_TYPES),
        ]

    def get_report_values(self):
        """Compute every number of the report. Called from the QWeb template."""
        self.ensure_one()
        # SQL "GROUP BY account": one (account, sum of balance) pair per account
        balances = self.env["account.move.line"]._read_group(
            domain=self._get_domain(),
            groupby=["account_id"],
            aggregates=["balance:sum"],
        )
        sections = {}
        for key, title, account_types, sign in SECTIONS:
            lines = sorted(
                [(account, sign * balance) for account, balance in balances
                 if account.account_type in account_types],
                key=lambda line: line[0].code,
            )
            sections[key] = {
                "title": title,
                "lines": lines,
                "total": sum(amount for _account, amount in lines),
            }
        gross_profit = sections["income"]["total"] - sections["cost"]["total"]
        operating_profit = gross_profit - sections["expense"]["total"]
        net_profit = operating_profit + sections["other_income"]["total"]
        return {
            "sections": sections,
            "gross_profit": gross_profit,
            "operating_profit": operating_profit,
            "net_profit": net_profit,
        }

    # ---- Buttons of the wizard ----
    def action_view(self):
        return self.env.ref("dulces_delicias.action_report_income_statement_html").report_action(self)

    def action_print_pdf(self):
        return self.env.ref("dulces_delicias.action_report_income_statement_pdf").report_action(self)

    def action_open_journal_items(self):
        """Show the journal items behind the numbers (to check / audit them)."""
        return {
            "type": "ir.actions.act_window",
            "name": "Detalle del Estado de Resultados",
            "res_model": "account.move.line",
            "view_mode": "list,pivot",
            "domain": self._get_domain(),
            "context": {"group_by": ["account_id"], "create": False},
        }
