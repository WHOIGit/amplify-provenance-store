from django.db import models
from enum import Enum

from schemas.provenance import ProvType, ProvVerb


class ProvNode(models.Model):
    """Base model for all PROV nodes"""
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    label = models.CharField(max_length=255)
    node_type = models.CharField(
        max_length=50,
        choices=ProvType.choices(),
    )
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['node_type']),
            models.Index(fields=['label']),
        ]

    def __str__(self):
        return f"{self.node_type}: {self.label}"

class ProvRelation(models.Model):
    """Represents a relationship between two PROV nodes"""
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # The subject-verb-object triple
    subject = models.ForeignKey(
        ProvNode,
        on_delete=models.CASCADE,
        related_name='relations_as_subject'
    )
    verb = models.CharField(
        max_length=50,
        choices=ProvVerb.choices(),
    )
    object = models.ForeignKey(
        ProvNode,
        on_delete=models.CASCADE,
        related_name='relations_as_object'
    )
    
    # Optional attributes
    run_id = models.CharField(max_length=255, blank=True, db_index=True, help_text="Client-provided identifier for sorting and grouping relations")
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['verb']),
            models.Index(fields=['subject', 'verb']),
            models.Index(fields=['object', 'verb']),
            models.Index(fields=['run_id', '-created_at'], name='prov_relation_run_created'),
        ]
        # TODO: add semantic constraints

    def __str__(self):
        return f"{self.subject} {self.verb} {self.object}"

# Example usage in Django shell:
"""
# Create some nodes
entity = ProvNode.objects.create(
    label="Dataset123",
    node_type=ProvType.ENTITY.value,
    description="A research dataset"
)

activity = ProvNode.objects.create(
    label="DataAnalysis",
    node_type=ProvType.ACTIVITY.value,
    description="Analysis of Dataset123"
)

# Create a relationship
relation = ProvRelation.objects.create(
    subject=entity,
    verb=ProvVerb.WAS_GENERATED_BY.value,
    object=activity,
    run_id="experiment_123"
)

# Query for all entities generated by activities
generated_entities = ProvNode.objects.filter(
    relations_as_subject__verb=ProvVerb.WAS_GENERATED_BY.value,
    relations_as_subject__object__node_type=ProvType.ACTIVITY.value
)

# Query for all relations in a specific run
run_relations = ProvRelation.objects.filter(run_id='experiment_123').order_by('-created_at')
"""