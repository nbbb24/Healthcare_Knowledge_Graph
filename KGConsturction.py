"""
Knowledge Graph Integration Module - Step 3
===========================================

This module handles the creation and management of an integrated knowledge graph
that represents medical policies, criteria, and codes as connected entities.
It enables reuse of shared components across multiple policies.

Author: Policy Automation Pipeline
Date: 2025
"""

import networkx as nx
import json
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from collections import defaultdict, Counter
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GraphNode:
    """Represents a node in the knowledge graph"""
    id: str
    type: str  # 'Policy', 'Criterion', 'Code', 'Condition', 'Patient'
    properties: Dict[str, Any]
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

@dataclass
class GraphEdge:
    """Represents an edge/relationship in the knowledge graph"""
    source_id: str
    target_id: str
    relationship: str  # 'REQUIRES', 'SATISFIES', 'HAS_CONDITION', etc.
    properties: Dict[str, Any] = None
    created_at: str = ""
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class ComponentLibrary:
    """
    Library of reusable components for knowledge graph integration.
    
    Maintains an index of existing components to enable reuse across policies.
    """
    
    def __init__(self):
        self.components = {}  # signature -> component_id
        self.usage_tracking = defaultdict(list)  # component_id -> [policy_ids]
        self.component_types = defaultdict(set)  # type -> {component_ids}
    
    def register_component(self, component_id: str, component_type: str, 
                          signature: str, policy_id: str):
        """Register a component for potential reuse"""
        self.components[signature] = component_id
        self.usage_tracking[component_id].append(policy_id)
        self.component_types[component_type].add(component_id)
    
    def find_reusable_component(self, signature: str) -> Optional[str]:
        """Find existing component with matching signature"""
        return self.components.get(signature)
    
    def get_shared_components(self) -> Dict[str, List[str]]:
        """Get components used by multiple policies"""
        return {
            comp_id: policies 
            for comp_id, policies in self.usage_tracking.items() 
            if len(policies) > 1
        }
    
    def get_component_usage(self, component_id: str) -> List[str]:
        """Get list of policies using a component"""
        return self.usage_tracking[component_id].copy()

class KnowledgeGraphQuery:
    """Helper class for querying the knowledge graph"""
    
    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph
    
    def find_policies_for_patient(self, patient_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find all policies a patient might qualify for"""
        qualifying_policies = []
        
        # Get all policy nodes
        policy_nodes = [
            (node_id, data) for node_id, data in self.graph.nodes(data=True)
            if data.get('type') == 'Policy'
        ]
        
        for policy_id, policy_data in policy_nodes:
            # Check if patient meets all criteria for this policy
            criteria_met = self._check_policy_criteria(policy_id, patient_criteria)
            
            if criteria_met['eligible']:
                qualifying_policies.append({
                    'policy_id': policy_id,
                    'policy_name': policy_data.get('name', policy_id),
                    'criteria_met': criteria_met
                })
        
        return qualifying_policies
    
    def _check_policy_criteria(self, policy_id: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if patient meets all criteria for a specific policy"""
        # Get all criteria required by this policy
        required_criteria = list(self.graph.successors(policy_id))
        
        results = {
            'eligible': True,
            'satisfied_criteria': [],
            'failed_criteria': [],
            'total_criteria': len(required_criteria)
        }
        
        for criterion_id in required_criteria:
            criterion_data = self.graph.nodes[criterion_id]
            
            if criterion_data.get('type') == 'Criterion':
                criterion_met = self._evaluate_criterion(criterion_data, patient_data)
                
                if criterion_met:
                    results['satisfied_criteria'].append(criterion_id)
                else:
                    results['failed_criteria'].append(criterion_id)
                    results['eligible'] = False
        
        return results
    
    def _evaluate_criterion(self, criterion_data: Dict[str, Any], 
                          patient_data: Dict[str, Any]) -> bool:
        """Evaluate if patient meets a specific criterion"""
        criterion_type = criterion_data.get('criterion_type')
        field = criterion_data.get('field')
        operator = criterion_data.get('operator')
        value = criterion_data.get('value')
        
        if not all([field, operator, value is not None]):
            return False
        
        patient_value = patient_data.get(field)
        
        if patient_value is None:
            return False
        
        # Evaluate based on operator
        if operator == '>=':
            return patient_value >= value
        elif operator == '<=':
            return patient_value <= value
        elif operator == '==':
            return patient_value == value
        elif operator == 'in':
            return patient_value in value
        elif operator == 'contains_any':
            if isinstance(patient_value, list) and isinstance(value, list):
                return any(item in patient_value for item in value)
        
        return False
    
    def get_policy_explanation(self, policy_id: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed explanation of policy evaluation"""
        policy_data = self.graph.nodes.get(policy_id, {})
        criteria_check = self._check_policy_criteria(policy_id, patient_data)
        
        explanation = {
            'policy_name': policy_data.get('name', policy_id),
            'eligible': criteria_check['eligible'],
            'summary': f"Patient {'qualifies' if criteria_check['eligible'] else 'does not qualify'} for {policy_data.get('name', policy_id)}",
            'detailed_criteria': []
        }
        
        # Get detailed explanation for each criterion
        required_criteria = list(self.graph.successors(policy_id))
        
        for criterion_id in required_criteria:
            criterion_data = self.graph.nodes[criterion_id]
            
            if criterion_data.get('type') == 'Criterion':
                criterion_met = self._evaluate_criterion(criterion_data, patient_data)
                
                explanation['detailed_criteria'].append({
                    'criterion_id': criterion_id,
                    'description': criterion_data.get('description', ''),
                    'required_value': criterion_data.get('value'),
                    'patient_value': patient_data.get(criterion_data.get('field')),
                    'satisfied': criterion_met,
                    'status': '✓' if criterion_met else '✗'
                })
        
        return explanation
    
    def find_similar_policies(self, policy_id: str) -> List[Dict[str, Any]]:
        """Find policies with similar criteria"""
        target_criteria = set(self.graph.successors(policy_id))
        similar_policies = []
        
        # Get all other policies
        other_policies = [
            (node_id, data) for node_id, data in self.graph.nodes(data=True)
            if data.get('type') == 'Policy' and node_id != policy_id
        ]
        
        for other_policy_id, other_policy_data in other_policies:
            other_criteria =