from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return User.objects.all().order_by("-date_joined")
        if self.request.user.is_authenticated:
            return User.objects.filter(pk=self.request.user.pk)
        return User.objects.none()

def _username_for(email, name=""):
    base = "".join(c for c in (name or email.split("@")[0]).lower() if c.isalnum() or c in "._-")[:100] or "user"
    username = base
    i = 1
    while User.objects.filter(username=username).exists():
        i += 1
        username = f"{base}{i}"
    return username

@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def csrf(request):
    return JsonResponse({"ok": True})

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""
    name = (request.data.get("name") or "").strip()
    if not email or not password:
        return Response({"detail": "Email and password are required."}, status=400)
    if len(password) < 8:
        return Response({"detail": "Password must be at least 8 characters."}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({"detail": "An account with that email already exists."}, status=400)
    user = User.objects.create_user(
        username=_username_for(email, name),
        email=email,
        password=password,
        first_name=name,
        role=User.Role.CUSTOMER,
    )
    login(request, user)
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_view(request):
    identifier = (request.data.get("identifier") or request.data.get("email") or "").strip()
    password = request.data.get("password") or ""
    user = User.objects.filter(email=identifier.lower()).first() if "@" in identifier else None
    username = user.username if user else identifier
    authenticated = authenticate(request, username=username, password=password)
    if not authenticated:
        return Response({"detail": "Invalid email/username or password."}, status=400)
    login(request, authenticated)
    return Response(UserSerializer(authenticated).data)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"ok": True})

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)
