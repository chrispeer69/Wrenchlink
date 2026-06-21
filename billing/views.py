from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Invoice, Subscription


stripe.api_key = settings.STRIPE_SECRET_KEY


def _price_map():
    return {
        "solo": settings.STRIPE_TECH_PRICE_ID,
        "starter": settings.STRIPE_STARTER_PRICE_ID,
        "pro": settings.STRIPE_PRO_PRICE_ID,
    }


@login_required
def overview(request):
    subscription = getattr(request.user, "subscription", None)
    invoices = subscription.invoices.all() if subscription else []
    return render(
        request,
        "billing/overview.html",
        {
            "subscription": subscription,
            "invoices": invoices,
            "stripe_enabled": bool(settings.STRIPE_SECRET_KEY),
        },
    )


@login_required
@require_POST
def create_checkout(request):
    plan = request.POST.get("plan", "")
    price_id = _price_map().get(plan)
    if not settings.STRIPE_SECRET_KEY or not price_id:
        messages.error(request, "This plan is not configured for checkout.")
        return redirect("billing:overview")
    if request.user.role == "technician" and plan != "solo":
        return HttpResponseBadRequest("Invalid plan for this account.")
    if request.user.role == "employer" and plan not in {"starter", "pro"}:
        return HttpResponseBadRequest("Invalid plan for this account.")

    subscription, _ = Subscription.objects.get_or_create(
        user=request.user, defaults={"plan": plan}
    )
    customer_id = subscription.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(
            email=request.user.email,
            name=request.user.get_full_name() or request.user.email,
            metadata={"wrenchlink_user_id": request.user.pk},
        )
        customer_id = customer.id
        subscription.stripe_customer_id = customer_id
        subscription.plan = plan
        subscription.save(update_fields=["stripe_customer_id", "plan", "updated_at"])

    success_url = request.build_absolute_uri(reverse("billing:overview")) + "?checkout=success"
    cancel_url = request.build_absolute_uri(reverse("billing:overview"))
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(request.user.pk),
        metadata={"wrenchlink_user_id": request.user.pk, "plan": plan},
    )
    return redirect(session.url, permanent=False)


@login_required
@require_POST
def customer_portal(request):
    subscription = getattr(request.user, "subscription", None)
    if not subscription or not subscription.stripe_customer_id:
        messages.error(request, "No Stripe billing account exists yet.")
        return redirect("billing:overview")
    session = stripe.billing_portal.Session.create(
        customer=subscription.stripe_customer_id,
        return_url=request.build_absolute_uri(reverse("billing:overview")),
    )
    return redirect(session.url, permanent=False)


def _as_datetime(timestamp):
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp, tz=dt_timezone.utc)


def _sync_subscription(stripe_subscription):
    customer_id = stripe_subscription.get("customer")
    subscription = Subscription.objects.filter(stripe_customer_id=customer_id).first()
    if not subscription:
        return
    metadata = stripe_subscription.get("metadata") or {}
    subscription.stripe_subscription_id = stripe_subscription.get("id")
    subscription.status = stripe_subscription.get("status", Subscription.Status.INCOMPLETE)
    subscription.plan = metadata.get("plan") or subscription.plan
    subscription.current_period_end = _as_datetime(
        stripe_subscription.get("current_period_end")
    )
    subscription.cancel_at_period_end = stripe_subscription.get(
        "cancel_at_period_end", False
    )
    subscription.save()


def _sync_invoice(stripe_invoice):
    customer_id = stripe_invoice.get("customer")
    subscription = Subscription.objects.filter(stripe_customer_id=customer_id).first()
    if not subscription:
        return
    Invoice.objects.update_or_create(
        stripe_invoice_id=stripe_invoice["id"],
        defaults={
            "subscription": subscription,
            "amount_due": Decimal(str(stripe_invoice.get("amount_due", 0))) / 100,
            "currency": stripe_invoice.get("currency", "usd").upper(),
            "status": stripe_invoice.get("status", "unknown"),
            "hosted_invoice_url": stripe_invoice.get("hosted_invoice_url") or "",
            "invoice_pdf": stripe_invoice.get("invoice_pdf") or "",
            "created_at": _as_datetime(stripe_invoice.get("created")),
        },
    )


@csrf_exempt
@require_POST
def webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponseBadRequest("Stripe webhook is not configured.")
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.headers.get("Stripe-Signature", ""),
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponseBadRequest("Invalid webhook.")

    event_type = event["type"]
    payload = event["data"]["object"]
    if event_type.startswith("customer.subscription."):
        _sync_subscription(payload)
    elif event_type.startswith("invoice."):
        _sync_invoice(payload)
    return HttpResponse(status=200)
