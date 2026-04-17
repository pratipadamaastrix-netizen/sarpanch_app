from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from representatives import views as rep_views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("sarpanch-login/", rep_views.sarpanch_login_phone_view, name="sarpanch_login"),
    path(
        "sarpanch-login/verify/",
        rep_views.sarpanch_login_verify_view,
        name="sarpanch_login_verify",
    ),
    path(
        "sarpanch-login/resend/",
        rep_views.sarpanch_resend_otp_view,
        name="sarpanch_resend_otp",
    ),
    path("check-static/", views.check_static),
    path(
        "sarpanch/profile/",
        rep_views.sarpanch_update_profile_view,
        name="sarpanch_update_profile",
    ),
    path("sarpanch/logout/", rep_views.sarpanch_logout_view, name="sarpanch_logout"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),

    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),

    path(
        "change-password/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/change_password.html"
        ),
        name="change_password"
    ),
    path(
        "change-password/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/change_password_done.html"
        ),
        name="password_change_done"
    ),

    path("forgot-password/", views.password_reset_username_view, name="password_reset"),
    path(
        "forgot-password/email/",
        views.password_reset_email_view,
        name="password_reset_email",
    ),
    path(
        "forgot-password/verify/",
        views.password_reset_verify_view,
        name="password_reset_verify",
    ),
    path(
        "forgot-password/set-password/",
        views.password_reset_set_password_view,
        name="password_reset_set_password",
    ),
]