from django import forms
from .models import TestResult


class TestResultUploadForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = ["customer", "product", "appointment", "file", "result_summary", "test_date", "notes", "is_released"]
        widgets = {
            "test_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ResultLookupForm(forms.Form):
    phone_number = forms.CharField(label="Phone Number", max_length=20)
    access_code = forms.CharField(label="Result Code", max_length=12)

    def clean_access_code(self):
        return self.cleaned_data["access_code"].strip().upper()

    def clean_phone_number(self):
        # Loosely normalize: strip spaces/dashes so "0912 299 7406" and "09122997406" both match
        raw = self.cleaned_data["phone_number"]
        return "".join(ch for ch in raw if ch.isdigit())
