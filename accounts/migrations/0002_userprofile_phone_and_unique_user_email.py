# Generated manually for unique auth_user.email (MySQL) and UserProfile.phone_number

from django.db import migrations, models


def apply_mysql_unique_email(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != "mysql":
        return
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'auth_user'
              AND index_name = 'auth_user_email_uniq'
            """
        )
        if cursor.fetchone()[0]:
            return
        cursor.execute("ALTER TABLE auth_user MODIFY email VARCHAR(254) NULL")
        cursor.execute("UPDATE auth_user SET email = NULL WHERE email = ''")
        cursor.execute("CREATE UNIQUE INDEX auth_user_email_uniq ON auth_user (email)")


def reverse_mysql_unique_email(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != "mysql":
        return
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'auth_user'
              AND index_name = 'auth_user_email_uniq'
            """
        )
        if cursor.fetchone()[0]:
            cursor.execute("DROP INDEX auth_user_email_uniq ON auth_user")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="phone_number",
            field=models.CharField(
                blank=True,
                help_text="10-digit Indian mobile number (without +91).",
                max_length=10,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(apply_mysql_unique_email, reverse_mysql_unique_email),
    ]
