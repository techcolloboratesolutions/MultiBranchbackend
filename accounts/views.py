from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Role, User
from accounts.permissions import IsAdminRole
from accounts.serializers import (
    LoginSerializer,
    RoleSerializer,
    UserAdminSerializer,
    UserPublicSerializer,
)


def _token_payload(user: User):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserPublicSerializer(user).data,
    }


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(_token_payload(serializer.validated_data["user"]))


class LookupUserView(APIView):
    """Populate institution fields on the login screen after username is entered."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        username = (request.query_params.get("username") or "").strip()
        if not username:
            return Response({"detail": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
        user = (
            User.objects.select_related("institution", "institution__main_institution", "role")
            .filter(username__iexact=username)
            .first()
        )
        if user is None:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserPublicSerializer(user).data)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserPublicSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"detail": "Logged out."})


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.select_related("institution").all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminRole]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("institution", "role").all().order_by("username")
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdminRole]
