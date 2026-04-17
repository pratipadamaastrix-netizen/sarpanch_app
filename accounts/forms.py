import re

from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from locations.models import State, District, Constituency, Mandal, LocalBody
from representatives.otp import normalize_phone_digits

from .models import UserProfile


class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    middle_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )

    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        max_length=10,
        min_length=10,
        label="Mobile number",
        widget=forms.TextInput(
            attrs={
                "placeholder": "10 digits",
                "pattern": r"\d{10}",
                "inputmode": "numeric",
                "autocomplete": "tel",
            }
        ),
        help_text="Indian mobile: 10 digits (country code +91 is added automatically).",
    )

    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    state = forms.ModelChoiceField(
        queryset=State.objects.all().order_by("name"),
        empty_label="Select State"
    )
    district = forms.ModelChoiceField(
        queryset=District.objects.none(),
        empty_label="Select District"
    )
    constituency = forms.ModelChoiceField(
        queryset=Constituency.objects.none(),
        empty_label="Select Constituency"
    )
    mandal = forms.ModelChoiceField(
        queryset=Mandal.objects.none(),
        empty_label="Select Mandal"
    )
    local_body = forms.ModelChoiceField(
        queryset=LocalBody.objects.none(),
        empty_label="Select Village / Municipality"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        state_id = self.data.get("state") or self.initial.get("state")
        district_id = self.data.get("district") or self.initial.get("district")
        constituency_id = self.data.get("constituency") or self.initial.get("constituency")
        mandal_id = self.data.get("mandal") or self.initial.get("mandal")

        if state_id:
            try:
                self.fields["district"].queryset = District.objects.filter(
                    state_id=state_id
                ).order_by("name")
            except (ValueError, TypeError):
                pass

        if district_id:
            try:
                self.fields["constituency"].queryset = Constituency.objects.filter(
                    district_id=district_id
                ).order_by("name")
            except (ValueError, TypeError):
                pass

        if constituency_id:
            try:
                self.fields["mandal"].queryset = Mandal.objects.filter(
                    constituency_id=constituency_id
                ).order_by("name")
            except (ValueError, TypeError):
                pass

        if mandal_id:
            try:
                self.fields["local_body"].queryset = LocalBody.objects.filter(
                    mandal_id=mandal_id
                ).order_by("name")
            except (ValueError, TypeError):
                pass

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username already exists.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_phone_number(self):
        raw = self.cleaned_data.get("phone_number") or ""
        digits = normalize_phone_digits(raw)
        if len(digits) != 10 or not re.fullmatch(r"\d{10}", digits):
            raise ValidationError("Enter exactly 10 digits for your mobile number.")
        if UserProfile.objects.filter(phone_number=digits).exists():
            raise ValidationError("This mobile number is already registered.")
        return digits

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        state = cleaned_data.get("state")
        district = cleaned_data.get("district")
        constituency = cleaned_data.get("constituency")
        mandal = cleaned_data.get("mandal")
        local_body = cleaned_data.get("local_body")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        if state and district and district.state_id != state.id:
            self.add_error("district", "District does not belong to selected state.")

        if district and constituency and constituency.district_id != district.id:
            self.add_error("constituency", "Constituency does not belong to selected district.")

        if constituency and mandal and mandal.constituency_id != constituency.id:
            self.add_error("mandal", "Mandal does not belong to selected constituency.")

        if mandal and local_body and local_body.mandal_id != mandal.id:
            self.add_error("local_body", "Village / Municipality does not belong to selected mandal.")

        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput())


class EditProfileForm(forms.Form):
    email = forms.EmailField(required=True)

    phone_number = forms.CharField(
        max_length=10,
        min_length=10,
        label="Mobile number",
        widget=forms.TextInput(
            attrs={
                "placeholder": "10 digits",
                "pattern": r"\d{10}",
                "inputmode": "numeric",
                "autocomplete": "tel",
            }
        ),
    )

    first_name = forms.CharField(max_length=100)
    middle_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )

    state = forms.ModelChoiceField(
        queryset=State.objects.filter(is_active=True).order_by("name"),
        empty_label="Select State"
    )
    district = forms.ModelChoiceField(
        queryset=District.objects.none(),
        empty_label="Select District"
    )
    constituency = forms.ModelChoiceField(
        queryset=Constituency.objects.none(),
        empty_label="Select Constituency"
    )
    mandal = forms.ModelChoiceField(
        queryset=Mandal.objects.none(),
        empty_label="Select Mandal"
    )
    local_body = forms.ModelChoiceField(
        queryset=LocalBody.objects.none(),
        empty_label="Select Village / Municipality"
    )

    def __init__(self, *args, user=None, **kwargs):
        self._user = user
        super().__init__(*args, **kwargs)

        state_id = self.data.get("state") or self.initial.get("state")
        district_id = self.data.get("district") or self.initial.get("district")
        constituency_id = self.data.get("constituency") or self.initial.get("constituency")
        mandal_id = self.data.get("mandal") or self.initial.get("mandal")

        if state_id:
            try:
                self.fields["district"].queryset = District.objects.filter(
                    state_id=state_id,
                    is_active=True
                ).order_by("name")
            except (ValueError, TypeError):
                pass

        if district_id:
            try:
                self.fields["constituency"].queryset = Constituency.objects.filter(
                    district_id=district_id,
                    is_active=True
                ).order_by("name")
            except (ValueError, TypeError):
                pass

        if constituency_id:
            try:
                self.fields["mandal"].queryset = Mandal.objects.filter(
                    constituency_id=constituency_id,
                    is_active=True
                ).order_by("display_order", "name")
            except (ValueError, TypeError):
                pass

        if mandal_id:
            try:
                self.fields["local_body"].queryset = LocalBody.objects.filter(
                    mandal_id=mandal_id,
                    is_active=True
                ).order_by("name")
            except (ValueError, TypeError):
                pass

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise ValidationError("Email is required.")
        qs = User.objects.filter(email__iexact=email)
        if self._user:
            qs = qs.exclude(pk=self._user.pk)
        if qs.exists():
            raise ValidationError("This email is already in use by another account.")
        return email

    def clean_phone_number(self):
        raw = self.cleaned_data.get("phone_number") or ""
        digits = normalize_phone_digits(raw)
        if len(digits) != 10 or not re.fullmatch(r"\d{10}", digits):
            raise ValidationError("Enter exactly 10 digits for your mobile number.")
        qs = UserProfile.objects.filter(phone_number=digits)
        if self._user:
            qs = qs.exclude(user_id=self._user.pk)
        if qs.exists():
            raise ValidationError("This mobile number is already in use by another account.")
        return digits

    def clean(self):
        cleaned_data = super().clean()

        state = cleaned_data.get("state")
        district = cleaned_data.get("district")
        constituency = cleaned_data.get("constituency")
        mandal = cleaned_data.get("mandal")
        local_body = cleaned_data.get("local_body")

        if state and district and district.state_id != state.id:
            self.add_error("district", "District does not belong to selected state.")

        if district and constituency and constituency.district_id != district.id:
            self.add_error("constituency", "Constituency does not belong to selected district.")

        if constituency and mandal and mandal.constituency_id != constituency.id:
            self.add_error("mandal", "Mandal does not belong to selected mandal.")

        if mandal and local_body and local_body.mandal_id != mandal.id:
            self.add_error("local_body", "Village / Municipality does not belong to selected mandal.")

        return cleaned_data


class ForgotPasswordUsernameForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username")


class ForgotPasswordEmailForm(forms.Form):
    email = forms.EmailField(label="Email address")


class ForgotPasswordOTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        label="One-time password (OTP)",
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "one-time-code"}),
    )


class AppSetPasswordForm(SetPasswordForm):
    """Same as Django's SetPasswordForm; kept for a single import point."""

    pass