import networkx as nx
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class NodeType(Enum):
    POLICY = "Policy"
    CRITERION = "Criterion"
    MEDICAL_CODE = "MedicalCode"
    PATIENT = "Patient"

class RelationType(Enum):
    REQUIRES = "requires"
    HAS = "has"
    QUALIFIES_FOR = "qualifies_for"
    SUPPORTS = "supports"

@dataclass
class GraphNode:
    id: str
    type: NodeType
    properties: Dict[str, Any]

@dataclass
class GraphEdge:
    source: str
    target: str
    relation: RelationType
    properties: Dict[str, Any] = None

class GenericKnowledgeGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes = {}
        self.medical_code_mapper = MedicalCodeMapper()
    
    def build_graph_from_policy(self, policy_data: Dict[str, Any]) -> nx.DiGraph:
        """Build knowledge graph from any policy data structure"""
        
        # Clear existing graph
        self.graph.clear()
        self.nodes.clear()
        
        # Add policy node
        policy_node = self._create_policy_node(policy_data)
        self._add_node(policy_node)
        
        # Add criterion nodes and connect to policy
        for criterion in policy_data.get("criteria", []):
            criterion_node = self._create_criterion_node(criterion)
            self._add_node(criterion_node)
            
            # Connect policy to criterion
            self._add_edge(GraphEdge(
                source=policy_node.id,
                target=criterion_node.id,
                relation=RelationType.REQUIRES
            ))
            
            # Add related medical codes if any
            self._add_medical_code_nodes(criterion, criterion_node.id)
        
        return self.graph
    
    def _create_policy_node(self, policy_data: Dict[str, Any]) -> GraphNode:
        return GraphNode(
            id=f"policy_{policy_data['policy_name'].lower().replace(' ', '_')}",
            type=NodeType.POLICY,
            properties={
                "name": policy_data["policy_name"],
                "total_criteria": policy_data.get("total_criteria", 0),
                "policy_type": "medical_approval"
            }
        )
    
    def _create_criterion_node(self, criterion) -> GraphNode:
        return GraphNode(
            id=f"criterion_{criterion.field_name}",
            type=NodeType.CRITERION,
            properties={
                "field_name": criterion.field_name,
                "operator": criterion.operator,
                "value": criterion.value,
                "description": criterion.description,
                "computable_rule": self._generate_computable_rule(criterion)
            }
        )
    
    def _generate_computable_rule(self, criterion) -> str:
        """Generate SQL-like computable rule from criterion"""
        if criterion.operator == ">=":
            return f"{criterion.field_name} >= {criterion.value}"
        elif criterion.operator == "==":
            return f"{criterion.field_name} = {criterion.value}"
        elif criterion.operator == "in":
            values = ', '.join([f"'{v}'" for v in criterion.value])
            return f"{criterion.field_name} IN ({values})"
        elif criterion.operator == "composite":
            # Handle complex BMI + comorbidity logic
            if "bmi_threshold" in criterion.value:
                bmi_thresh = criterion.value["bmi_threshold"]
                return f"(patient_bmi >= 40) OR (patient_bmi >= {bmi_thresh} AND comorbidity_flag = 1)"
        return f"{criterion.field_name} {criterion.operator} {criterion.value}"
    
    def _add_medical_code_nodes(self, criterion, criterion_node_id: str):
        """Add medical code nodes for procedures, diagnoses, etc."""
        
        # Add procedure codes
        if criterion.field_name == "procedure_code" and criterion.operator == "in":
            for code in criterion.value:
                code_description = self.medical_code_mapper.get_cpt_description(code)
                code_node = GraphNode(
                    id=f"cpt_{code}",
                    type=NodeType.MEDICAL_CODE,
                    properties={
                        "code": code,
                        "code_type": "CPT",
                        "description": code_description,
                        "category": "procedure"
                    }
                )
                self._add_node(code_node)
                
                # Connect criterion to code
                self._add_edge(GraphEdge(
                    source=criterion_node_id,
                    target=code_node.id,
                    relation=RelationType.SUPPORTS
                ))
        
        # Add comorbidity mappings
        if "comorbidity" in criterion.field_name:
            comorbidity_codes = self.medical_code_mapper.get_common_comorbidity_codes()
            for condition, icd_codes in comorbidity_codes.items():
                for icd_code in icd_codes:
                    code_node = GraphNode(
                        id=f"icd_{icd_code.replace('.', '_')}",
                        type=NodeType.MEDICAL_CODE,
                        properties={
                            "code": icd_code,
                            "code_type": "ICD-10",
                            "description": f"{condition} - {icd_code}",
                            "category": "diagnosis"
                        }
                    )
                    self._add_node(code_node)
                    
                    self._add_edge(GraphEdge(
                        source=code_node.id,
                        target=criterion_node_id,
                        relation=RelationType.SUPPORTS
                    ))
    
    def _add_node(self, node: GraphNode):
        self.graph.add_node(node.id, type=node.type.value, **node.properties)
        self.nodes[node.id] = node
    
    def _add_edge(self, edge: GraphEdge):
        props = edge.properties or {}
        self.graph.add_edge(edge.source, edge.target, relation=edge.relation.value, **props)
    
    def add_patient_node(self, patient_data: Dict[str, Any]) -> str:
        """Add a patient node and connect to relevant medical codes"""
        patient_id = f"patient_{patient_data.get('patient_id', 'unknown')}"
        
        patient_node = GraphNode(
            id=patient_id,
            type=NodeType.PATIENT,
            properties=patient_data
        )
        self._add_node(patient_node)
        
        # Connect patient to their procedure codes
        if "procedure_code" in patient_data:
            proc_code = patient_data["procedure_code"]
            cpt_node_id = f"cpt_{proc_code}"
            if cpt_node_id in self.nodes:
                self._add_edge(GraphEdge(
                    source=patient_id,
                    target=cpt_node_id,
                    relation=RelationType.HAS
                ))
        
        # Connect patient to their diagnosis codes
        if "diagnosis_codes" in patient_data:
            for diag_code in patient_data["diagnosis_codes"]:
                icd_node_id = f"icd_{diag_code.replace('.', '_')}"
                if icd_node_id in self.nodes:
                    self._add_edge(GraphEdge(
                        source=patient_id,
                        target=icd_node_id,
                        relation=RelationType.HAS
                    ))
        
        return patient_id
    
    def get_policy_paths_for_patient(self, patient_id: str) -> List[List[str]]:
        """Get all paths from patient to policy nodes"""
        policy_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Policy']
        paths = []
        
        for policy_node in policy_nodes:
            try:
                patient_paths = list(nx.all_simple_paths(
                    self.graph, 
                    source=patient_id, 
                    target=policy_node, 
                    cutoff=4
                ))
                paths.extend(patient_paths)
            except nx.NetworkXNoPath:
                continue
        
        return paths
    
    def export_graph_data(self) -> Dict[str, Any]:
        """Export graph for visualization or storage"""
        nodes_data = []
        edges_data = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            nodes_data.append({
                "id": node_id,
                "type": node_data.get("type"),
                "properties": {k: v for k, v in node_data.items() if k != "type"}
            })
        
        for source, target, edge_data in self.graph.edges(data=True):
            edges_data.append({
                "source": source,
                "target": target,
                "relation": edge_data.get("relation"),
                "properties": {k: v for k, v in edge_data.items() if k != "relation"}
            })
        
        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "statistics": {
                "total_nodes": len(nodes_data),
                "total_edges": len(edges_data),
                "node_types": list(set([n["type"] for n in nodes_data])),
                "relation_types": list(set([e["relation"] for e in edges_data]))
            }
        }

class MedicalCodeMapper:
    """Handles mapping clinical terms to standard medical codes"""
    
    def __init__(self):
        # In a real implementation, these would come from APIs or databases
        self.cpt_codes = {
            "43644": "Laparoscopic Roux-en-Y gastric bypass",
            "43775": "Laparoscopic sleeve gastrectomy",
            "43770": "Laparoscopic adjustable gastric banding",
            "43845": "Biliopancreatic diversion with duodenal switch",
            "33533": "Coronary artery bypass",
            "33510": "Aortic valve replacement",
            "47562": "Laparoscopic cholecystectomy"
        }
        
        self.comorbidity_mappings = {
            "diabetes": ["E11.9", "E10.9"],
            "hypertension": ["I10"],
            "sleep_apnea": ["G47.33"],
            "cardiovascular_disease": ["I25.9"],
            "cardiomyopathy": ["I42.9"]
        }
    
    def get_cpt_description(self, code: str) -> str:
        return self.cpt_codes.get(code, f"CPT {code} - Description not available")
    
    def get_common_comorbidity_codes(self) -> Dict[str, List[str]]:
        return self.comorbidity_mappings
    
    def map_clinical_term_to_codes(self, term: str, code_type: str = "both") -> Dict[str, List[str]]:
        """Map clinical terms to medical codes"""
        results = {"CPT": [], "ICD-10": []}
        
        term_lower = term.lower()
        
        # Search CPT codes
        if code_type in ["CPT", "both"]:
            for code, description in self.cpt_codes.items():
                if term_lower in description.lower():
                    results["CPT"].append(code)
        
        # Search ICD-10 codes  
        if code_type in ["ICD-10", "both"]:
            for condition, codes in self.comorbidity_mappings.items():
                if term_lower in condition or condition in term_lower:
                    results["ICD-10"].extend(codes)
        
        return results

# Example usage showing flexibility
def demonstrate_flexibility():
    """Show how the same system works for different medical policies"""
    
    # Example 1: Bariatric Surgery Policy
    bariatric_data = {
        "policy_name": "Bariatric Surgery",
        "criteria": [
            type('Criterion', (), {
                'field_name': 'patient_age',
                'operator': '>=',
                'value': 18,
                'description': 'Patient must be 18 years or older'
            })(),
            type('Criterion', (), {
                'field_name': 'procedure_code',
                'operator': 'in',
                'value': ['43644', '43775', '43770'],
                'description': 'Must be approved bariatric procedure'
            })()
        ],
        "total_criteria": 2
    }
    
    # Example 2: Cardiac Surgery Policy
    cardiac_data = {
        "policy_name": "Cardiac Surgery",
        "criteria": [
            type('Criterion', (), {
                'field_name': 'patient_age',
                'operator': '>=',
                'value': 21,
                'description': 'Patient must be 21 years or older'
            })(),
            type('Criterion', (), {
                'field_name': 'procedure_code',
                'operator': 'in',
                'value': ['33533', '33510'],
                'description': 'Must be approved cardiac procedure'
            })()
        ],
        "total_criteria": 2
    }
    
    # Build graphs for both policies
    builder = GenericKnowledgeGraphBuilder()
    
    bariatric_graph = builder.build_graph_from_policy(bariatric_data)
    print(f"Bariatric graph: {bariatric_graph.number_of_nodes()} nodes, {bariatric_graph.number_of_edges()} edges")
    
    cardiac_graph = builder.build_graph_from_policy(cardiac_data)
    print(f"Cardiac graph: {cardiac_graph.number_of_nodes()} nodes, {cardiac_graph.number_of_edges()} edges")
    
    return builder

if __name__ == "__main__":
    demonstrate_flexibility()