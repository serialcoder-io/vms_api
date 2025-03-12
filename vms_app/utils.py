from django.contrib.auth.models import Group
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)
from .models import AuditTrail
from datetime import datetime, date
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def logs_audit_action(instance, action, description, user):
    """ log audit after create, update and delete and object in the database"""
    try:
        AuditTrail.objects.create(
            user=user,
            table_name=instance.__class__.__name__,
            object_id=instance.pk,
            description=description,
            action=action,
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'audit pour {instance}: {e}")


def validate_and_format_date(date_input):
    """
    Validate a date input and return it in the 'YYYY-MM-DD' format.
    The input can be a string (in various formats) or a datetime.date object.
    """
    if isinstance(date_input, (datetime, date)):
        # If the input is already a date or datetime object, just format it
        return date_input.strftime('%Y-%m-%d')

    # If the input is a string, try parsing it with different formats
    date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%d-%m-%y']

    for date_format in date_formats:
        try:
            # Attempt to parse the string using the current format
            parsed_date = datetime.strptime(date_input, date_format)
            # Return the date formatted as 'YYYY-MM-DD'
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            # Continue trying the next format
            continue

    # If none of the formats match, raise an error
    raise ValueError("The provided date is not in a valid format. "
                     "Expected formats: 'YYYY-MM-DD', 'DD-MM-YYYY', 'DD-MM-YY'.")

def get_approvers_emails():
    try:
        group = Group.objects.get(name='request_approver')  # Pas besoin de décomposer
        approvers = group.user_set.all()
        emails = [user.email for user in approvers]
        return emails if emails else []
    except Group.DoesNotExist:
        return []

def send_email_to_approvers(html_content, text_content):
    approvers_emails = get_approvers_emails()
    if approvers_emails:
        msg = EmailMultiAlternatives(
            "Approve voucher request",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            approvers_emails,
        )
        # add html version of the email
        msg.attach_alternative(html_content, "text/html")
        msg.send()


def get_greeting():
    current_hour = timezone.localtime(timezone.now()).hour
    if 5 <= current_hour < 12:
        return "Good Morning"
    elif 12 <= current_hour < 18:
        return "Good Afternoon"
    else:
        return "Good Evening"


def notify_requests_approvers(request_ref):
    """ this function emails all voucher_requests approvers after a request has been paid"""
    text_content = render_to_string(
        "emails/approve_request_email.txt",
        context={"request_ref": request_ref, "base_url": settings.BASE_URL, "greeting": get_greeting()},
    )
    html_content = render_to_string(
        "emails/approve_request_email.html",
        context={"request_ref": request_ref, "base_url": settings.BASE_URL, "greeting": get_greeting()},
    )
    send_email_to_approvers(html_content, text_content)
