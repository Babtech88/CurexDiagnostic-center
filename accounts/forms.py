from django import forms
from django.contrib.auth.models import User
from .models import StaffProfile


class StaffCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=StaffProfile.ROLE_CHOICES)
    phone_number = forms.CharField(max_length=20, required=False)
    hire_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, allowed_roles=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_roles is not None:
            self.fields["role"].choices = [
                choice for choice in StaffProfile.ROLE_CHOICES if choice[0] in allowed_roles
            ]

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["username"],
            email=data.get("email", ""),
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )
        profile = StaffProfile.objects.create(
            user=user,
            role=data["role"],
            phone_number=data.get("phone_number", ""),
            hire_date=data.get("hire_date"),
        )
        return profile


class StaffEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    new_password = forms.CharField(
        required=False, widget=forms.PasswordInput,
        help_text="Leave blank to keep the current password.",
    )

    class Meta:
        model = StaffProfile
        fields = ["role", "phone_number", "hire_date", "is_active_staff", "notes", "photo"]
        widgets = {
            "hire_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user.first_name = self.cleaned_data["first_name"]
        profile.user.last_name = self.cleaned_data.get("last_name", "")
        profile.user.email = self.cleaned_data.get("email", "")
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            profile.user.set_password(new_password)
        if commit:
            profile.user.save()
            profile.save()
        return profile
