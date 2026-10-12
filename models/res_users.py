from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class ResUsers(models.Model):
    _inherit = "res.users"

    company_currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Company Currency",
    )
    purchase_order_limit = fields.Monetary(
        string="Purchase Order Limit",
        currency_field="company_currency_id",
        default=10000.0,
    )
    can_edit_purchase_order_limit = fields.Boolean(
        compute="_compute_can_edit_purchase_order_limit",
    )

    @api.depends_context("uid")
    def _compute_can_edit_purchase_order_limit(self):
        can_edit = self.env.user.has_group(
            "purchase_order_approval.group_purchase_order_limit_manager"
        )
        for user in self:
            user.can_edit_purchase_order_limit = can_edit

    def _check_purchase_order_limit_edit(self, vals_list):
        if self.env.user.has_group(
            "purchase_order_approval.group_purchase_order_limit_manager"
        ):
            return
        if any("purchase_order_limit" in vals for vals in vals_list):
            raise AccessError(_(
                "Only a Purchase Order Limit Manager can change the Purchase Order Limit."
            ))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_purchase_order_limit_edit(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        self._check_purchase_order_limit_edit([vals])
        return super().write(vals)
