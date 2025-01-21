from ninja import NinjaAPI
from django.db import transaction
from django.shortcuts import get_object_or_404
from typing import List

from .models import ProvNode, ProvRelation

from schemas.provenance import (
    NodeCreate, NodeResponse,
    RelationCreate, RelationResponse,
    ProvenanceRecord, ProvenanceResponse
)

api = NinjaAPI(title="Provenance API")

@api.post("/nodes", response=NodeResponse)
def create_node(request, node_data: NodeCreate):
    """Create a new provenance node if it doesn't already exist"""
    node, created = ProvNode.objects.get_or_create(
        label=node_data.label,
        defaults={
            "node_type": node_data.node_type,
            "description": node_data.description,
            "metadata": node_data.metadata
        }
    )
    
    return NodeResponse(
        label=node.label,
        node_type=node.node_type,
        description=node.description,
        metadata=node.metadata,
        created_at=node.created_at
    )

@api.get("/nodes/{label}", response=NodeResponse)
def get_node(request, label: str):
    """Retrieve a node by its label"""
    node = get_object_or_404(ProvNode, label=label)
    return NodeResponse(
        label=node.label,
        node_type=node.node_type,
        description=node.description,
        metadata=node.metadata,
        created_at=node.created_at
    )

@api.post("/relations", response=RelationResponse)
def create_relation(request, relation_data: RelationCreate, run_id: str):
    """Create a new provenance relation between existing nodes"""
    subject = get_object_or_404(ProvNode, label=relation_data.subject_label)
    object = get_object_or_404(ProvNode, label=relation_data.object_label)
    
    relation = ProvRelation.objects.create(
        subject=subject,
        verb=relation_data.verb,
        object=object,
        run_id=run_id,
        start_time=relation_data.start_time,
        end_time=relation_data.end_time,
        metadata=relation_data.metadata
    )
    
    return RelationResponse(
        subject_label=subject.label,
        verb=relation.verb,
        object_label=object.label,
        run_id=relation.run_id,
        start_time=relation.start_time,
        end_time=relation.end_time,
        metadata=relation.metadata,
        created_at=relation.created_at
    )

@api.get("/relations", response=List[RelationResponse])
def get_relations(request, run_id: str):
    """Get all relations for a specific run_id"""
    relations = ProvRelation.objects.filter(run_id=run_id).order_by('created_at')
    
    return [
        RelationResponse(
            subject_label=r.subject.label,
            verb=r.verb,
            object_label=r.object.label,
            run_id=r.run_id,
            start_time=r.start_time,
            end_time=r.end_time,
            metadata=r.metadata,
            created_at=r.created_at
        )
        for r in relations
    ]

@api.post("/provenance", response=ProvenanceResponse)
@transaction.atomic
def create_provenance_record(request, record: ProvenanceRecord):
    """Create multiple nodes and relations in a single transaction"""
    # First create all nodes
    for node_data in record.nodes:
        ProvNode.objects.get_or_create(
            label=node_data.label,
            defaults={
                "node_type": node_data.node_type,
                "description": node_data.description,
                "metadata": node_data.metadata
            }
        )
    
    # Then create all relations
    created_relations = []
    for relation_data in record.relations:
        subject = get_object_or_404(ProvNode, label=relation_data.subject_label)
        object = get_object_or_404(ProvNode, label=relation_data.object_label)
        
        relation = ProvRelation.objects.create(
            subject=subject,
            verb=relation_data.verb,
            object=object,
            run_id=record.run_id,
            start_time=relation_data.start_time,
            end_time=relation_data.end_time,
            metadata=relation_data.metadata
        )
        created_relations.append(
            RelationResponse(
                subject_label=subject.label,
                verb=relation.verb,
                object_label=object.label,
                run_id=relation.run_id,
                start_time=relation.start_time,
                end_time=relation.end_time,
                metadata=relation.metadata,
                created_at=relation.created_at
            )
        )
    
    return ProvenanceResponse(relations=created_relations)