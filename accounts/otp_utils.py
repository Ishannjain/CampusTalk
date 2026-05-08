import random
import hashlib
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP

def generate_otp(user):
    """
    Generates a secure 6-digit numeric OTP, invalidates old ones,
    and stores the hash in the database.
    """
    # Invalidate old OTPs for this user
    OTP.objects.filter(user=user, is_used=False).update(is_used=True)
    
    # Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    
    # Securely hash the OTP
    otp_hash = hashlib.sha256(otp_code.encode()).hexdigest()
    
    # Set expiration (5 minutes)
    expires_at = timezone.now() + timedelta(minutes=5)
    
    # Store OTP record
    OTP.objects.create(
        user=user,
        otp_hash=otp_hash,
        expires_at=expires_at
    )
    
    return otp_code

def send_otp_email(user, otp_code):
    """
    Sends the OTP code to the user's email address.
    """
    subject = "Verify Your Email Address"
    greeting = f"Hello {user.first_name if user.first_name else user.username},"
    
    message = f"""{greeting}

Your verification code for CampusTalk is: {otp_code}

This OTP is valid for 5 minutes and can only be used once.

If you did not request this registration, please ignore this email.

Security notice: Never share your OTP with anyone.

Best regards,
CampusTalk Team
"""
    
    # You can also support HTML templates if configured in settings
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def verify_otp_code(user, otp_code):
    """
    Validates the OTP code provided by the user.
    Checks: Correct OTP, Not expired, Not previously used, and Attempt limits.
    """
    otp_record = OTP.objects.filter(user=user, is_used=False).first()
    
    if not otp_record:
        return False, "No active OTP found. Please request a new one."
    
    # Check rate limiting: max 5 attempts per OTP
    if otp_record.verification_attempts >= 5:
        otp_record.is_used = True
        otp_record.save()
        return False, "Too many failed attempts. This OTP is now invalid. Please request a new one."
    
    # Check expiration
    if timezone.now() > otp_record.expires_at:
        otp_record.is_used = True
        otp_record.save()
        return False, "OTP has expired. Please request a new one."
    
    # Verify hash
    provided_hash = hashlib.sha256(otp_code.encode()).hexdigest()
    
    otp_record.verification_attempts += 1
    otp_record.last_verification_attempt = timezone.now()
    
    if provided_hash == otp_record.otp_hash:
        otp_record.is_used = True
        otp_record.save()
        return True, "OTP verified successfully."
    else:
        otp_record.save()
        return False, f"Invalid OTP. {5 - otp_record.verification_attempts} attempts remaining."
