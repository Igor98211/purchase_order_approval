from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseOrderApproval(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.po_double_validation = "one_step"
        cls.partner = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.product = cls.env["product.product"].create({
            "name": "Test Product",
            "purchase_ok": True,
        })
        cls.user = cls._create_user("po.limit.user")
        cls.manager = cls._create_user("po.limit.manager", manager=True)

    @classmethod
    def _create_user(cls, login, manager=False):
        groups = cls.env.ref("purchase.group_purchase_user")
        if manager:
            groups |= cls.env.ref(
                "purchase_order_approval.group_purchase_order_limit_manager"
            )
            groups |= cls.env.ref("base.group_erp_manager")
        return cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": login,
            "login": login,
            "group_ids": [Command.link(group.id) for group in groups],
        })

    def _create_order(self, amount=None):
        values = {"partner_id": self.partner.id}
        if amount is not None:
            values["order_line"] = [Command.create({
                "product_id": self.product.id,
                "product_qty": 1,
                "price_unit": amount,
            })]
        order = self.env["purchase.order"].create(values)
        if amount is not None and order.amount_untaxed != amount:
            order.order_line.price_unit = amount
        return order

    def test_confirm_within_user_limit(self):
        """An order of 5,000 is within the default limit of 10,000."""
        order = self._create_order(5000)
        self.assertEqual(self.user.purchase_order_limit, 10000)

        result = order.with_user(self.user).button_confirm()

        self.assertTrue(result)
        self.assertEqual(order.state, "purchase")

    def test_confirm_exceeds_user_limit(self):
        """An order of 15,000 is blocked for a regular user."""
        order = self._create_order(15000)

        with self.assertRaises(UserError) as error:
            order.with_user(self.user).button_confirm()

        self.assertIn("exceeds your purchase limit", str(error.exception))
        self.assertEqual(order.state, "draft")

    def test_manager_confirms_order_over_limit(self):
        """A Purchase Order Limit Manager can confirm an order of 15,000."""
        order = self._create_order(15000)

        order.with_user(self.manager).button_confirm()

        self.assertEqual(order.state, "purchase")

    def test_large_order(self):
        """Large Order is set only when the untaxed amount is above 5,000."""
        self.assertFalse(self._create_order(4000).large_order)
        self.assertFalse(self._create_order(5000).large_order)
        self.assertTrue(self._create_order(6000).large_order)

    def test_large_order_warning_does_not_block_confirmation(self):
        """A large order within the user limit is confirmed and only warns."""
        order = self._create_order(6000)

        result = order.with_user(self.user).button_confirm()

        self.assertEqual(order.state, "purchase")
        self.assertEqual(result["tag"], "display_notification")
        self.assertIn(
            "This is a large purchase order.",
            result["params"]["message"],
        )

    def test_empty_order_cannot_be_confirmed(self):
        """An order without lines cannot be confirmed, including by a manager."""
        order = self._create_order()

        with self.assertRaises(UserError) as error:
            order.with_user(self.manager).button_confirm()

        self.assertIn("at least one order line", str(error.exception))
        self.assertEqual(order.state, "draft")

    def test_purchase_order_limit_is_editable_only_for_manager(self):
        self.assertFalse(self.user.with_user(self.user).can_edit_purchase_order_limit)
        self.assertTrue(self.user.with_user(self.manager).can_edit_purchase_order_limit)

    def test_regular_user_cannot_change_purchase_order_limit(self):
        with self.assertRaises(AccessError):
            self.user.with_user(self.user).write({"purchase_order_limit": 20000})

        self.assertEqual(self.user.purchase_order_limit, 10000)

    def test_manager_can_change_purchase_order_limit(self):
        self.user.with_user(self.manager).write({"purchase_order_limit": 8000})

        self.assertEqual(self.user.purchase_order_limit, 8000)
