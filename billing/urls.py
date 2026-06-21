from django.urls import path

from . import views


app_name = "billing"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("checkout/", views.create_checkout, name="checkout"),
    path("portal/", views.customer_portal, name="portal"),
    path("webhook/", views.webhook, name="webhook"),
]
