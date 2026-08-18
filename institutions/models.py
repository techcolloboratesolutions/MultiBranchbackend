from django.db import models


class MainInstitution(models.Model):
    """Legacy table: ADMN_INSTN_MAIN."""

    name = models.CharField(max_length=255)
    place = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    po_box = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    fax = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    legal_name = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "admn_instn_main"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Institution(models.Model):
    """Legacy table: ADMN_INSTN_MASTER. A branch of a MainInstitution."""

    name = models.CharField(max_length=255)
    main_institution = models.ForeignKey(
        MainInstitution,
        on_delete=models.PROTECT,
        related_name="institutions",
    )
    address = models.TextField(blank=True)
    po_box = models.CharField(max_length=50, blank=True)
    phone1 = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    fax = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    contact_person = models.CharField(max_length=255, blank=True)
    contact_number = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "admn_instn_master"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["main_institution", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name
