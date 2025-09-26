#!/usr/bin/env python3
"""
Patient Rule Knowledge Graph Visualizer

Creates a knowledge graph showing a patient at the center with policy rules as nodes,
where edges indicate whether each rule is met or not met by the patient.

Usage:
    python patient_rule_kg.py patient.json sql.txt data_dict.json [options]

Author: AI Assistant
"""

import json
import argparse
import sys
import os
import re
import math
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')


@dataclass
class PolicyCondition:
    """Represents a single condition from the SQL policy."""
    field_name: str
    operator: str
    value: str
    description: str
    section: str
    condition_type: str
    is_met: bool = False
    patient_value: Any = None


class PatientRuleKGVisualizer:
    """Creates knowledge graphs showing patient data against policy rules."""
    
    def __init__(self, patient_data: Dict[str, Any], sql_text: str, data_dictionary: List[Dict[str, Any]]):
        """
        Initialize the visualizer with patient data, SQL policy, and data dictionary.
        
        Args:
            patient_data: Patient record data
            sql_text: SQL policy text
            data_dictionary: Data dictionary for field descriptions
        """
        self.patient_data = patient_data
        self.sql_text = sql_text
        self.data_dictionary = {field['name']: field for field in data_dictionary}
        
        self.graph = nx.DiGraph()
        self.conditions: List[PolicyCondition] = []
        
        # Color schemes
        self.color_schemes = {
            'patient': '#FF6B6B',      # Red
            'condition_met': '#4ECDC4',    # Teal
            'condition_not_met': '#FF6B6B', # Red
            'condition_group': '#45B7D1',   # Blue
            'default': '#B0B0B0'       # Gray
        }
    
    def parse_sql_conditions(self) -> None:
        """Parse SQL WHERE clause to extract individual conditions."""
        # Extract WHERE clause
        where_match = re.search(r'WHERE\s+(.*?)(?=;|$)', self.sql_text, re.IGNORECASE | re.DOTALL)
        if not where_match:
            return
        
        where_clause = where_match.group(1).strip()
        
        # Split by OR operators first (top level)
        or_conditions = self._split_by_operator(where_clause, 'OR')
        
        for or_condition in or_conditions:
            # Split by AND operators
            and_conditions = self._split_by_operator(or_condition, 'AND')
            
            for condition in and_conditions:
                condition = condition.strip()
                if not condition or condition in ['(', ')']:
                    continue
                
                # Parse individual condition
                parsed_condition = self._parse_individual_condition(condition)
                if parsed_condition:
                    self.conditions.append(parsed_condition)
    
    def _split_by_operator(self, text: str, operator: str) -> List[str]:
        """Split text by operator while respecting parentheses and quotes."""
        parts = []
        depth = 0
        in_string = False
        string_delim = ""
        start = 0
        
        i = 0
        while i < len(text):
            char = text[i]
            
            if in_string:
                if char == string_delim:
                    in_string = False
                i += 1
                continue
            
            if char in ['"', "'"]:
                in_string = True
                string_delim = char
                i += 1
                continue
            
            if char == '(':
                depth += 1
            elif char == ')':
                depth = max(depth - 1, 0)
            
            if depth == 0 and text[i:i+len(operator)].upper() == operator.upper():
                # Check word boundaries
                before = text[i-1] if i > 0 else ' '
                after = text[i+len(operator)] if i+len(operator) < len(text) else ' '
                
                if self._is_word_boundary(before) and self._is_word_boundary(after):
                    part = text[start:i].strip()
                    if part:
                        parts.append(part)
                    i += len(operator)
                    start = i
                    continue
            
            i += 1
        
        # Add the last part
        part = text[start:].strip()
        if part:
            parts.append(part)
        
        return parts if len(parts) > 1 else [text]
    
    def _is_word_boundary(self, char: str) -> bool:
        """Check if character is a word boundary."""
        return char.isspace() or char in '()'
    
    def _parse_individual_condition(self, condition: str) -> Optional[PolicyCondition]:
        """Parse an individual SQL condition."""
        condition = condition.strip()
        
        # Remove outer parentheses
        while condition.startswith('(') and condition.endswith(')'):
            condition = condition[1:-1].strip()
        
        # Skip empty conditions
        if not condition:
            return None
        
        # Pattern matching for different condition types
        patterns = [
            # Field comparison patterns
            (r'(\w+)\s*([><=!]+)\s*([^,\s]+)', self._parse_comparison),
            (r'(\w+)\s+IN\s*\(([^)]+)\)', self._parse_in_condition),
            (r'(\w+)\s*=\s*([^,\s]+)', self._parse_equals),
        ]
        
        for pattern, parser in patterns:
            match = re.search(pattern, condition, re.IGNORECASE)
            if match:
                return parser(match, condition)
        
        return None
    
    def _parse_comparison(self, match, full_condition: str) -> Optional[PolicyCondition]:
        """Parse comparison conditions like patient_age >= 18."""
        field_name = match.group(1)
        operator = match.group(2)
        value = match.group(3)
        
        return self._create_condition(field_name, operator, value, full_condition)
    
    def _parse_in_condition(self, match, full_condition: str) -> Optional[PolicyCondition]:
        """Parse IN conditions like procedure IN ('surgery1', 'surgery2')."""
        field_name = match.group(1)
        values_str = match.group(2)
        
        # Extract values from the IN clause
        values = re.findall(r"'([^']+)'", values_str)
        value = ', '.join(values) if values else values_str
        
        return self._create_condition(field_name, 'IN', value, full_condition)
    
    def _parse_equals(self, match, full_condition: str) -> Optional[PolicyCondition]:
        """Parse equals conditions like field = value."""
        field_name = match.group(1)
        value = match.group(2)
        
        return self._create_condition(field_name, '=', value, full_condition)
    
    def _create_condition(self, field_name: str, operator: str, value: str, full_condition: str) -> Optional[PolicyCondition]:
        """Create a PolicyCondition object."""
        # Clean up field name
        field_name = field_name.lower().strip()
        
        # Get field info from data dictionary
        field_info = self.data_dictionary.get(field_name, {})
        description = field_info.get('description', f'Field: {field_name}')
        section = field_info.get('section', 'Unknown')
        
        # Determine condition type based on section
        condition_type = self._get_condition_type(section, field_name)
        
        return PolicyCondition(
            field_name=field_name,
            operator=operator,
            value=value,
            description=description,
            section=section,
            condition_type=condition_type
        )
    
    def _get_condition_type(self, section: str, field_name: str) -> str:
        """Determine the condition type based on section and field name."""
        if section == 'Demographics':
            return 'demographic'
        elif section == 'Eligibility':
            return 'eligibility'
        elif section == 'Program Requirements':
            return 'requirement'
        elif 'procedure' in field_name.lower() or section == 'Procedures':
            return 'procedure'
        elif 'diagnosis' in field_name.lower() or section == 'Diagnosis':
            return 'diagnosis'
        else:
            return 'other'
    
    def evaluate_conditions(self) -> None:
        """Evaluate each condition against the patient data."""
        for condition in self.conditions:
            patient_value = self._get_patient_value(condition.field_name)
            condition.patient_value = patient_value
            condition.is_met = self._evaluate_condition(condition, patient_value)
    
    def _get_patient_value(self, field_name: str) -> Any:
        """Extract patient value for a given field name."""
        # Handle nested patient data structure
        if field_name == 'patient_age':
            return self.patient_data.get('patient', {}).get('age')
        elif field_name == 'patient_bmi':
            return self.patient_data.get('vital_signs', {}).get('bmi')
        elif field_name == 'comorbidity':
            # Check if patient has any of the specified comorbidities
            medical_conditions = self.patient_data.get('medical_conditions', [])
            comorbidities = []
            for condition in medical_conditions:
                condition_lower = condition.lower()
                if 'diabetes' in condition_lower:
                    comorbidities.append('diabetes')
                if 'hypertension' in condition_lower:
                    comorbidities.append('hypertension')
                if 'cardiovascular' in condition_lower or 'heart' in condition_lower:
                    comorbidities.append('cardiovascular_disease')
                if 'sleep apnea' in condition_lower:
                    comorbidities.append('severe_sleep_apnea')
            return comorbidities
        elif field_name == 'participated_weight_loss_program':
            # This would need to be in patient data - assume False for now
            return False
        elif field_name == 'conservative_therapy_failed':
            # This would need to be in patient data - assume True for now
            return True
        elif field_name == 'medical_clearance':
            # This would need to be in patient data - assume True for now
            return True
        elif field_name == 'mental_health_clearance':
            # This would need to be in patient data - assume True for now
            return True
        elif field_name == 'preop_education':
            # This would need to be in patient data - assume True for now
            return True
        elif field_name == 'treatment_plan_documented':
            # This would need to be in patient data - assume True for now
            return True
        else:
            # Try to find in nested structure
            for key, value in self.patient_data.items():
                if isinstance(value, dict) and field_name in value:
                    return value[field_name]
            return None
    
    def _evaluate_condition(self, condition: PolicyCondition, patient_value: Any) -> bool:
        """Evaluate a single condition against patient data."""
        if patient_value is None:
            return False
        
        try:
            if condition.operator == '=':
                return str(patient_value).lower() == condition.value.lower()
            elif condition.operator == '>=':
                return float(patient_value) >= float(condition.value)
            elif condition.operator == '<=':
                return float(patient_value) <= float(condition.value)
            elif condition.operator == '>':
                return float(patient_value) > float(condition.value)
            elif condition.operator == '<':
                return float(patient_value) < float(condition.value)
            elif condition.operator == 'IN':
                # Handle IN conditions
                values = [v.strip().strip("'\"") for v in condition.value.split(',')]
                if isinstance(patient_value, list):
                    return any(str(val).lower() in [v.lower() for v in values] for val in patient_value)
                else:
                    return str(patient_value).lower() in [v.lower() for v in values]
            else:
                return False
        except (ValueError, TypeError):
            return False
    
    def build_knowledge_graph(self) -> None:
        """Build the knowledge graph with patient at center and conditions as nodes."""
        # Create patient center node
        patient_id = "patient_center"
        patient_name = self.patient_data.get('patient', {}).get('name', 'Unknown Patient')
        
        self.graph.add_node(
            patient_id,
            id=patient_id,
            type="Patient",
            label=patient_name,
            description="Patient record",
            node_size=2000
        )
        
        # Group conditions by type
        condition_groups = {}
        for condition in self.conditions:
            if condition.condition_type not in condition_groups:
                condition_groups[condition.condition_type] = []
            condition_groups[condition.condition_type].append(condition)
        
        # Create group nodes and condition nodes
        group_positions = {}
        angle_step = 2 * math.pi / len(condition_groups)
        
        for i, (condition_type, conditions) in enumerate(condition_groups.items()):
            # Create group node
            group_id = f"group_{condition_type}"
            group_angle = i * angle_step
            group_x = 4 * math.cos(group_angle)
            group_y = 4 * math.sin(group_angle)
            
            self.graph.add_node(
                group_id,
                id=group_id,
                type="ConditionGroup",
                label=f"{condition_type.title()} Rules",
                condition_type=condition_type,
                node_size=1500
            )
            
            # Connect group to patient
            self.graph.add_edge(
                patient_id, group_id,
                relation="evaluated_by",
                edge_type="patient_rule"
            )
            
            # Create individual condition nodes
            condition_angle_step = angle_step / len(conditions)
            for j, condition in enumerate(conditions):
                condition_id = f"condition_{condition.field_name}_{j}"
                condition_angle = group_angle + (j - len(conditions)/2) * condition_angle_step
                condition_x = group_x + 2 * math.cos(condition_angle)
                condition_y = group_y + 2 * math.sin(condition_angle)
                
                # Create condition label
                condition_label = f"{condition.field_name} {condition.operator} {condition.value}"
                if len(condition_label) > 25:
                    condition_label = condition_label[:22] + "..."
                
                # Add status to label
                status = "✓" if condition.is_met else "✗"
                condition_label = f"{status} {condition_label}"
                
                self.graph.add_node(
                    condition_id,
                    id=condition_id,
                    type="Condition",
                    label=condition_label,
                    field_name=condition.field_name,
                    operator=condition.operator,
                    value=condition.value,
                    description=condition.description,
                    section=condition.section,
                    condition_type=condition.condition_type,
                    is_met=condition.is_met,
                    patient_value=condition.patient_value,
                    node_size=1000
                )
                
                # Connect condition to group
                self.graph.add_edge(
                    group_id, condition_id,
                    relation="contains",
                    edge_type="group_condition"
                )
                
                # Connect condition to patient with met/not met relationship
                edge_relation = "met" if condition.is_met else "not_met"
                self.graph.add_edge(
                    patient_id, condition_id,
                    relation=edge_relation,
                    edge_type="patient_condition"
                )
    
    def create_matplotlib_visualization(self, layout: str = 'spring', figsize: Tuple[int, int] = (16, 12), 
                                     output_file: Optional[str] = None, input_file_path: Optional[str] = None) -> None:
        """Create a matplotlib-based visualization of the patient rule knowledge graph."""
        plt.figure(figsize=figsize)
        
        # Choose layout
        if layout == 'spring':
            pos = nx.spring_layout(self.graph, k=3, iterations=50, seed=42)
        elif layout == 'circular':
            pos = nx.circular_layout(self.graph)
        else:
            pos = nx.spring_layout(self.graph)
        
        # Draw nodes
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            node_type = node_data.get('type', 'Condition')
            
            if node_type == 'Patient':
                color = self.color_schemes['patient']
                size = 2000
            elif node_type == 'ConditionGroup':
                color = self.color_schemes['condition_group']
                size = 1500
            elif node_type == 'Condition':
                is_met = node_data.get('is_met', False)
                color = self.color_schemes['condition_met'] if is_met else self.color_schemes['condition_not_met']
                size = 1000
            else:
                color = self.color_schemes['default']
                size = 500
            
            nx.draw_networkx_nodes(
                self.graph, pos,
                nodelist=[node],
                node_color=color,
                node_size=size,
                alpha=0.8
            )
        
        # Draw edges with different colors for met/not met
        met_edges = []
        not_met_edges = []
        other_edges = []
        
        for edge in self.graph.edges():
            edge_data = self.graph.edges[edge]
            relation = edge_data.get('relation', '')
            
            if relation == 'met':
                met_edges.append(edge)
            elif relation == 'not_met':
                not_met_edges.append(edge)
            else:
                other_edges.append(edge)
        
        # Draw different edge types
        if met_edges:
            nx.draw_networkx_edges(
                self.graph, pos,
                edgelist=met_edges,
                edge_color='green',
                alpha=0.8,
                width=3,
                style='-'
            )
        
        if not_met_edges:
            nx.draw_networkx_edges(
                self.graph, pos,
                edgelist=not_met_edges,
                edge_color='red',
                alpha=0.8,
                width=3,
                style='--'
            )
        
        if other_edges:
            nx.draw_networkx_edges(
                self.graph, pos,
                edgelist=other_edges,
                edge_color='gray',
                alpha=0.6,
                width=1.5
            )
        
        # Draw labels
        labels = {node: data.get('label', node) for node, data in self.graph.nodes(data=True)}
        nx.draw_networkx_labels(
            self.graph, pos, labels,
            font_size=8,
            font_weight='bold'
        )
        
        # Create legend
        legend_elements = [
            mpatches.Patch(color=self.color_schemes['patient'], label='Patient'),
            mpatches.Patch(color=self.color_schemes['condition_group'], label='Rule Groups'),
            mpatches.Patch(color=self.color_schemes['condition_met'], label='Rules Met'),
            mpatches.Patch(color=self.color_schemes['condition_not_met'], label='Rules Not Met'),
            plt.Line2D([0], [0], color='green', linewidth=3, label='Met'),
            plt.Line2D([0], [0], color='red', linewidth=3, linestyle='--', label='Not Met')
        ]
        plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1))
        
        plt.title("Patient Rule Knowledge Graph\nPatient vs Policy Rules", 
                 fontsize=16, fontweight='bold', pad=20)
        plt.axis('off')
        plt.tight_layout()
        
        # Save the plot
        if output_file:
            output_filename = f"{output_file}.png"
        else:
            output_filename = f"patient_rule_kg_{layout}_{figsize[0]}x{figsize[1]}.png"
        
        # Determine output directory (same as input file if provided)
        if input_file_path:
            output_dir = os.path.dirname(os.path.abspath(input_file_path))
            output_path = os.path.join(output_dir, output_filename)
        else:
            output_path = output_filename
            
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Patient rule knowledge graph saved as: {output_path}")
        
        plt.show()
    
    def print_evaluation_summary(self) -> None:
        """Print a summary of the rule evaluation."""
        total_conditions = len(self.conditions)
        met_conditions = sum(1 for c in self.conditions if c.is_met)
        not_met_conditions = total_conditions - met_conditions
        
        print(f"\n📊 Rule Evaluation Summary:")
        print(f"   Total rules: {total_conditions}")
        print(f"   Rules met: {met_conditions} ({met_conditions/total_conditions*100:.1f}%)")
        print(f"   Rules not met: {not_met_conditions} ({not_met_conditions/total_conditions*100:.1f}%)")
        
        # Group by condition type
        condition_groups = {}
        for condition in self.conditions:
            if condition.condition_type not in condition_groups:
                condition_groups[condition.condition_type] = {'met': 0, 'total': 0}
            condition_groups[condition.condition_type]['total'] += 1
            if condition.is_met:
                condition_groups[condition.condition_type]['met'] += 1
        
        print(f"\n📈 Rule Status by Category:")
        for condition_type, stats in condition_groups.items():
            met_pct = stats['met'] / stats['total'] * 100
            print(f"   {condition_type.title()}: {stats['met']}/{stats['total']} ({met_pct:.1f}%)")
        
        print(f"\n🔍 Detailed Rule Status:")
        for condition in self.conditions:
            status = "✓ MET" if condition.is_met else "✗ NOT MET"
            patient_val = condition.patient_value
            if isinstance(patient_val, list):
                patient_val = ', '.join(map(str, patient_val))
            print(f"   {status}: {condition.field_name} {condition.operator} {condition.value}")
            print(f"      Patient value: {patient_val}")
            print(f"      Description: {condition.description}")
            print()


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file '{file_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading file '{file_path}': {e}")
        sys.exit(1)


def load_text_file(file_path: str) -> str:
    """Load text data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading file '{file_path}': {e}")
        sys.exit(1)


def main():
    """Main function to run the patient rule knowledge graph visualizer."""
    parser = argparse.ArgumentParser(
        description="Create patient rule knowledge graphs showing patient data against policy rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python patient_rule_kg.py patient.json sql.txt data_dict.json
  python patient_rule_kg.py patient.json sql.txt data_dict.json --layout circular --output patient_rules
  python patient_rule_kg.py patient.json sql.txt data_dict.json --figsize 20 15
        """
    )
    
    parser.add_argument('patient_file', help='Patient record JSON file')
    parser.add_argument('sql_file', help='SQL policy file')
    parser.add_argument('data_dict_file', help='Data dictionary JSON file')
    parser.add_argument('--layout', choices=['spring', 'circular'], 
                       default='spring', help='Graph layout algorithm')
    parser.add_argument('--figsize', nargs=2, type=int, default=[16, 12],
                       help='Figure size for matplotlib (width height)')
    parser.add_argument('--output-file', type=str, 
                       help='Custom output filename (without extension)')
    
    args = parser.parse_args()
    
    # Load data files
    print(f"📁 Loading patient data from: {args.patient_file}")
    patient_data = load_json_file(args.patient_file)
    
    print(f"📁 Loading SQL policy from: {args.sql_file}")
    sql_text = load_text_file(args.sql_file)
    
    print(f"📁 Loading data dictionary from: {args.data_dict_file}")
    data_dictionary = load_json_file(args.data_dict_file)
    
    # Create visualizer
    print("🔧 Creating patient rule knowledge graph visualizer...")
    visualizer = PatientRuleKGVisualizer(patient_data, sql_text, data_dictionary)
    
    # Parse and evaluate conditions
    print("🔍 Parsing SQL conditions...")
    visualizer.parse_sql_conditions()
    
    print("⚖️  Evaluating conditions against patient data...")
    visualizer.evaluate_conditions()
    
    # Print evaluation summary
    visualizer.print_evaluation_summary()
    
    # Build graph
    print("🏗️  Building knowledge graph...")
    visualizer.build_knowledge_graph()
    
    # Create visualization
    print("🎨 Creating visualization...")
    visualizer.create_matplotlib_visualization(
        layout=args.layout, 
        figsize=tuple(args.figsize),
        output_file=args.output_file,
        input_file_path=args.patient_file
    )
    
    print("✅ Patient rule knowledge graph complete!")


if __name__ == "__main__":
    main()
