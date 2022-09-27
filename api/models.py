from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


COINS = {5, 10, 20, 50, 100}


ROLE_CHOICES = (
    ("buyer", "Buyer"),
    ("seller", "Seller"),
)


DEPOSIT_CHOICES = [(c, str(c)) for c in COINS]


def validate_is_multiple_of_five(value):
    if value % 5 != 0:
        raise ValidationError(
            _('%(value)s is not a multiple of 5'),
            params={'value': value},
        )


class User(AbstractUser):
    deposit = models.IntegerField(default=0, choices=DEPOSIT_CHOICES)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')


class Product(models.Model):
    name = models.CharField(max_length=100)
    amount_available = models.IntegerField(default=0)
    cost = models.FloatField(validators=[validate_is_multiple_of_five])
    seller_id = models.ForeignKey(User, related_name='products', on_delete=models.CASCADE)
