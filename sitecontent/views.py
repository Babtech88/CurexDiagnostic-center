from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import StaffProfile
from accounts.permissions import staff_required, manager_required
from .forms import TestimonialForm, ArticleForm, StaffPublicProfileForm
from .models import Testimonial, Article, NewsletterSubscriber


# ---------- Public newsletter signup ----------

def newsletter_signup(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        next_url = request.POST.get("next") or "storefront:home"
        if email:
            _, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if created:
                messages.success(request, "Thanks for subscribing! We'll keep you posted on health tips and offers.")
            else:
                messages.info(request, "You're already subscribed — thanks for sticking with us!")
        else:
            messages.error(request, "Please enter a valid email address.")
        return redirect(next_url)
    return redirect("storefront:home")


# ---------- Public article browsing ----------

def article_public_list(request):
    articles = Article.objects.filter(is_published=True)
    return render(request, "sitecontent/public_article_list.html", {"articles": articles})


def article_public_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    return render(request, "sitecontent/public_article_detail.html", {"article": article})


# ---------- Testimonials ----------

@staff_required
def testimonial_list(request):
    testimonials = Testimonial.objects.all()
    return render(request, "sitecontent/testimonial_list.html", {"testimonials": testimonials})


@staff_required
def testimonial_create(request):
    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Testimonial added.")
            return redirect("sitecontent:testimonial_list")
    else:
        form = TestimonialForm()
    return render(request, "sitecontent/testimonial_form.html", {"form": form, "title": "Add Testimonial"})


@staff_required
def testimonial_edit(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if request.method == "POST":
        form = TestimonialForm(request.POST, request.FILES, instance=testimonial)
        if form.is_valid():
            form.save()
            messages.success(request, "Testimonial updated.")
            return redirect("sitecontent:testimonial_list")
    else:
        form = TestimonialForm(instance=testimonial)
    return render(request, "sitecontent/testimonial_form.html", {"form": form, "title": "Edit Testimonial"})


@staff_required
def testimonial_delete(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if request.method == "POST":
        testimonial.delete()
        messages.success(request, "Testimonial deleted.")
    return redirect("sitecontent:testimonial_list")


# ---------- Articles ----------

@staff_required
def article_list(request):
    articles = Article.objects.all()
    return render(request, "sitecontent/article_list.html", {"articles": articles})


@staff_required
def article_create(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Article saved.")
            return redirect("sitecontent:article_list")
    else:
        form = ArticleForm()
    return render(request, "sitecontent/article_form.html", {"form": form, "title": "Write Article"})


@staff_required
def article_edit(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Article updated.")
            return redirect("sitecontent:article_list")
    else:
        form = ArticleForm(instance=article)
    return render(request, "sitecontent/article_form.html", {"form": form, "title": "Edit Article"})


@staff_required
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        article.delete()
        messages.success(request, "Article deleted.")
    return redirect("sitecontent:article_list")


# ---------- Public staff profiles (Doctors/Specialists section) ----------

@manager_required
def staff_public_profiles(request):
    profiles = StaffProfile.objects.select_related("user").all()
    return render(request, "sitecontent/staff_public_list.html", {"profiles": profiles})


@manager_required
def staff_public_edit(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    if request.method == "POST":
        form = StaffPublicProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Public profile updated.")
            return redirect("sitecontent:staff_public_profiles")
    else:
        form = StaffPublicProfileForm(instance=profile)
    return render(request, "sitecontent/staff_public_form.html", {"form": form, "profile": profile})
