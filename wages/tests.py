from decimal import Decimal

from django.test import SimpleTestCase

from core.money import calculate_partner_wage, calculate_total_business


class WageCalculationTests(SimpleTestCase):
    def test_business_is_receipt_minus_payment(self):
        business = calculate_total_business(Decimal("1000000.00"), Decimal("400000.00"))
        self.assertEqual(business, Decimal("600000.00"))

    def test_partner_wage_is_business_times_share(self):
        wage = calculate_partner_wage(Decimal("600000.00"), Decimal("25"))
        self.assertEqual(wage, Decimal("150000.00"))

    def test_example_three_partners(self):
        business = Decimal("600000.00")
        self.assertEqual(calculate_partner_wage(business, Decimal("40")), Decimal("240000.00"))
        self.assertEqual(calculate_partner_wage(business, Decimal("35")), Decimal("210000.00"))
        self.assertEqual(calculate_partner_wage(business, Decimal("25")), Decimal("150000.00"))
