# campaign/models.py
from django.db import models
from django.utils import timezone
from typing import Optional
from django.db import transaction
from typing import Any


class Brand(models.Model):
    name: str = models.CharField(max_length=255)
    daily_budget: float = models.FloatField()
    monthly_budget: float = models.FloatField()
    current_daily_spend: float = models.FloatField(default=0.0)
    current_monthly_spend: float = models.FloatField(default=0.0)

    def __str__(self) -> str:
        return self.name

class Campaign(models.Model):
    name: str = models.CharField(max_length=255)
    brand: Optional[Brand] = models.ForeignKey(Brand, on_delete=models.CASCADE)
    is_active: bool = models.BooleanField(default=True)
    total_spend_today: float = models.FloatField(default=0.0)
    total_spend_month: float = models.FloatField(default=0.0)
    allowed_start_hour: int = models.IntegerField(default=0)
    allowed_end_hour: int = models.IntegerField(default=23)

    def is_within_daypart(self) -> bool:
        now_hour: int = timezone.now().hour
        return self.allowed_start_hour <= now_hour <= self.allowed_end_hour

    def __str__(self) -> str:
        return self.name

class SpendLog(models.Model):
    campaign: Optional[Campaign] = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    amount: float = models.FloatField()
    timestamp: timezone.datetime = models.DateTimeField(auto_now_add=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        with transaction.atomic():
            # Update campaign spends
            self.campaign.total_spend_today += self.amount
            self.campaign.total_spend_month += self.amount
            self.campaign.save()
            # Update brand spends
            self.campaign.brand.current_daily_spend += self.amount
            self.campaign.brand.current_monthly_spend += self.amount
            self.campaign.brand.save()
            super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.campaign.name} - ${self.amount} at {self.timestamp}"
