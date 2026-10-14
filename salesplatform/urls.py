
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.utils.html import escape


def robots_txt(request):
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "Disallow: /admin/\n"
        "Disallow: /accounts/\n"
        "Disallow: /dashboard/\n"
        "Disallow: /inventory/\n"
        "Disallow: /sales/\n"
        "Disallow: /customers/\n"
        "\n"
        "Sitemap: https://curexdiagnostics.com/sitemap.xml\n"
    )
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    urls = [
        "https://curexdiagnostics.com/",
        "https://curexdiagnostics.com/catalog/",
    ]

    entries = "\n".join(
        f"  <url><loc>{escape(url)}</loc></url>"
        for url in urls
    )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>"
    )

    return HttpResponse(xml, content_type="application/xml")


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("salesplatform.storefront_urls")),
    path("order/", include("orders.urls")),

    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("inventory/", include("inventory.urls")),
    path("sales/", include("sales.urls")),
    path("customers/", include("customers.urls")),
    path("whatsapp-bot/", include("whatsapp_bot.urls")),
    path("results/", include("results.urls")),
    path("content/", include("sitecontent.urls")),
    path("articles/", include("sitecontent.public_urls")),

    path("sitemap.xml", sitemap_xml, name="sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
