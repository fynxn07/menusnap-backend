from django.urls import path

from .views import (
    ChangePasswordview,
    GoogleCallbackView,
    GoogleLoginView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    RequestOTPView,
    ResetPasswordView,
    RestaurantRegisterView,
    UserProfileView,
    VerifyOTPView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("change_password/", ChangePasswordview.as_view()),
    path("register/", RestaurantRegisterView.as_view(), name="register"),
    path("google/login/", GoogleLoginView.as_view()),
    path("google/callback/", GoogleCallbackView.as_view()),
    path("token_refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password_request-otp/", RequestOTPView.as_view()),
    path("password_verify-otp/", VerifyOTPView.as_view()),
    path("password_reset/", ResetPasswordView.as_view()),
]
