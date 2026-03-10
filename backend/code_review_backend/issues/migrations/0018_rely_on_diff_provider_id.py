# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import uuid

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
        # Create a field that will hold the new UUID PK
        migrations.AddField(
            model_name="diff",
            name="tmp_uuid",
            field=models.UUIDField(default=uuid.uuid4),
        ),
        # Switch the PK fields
        migrations.RemoveField("diff", "id"),
        migrations.RenameField(model_name="diff", old_name="tmp_uuid", new_name="id"),
        migrations.AlterField(
            model_name="diff",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, primary_key=True, serialize=False
            ),
        ),
        migrations.AlterModelOptions(
            name="diff",
            options={"ordering": ("created",)},
        ),
    ]
