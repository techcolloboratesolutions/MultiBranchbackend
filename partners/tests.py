from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from institutions.models import Institution, MainInstitution
from partners.models import Partner, PartnerGroup, PartnerGroupEntry


class PartnerShareTests(TestCase):
    def setUp(self):
        main = MainInstitution.objects.create(name="Horizon Group")
        self.inst = Institution.objects.create(name="Head Office", main_institution=main)
        self.other_inst = Institution.objects.create(name="Branch Two", main_institution=main)
        self.group = PartnerGroup.objects.create(name="Profit Sharing", is_profit_sharing=True)
        self.other_group = PartnerGroup.objects.create(name="Branch Partners", is_profit_sharing=True)
        self.partner = Partner.objects.create(name="Partner A")
        self.partner_b = Partner.objects.create(name="Partner B")

    def test_share_percent_out_of_range_fails_clean(self):
        entry = PartnerGroupEntry(
            partner_group=self.group,
            institution=self.inst,
            partner=self.partner,
            share_percent=Decimal("120"),
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_group_institution_shares_cannot_exceed_100(self):
        PartnerGroupEntry.objects.create(
            partner_group=self.group,
            institution=self.inst,
            partner=self.partner,
            share_percent=Decimal("60"),
        )
        entry = PartnerGroupEntry(
            partner_group=self.group,
            institution=self.inst,
            partner=self.partner_b,
            share_percent=Decimal("50"),
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_same_group_other_institution_does_not_count(self):
        PartnerGroupEntry.objects.create(
            partner_group=self.group,
            institution=self.other_inst,
            partner=self.partner,
            share_percent=Decimal("80"),
        )
        entry = PartnerGroupEntry(
            partner_group=self.group,
            institution=self.inst,
            partner=self.partner_b,
            share_percent=Decimal("80"),
        )
        entry.full_clean()

    def test_institution_cannot_have_two_groups(self):
        PartnerGroupEntry.objects.create(
            partner_group=self.group,
            institution=self.inst,
            partner=self.partner,
            share_percent=Decimal("40"),
        )
        entry = PartnerGroupEntry(
            partner_group=self.other_group,
            institution=self.inst,
            partner=self.partner_b,
            share_percent=Decimal("40"),
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_partner_can_join_another_group_at_another_institution(self):
        PartnerGroupEntry.objects.create(
            partner_group=self.group,
            institution=self.inst,
            partner=self.partner,
            share_percent=Decimal("40"),
        )
        entry = PartnerGroupEntry(
            partner_group=self.other_group,
            institution=self.other_inst,
            partner=self.partner,
            share_percent=Decimal("40"),
        )
        entry.full_clean()

    def test_inactive_partners_do_not_count_toward_share_total(self):
        PartnerGroupEntry.objects.create(
            partner_group=self.group,
            institution=self.inst,
            partner=self.partner,
            share_percent=Decimal("80"),
            is_active=False,
        )
        entry = PartnerGroupEntry(
            partner_group=self.group,
            institution=self.inst,
            partner=self.partner_b,
            share_percent=Decimal("100"),
            is_active=True,
        )
        entry.full_clean()
