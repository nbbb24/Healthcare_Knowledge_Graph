import argparse
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib.pyplot as plt
import networkx as nx


@dataclass
class CodeEntry:
    code: str
    code_type: str
    description: str
    source_key: str


class KnowledgeGraphGenerator:
    """Builds and visualises a knowledge graph from a SQL policy definition."""

    def __init__(
        self,
        sql_path: str,
        code_dictionary_path: str,
        output_dir: Optional[str] = None,
        nodes_filename: str = "kg_nodes.json",
        edges_filename: str = "kg_edges.json",
        patient_data_path: Optional[str] = None,
    ) -> None:
        self.sql_path = Path(sql_path)
        self.code_dictionary_path = Path(code_dictionary_path)
        self.patient_data_path = Path(patient_data_path) if patient_data_path else None
        self.output_dir = Path(output_dir) if output_dir else self.sql_path.parent
        self.nodes_filename = nodes_filename
        self.edges_filename = edges_filename

        self.graph = nx.DiGraph()
        self.nodes: Dict[str, Dict[str, str]] = {}
        self.edges: List[Dict[str, str]] = []
        self._edge_keys: set[Tuple[str, str]] = set()

        self._condition_counter = 0
        self._group_counter = 0
        self._patient_counter = 0

        self.code_index: Dict[str, CodeEntry] = {}
        self.range_index: List[CodeEntry] = []
        self.patient_data: List[Dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(self) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        sql_text = self._read_sql()
        where_clause = self._extract_where_clause(sql_text)
        self._load_code_dictionary()
        
        # Load patient data if provided
        if self.patient_data_path:
            self._load_patient_data()

        root_id = self._register_node(
            node_id=self._make_root_id(),
            node_type="Query",
            label=f"SQL Query: {self.sql_path.stem}",
            file=str(self.sql_path.resolve()),
        )

        if where_clause:
            self._build_expression_tree(where_clause, root_id, incoming_operator="ROOT")
        
        # Add patient nodes if patient data is loaded
        if self.patient_data:
            self._add_patient_nodes(root_id)

        return list(self.nodes.values()), list(self.edges)

    def save(self) -> Tuple[Path, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        nodes_path = self.output_dir / self.nodes_filename
        edges_path = self.output_dir / self.edges_filename

        with nodes_path.open("w", encoding="utf-8") as fh:
            json.dump(list(self.nodes.values()), fh, indent=2)

        with edges_path.open("w", encoding="utf-8") as fh:
            json.dump(list(self.edges), fh, indent=2)

        return nodes_path, edges_path

    def plot(self, scatter: bool = False, output_path: Optional[str] = None, show: bool = False, 
             policy_only: bool = False) -> Optional[Path]:
        if not self.graph.nodes:
            raise RuntimeError("Graph is empty. Call generate() before plotting.")

        # Filter nodes if policy_only is True
        if policy_only:
            filtered_nodes = [n for n in self.graph.nodes if self.graph.nodes[n].get("type") != "Patient"]
            subgraph = self.graph.subgraph(filtered_nodes)
        else:
            subgraph = self.graph

        pos = self._layout_positions(scatter=scatter, graph=subgraph)
        colors = {
            "Query": "#1f77b4",
            "LogicalOperator": "#2ca02c",
            "Condition": "#ff7f0e",
            "Code": "#6a3d9a",
            "Patient": "#d62728",
        }

        node_colors = [colors.get(subgraph.nodes[n].get("type"), "#7f7f7f") for n in subgraph.nodes]
        labels = {n: subgraph.nodes[n].get("label", n) for n in subgraph.nodes}

        plt.figure(figsize=(14, 10))
        nx.draw_networkx(
            subgraph,
            pos,
            labels=labels,
            node_color=node_colors,
            node_size=900,
            font_size=8,
            font_weight="bold",
            edge_color="#555555",
            arrows=True,
            arrowstyle="-|>",
            arrowsize=12,
        )

        # Only show legend for node types that exist in the subgraph
        existing_types = set(subgraph.nodes[n].get("type") for n in subgraph.nodes)
        legend_handles = [
            plt.Line2D([0], [0], marker="o", color="w", label=node_type, markerfacecolor=color, markersize=10)
            for node_type, color in colors.items()
            if node_type in existing_types
        ]
        plt.legend(handles=legend_handles, loc="best")
        plt.axis("off")
        
        # Set title based on whether it's policy-only or not
        title = "Knowledge Graph: Bariatric Surgery Policy" + (" (Policy Only)" if policy_only else "")
        plt.title(title, fontsize=16, fontweight="bold")
        
        plt.tight_layout()

        saved_path: Optional[Path] = None
        if output_path:
            saved_path = Path(output_path)
            saved_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(saved_path, dpi=300)

        if show:
            plt.show()

        plt.close()
        return saved_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _make_root_id(self) -> str:
        return f"query_{self.sql_path.stem}"

    def _read_sql(self) -> str:
        if not self.sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {self.sql_path}")
        return self.sql_path.read_text(encoding="utf-8")

    def _extract_where_clause(self, sql_text: str) -> str:
        pattern = re.compile(r"\bWHERE\b", re.IGNORECASE)
        match = pattern.search(sql_text)
        if not match:
            return ""

        start = match.end()
        end = sql_text.find(";", start)
        if end == -1:
            end = len(sql_text)

        clause = sql_text[start:end]
        clause = self._strip_sql_comments(clause)
        return clause.strip()

    def _strip_sql_comments(self, clause: str) -> str:
        no_line_comments = re.sub(r"--.*", "", clause)
        no_block_comments = re.sub(r"/\*.*?\*/", "", no_line_comments, flags=re.DOTALL)
        return no_block_comments

    def _load_code_dictionary(self) -> None:
        if not self.code_dictionary_path.exists():
            raise FileNotFoundError(f"Code dictionary not found: {self.code_dictionary_path}")

        data = json.loads(self.code_dictionary_path.read_text(encoding="utf-8"))
        for code_type, entries in data.items():
            if not isinstance(entries, dict):
                continue
            for key, description in entries.items():
                entry = CodeEntry(code=key, code_type=code_type, description=description, source_key=key)
                if "-" in key and not key.startswith("-"):
                    self.range_index.append(entry)
                else:
                    self.code_index[key.upper()] = entry

    def _load_patient_data(self) -> None:
        """Load patient data from JSON file(s)."""
        if not self.patient_data_path or not self.patient_data_path.exists():
            print(f"⚠️  Patient data file not found: {self.patient_data_path}")
            return

        try:
            data = json.loads(self.patient_data_path.read_text(encoding="utf-8"))
            
            # Handle different JSON structures
            if isinstance(data, dict):
                if "patient" in data:
                    # Single patient record with full structure
                    self.patient_data = [self._normalize_patient_data(data)]
                else:
                    # Patient data dictionary format
                    self.patient_data = [self._normalize_patient_data({"patient": data})]
            elif isinstance(data, list):
                # Multiple patients
                self.patient_data = [self._normalize_patient_data(patient) for patient in data]
            
            print(f"✅ Loaded {len(self.patient_data)} patient record(s)")
            
        except Exception as e:
            print(f"❌ Error loading patient data: {e}")
            self.patient_data = []

    def _normalize_patient_data(self, raw_data: Dict) -> Dict:
        """Normalize patient data to a consistent format."""
        patient_info = raw_data.get("patient", {})
        
        # Extract key information
        normalized = {
            "id": patient_info.get("mrn", patient_info.get("id", f"patient_{self._patient_counter}")),
            "name": patient_info.get("name", "Unknown Patient"),
            "age": patient_info.get("age", 0),
            "bmi": 0.0,
            "diagnosis_codes": [],
            "procedure_codes": [],
            "meets_criteria": False,
            "raw_data": raw_data
        }
        
        # Extract BMI from vital signs or direct field
        vital_signs = raw_data.get("vital_signs", {})
        if "bmi" in vital_signs:
            normalized["bmi"] = float(vital_signs["bmi"])
        elif "patient_bmi" in raw_data:
            normalized["bmi"] = float(raw_data["patient_bmi"])
        
        # Extract diagnosis codes
        medical_conditions = raw_data.get("medical_conditions", [])
        for condition in medical_conditions:
            # Try to extract ICD-10 codes from condition descriptions
            if "BMI" in condition and "40" in condition:
                normalized["diagnosis_codes"].append("E66.01")  # Morbid obesity
            elif "Diabetes" in condition:
                normalized["diagnosis_codes"].append("E11.9")  # Type 2 diabetes
            elif "Hypertension" in condition:
                normalized["diagnosis_codes"].append("I10")  # Essential hypertension
        
        # Extract procedure codes if available
        if "procedure_code_CPT" in raw_data and raw_data["procedure_code_CPT"]:
            normalized["procedure_codes"].append(raw_data["procedure_code_CPT"])
        
        # Determine if patient meets criteria (simplified logic)
        normalized["meets_criteria"] = (
            normalized["age"] >= 18 and 
            (normalized["bmi"] >= 40 or (normalized["bmi"] >= 35 and len(normalized["diagnosis_codes"]) > 0))
        )
        
        return normalized

    def _add_patient_nodes(self, root_id: str) -> None:
        """Add patient nodes to the knowledge graph."""
        for patient in self.patient_data:
            patient_id = f"patient_{patient['id']}"
            
            # Create patient node
            self._register_node(
                node_id=patient_id,
                node_type="Patient",
                label=f"Patient: {patient['name']}",
                patient_name=patient["name"],
                patient_age=str(patient["age"]),
                patient_bmi=str(patient["bmi"]),
                meets_criteria=str(patient["meets_criteria"]),
                diagnosis_codes=", ".join(patient["diagnosis_codes"]),
                procedure_codes=", ".join(patient["procedure_codes"])
            )
            
            # Connect patient to root query
            self._register_edge(root_id, patient_id, relation="evaluates", evaluation_type="patient_data")
            
            # Connect patient to relevant diagnosis codes
            for diag_code in patient["diagnosis_codes"]:
                code_id = f"code_ICD10_Diagnosis_{diag_code}".replace(".", "_")
                if code_id in self.nodes:
                    self._register_edge(patient_id, code_id, relation="has_diagnosis", code_type="ICD10_Diagnosis")
            
            # Connect patient to relevant procedure codes
            for proc_code in patient["procedure_codes"]:
                code_id = f"code_CPT_{proc_code}"
                if code_id in self.nodes:
                    self._register_edge(patient_id, code_id, relation="has_procedure", code_type="CPT")

    def _build_expression_tree(self, expression: str, parent_id: str, incoming_operator: str) -> None:
        expression = self._strip_enclosing_parentheses(expression.strip())

        for operator in ("OR", "AND"):
            parts = self._split_top_level(expression, operator)
            if len(parts) > 1:
                group_id = self._next_group_id(operator)
                self._register_node(
                    node_id=group_id,
                    node_type="LogicalOperator",
                    label=f"{operator} group",
                    operator=operator,
                )
                self._register_edge(parent_id, group_id, relation="logic", logical_operator=incoming_operator)
                for part in parts:
                    self._build_expression_tree(part, group_id, incoming_operator=operator)
                return

        condition_id = self._next_condition_id()
        label = self._clean_condition_text(expression)
        self._register_node(node_id=condition_id, node_type="Condition", label=label, raw_expression=expression)
        self._register_edge(parent_id, condition_id, relation="logic", logical_operator=incoming_operator)

        for code_entry in self._extract_codes(label):
            code_id = f"code_{code_entry.code_type}_{code_entry.code}".replace(" ", "_")
            self._register_node(
                node_id=code_id,
                node_type="Code",
                label=f"{code_entry.code_type}: {code_entry.code}",
                code=code_entry.code,
                code_type=code_entry.code_type,
                description=code_entry.description,
                source_key=code_entry.source_key,
            )
            self._register_edge(condition_id, code_id, relation="references", code_type=code_entry.code_type)

    def _strip_enclosing_parentheses(self, text: str) -> str:
        while text.startswith("(") and text.endswith(")"):
            depth = 0
            valid = True
            for index, char in enumerate(text):
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0 and index != len(text) - 1:
                        valid = False
                        break
            if valid and depth == 0:
                text = text[1:-1].strip()
            else:
                break
        return text

    def _split_top_level(self, expression: str, operator: str) -> List[str]:
        tokens: List[str] = []
        depth = 0
        in_string = False
        string_delim = ""
        start = 0
        upper_expression = expression.upper()
        op_len = len(operator)

        index = 0
        while index < len(expression):
            char = expression[index]
            if in_string:
                if char == string_delim:
                    in_string = False
                index += 1
                continue

            if char in {'"', "'"}:
                in_string = True
                string_delim = char
                index += 1
                continue

            if char == "(":
                depth += 1
                index += 1
                continue

            if char == ")":
                depth = max(depth - 1, 0)
                index += 1
                continue

            if depth == 0 and upper_expression[index:index + op_len] == operator:
                before = expression[index - 1] if index > 0 else " "
                after_index = index + op_len
                after = expression[after_index] if after_index < len(expression) else " "
                if self._is_boundary(before) and self._is_boundary(after):
                    token = expression[start:index].strip()
                    if token:
                        tokens.append(token)
                    index += op_len
                    start = index
                    continue

            index += 1

        token = expression[start:].strip()
        if token:
            tokens.append(token)

        return tokens if len(tokens) > 1 else [expression]

    def _is_boundary(self, character: str) -> bool:
        return character.isspace() or character in {"(", ")"}

    def _clean_condition_text(self, expression: str) -> str:
        return re.sub(r"\s+", " ", expression).strip()

    def _extract_codes(self, condition: str) -> Iterable[CodeEntry]:
        seen: set[str] = set()
        for token in re.findall(r"'([^']+)'", condition):
            normalised = token.upper()
            if normalised in seen:
                continue
            seen.add(normalised)

            if not self._looks_like_code(normalised):
                continue

            entry = self._lookup_code(normalised)
            if entry:
                yield entry

    def _looks_like_code(self, token: str) -> bool:
        # Accept alphanumeric strings with at least one digit (filters out words like 'TRUE').
        return bool(re.search(r"\d", token))

    def _lookup_code(self, token: str) -> Optional[CodeEntry]:
        direct = self.code_index.get(token)
        if direct:
            return CodeEntry(code=token, code_type=direct.code_type, description=direct.description, source_key=direct.source_key)

        for entry in self.range_index:
            if self._code_in_range(token, entry.source_key):
                return CodeEntry(code=token, code_type=entry.code_type, description=entry.description, source_key=entry.source_key)
        return None

    def _code_in_range(self, token: str, range_key: str) -> bool:
        if "-" not in range_key:
            return False
        start_code, end_code = range_key.split("-", maxsplit=1)
        if len(token) != len(start_code):
            return False
        return start_code.upper() <= token <= end_code.upper()

    def _next_condition_id(self) -> str:
        self._condition_counter += 1
        return f"condition_{self._condition_counter:03d}"

    def _next_group_id(self, operator: str) -> str:
        self._group_counter += 1
        return f"group_{operator.lower()}_{self._group_counter:03d}"

    def _register_node(self, node_id: str, node_type: str, label: str, **attributes: str) -> str:
        if node_id not in self.nodes:
            payload = {"id": node_id, "type": node_type, "label": label}
            payload.update(attributes)
            self.nodes[node_id] = payload
            self.graph.add_node(node_id, **payload)
        else:
            self.nodes[node_id].update(attributes)
            self.graph.nodes[node_id].update(attributes)
        return node_id

    def _register_edge(self, source: str, target: str, relation: str, **attributes: str) -> None:
        key = (source, target)
        if key not in self._edge_keys:
            payload = {"source": source, "target": target, "relation": relation}
            payload.update(attributes)
            self.edges.append(payload)
            self.graph.add_edge(source, target, **payload)
            self._edge_keys.add(key)
        else:
            self.graph.edges[source, target].update(attributes)

    def _layout_positions(self, scatter: bool = False, graph: Optional[nx.Graph] = None) -> Dict[str, Tuple[float, float]]:
        target_graph = graph if graph is not None else self.graph
        
        if scatter:
            return {node: (math.cos(index), math.sin(index)) for index, node in enumerate(target_graph.nodes)}

        # spring layout picks a readable arrangement for most DAG-like graphs
        return nx.spring_layout(target_graph, seed=42)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and plot a knowledge graph from a SQL policy definition.")
    parser.add_argument("--sql", required=True, help="Path to the SQL file containing the policy definition.")
    parser.add_argument("--codes", required=True, help="Path to the code dictionary JSON file.")
    parser.add_argument("--patient-data", help="Path to the patient data JSON file (optional).")
    parser.add_argument("--output-dir", help="Directory where KG JSON files should be written. Defaults to the SQL file directory.")
    parser.add_argument("--nodes-filename", default="kg_nodes.json", help="Filename for the nodes JSON output.")
    parser.add_argument("--edges-filename", default="kg_edges.json", help="Filename for the edges JSON output.")
    parser.add_argument("--plot-path", help="Optional path to save a PNG of the knowledge graph.")
    parser.add_argument("--show-plot", action="store_true", help="Display the graph after generating it.")
    parser.add_argument("--scatter-layout", action="store_true", help="Use a deterministic circular scatter layout instead of spring embedding.")
    parser.add_argument("--policy-only", action="store_true", help="Plot only policy-related nodes (exclude patient data).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generator = KnowledgeGraphGenerator(
        sql_path=args.sql,
        code_dictionary_path=args.codes,
        output_dir=args.output_dir,
        nodes_filename=args.nodes_filename,
        edges_filename=args.edges_filename,
        patient_data_path=args.patient_data,
    )

    nodes, edges = generator.generate()
    nodes_path, edges_path = generator.save()

    print("✅ Knowledge graph generated")
    print(f"   Nodes written to: {nodes_path}")
    print(f"   Edges written to: {edges_path}")
    print(f"   Total nodes: {len(nodes)}")
    print(f"   Total edges: {len(edges)}")

    if args.plot_path or args.show_plot:
        saved_path = generator.plot(scatter=args.scatter_layout, output_path=args.plot_path, show=args.show_plot, policy_only=args.policy_only)
        if saved_path:
            print(f"   Plot saved to: {saved_path}")


if __name__ == "__main__":
    main()
