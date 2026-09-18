
import logging

from botocore.exceptions import ClientError

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import lab_required
from whatsapp_bot.services import WhatsAppSendError, send_whatsapp_text

from .forms import TestResultUploadForm, ResultLookupForm
from .models import TestResult


logger = logging.getLogger(__name__)


# ============================================================
# STAFF-FACING
# ============================================================


@lab_required
def result_list(request):
    results = (
        TestResult.objects
        .select_related("customer", "product")
        .all()
    )

    profile = getattr(request.user, "staff_profile", None)

    if (
        profile
        and profile.role == "lab_tech"
        and not request.user.is_superuser
    ):
        results = results.filter(
            uploaded_by=request.user
        )

    query = request.GET.get("q", "").strip()

    if query:
        results = results.filter(
            customer__name__icontains=query
        )

    return render(
        request,
        "results/result_list.html",
        {
            "results": results,
            "query": query,
        },
    )


# ============================================================
# RESULT UPLOAD
# ============================================================


@lab_required
def result_upload(request):
    if request.method == "POST":
        form = TestResultUploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            result = form.save(commit=False)
            result.uploaded_by = request.user

            try:
                result.save()

            except ClientError as exc:
                error_response = (
                    getattr(exc, "response", {}) or {}
                )

                error = (
                    error_response.get("Error", {}) or {}
                )

                metadata = (
                    error_response.get(
                        "ResponseMetadata",
                        {},
                    )
                    or {}
                )

                logger.exception(
                    "SUPABASE S3 UPLOAD FAILED | "
                    "code=%r | message=%r | status=%r | "
                    "bucket=%r | key=%r",
                    error.get("Code"),
                    error.get("Message"),
                    metadata.get("HTTPStatusCode"),
                    getattr(
                        result.file.storage,
                        "bucket_name",
                        None,
                    ),
                    getattr(
                        result.file,
                        "name",
                        None,
                    ),
                )

                messages.error(
                    request,
                    "The result file could not be uploaded. "
                    "Please try again or contact the administrator.",
                )

                return render(
                    request,
                    "results/result_form.html",
                    {
                        "form": form,
                        "title": "Upload a Result",
                    },
                )

            messages.success(
                request,
                f"Result uploaded. Access code: "
                f"{result.access_code}",
            )

            return redirect(
                "results:result_detail",
                pk=result.pk,
            )

    else:
        form = TestResultUploadForm()

    return render(
        request,
        "results/result_form.html",
        {
            "form": form,
            "title": "Upload a Result",
        },
    )


# ============================================================
# RESULT DETAIL
# ============================================================


@lab_required
def result_detail(request, pk):
    result = get_object_or_404(
        TestResult,
        pk=pk,
    )

    profile = getattr(
        request.user,
        "staff_profile",
        None,
    )

    if (
        profile
        and profile.role == "lab_tech"
        and result.uploaded_by_id
        not in (None, request.user.id)
    ):
        messages.error(
            request,
            "You can only access results "
            "in your laboratory workspace.",
        )

        return redirect(
            "results:result_list"
        )

    return render(
        request,
        "results/result_detail.html",
        {
            "result": result,
        },
    )


# ============================================================
# NOTIFY PATIENT VIA WHATSAPP
# ============================================================


@lab_required
def result_notify_patient(request, pk):
    """
    Send a WhatsApp notification to the patient
    when their laboratory result is ready.

    SITE_NAME and SITE_BASE_URL are accessed safely
    with fallbacks so a missing deployment setting
    cannot cause an AttributeError.
    """

    result = get_object_or_404(
        TestResult,
        pk=pk,
    )

    # --------------------------------------------------------
    # Check patient phone number
    # --------------------------------------------------------

    patient_phone = (
        getattr(
            result.customer,
            "phone_number",
            "",
        )
        or ""
    ).strip()

    if not patient_phone:
        messages.error(
            request,
            "This patient has no phone number on file.",
        )

        return redirect(
            "results:result_detail",
            pk=pk,
        )

    # --------------------------------------------------------
    # Safe site configuration
    # --------------------------------------------------------

    site_name = getattr(
        settings,
        "SITE_NAME",
        "Curex Diagnostic Centre",
    )

    site_base_url = getattr(
        settings,
        "SITE_BASE_URL",
        "https://curex-diagnostic-center.vercel.app",
    )

    site_name = str(site_name).strip()

    site_base_url = (
        str(site_base_url)
        .strip()
        .rstrip("/")
    )

    # Prevent an empty environment variable
    # from producing a broken URL or message.
    if not site_name:
        site_name = "Curex Diagnostic Centre"

    if not site_base_url:
        site_base_url = (
            "https://curex-diagnostic-center.vercel.app"
        )

    lookup_url = (
        f"{site_base_url}/results/"
    )

    # --------------------------------------------------------
    # Build WhatsApp message
    # --------------------------------------------------------

    patient_name = (
        getattr(
            result.customer,
            "name",
            "",
        )
        or "Patient"
    ).strip()

    access_code = (
        getattr(
            result,
            "access_code",
            "",
        )
        or ""
    ).strip()

    message = (
        f"Hello {patient_name}, "
        f"your result is ready at {site_name}.\n\n"
        f"To view and print your result, go to:\n"
        f"{lookup_url}\n\n"
        f"Phone: {patient_phone}\n"
        f"Result Code: {access_code}\n\n"
        "Keep this code private - it is needed "
        "to access your result."
    )

    # --------------------------------------------------------
    # Send WhatsApp message
    # --------------------------------------------------------

    try:
        send_whatsapp_text(
            patient_phone,
            message,
        )

        # Only mark the patient as notified
        # after WhatsApp sending succeeds.
        result.patient_notified_at = timezone.now()

        result.save(
            update_fields=[
                "patient_notified_at",
            ],
        )

        messages.success(
            request,
            "Patient notified via WhatsApp.",
        )

    except WhatsAppSendError:
        logger.exception(
            "WHATSAPP NOTIFICATION FAILED | result_id=%s",
            pk,
        )

        messages.error(
            request,
            "Could not send WhatsApp message — "
            "check the bot's connection.",
        )

    except Exception:
        # Protect the staff dashboard from an unexpected
        # WhatsApp/provider exception.
        logger.exception(
            "UNEXPECTED WHATSAPP ERROR | result_id=%s",
            pk,
        )

        messages.error(
            request,
            "An unexpected error occurred while "
            "sending the WhatsApp notification.",
        )

    # --------------------------------------------------------
    # Return to result detail
    # --------------------------------------------------------

    return redirect(
        "results:result_detail",
        pk=pk,
    )


# ============================================================
# PUBLIC RESULT LOOKUP
# ============================================================


def result_lookup(request):
    result = None

    if request.method == "POST":
        form = ResultLookupForm(
            request.POST
        )

        if form.is_valid():
            phone_digits = (
                form.cleaned_data[
                    "phone_number"
                ]
            )

            code = (
                form.cleaned_data[
                    "access_code"
                ]
            )

            candidates = (
                TestResult.objects
                .filter(
                    access_code=code,
                    is_released=True,
                )
                .select_related("customer")
            )

            for candidate in candidates:

                stored_phone = (
                    getattr(
                        candidate.customer,
                        "phone_number",
                        "",
                    )
                    or ""
                )

                stored_digits = "".join(
                    ch
                    for ch in stored_phone
                    if ch.isdigit()
                )

                # Compare last 10 digits so:
                #
                # 08030000001
                #
                # and
                #
                # 2348030000001
                #
                # can match.
                if (
                    phone_digits
                    and stored_digits[-10:]
                    == phone_digits[-10:]
                ):
                    result = candidate
                    break

            if not result:
                messages.error(
                    request,
                    "No result found for that phone "
                    "number and code. "
                    "Please double-check and try again.",
                )

    else:
        form = ResultLookupForm()

    return render(
        request,
        "results/lookup.html",
        {
            "form": form,
            "result": result,
        },
    )


# ============================================================
# PUBLIC RESULT VIEW / PRINT
# ============================================================


def result_view_print(
    request,
    pk,
    access_code,
):
    result = get_object_or_404(
        TestResult,
        pk=pk,
        access_code=access_code,
        is_released=True,
    )

    return render(
        request,
        "results/view_print.html",
        {
            "result": result,
        },
    )
