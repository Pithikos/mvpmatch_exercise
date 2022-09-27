from .models import User, Product, COINS
from .serializers import UserSerializer, ProductSerializer
from .roles import is_creator

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.viewsets import ModelViewSet
from rest_framework_roles.granting import is_self
from rest_framework_roles.decorators import allowed
from rest_framework.decorators import action
from rest_framework.response import Response


def coinize_money(amount):
    """
    Split amount into list of discrete coins
    """
    assert amount >= 0, f"Must be positive, got {amount}"
    coins = []
    remaining = amount

    for valuta in sorted(COINS, reverse=True):
        if remaining >= valuta:
            remaining -= valuta
            coins.append(valuta)

    return coins


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    view_permissions = {
        'retrieve': {'user': is_self, 'admin': True},
        'create': {'anon': True},
        'list': {'admin': True},
        'update': {'user': is_self, 'admin': True},
        'destroy': {'user': is_self, 'admin': True},
    }

    @allowed('buyer')
    @action(detail=True, methods=['post'])
    # TODO: Obliterate in favor of PATCH users/<id>/.
    def deposit(self, request, pk=None):
        """
        Deposit money
        """
        user = self.get_object()
        data = {"deposit": user.deposit + int(request.POST["deposit"])}
        serializer = UserSerializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': 'Deposit successfull'})

    @allowed('buyer')
    @action(detail=True, methods=['post'])
    # TODO: Rename to reset_deposit or take 'deposit' as param
    def reset(self, request, pk=None):
        """
        Reset deposit
        """
        user = self.get_object()
        user.deposit = 0.0
        user.save()
        return Response({'status': 'Deposit reset successfully'})


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    view_permissions = {
        'retrieve': {'user': True, 'anon': True},
        'create': {'seller': True},
        'list': {'user': True, 'anon': True},
        'update': {'seller': is_creator},
        'destroy': {'seller': is_creator},
    }

    def create(self, request, pk=None):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data["seller_id"] = request.user
        serializer.save()
        return Response({'status': 'Product created'})

    @allowed('buyer')
    @action(detail=True, methods=['post'])
    def buy(self, request, pk=None):
        """
        Buy product
        """
        try:
            amount = int(request.data["amount"])
        except ValueError:
            raise ParseError("amount must be int")
        product = self.get_object()
        user = request.user

        if amount > product.amount_available:
            raise ValidationError("amount is above available_amount of product")

        total_cost = amount*product.cost
        if total_cost > user.deposit:
            raise ValidationError("not enough deposit")

        change = user.deposit - total_cost
        user.deposit -= total_cost
        product.amount_available -= amount

        # Ensure both updated or nothing
        with transaction.atomic():
            user.save()
            product.save()

        return Response({'spent': total_cost, 'change': coinize_money(change)})
