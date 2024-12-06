from rest_framework import serializers

from code_review_backend.issues.models import IssueLink


class IssueLinkHashSerializer(serializers.ModelSerializer):
    """Serialize an Issue hash from the IssueLink M2M"""

    id = serializers.UUIDField(source="issue_id")
    hash = serializers.CharField(source="issue__hash", max_length=32)

    class Meta:
        model = IssueLink
        fields = ("id", "hash")
        read_only_fields = ("id", "hash")