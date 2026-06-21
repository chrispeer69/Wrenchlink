from django import forms
from django.core.exceptions import ValidationError

from .models import (
    ApplicationMessage,
    Certification,
    Education,
    EmployerProfile,
    EmployerReview,
    Job,
    NotificationPreference,
    ProfessionalReference,
    TechnicianDocument,
    TechnicianProfile,
    TechnicianReview,
    WorkHistory,
)


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(field.widget, forms.ClearableFileInput):
                css_class = "form-file-input"
            else:
                css_class = "form-input"
            field.widget.attrs.setdefault("class", css_class)


class TechnicianProfileForm(StyledModelForm):
    skills_text = forms.CharField(
        required=False,
        label="Skills",
        help_text="Comma-separated, for example: Diagnostics, ASE Master, ADAS",
    )

    class Meta:
        model = TechnicianProfile
        fields = (
            "professional_title",
            "city_pool",
            "bio",
            "phone",
            "years_experience",
            "availability",
            "preferred_schedule",
            "minimum_pay",
            "willing_to_relocate",
            "is_visible",
        )
        widgets = {"bio": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["skills_text"].initial = ", ".join(self.instance.skills)

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.skills = [
            item.strip()
            for item in self.cleaned_data.get("skills_text", "").split(",")
            if item.strip()
        ]
        if commit:
            profile.save()
        return profile


class EmployerProfileForm(StyledModelForm):
    perks_text = forms.CharField(
        required=False,
        label="Perks",
        help_text="Comma-separated",
    )

    class Meta:
        model = EmployerProfile
        fields = (
            "company_name",
            "shop_type",
            "city_pool",
            "description",
            "phone",
            "website",
            "address",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["perks_text"].initial = ", ".join(self.instance.perks)

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.perks = [
            item.strip()
            for item in self.cleaned_data.get("perks_text", "").split(",")
            if item.strip()
        ]
        if commit:
            profile.save()
        return profile


class NotificationPreferenceForm(StyledModelForm):
    class Meta:
        model = NotificationPreference
        fields = (
            "in_app_messages",
            "email_messages",
            "in_app_applications",
            "email_applications",
            "in_app_offers",
            "email_offers",
            "in_app_credentials",
            "email_credentials",
            "in_app_job_matches",
            "email_job_matches",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        labels = {
            "in_app_messages": "Messages",
            "email_messages": "Messages",
            "in_app_applications": "Application activity",
            "email_applications": "Application activity",
            "in_app_offers": "Invitations and offers",
            "email_offers": "Invitations and offers",
            "in_app_credentials": "Credential requests",
            "email_credentials": "Credential requests",
            "in_app_job_matches": "Matching jobs",
            "email_job_matches": "Matching jobs",
        }
        for name, label in labels.items():
            self.fields[name].label = label


class JobForm(StyledModelForm):
    benefits_text = forms.CharField(
        required=False,
        label="Benefits",
        help_text="Comma-separated, maximum 12 benefits.",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = Job
        fields = (
            "title",
            "city_pool",
            "category",
            "schedule",
            "pay_min",
            "pay_max",
            "experience_years",
            "certification_requirement",
            "description",
            "status",
        )
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 9,
                    "maxlength": 5000,
                    "placeholder": "Describe the work, team, tools, expectations, and what success looks like.",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["benefits_text"].initial = ", ".join(self.instance.benefits)

    def save(self, commit=True):
        job = super().save(commit=False)
        job.benefits = [
            item.strip()
            for item in self.cleaned_data.get("benefits_text", "").split(",")
            if item.strip()
        ]
        if commit:
            job.save()
        return job

    def clean(self):
        cleaned = super().clean()
        pay_min = cleaned.get("pay_min")
        pay_max = cleaned.get("pay_max")
        if pay_min is not None and pay_max is not None and pay_max < pay_min:
            self.add_error("pay_max", "Maximum pay must be at least the minimum pay.")
        return cleaned

    def clean_benefits_text(self):
        benefits = [
            item.strip()
            for item in self.cleaned_data.get("benefits_text", "").split(",")
            if item.strip()
        ]
        if len(benefits) > 12:
            raise ValidationError("List no more than 12 benefits.")
        if any(len(item) > 80 for item in benefits):
            raise ValidationError("Each benefit must be 80 characters or fewer.")
        return ", ".join(benefits)


class TechnicianDocumentForm(StyledModelForm):
    class Meta:
        model = TechnicianDocument
        fields = ("name", "file")

    def save(self, commit=True):
        document = super().save(commit=False)
        upload = self.cleaned_data["file"]
        document.content_type = getattr(upload, "content_type", "")
        document.file_size = upload.size
        if commit:
            document.save()
        return document


class CertificationForm(StyledModelForm):
    class Meta:
        model = Certification
        fields = (
            "name",
            "issuing_organization",
            "credential_id",
            "issued_date",
            "expiry_date",
            "file",
        )
        widgets = {
            "issued_date": forms.DateInput(attrs={"type": "date"}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        issued = cleaned.get("issued_date")
        expiry = cleaned.get("expiry_date")
        if issued and expiry and expiry < issued:
            self.add_error("expiry_date", "Expiry date cannot be before issue date.")
        return cleaned

    def save(self, commit=True):
        certification = super().save(commit=False)
        upload = self.cleaned_data.get("file")
        if upload:
            certification.content_type = getattr(upload, "content_type", "")
            certification.file_size = upload.size
        if commit:
            certification.save()
        return certification


class WorkHistoryForm(StyledModelForm):
    class Meta:
        model = WorkHistory
        fields = (
            "company",
            "role",
            "location",
            "start_date",
            "end_date",
            "description",
        )
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4, "maxlength": 1500}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date cannot be before start date.")
        return cleaned


class EducationForm(StyledModelForm):
    class Meta:
        model = Education
        fields = ("school", "program", "completion_year")

    def clean_completion_year(self):
        year = self.cleaned_data.get("completion_year")
        if year and not 1950 <= year <= 2100:
            raise ValidationError("Enter a year between 1950 and 2100.")
        return year


class ProfessionalReferenceForm(StyledModelForm):
    class Meta:
        model = ProfessionalReference
        fields = ("name", "relationship", "email", "phone")

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("email") and not cleaned.get("phone"):
            raise ValidationError("Add an email address or phone number.")
        return cleaned


class ApplicationMessageForm(StyledModelForm):
    class Meta:
        model = ApplicationMessage
        fields = ("body",)
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 3,
                    "maxlength": 600,
                    "placeholder": "Write a concise message (600 characters maximum).",
                }
            )
        }


RATING_CHOICES = [(value, f"{value} / 5") for value in range(1, 6)]


class TechnicianReviewForm(StyledModelForm):
    class Meta:
        model = TechnicianReview
        fields = ("skill", "reliability", "communication", "comment")
        widgets = {
            "skill": forms.Select(choices=RATING_CHOICES),
            "reliability": forms.Select(choices=RATING_CHOICES),
            "communication": forms.Select(choices=RATING_CHOICES),
            "comment": forms.Textarea(attrs={"rows": 4, "maxlength": 1000}),
        }


class EmployerReviewForm(StyledModelForm):
    class Meta:
        model = EmployerReview
        fields = ("professionalism", "communication", "workplace", "comment")
        widgets = {
            "professionalism": forms.Select(choices=RATING_CHOICES),
            "communication": forms.Select(choices=RATING_CHOICES),
            "workplace": forms.Select(choices=RATING_CHOICES),
            "comment": forms.Textarea(attrs={"rows": 4, "maxlength": 1000}),
        }
