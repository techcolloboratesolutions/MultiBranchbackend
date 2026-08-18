from django.test import TestCase

from institutions.models import Institution, MainInstitution


class InstitutionModelTests(TestCase):
    def test_main_institution_has_many_branches(self):
        main = MainInstitution.objects.create(name="Horizon Group")
        Institution.objects.create(name="Head Office", main_institution=main)
        Institution.objects.create(name="Branch 2", main_institution=main)
        self.assertEqual(main.institutions.count(), 2)
