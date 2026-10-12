# Purchase Order: Automatic Checks — Limits, Permissions, Warnings, and Confirmation Blocking

## 1. Goal

Develop an Odoo 19 module `purchase_order_approval` that adds automatic checks to the standard Purchase Order before confirmation.

The module must:

- control the maximum purchase order amount;
- use an individual purchase limit for each user;
- warn users about large purchase orders;
- block confirmation when mandatory conditions are not met;
- allow a manager to confirm orders that exceed the regular user's limit.

Use the standard Odoo model:

```text
purchase.order
```

Do not modify the Odoo core.

---

## 2. User Purchase Order Limit

Add a new field to `res.users`:

```text
Purchase Order Limit
```

Type:

```python
fields.Monetary
```

Default value:

```text
10,000
```

The field must be available in the user settings.

Example:

```text
User: John
Purchase Order Limit: €10,000
```

---

## 3. Purchase Order Amount Check

For each Purchase Order, use the untaxed order amount:

```text
Order Total = amount_untaxed
```

Use the standard Odoo field:

```text
amount_untaxed
```

### Rule

If:

```text
amount_untaxed <= user's purchase limit
```

the regular user can confirm the Purchase Order.

If:

```text
amount_untaxed > user's purchase limit
```

the regular user cannot confirm the Purchase Order.

When confirmation is attempted, show:

```text
You cannot confirm this purchase order because its amount exceeds your purchase limit.
```

---

## 4. Purchase Order Limit Manager Group

Create a security group:

```text
Purchase Order Limit Manager
```

A user belonging to this group is considered a manager.

A manager can confirm Purchase Orders regardless of their individual purchase limit.

Example:

```text
User limit = €10,000
Order = €15,000
```

Regular user:

```text
Confirm → BLOCKED
```

Manager:

```text
Confirm → ALLOWED
```

---

## 5. Large Order Warning

Add a computed field to `purchase.order`:

```text
Large Order
```

Type:

```python
fields.Boolean
```

Rule:

```text
amount_untaxed > 5,000
```

→ `Large Order = True`

Otherwise:

```text
Large Order = False
```

The field must be visible on the Purchase Order form.

Example:

```text
Untaxed Amount: €7,500

☑ Large Order
```

---

## 6. Warning During Confirmation

If a Purchase Order is a `Large Order`, show the following warning when the user attempts to confirm it:

```text
This is a large purchase order. Please make sure that the purchase has been properly reviewed.
```

This warning must **not** block confirmation.

A user can still confirm a Large Order if all other confirmation rules are satisfied.

---

## 7. Empty Purchase Order

A Purchase Order cannot be confirmed if it has no order lines.

When attempting to confirm an empty Purchase Order, show:

```text
A purchase order must contain at least one order line.
```

Confirmation must be blocked.

---

## 8. Where the Checks Must Be Performed

The main business checks must be performed when the Purchase Order is being confirmed.

Use the standard Odoo Purchase Order confirmation workflow.

Do not rely only on:

- `onchange`;
- view logic;
- UI-only restrictions.

The checks must also work when the Purchase Order is modified or confirmed through the ORM/API.

---

## 9. Editing the Purchase Order Limit

A regular user must not be able to change their own:

```text
Purchase Order Limit
```

Only a user belonging to:

```text
Purchase Order Limit Manager
```

may modify Purchase Order Limits.

---

## 10. Views

Extend the standard Purchase Order form.

Add:

```text
Large Order
```

to an appropriate location in the Purchase Order form.

Extend the user form and add:

```text
Purchase Order Limit
```

The Purchase Order Limit Manager group must be available in the user settings.

---

## 11. Security

Create the security group:

```text
Purchase Order Limit Manager
```

The manager must be able to:

- modify Purchase Order Limits;
- confirm Purchase Orders that exceed the regular user's limit.

Regular users:

- can see their Purchase Order Limit;
- cannot modify their Purchase Order Limit;
- cannot confirm a Purchase Order that exceeds their limit.

---

## 12. Technical Requirements

Use:

- standard Odoo ORM;
- model inheritance;
- `res.users`;
- `purchase.order`;
- computed fields;
- `@api.depends`;
- confirmation-time validation;
- `UserError` or another appropriate Odoo exception;
- XML views;
- security groups;
- automated tests.

Do not modify:

```text
odoo/addons/purchase/
```

All custom code must be located in:

```text
addons/purchase_order_approval/
```

Target version:

```text
Odoo 19
```

---

## 13. Automated Tests

Add automated tests for at least the following cases.

### Test 1 — Order Within User Limit

```text
User limit = €10,000
Order = €5,000
```

Expected:

```text
Confirm → SUCCESS
```

---

### Test 2 — Order Exceeds User Limit

```text
User limit = €10,000
Order = €15,000
```

Expected:

```text
Confirm → UserError
```

---

### Test 3 — Manager

```text
User limit = €10,000
Order = €15,000
User = Purchase Order Limit Manager
```

Expected:

```text
Confirm → SUCCESS
```

---

### Test 4 — Large Order

For:

```text
Order = €4,000
```

Expected:

```text
large_order = False
```

For:

```text
Order = €6,000
```

Expected:

```text
large_order = True
```

---

### Test 5 — Empty Purchase Order

Create a Purchase Order without order lines and attempt to confirm it.

Expected:

```text
UserError
```

---

## 14. Out of Scope

Do not add the following features unless explicitly required later:

- multi-level approval;
- multi-company-specific limits;
- currency-specific limits;
- separate models for approval limits;
- complex approval workflows;
- additional approval stages;
- changes to the standard Odoo Purchase module.

Keep the implementation small enough to understand the complete module.

---

## 15. Expected Module Structure

A possible structure is:

```text
purchase_order_approval/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── purchase_order.py
│   └── res_users.py
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
├── views/
│   ├── purchase_order_views.xml
│   └── res_users_views.xml
└── tests/
    ├── __init__.py
    └── test_purchase_order_approval.py
```

The exact structure may be adjusted if Odoo 19 conventions require it.
