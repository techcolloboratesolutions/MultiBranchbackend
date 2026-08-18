from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from institutions.models import Institution, MainInstitution
from partners.models import Partner, PartnerGroup, PartnerGroupEntry


class PartnerShareTests(TestCase):
    def setUp(self):
        main = MainInstitution.objects.create(name="Horizon Group")
        self.inst = Institution.objects.create(name="Head Office", main_institution=main)
        self.group = PartnerGroup.objects.create(name="Profit Sharing", is_profit_sharing=True)
        self.partner = Partner.objects.create(name="Partner A")

    def test_share_percent_out_of_range_fails_clean(self):
        entry = PartnerGroupEntry(
            partner_group=self.group,
            institution=self.inst,
            partner=self.partner,
            share_percent=Decimal("120"),
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()
