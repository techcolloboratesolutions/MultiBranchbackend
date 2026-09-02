from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from core.money import calculate_balance, calculate_partner_wage, calculate_total_business
from institutions.models import Institution, MainInstitution
from partners.models import Partner, PartnerGroup, PartnerGroupEntry
from wages.services import profit_share_entries


class WageCalculationTests(SimpleTestCase):
    def test_business_is_receipt_plus_payment(self):
        business = calculate_total_business(Decimal("1000000.00"), Decimal("400000.00"))
        self.assertEqual(business, Decimal("1400000.00"))

    def test_balance_is_sales_minus_expense(self):
        balance = calculate_balance(Decimal("1000000.00"), Decimal("400000.00"), Decimal("100000.00"))
        self.assertEqual(balance, Decimal("900000.00"))

    def test_partner_wage_is_balance_times_share(self):
        balance = calculate_balance(Decimal("1000000.00"), Decimal("400000.00"), Decimal("100000.00"))
        wage = calculate_partner_wage(balance, Decimal("25"))
        self.assertEqual(wage, Decimal("225000.00"))

    def test_example_three_partners(self):
        balance = Decimal("600000.00")
        self.assertEqual(calculate_partner_wage(balance, Decimal("40")), Decimal("240000.00"))
        self.assertEqual(calculate_partner_wage(balance, Decimal("35")), Decimal("210000.00"))
        self.assertEqual(calculate_partner_wage(balance, Decimal("25")), Decimal("150000.00"))


class WagePartnerScopeTests(TestCase):
    def setUp(self):
        main = MainInstitution.objects.create(name="Horizon Group")
        self.inst = Institution.objects.create(name="Head Office", main_institution=main)
        other = Institution.objects.create(name="Branch Two", main_institution=main)
        group = PartnerGroup.objects.create(name="Profit Sharing", is_profit_sharing=True)
        other_group = PartnerGroup.objects.create(name="WhatsApp Only", is_profit_sharing=False)
        self.local = Partner.objects.create(name="Local Partner")
        other_partner = Partner.objects.create(name="Other Branch Partner")
        extra = Partner.objects.create(name="Non Profit Partner")
        third = Institution.objects.create(name="Branch Three", main_institution=main)
        PartnerGroupEntry.objects.create(
            partner_group=group,
            institution=self.inst,
            partner=self.local,
            share_percent=Decimal("100"),
        )
        PartnerGroupEntry.objects.create(
            partner_group=group,
            institution=other,
            partner=other_partner,
            share_percent=Decimal("100"),
        )
        PartnerGroupEntry.objects.create(
            partner_group=other_group,
            institution=third,
            partner=extra,
            share_percent=Decimal("10"),
        )

    def test_wages_only_include_profit_sharing_partners_for_institution(self):
        names = [entry.partner.name for entry in profit_share_entries(self.inst.id)]
        self.assertEqual(names, ["Local Partner"])
