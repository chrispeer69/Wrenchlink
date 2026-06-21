from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from marketplace.models import CityPool, EmployerProfile, TechnicianProfile

from .models import User


class StyledFormMixin:
    def _style_fields(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            else:
                css_class = "form-input"
            field.widget.attrs.setdefault("class", css_class)


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "you@example.com",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].widget.attrs.update(
            {"autocomplete": "current-password", "placeholder": "Your password"}
        )
        self._style_fields()

    def clean(self):
        email = self.cleaned_data.get("username")
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if user:
                self.cleaned_data["username"] = user.username
        return super().clean()

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff and not user.email_verified:
            raise forms.ValidationError(
                "Verify your email before signing in.",
                code="email_not_verified",
            )


class TechnicianRegistrationForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField()
    city_pool = forms.ModelChoiceField(
        queryset=CityPool.objects.filter(is_active=True), required=False
    )
    professional_title = forms.CharField(max_length=150)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "professional_title",
            "city_pool",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "first_name": "First name",
            "last_name": "Last name",
            "email": "you@example.com",
            "professional_title": "e.g. Master Auto Technician",
            "password1": "Create a password",
            "password2": "Confirm your password",
        }
        for name, placeholder in placeholders.items():
            self.fields[name].widget.attrs["placeholder"] = placeholder
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"
        self._style_fields()

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already exists for this email.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.role = User.Role.TECHNICIAN
        if commit:
            user.save()
            TechnicianProfile.objects.create(
                user=user,
                city_pool=self.cleaned_data.get("city_pool"),
                professional_title=self.cleaned_data["professional_title"],
            )
        return user


class EmployerRegistrationForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField()
    company_name = forms.CharField(max_length=200)
    shop_type = forms.ChoiceField(choices=EmployerProfile.ShopType.choices)
    city_pool = forms.ModelChoiceField(
        queryset=CityPool.objects.filter(is_active=True), required=False
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "company_name",
            "shop_type",
            "city_pool",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "first_name": "Contact first name",
            "last_name": "Contact last name",
            "email": "hiring@yourshop.com",
            "company_name": "Shop or company name",
            "password1": "Create a password",
            "password2": "Confirm your password",
        }
        for name, placeholder in placeholders.items():
            self.fields[name].widget.attrs["placeholder"] = placeholder
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"
        self._style_fields()

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already exists for this email.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.role = User.Role.EMPLOYER
        if commit:
            user.save()
            EmployerProfile.objects.create(
                user=user,
                company_name=self.cleaned_data["company_name"],
                shop_type=self.cleaned_data["shop_type"],
                city_pool=self.cleaned_data.get("city_pool"),
            )
        return user
