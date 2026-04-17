import razorpay
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import Payment
from accounts.utils import ensure_user_profile


# CREATE ORDER
@login_required
def payment_page(request):
    profile = ensure_user_profile(request.user)

    if profile.is_paid_user:
        return redirect("dashboard")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    amount = 2000  # ₹20 in paise

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    # Save in DB
    payment = Payment.objects.create(
        user=request.user,
        amount=amount,
        razorpay_order_id=order["id"]
    )

    context = {
        "order_id": order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": amount
    }

    return render(request, "payments/payment.html", context)


# VERIFY PAYMENT
@login_required
def payment_success(request):
    if request.method == "POST":
        data = request.POST

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })

            payment = Payment.objects.get(razorpay_order_id=data['razorpay_order_id'])

            payment.razorpay_payment_id = data['razorpay_payment_id']
            payment.razorpay_signature = data['razorpay_signature']
            payment.status = "success"
            payment.save()

            # Mark user paid
            profile = ensure_user_profile(request.user)
            profile.is_paid_user = True
            profile.save()

            return render(request, "payments/payment_success.html")

        except:
            return redirect("payment_failed")

    return redirect("payment_page")


@login_required
def payment_failed(request):
    return render(request, "payments/payment_failed.html")