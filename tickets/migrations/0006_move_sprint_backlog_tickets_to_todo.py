from django.db import migrations


def forwards(apps, schema_editor):
    # Tickets already in a sprint shouldn't sit in "backlog": the board no longer
    # has that column, so they would disappear from it.
    Ticket = apps.get_model('tickets', 'Ticket')
    Ticket.objects.filter(sprint__isnull=False, status='backlog').update(status='todo')


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0005_alter_ticket_options'),
    ]

    operations = [
        # No reverse step: we can't know which tickets were "backlog" before.
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]