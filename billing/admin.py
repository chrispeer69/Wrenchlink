from django.contrib import admin

from .models import Invoice, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "current_period_end")
    list_filter = ("plan", "status")
    search_fields = ("user__email", "stripe_customer_id", "stripe_subscription_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("stripe_invoice_id", "subscription", "amount_due", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("stripe_invoice_id", "subscription__user__email")
