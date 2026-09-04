from django import forms
from django.core.validators import RegexValidator

from .models import FreeBookDownload


phone_validator = RegexValidator(
    regex=r"^\+?[0-9][0-9\s().-]{6,24}$",
    message="Enter a valid phone number, including the country code where possible.",
)


class FreeBookDownloadForm(forms.ModelForm):
    phone = forms.CharField(max_length=30, validators=[phone_validator])
    privacy_consent = forms.BooleanField(
        required=True,
        label=(
            "I understand that my name, email address, and phone number will be "
            "recorded so Awakening Saints can manage this free download."
        ),
    )
    marketing_consent = forms.BooleanField(
        required=False,
        label="I would also like to receive occasional updates from Awakening Saints.",
    )

    class Meta:
        model = FreeBookDownload
        fields = (
            "full_name",
            "email",
            "phone",
            "privacy_consent",
            "marketing_consent",
        )
        widgets = {
            "full_name": forms.TextInput(
                attrs={"autocomplete": "name", "placeholder": "Your full name"}
            ),
            "email": forms.EmailInput(
                attrs={"autocomplete": "email", "placeholder": "you@example.com"}
            ),
            "phone": forms.TextInput(
                attrs={
                    "autocomplete": "tel",
                    "inputmode": "tel",
                    "placeholder": "+256 700 000000",
                }
            ),
        }

    def clean_full_name(self):
        return " ".join(self.cleaned_data["full_name"].split())

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_phone(self):
        return " ".join(self.cleaned_data["phone"].split())
