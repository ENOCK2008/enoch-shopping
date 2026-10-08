from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, csrf, register, login_view, logout_view, me

router = DefaultRouter()
router.register("", UserViewSet, basename="user")

urlpatterns = [
    path("csrf/", csrf),
    path("register/", register),
    path("login/", login_view),
    path("logout/", logout_view),
    path("me/", me),
    path("", include(router.urls)),
]
