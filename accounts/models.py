from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from institutions.models import Institution


class Role(models.Model):
    """Legacy table: ADMN_ROLES. institution is null for global roles (ADMIN, MANAGER)."""

    class Code(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"

    role_code = models.CharField(max_length=50, db_index=True)
    role_description = models.CharField(max_length=255)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="roles",
        help_text="Null means the role is global (not tied to one branch).",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "admn_roles"
        constraints = [
            models.UniqueConstraint(
                fields=["role_code", "institution"],
                name="uniq_role_code_institution",
            ),
            models.UniqueConstraint(
                fields=["role_code"],
                condition=models.Q(institution__isnull=True),
                name="uniq_global_role_code",
            ),
        ]

    def __str__(self) -> str:
        scope = self.institution.name if self.institution_id else "global"
        return f"{self.role_code} ({scope})"


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required.")
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("status", User.Status.ACTIVE)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Legacy table: ADMN_USER_MASTER.

    Intentionally omitted as stored fields:
    - PASSWORD (use Django password hashing via set_password)
    - SECRETQUESTION / ANSWER (use PasswordResetToken)
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        LOCKED = "LOCKED", "Locked"
        INACTIVE = "INACTIVE", "Inactive"

    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.PROTECT,
        related_name="users",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="users",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "admn_user_master"
        indexes = [
            models.Index(fields=["institution", "is_active"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self) -> str:
        return self.username

    def can_login(self) -> bool:
        return self.is_active and self.status == self.Status.ACTIVE

    @property
    def role_code(self) -> str:
        return self.role.role_code

    @property
    def is_admin_role(self) -> bool:
        return self.role.role_code == Role.Code.ADMIN

    @property
    def is_manager_role(self) -> bool:
        return self.role.role_code == Role.Code.MANAGER


class PasswordResetToken(models.Model):
    """Hashed one-time reset token. Replaces legacy SECRETQUESTION / ANSWER."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "password_reset_token"
        indexes = [
            models.Index(fields=["user", "expires_at"]),
        ]

    def __str__(self) -> str:
        return f"reset:{self.user.username}"
