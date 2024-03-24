from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"),
    path("listing/<int:id>", views.auction, name="auction"),
    path("listing/<int:id>/bid", views.auction_placebid, name="auction_placebid"),
    path("listing/<int:id>/close", views.auction_close, name="auction_close"),
    path("listing/<int:id>/comment", views.auction_comment, name="auction_comment"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("watchlist/add", views.watchlist_add, name="watchlist_add"),
    path("watchlist/remove", views.watchlist_remove, name="watchlist_remove"),
    path("categories", views.categories, name="categories"),
    path("category/<int:id>", views.category, name="category"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)