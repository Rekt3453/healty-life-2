# Manual migration to add medicamentos, estudios, reposo columns to consultas_medicas

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('citas', '0009_alter_consultamedica_options_alter_factura_options'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE consultas_medicas
                ADD COLUMN IF NOT EXISTS medicamentos TEXT,
                ADD COLUMN IF NOT EXISTS estudios TEXT,
                ADD COLUMN IF NOT EXISTS reposo TEXT;
            """,
            reverse_sql="""
                ALTER TABLE consultas_medicas
                DROP COLUMN IF EXISTS medicamentos,
                DROP COLUMN IF EXISTS estudios,
                DROP COLUMN IF EXISTS reposo;
            """,
        ),
    ]
