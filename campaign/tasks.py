#campaign/tasks.py
from celery import shared_task
from django.utils.timezone import now, localtime
from django.db import transaction
import logging
from datetime import datetime
from typing import Optional
from .models import Campaign, Brand

logger = logging.getLogger(__name__)

@shared_task
def check_and_pause_overspend_campaigns() -> None:
    logger.info("Starting check_and_pause_overspend_campaigns task")
    campaigns = Campaign.objects.select_related('brand').all()
    current_hour = localtime(now()).hour
    logger.info(f"Current hour (local): {current_hour}")
    
    for campaign in campaigns:
        brand = campaign.brand
        is_within_daypart = campaign.is_within_daypart()
        logger.info(
            f"Campaign: {campaign.name}, "
            f"Is Active: {campaign.is_active}, "
            f"Within Daypart: {is_within_daypart}, "
            f"Total Spend Today: {campaign.total_spend_today}, "
            f"Total Spend Month: {campaign.total_spend_month}, "
            f"Brand Daily Budget: {brand.daily_budget}, "
            f"Brand Monthly Budget: {brand.monthly_budget}, "
            f"Brand Current Daily Spend: {brand.current_daily_spend}, "
            f"Brand Current Monthly Spend: {brand.current_monthly_spend}"
        )
        
        if is_within_daypart and campaign.is_active:
            if (
                campaign.total_spend_today >= brand.daily_budget or
                campaign.total_spend_month >= brand.monthly_budget or
                brand.current_daily_spend >= brand.daily_budget or
                brand.current_monthly_spend >= brand.monthly_budget
            ):
                logger.info(f"Pausing campaign {campaign.name} due to budget overrun")
                with transaction.atomic():
                    campaign.is_active = False
                    campaign.save()
                    logger.info(f"Campaign {campaign.name} paused, is_active: {campaign.is_active}")
            else:
                logger.info(f"Campaign {campaign.name} within budget, no action needed")
        else:
            logger.info(f"Campaign {campaign.name} not paused: not active or outside daypart")

@shared_task
def enforce_dayparting() -> None:
    current_hour = localtime(now()).hour
    logger.info(f"Running enforce_dayparting, current hour: {current_hour}")
    campaigns = Campaign.objects.all()
    for campaign in campaigns:
        within_window = campaign.allowed_start_hour <= current_hour <= campaign.allowed_end_hour
        should_be_active = within_window and (
            campaign.total_spend_today < campaign.brand.daily_budget and
            campaign.total_spend_month < campaign.brand.monthly_budget and
            campaign.brand.current_daily_spend < campaign.brand.daily_budget and
            campaign.brand.current_monthly_spend < campaign.brand.monthly_budget
        )
        if should_be_active != campaign.is_active:
            campaign.is_active = should_be_active
            campaign.save()
            logger.info(f"Campaign {campaign.name} {'activated' if should_be_active else 'deactivated'}")

@shared_task
def reset_daily_spends() -> None:
    current_time = localtime(now())
    if current_time.hour != 0:
        logger.info("Not midnight, skipping daily reset")
        return
    logger.info(f"Running reset_daily_spends at {current_time}")
    with transaction.atomic():
        campaigns = Campaign.objects.select_related('brand').all()
        for campaign in campaigns:
            campaign.total_spend_today = 0.0
            campaign.is_active = (
                campaign.allowed_start_hour <= current_time.hour <= campaign.allowed_end_hour
                and campaign.total_spend_month < campaign.brand.monthly_budget
                and campaign.brand.current_monthly_spend < campaign.brand.monthly_budget
            )
            campaign.save()
            logger.info(f"Campaign {campaign.name} daily spend reset, is_active: {campaign.is_active}")
        Brand.objects.all().update(current_daily_spend=0.0)
        logger.info("All brand daily spends reset")

@shared_task
def reset_monthly_spends() -> None:
    current_time = localtime(now())
    if current_time.day != 1 or current_time.hour != 0:
        logger.info("Not first day of month at midnight, skipping monthly reset")
        return
    logger.info(f"Running reset_monthly_spends at {current_time}")
    with transaction.atomic():
        campaigns = Campaign.objects.select_related('brand').all()
        for campaign in campaigns:
            campaign.total_spend_month = 0.0
            campaign.is_active = (
                campaign.allowed_start_hour <= current_time.hour <= campaign.allowed_end_hour
                and campaign.total_spend_today < campaign.brand.daily_budget
                and campaign.brand.current_daily_spend < campaign.brand.daily_budget
            )
            campaign.save()
            logger.info(f"Campaign {campaign.name} monthly spend reset, is_active: {campaign.is_active}")
        Brand.objects.all().update(current_monthly_spend=0.0)
        logger.info("All brand monthly spends reset")