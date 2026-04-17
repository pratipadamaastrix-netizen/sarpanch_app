from django import forms

from .models import Representative


class SarpanchPhoneForm(forms.Form):
    mobile_number = forms.CharField(
        label="Mobile number",
        max_length=20,
        help_text="Enter the mobile number registered for your Gram Panchayat.",
    )


class SarpanchOtpForm(forms.Form):
    otp = forms.CharField(
        label="OTP",
        max_length=6,
        min_length=6,
        help_text="Enter the 6-digit code sent to your phone.",
    )


class SarpanchUpdateForm(forms.ModelForm):
    class Meta:
        model = Representative
        fields = ("photo", "age", "email")
        widgets = {
            "age": forms.NumberInput(attrs={"min": 1, "max": 120}),
            "email": forms.EmailInput(attrs={"placeholder": "Optional"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False
        self.fields["age"].required = True
        if self.instance and self.instance.pk and self.instance.photo:
            self.fields["photo"].required = False
        else:
            self.fields["photo"].required = True

    def clean_age(self):
        age = self.cleaned_data.get("age")
        if age is None:
            raise forms.ValidationError("Age is required.")
        if age < 1 or age > 120:
            raise forms.ValidationError("Enter a valid age.")
        return age
