from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Meta:
        db_table = "users"
        verbose_name = verbose_name_plural = _("ユーザー")
