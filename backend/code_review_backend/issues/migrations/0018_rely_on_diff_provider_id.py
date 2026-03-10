# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.db import migrations, models
from django.db.models import F


def _update_provider_id(apps, schema_editor):
    """
    Update all diffs, setting the current ID as the provider ID.
    This step is required no to loose the Phabricator integer ID,
    which is the reference used by most developers.
    The previous value (PHID-DIFF-xxxxxxxxxxxxxxxxxxxx) is dropped,
    then the PK is replaced by a random UUID, allowing the support
    of other providers without a known unique integer identifier.
    """
    Diff = apps.get_model("issues", "Diff")
    Diff.objects.update(provider_id=F("id"))


def _reset_postgres_sequense(apps, schema_editor):
    """
    PostgreSQL needs to update the auto increment sequence value, otherwise
    conflicts would happen when we reach the initial Diff ID.

    This command was initially generated with ./manage.py sqlsequencereset issues
    """
    if schema_editor.connection.vendor != "postgresql":
        # The SQLite backend automatically handles the auto increment update
        return
    schema_editor.execute(
        """SELECT setval(
            pg_get_serial_sequence('"issues_diff"','id'),
            coalesce(max("id"), 1),
            max("id") IS NOT null
        ) FROM "issues_diff";
        """,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("issues", "0017_rename_phid_diff_provider_id"),
    ]

    operations = [
        # Save the Phabricator integer ID in Diff.provider_id
        migrations.RunPython(
            _update_provider_id,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="diff",
            name="id",
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterModelOptions(
            name="diff",
            options={"ordering": ("created",)},
        ),
        # Restore the sequence with PostgreSQL backend
        migrations.RunPython(
            _reset_postgres_sequense,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
