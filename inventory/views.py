from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import staff_required, manager_required
from .forms import ProductForm, CategoryForm, SupplierForm, PromotionForm, RestockForm
from .models import Product, Category, Supplier, Promotion, StockMovement


# ---------- Public storefront ----------

CATEGORY_ICONS = {
    "Haematology": "bi-droplet-half",
    "Clinical Chemistry": "bi-flask",
    "Blood Serology": "bi-shield-plus",
    "Microbiology & Parasitology": "bi-bug",
    "Semen Analysis": "bi-gender-male",
    "Skin Tests": "bi-bandaid",
    "Ultrasound Scan": "bi-soundwave",
    "Pregnancy Test": "bi-heart-pulse",
    "Hormonal Profiles": "bi-activity",
    "ECG": "bi-heart-pulse-fill",
    "Reagents & Kits": "bi-eyedropper",
    "Consumables": "bi-box-seam",
}
INTERNAL_ONLY_CATEGORIES = ["Reagents & Kits", "Consumables"]


SHOWCASE_SERVICES = [
    ("Blood Test", "Full Blood Count", "bi-droplet-half"),
    ("Urinalysis", "Urinalysis", "bi-eyedropper"),
    ("Ultrasound", "Obstetric Ultrasound Scan", "bi-soundwave"),
    ("ECG", "Pre-Exercise ECG", "bi-heart-pulse-fill"),
    ("Pregnancy Test", "Pregnancy Test (Urine)", "bi-heart-pulse"),
    ("Malaria Test", "Malaria Parasite", "bi-bug"),
]


def storefront_home(request):
    today = timezone.localdate()
    active_promotions = Promotion.objects.filter(
        is_active=True, start_date__lte=today, end_date__gte=today
    ).prefetch_related("products")
    featured_products = Product.objects.filter(is_active=True, promotions__in=active_promotions).distinct()[:12]

    billable_products = Product.objects.filter(is_active=True).exclude(category__name__in=INTERNAL_ONLY_CATEGORIES)
    popular_products = billable_products.order_by("name")[:8]
    total_tests = billable_products.count()

    categories = Category.objects.exclude(name__in=INTERNAL_ONLY_CATEGORIES).filter(products__is_active=True).distinct()
    categories_with_icons = [
        {"obj": c, "icon": CATEGORY_ICONS.get(c.name, "bi-clipboard2-pulse")} for c in categories
    ]

    showcase_services = []
    for label, search_term, icon in SHOWCASE_SERVICES:
        product = billable_products.filter(name__icontains=search_term).first()
        if product:
            showcase_services.append({"label": label, "product": product, "icon": icon})

    from sitecontent.models import Testimonial, Article

    testimonials = Testimonial.objects.filter(is_approved=True)[:9]
    articles = Article.objects.filter(is_published=True)[:3]

    return render(request, "storefront/home.html", {
        "promotions": active_promotions,
        "featured_products": featured_products,
        "popular_products": popular_products,
        "categories": categories_with_icons,
        "total_tests": total_tests,
        "total_categories": categories.count(),
        "showcase_services": showcase_services,
        "testimonials": testimonials,
        "articles": articles,
    })


def storefront_catalog(request):
    products = Product.objects.filter(is_active=True).exclude(
        category__name__in=INTERNAL_ONLY_CATEGORIES
    ).select_related("category")
    query = request.GET.get("q", "")
    category_id = request.GET.get("category", "")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        products = products.filter(category_id=category_id)
    categories = Category.objects.exclude(name__in=INTERNAL_ONLY_CATEGORIES).filter(
        products__is_active=True
    ).distinct().order_by("name")
    return render(request, "storefront/catalog.html", {
        "products": products, "categories": categories, "query": query, "category_id": category_id,
    })


def storefront_product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return render(request, "storefront/product_detail.html", {"product": product})


# ---------- Staff-facing inventory management ----------

@staff_required
def product_list(request):
    products = Product.objects.select_related("category", "supplier").all()
    query = request.GET.get("q", "")
    filter_type = request.GET.get("filter", "")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
    if filter_type == "low_stock":
        products = [p for p in products if p.is_low_stock]
    elif filter_type == "expiring":
        products = [p for p in products if p.is_expiring_soon or p.is_expired]
    return render(request, "inventory/product_list.html", {
        "products": products, "query": query, "filter_type": filter_type,
    })


@staff_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    movements = product.stock_movements.all()[:20]
    return render(request, "inventory/product_detail.html", {"product": product, "movements": movements})


@manager_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            StockMovement.objects.create(
                product=product, quantity_change=product.stock_quantity,
                reason=StockMovement.REASON_RESTOCK, note="Initial stock", created_by=request.user,
            )
            messages.success(request, "Product added.")
            return redirect("inventory:product_list")
    else:
        form = ProductForm()
    return render(request, "inventory/product_form.html", {"form": form, "title": "Add Product"})


@manager_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("inventory:product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "inventory/product_form.html", {"form": form, "title": f"Edit {product.name}"})


@manager_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("inventory:product_list")
    return render(request, "inventory/product_confirm_delete.html", {"product": product})


@staff_required
def product_restock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = RestockForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data["quantity"]
            product.stock_quantity += qty
            product.save(update_fields=["stock_quantity"])
            StockMovement.objects.create(
                product=product, quantity_change=qty, reason=StockMovement.REASON_RESTOCK,
                note=form.cleaned_data.get("note", ""), created_by=request.user,
            )
            messages.success(request, f"Added {qty} units to {product.name}.")
            return redirect("inventory:product_detail", pk=pk)
    else:
        form = RestockForm()
    return render(request, "inventory/restock_form.html", {"form": form, "product": product})


@staff_required
def alerts_view(request):
    products = Product.objects.filter(is_active=True)
    low_stock = [p for p in products if p.is_low_stock]
    expiring = [p for p in products if p.is_expiring_soon and not p.is_expired]
    expired = [p for p in products if p.is_expired]
    return render(request, "inventory/alerts.html", {
        "low_stock": low_stock, "expiring": expiring, "expired": expired,
    })


# ---------- Categories & Suppliers ----------

@manager_required
def category_list(request):
    categories = Category.objects.all()
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added.")
            return redirect("inventory:category_list")
    else:
        form = CategoryForm()
    return render(request, "inventory/category_list.html", {"categories": categories, "form": form})


@manager_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted.")
    return redirect("inventory:category_list")


@manager_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    if request.method == "POST":
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier added.")
            return redirect("inventory:supplier_list")
    else:
        form = SupplierForm()
    return render(request, "inventory/supplier_list.html", {"suppliers": suppliers, "form": form})


@manager_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        supplier.delete()
        messages.success(request, "Supplier deleted.")
    return redirect("inventory:supplier_list")


# ---------- Promotions (advertised sales) ----------

@manager_required
def promotion_list(request):
    promotions = Promotion.objects.all().prefetch_related("products")
    return render(request, "inventory/promotion_list.html", {"promotions": promotions})


@manager_required
def promotion_create(request):
    if request.method == "POST":
        form = PromotionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Promotion created and now advertised on the storefront.")
            return redirect("inventory:promotion_list")
    else:
        form = PromotionForm()
    return render(request, "inventory/promotion_form.html", {"form": form, "title": "New Promotion"})


@manager_required
def promotion_edit(request, pk):
    promotion = get_object_or_404(Promotion, pk=pk)
    if request.method == "POST":
        form = PromotionForm(request.POST, instance=promotion)
        if form.is_valid():
            form.save()
            messages.success(request, "Promotion updated.")
            return redirect("inventory:promotion_list")
    else:
        form = PromotionForm(instance=promotion)
    return render(request, "inventory/promotion_form.html", {"form": form, "title": f"Edit {promotion.title}"})


@manager_required
def promotion_delete(request, pk):
    promotion = get_object_or_404(Promotion, pk=pk)
    if request.method == "POST":
        promotion.delete()
        messages.success(request, "Promotion deleted.")
        return redirect("inventory:promotion_list")
    return render(request, "inventory/promotion_confirm_delete.html", {"promotion": promotion})
