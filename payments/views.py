import razorpay
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import Payment
from accounts.utils import ensure_user_profile


# ✅ CREATE ORDER / SHOW PAYMENT PAGE
@login_required
def payment_page(request):
    profile = ensure_user_profile(request.user)

    # 🔥 Prevent repeat payment
    if profile.is_paid_user or Payment.objects.filter(user=request.user, is_paid=True).exists():
        return redirect("dashboard")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    amount = 100  # ₹1 in paise

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    # Save order in DB
    Payment.objects.create(
        user=request.user,
        amount=amount,
        razorpay_order_id=order["id"],
        status="created",
        is_paid=False
    )

    return render(request, "payments/payment.html", {
        "order_id": order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": amount
    })


# ✅ PAYMENT SUCCESS (GET BASED)
@login_required
def payment_success(request):
    payment_id = request.GET.get("payment_id")

    # 🔥 Get latest payment record
    payment = Payment.objects.filter(user=request.user).last()

    if payment:
        payment.razorpay_payment_id = payment_id
        payment.status = "success"
        payment.is_paid = True
        payment.save()

        # 🔥 Mark user as paid
        profile = ensure_user_profile(request.user)
        profile.is_paid_user = True
        profile.save()

    return render(request, "payments/payment_success.html", {
        "payment_id": payment_id
    })


# ✅ PAYMENT FAILED
@login_required
def payment_failed(request):
    return render(request, "payments/payment_failed.html")