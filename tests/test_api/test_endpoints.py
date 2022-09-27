from api.models import User, Product

import pytest
from rest_framework.test import APIClient


class TestUser:

    # Extra cases:
    #  - Test deposit increments and not resets
    #  - Test deposit/reset only themselves

    def test_only_buyer_can_deposit(self, buyer, seller, client, db):
        # Disallowed
        client.force_login(seller)
        resp = client.post(f"/users/{seller.id}/deposit/", {"deposit": 10})
        resp.status_code == 403
        assert User.objects.get(username=seller.username).deposit == 0

        # Allowed
        client.force_login(buyer)
        resp = client.post(f"/users/{buyer.id}/deposit/", {"deposit": 10})
        resp.status_code == 200
        assert User.objects.get(username=buyer.username).deposit == 10

    @pytest.mark.parametrize("deposit_value,is_valid", (
        (0, False),
        (1, False),
        (5, True),
        (10, True),
        (20, True),
        (50, True),
        (100, True),
        (200, False),
    ))
    def test_deposit_coins(self, deposit_value, is_valid, client, user):
        client.force_login(user)
        resp = client.get(f"/users/{user.id}/")
        assert resp.json()["deposit"] == 0

        # Deposit
        resp = client.post(f"/users/{user.id}/deposit/", {"deposit": deposit_value})
        if is_valid:
            assert resp.status_code == 200, resp.json()
        else:
            assert resp.status_code == 400

    def test_only_buyer_reset_deposit(self, client, buyer, seller):
        buyer.deposit = 50.0
        buyer.save()
        seller.deposit = 50.0
        seller.save()

        # Seller can't reset
        client.force_login(seller)
        resp = client.post(f"/users/{seller.id}/reset/")
        assert resp.status_code == 403
        assert User.objects.get(pk=seller.id).deposit == 50.0

        # Buyer can reset
        client.force_login(buyer)
        resp = client.post(f"/users/{buyer.id}/reset/")
        assert resp.status_code == 200
        assert User.objects.get(pk=buyer.id).deposit == 0.0


class TestProduct:

    def test_only_seller_can_create_product(self, buyer, seller, client):

        # Allowed
        client.force_login(seller)
        resp = client.post(f"/products/", {"name": "productA", "cost": 25.0})
        resp.status_code == 200
        assert Product.objects.count() == 1

        # Disallowed
        client.force_login(buyer)
        resp = client.post(f"/products/", {"name": "productB", "cost": 25.0})
        resp.status_code == 403
        assert Product.objects.count() == 1

    def test_cost_must_be_multiple_of_5(self, seller, client):
        client.force_login(seller)
        resp = client.post(f"/products/", {"name": "myproduct", "cost": 2.0})
        resp.status_code == 400
        assert "not a multiple of 5" in resp.json()["cost"][0]
        assert Product.objects.count() == 0

    def test_only_product_creator_can_delete_the_product(self, client, db):
        seller_a = User.objects.create(username="seller_a", role="seller")
        seller_b = User.objects.create(username="seller_b", role="seller")

        # Seller A creates a product
        client.force_login(seller_a)
        resp = client.post(f"/products/", {"name": "productA", "cost": 25.0})
        resp.status_code == 200
        assert Product.objects.count() == 1
        product_id = Product.objects.last().id

        # Seller B can't edit
        client.force_login(seller_b)
        resp = client.patch(f"/products/{product_id}/", {"cost": 50})
        resp.status_code == 403
        assert Product.objects.last().cost == 25.0

        # Seller A can edit
        client = APIClient()
        client.force_login(seller_a)
        resp = client.patch(f"/products/{product_id}/", {"cost": 50})
        resp.status_code == 200
        assert Product.objects.last().cost == 50.0

    def test_buy(self, client, buyer, seller):
        buyer.deposit = 170
        buyer.save()
        product = Product.objects.create(name="pc", cost=50, amount_available=10, seller_id=seller)

        # Buyer can't buy above the amount
        client.force_login(buyer)
        resp = client.post(f"/products/{product.id}/buy/", {"amount": 100})
        assert resp.status_code == 400
        assert "above available_amount" in resp.json()[0]
        assert User.objects.get(pk=buyer.id).deposit == 170  # initial deposit

        # Buyer can't afford
        resp = client.post(f"/products/{product.id}/buy/", {"amount": 10})
        assert resp.status_code == 400
        assert "not enough deposit" in resp.json()[0]

        # Change is given back
        resp = client.post(f"/products/{product.id}/buy/", {"amount": 3})
        expected_cost = 150
        assert resp.status_code == 200
        assert resp.json() == {"spent": 150, "change": [20]}
        assert Product.objects.get(pk=product.id).amount_available == 7
        assert User.objects.get(pk=buyer.id).deposit == 20
