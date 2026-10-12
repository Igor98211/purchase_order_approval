from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    large_order = fields.Boolean(
        string="Large Order",
        compute="_compute_large_order",
    )

    @api.depends("amount_untaxed")
    def _compute_large_order(self):
        for order in self:
            order.large_order = order.amount_untaxed > 5000

    def _confirmation_error_message(self):
        self.ensure_one()
        error_msg = super()._confirmation_error_message()
        if error_msg:
            return error_msg
        if not self.order_line.filtered(lambda line: not line.display_type):
            return _("A purchase order must contain at least one order line.")
        if self.env.user.has_group(
            "purchase_order_approval.group_purchase_order_limit_manager"
        ):
            return False
        amount_untaxed = self.currency_id._convert(
            self.amount_untaxed,
            self.env.company.currency_id,
            self.company_id,
            self.date_order.date(),
        )
        if amount_untaxed > self.env.user.purchase_order_limit:
            return _(
                "You cannot confirm this purchase order because its amount exceeds your purchase limit."
            )
        return False

    def button_confirm(self):
        large_orders = self.filtered(
            lambda order: order.state in ("draft", "sent") and order.large_order
        )
        res = super().button_confirm()
        if large_orders and res is True:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "warning",
                    "title": _("Warning"),
                    "message": _(
                        "This is a large purchase order. Please make sure that the purchase has been properly reviewed."
                    ),
                    "sticky": True,
                    "next": {"type": "ir.actions.client", "tag": "soft_reload"},
                },
            }
        return res
