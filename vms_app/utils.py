from .models import AuditTrails
from datetime import datetime, date


def logs_audit_action(instance, action, description, user):
    try:
        AuditTrails.objects.create(
            user=user,
            table_name=instance.__class__.__name__,
            object_id=instance.pk,
            description=description,
            action=action,
        )
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'audit: {e}")


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


