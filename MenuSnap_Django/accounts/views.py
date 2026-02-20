import random
from datetime import timedelta
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PasswordResetOTP, User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RequestOtpSerializer,
    ResetPasswordSerializer,
    RestaurantRegisterSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    VerifyOTPSerializer,
)
from .tasks import send_otp_email

# Create your views here.


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully"})

        return Response(serializer.errors, status=400)


class RestaurantRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RestaurantRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "Restaurant registered successfully",
                "email": user.email,
                "restaurant": user.restaurant.name,
                "role": user.role,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response(
                {"detail": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        onboarding_completed = (
            user.restaurant.is_onboarding_completed if user.restaurant else False
        )

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["role"] = user.role
        refresh["is_onboarding_completed"] = onboarding_completed

        response = Response(
            {
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
        )

        return response


class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }

        google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
            params
        )

        return Response({"auth_url": google_auth_url})


class GoogleCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        code = request.GET.get("code")

        if not code:
            return Response(
                {"error": "Authorization code missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return Response(
                {"error": "Failed to fetch Google access token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_info = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()

        email = user_info.get("email")
        name = user_info.get("name")

        if not email:
            return Response(
                {"error": "Email not provided by Google"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "name": name or email.split("@")[0],
                "role": User.Role.RESTAURANT_ADMIN,
                "is_active": True,
            },
        )

        onboarding_completed = (
            user.restaurant.is_onboarding_completed if user.restaurant else False
        )

        refresh = RefreshToken.for_user(user)

        refresh["email"] = user.email
        refresh["role"] = user.role
        refresh["is_onboarding_completed"] = onboarding_completed

        frontend_callback_url = "http://localhost:5173/auth/google/callback"

        params = {
            "access": str(refresh.access_token),
            "onboarding_completed": str(onboarding_completed).lower(),
        }

        redirect_url = f"{frontend_callback_url}?{urlencode(params)}"
        response = redirect(redirect_url)

        # 🔐 Set refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
        )

        return response


class RefreshTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"detail": "No refresh token provided"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(refresh_token)
            access = str(refresh.access_token)

            return Response({"access": access}, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {"detail": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    def post(self, request):
        response = Response(
            {"detail": "Logged out successfully"}, status=status.HTTP_200_OK
        )
        response.delete_cookie("refresh_token")
        return response


class ChangePasswordview(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            request.user.set_password(serializer.validated_data["new_password"])
            request.user.save()
            return Response({"message": "Password Updated Successfully"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {"message": "If the email exists, an OTP has been sent."},
                status=status.HTTP_200_OK,
            )

        otp = str(random.randint(100000, 999999))
        expires = timezone.now() + timedelta(minutes=10)

        PasswordResetOTP.objects.create(user=user, otp=otp, expires_at=expires)

        send_otp_email.delay(user.email, otp)

        return Response({"message": "If the email exists, an OTP has been sent."})


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {"detail": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST
            )

        record = (
            PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not record:
            return Response({"detail": "Invalid OTP"}, status=400)

        if record.expires_at < timezone.now():
            return Response({"detail": "OTP expired"}, status=400)

        if record.attempts >= 5:
            return Response({"detail": "Too many attempts"}, status=400)

        record.is_verified = True
        record.save()

        return Response({"session_token": record.session_token})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["session_token"]
        password = serializer.validated_data["new_password"]

        record = PasswordResetOTP.objects.filter(
            session_token=token, is_verified=True, is_used=False
        ).first()

        if not record:
            return Response({"detail": "Invalid or expired session"}, status=400)

        user = record.user
        user.set_password(password)
        user.save()

        record.is_used = True
        record.save()

        return Response({"message": "Password reset successful"})
