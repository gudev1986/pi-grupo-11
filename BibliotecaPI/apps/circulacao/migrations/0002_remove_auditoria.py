from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('circulacao', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Auditoria',
        ),
    ]