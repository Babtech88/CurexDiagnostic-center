import logging

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import staff_required, lab_required
from whatsapp_bot.services import WhatsAppSendError, send_whatsapp_text
from .forms import TestResultUploadForm, ResultLookupForm
from .models import TestResult

logger = logging.getLogger(__name__)


# ---------- Staff-facing ----------

@lab_required
def result_list(request):
    results = TestResult.objects.select_related("customer", "product").all()
    profile = getattr(request.user, "staff_profile", None)
    if profile and profile.role == "lab_tech" and not request.user.is_superuser:
        results = results.filter(uploaded_by=request.user)
    query = request.GET.get("q", "")
    if query:
        results = results.filter(customer__name__icontains=query)
    return render(request, "results/result_list.html", {"results": results, "query": query})


@lab_required
def result_upload(request):
    if request.method == "POST":
        form = TestResultUploadForm(request.POST, request.FILES)
        if form.is_valid():
            result = form.save(commit=False)
            result.uploaded_by = request.user
            result.save()
            messages.success(request, f"Result uploaded. Access code: {result.access_code}")
            return redirect("results:result_detail", pk=result.pk)
    else:
        form = TestResultUploadForm()
    return render(request, "results/result_form.html", {"form": form, "title": "Upload a Result"})


@lab_required
def result_detail(request, pk):
    result = get_object_or_404(TestResult, pk=pk)
    profile = getattr(request.user, "staff_profile", None)
    if profile and profile.role == "lab_tech" and result.uploaded_by_id not in (None, request.user.id):
        messages.error(request, "You can only access results in your laboratory workspace.")
        return redirect("results:result_list")
    return render(request, "results/result_detail.html", {"result": result})


@lab_required
def result_notify_patient(request, pk):
    result = get_object_or_404(TestResult, pk=pk)
    if not result.customer.phone_number:
        messages.error(request, "This patient has no phone number on file.")
        return redirect("results:result_detail", pk=pk)

    lookup_url = f"{settings.SITE_BASE_URL}/results/"
    message = (
        f"Hello {result.customer.name}, your result is ready at {settings.SITE_NAME}.\n\n"
        f"To view and print it, go to: {lookup_url}\n"
        f"Phone: {result.customer.phone_number}\n"
        f"Result Code: {result.access_code}\n\n"
        "Keep this code private - it's needed to access your result."
    )
    try:
        send_whatsapp_text(result.customer.phone_number, message)
        result.patient_notified_at = timezone.now()
        result.save(update_fields=["patient_notified_at"])
        messages.success(request, "Patient notified via WhatsApp.")
    except WhatsAppSendError:
        logger.error("Could not notify patient of result %s", pk)
        messages.error(request, "Could not send WhatsApp message — check the bot's connection.")

    return redirect("results:result_detail", pk=pk)


# ---------- Public-facing ----------

def result_lookup(request):
    result = None
    if request.method == "POST":
        form = ResultLookupForm(request.POST)
        if form.is_valid():
            phone_digits = form.cleaned_data["phone_number"]
            code = form.cleaned_data["access_code"]
            candidates = TestResult.objects.filter(access_code=code, is_released=True).select_related("customer")
            for candidate in candidates:
                stored_digits = "".join(ch for ch in candidate.customer.phone_number if ch.isdigit())
                # Compare last 10 digits so "08030000001" and "2348030000001" both match
                if stored_digits[-10:] == phone_digits[-10:] and phone_digits:
                    result = candidate
                    break
            if not result:
                messages.error(request, "No result found for that phone number and code. Please double-check and try again.")
    else:
        form = ResultLookupForm()

    return render(request, "results/lookup.html", {"form": form, "result": result})


def result_view_print(request, pk, access_code):
    result = get_object_or_404(TestResult, pk=pk, access_code=access_code, is_released=True)
    return render(request, "results/view_print.html", {"result": result})
