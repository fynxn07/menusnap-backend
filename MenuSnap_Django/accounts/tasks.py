from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from celery import shared_task

from .models import InactiveEmailLog, PasswordResetOTP, User


@shared_task
def send_otp_email(email, otp):
    send_mail(
        subject="Password Reset OTP",
        message=f"Your OTP is {otp}. It expires in 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


@shared_task
def send_inactive_user_reminders():
    cutoff = timezone.now() - timedelta(days=3)

    users = User.objects.filter(last_login__lt=cutoff, is_active=True)

    for user in users:

        last_email = (
            InactiveEmailLog.objects.filter(user=user).order_by("-sent_at").first()
        )

        if last_email and user.last_login and last_email.sent_at > user.last_login:
            continue

        send_mail(
            subject="We miss you!",
            message="You have not logged in for a while.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        InactiveEmailLog.objects.create(user=user)
