# Copyright 2021 Ecosoft
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class TestHrExpensePayToVendor(TransactionCase):
    def setUp(self):
        super(TestHrExpensePayToVendor, self).setUp()
        self.vendor = self.env["res.partner"].create({"name": "Test Vendor"})
        self.payment_obj = self.env["account.payment"]
        self.account_payment_register = self.env["account.payment.register"]
        self.payment_journal = self.env["account.journal"].search(
            [("type", "in", ["cash", "bank"])], limit=1
        )

        self.main_company = company = self.env.ref("base.main_company")
        self.expense_journal = self.env["account.journal"].create(
            {
                "name": "Purchase Journal - Test",
                "code": "HRTPJ",
                "type": "purchase",
                "company_id": company.id,
            }
        )

    def _get_payment_wizard(self, expense_sheet):
        action = expense_sheet.action_register_payment()
        ctx = action.get("context")
        with Form(
            self.account_payment_register.with_context(ctx),
            view="account.view_account_payment_register_form",
        ) as f:
            f.journal_id = self.payment_journal
            f.amount = self.expense_sheet.total_amount
        register_payment = f.save()
        return register_payment

    def test_hr_expense_work_acceptance(self):
        """When expense is set to pay to vendor, I expect,
        - After post journal entries, all journal items will use partner_id = vendor
        - After make payment, all journal items will use partner_id = vendor
        """
        self.expense_sheet = self.env["hr.expense.sheet"].create(
            {
                "employee_id": self.ref("hr.employee_admin"),
                "name": "Expense test",
                "journal_id": self.expense_journal.id,
            }
        )
        self.expenses = self.env["hr.expense"].create(
            [
                {
                    "name": "Expense Line 1",
                    "employee_id": self.ref("hr.employee_admin"),
                    "product_id": self.ref("hr_expense.air_ticket"),
                    "unit_amount": 1,
                    "quantity": 10,
                    "sheet_id": self.expense_sheet.id,
                },
                {
                    "name": "Expense Line 1",
                    "employee_id": self.ref("hr.employee_admin"),
                    "product_id": self.ref("hr_expense.air_ticket"),
                    "unit_amount": 1,
                    "quantity": 20,
                    "sheet_id": self.expense_sheet.id,
                },
            ]
        )
        # No WA
        for expense in self.expenses:
            self.assertEqual(expense.qty_accepted, 0)
        # Create WA
        res = self.expense_sheet.with_context(create_wa=True).action_view_wa()
        f = Form(self.env[res["res_model"]].with_context(res["context"]))
        work_acceptance = f.save()
        # WA Accepted
        work_acceptance.button_accept()
        for expense in self.expenses:
            self.assertEqual(expense.qty_accepted, expense.quantity)
