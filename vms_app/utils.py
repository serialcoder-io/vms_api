from .models import AuditTrails
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