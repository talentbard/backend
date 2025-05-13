from django.urls import path
from .views import UserSignupView, UserLoginView, TokenRefreshView, UserProfileView, GoogleLoginSendOTP, VerifyOTPView

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='user_signup'),
    path('login/', UserLoginView.as_view(), name='user_login'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path("google-login/send-otp/", GoogleLoginSendOTP.as_view(), name="google_send_otp"),
    path("google-login/verify-otp/", VerifyOTPView.as_view(), name="google_verify_otp"),

]