from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Commission
from .services import create_commission


class CommissionTests(TestCase):
    def setUp(self):
        self.seller = get_user_model().objects.create_user(
            username="seller", password="test-password-123"
        )

    def test_commission_and_seller_earnings_are_calculated(self):
        record = Commission.objects.create(
            seller=self.seller,
            order_reference="ORDER-001",
            order_amount=Decimal("100000"),
            commission_rate=Decimal("5.00"),
        )
        self.assertEqual(record.commission_amount, Decimal("5000.00"))
        self.assertEqual(record.seller_earnings, Decimal("95000.00"))

    def test_service_does_not_duplicate_same_seller_order(self):
        first, created_first = create_commission(
            seller=self.seller, order_reference="ORDER-002", order_amount="20000"
        )
        second, created_second = create_commission(
            seller=self.seller, order_reference="ORDER-002", order_amount="20000"
        )
        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Commission.objects.filter(order_reference="ORDER-002").count(), 1)
