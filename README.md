# Medical Policy Knowledge Graph Generator

A comprehensive Python toolkit for generating and visualizing knowledge graphs from medical policies, patient data, and SQL-based eligibility criteria. This project focuses on bariatric surgery policies and creates interactive visualizations to understand complex medical decision rules.

## 🎯 Overview

This project provides tools to:
- Parse SQL-based medical policy rules into structured knowledge graphs
- Visualize patient data against policy criteria
- Generate interactive and static visualizations of medical decision trees
- Support multiple data formats and visualization layouts

## 📁 Project Structure

```
├── generate_kg.py              # Main knowledge graph generator from SQL policies
├── patient_kg.py               # Patient data knowledge graph visualizer
├── patient_rule_kg.py          # Patient vs policy rule evaluator
├── generate_policy_rule_kg.py  # Policy rule knowledge graph generator
├── test1/                      # Example data and outputs
│   ├── Patient_Record.json     # Sample patient data
│   ├── Patient_data_dictionary.json  # Patient data schema
│   ├── SQL_CGSURG83.txt       # Sample SQL policy
│   ├── Data_dictionary_CGSURG83.json  # Field definitions
│   ├── Policy_CGSURG83.json   # Structured policy rules
│   └── *.png                   # Generated visualizations
├── scripts/                    # Shell scripts for easy execution
└── requirements.txt            # Python dependencies
```

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd medical-policy-kg
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Install spaCy medical model for advanced NLP:
```bash
python -m spacy download en_core_web_sm
pip install https://github.com/allenai/scispacy/releases/download/v0.5.3/en_core_sci_md-0.5.3-py3-none-any.whl
```

### Basic Usage

#### 1. Generate Policy Knowledge Graph
```bash
python generate_kg.py --sql test1/SQL_CGSURG83.txt --codes test1/Data_dictionary_CGSURG83.json --plot-path policy_kg.png --show-plot
```

#### 2. Visualize Patient Data
```bash
python patient_kg.py test1/Patient_Record.json --layout spring --figsize 15 10
```

#### 3. Evaluate Patient Against Policy Rules
```bash
python patient_rule_kg.py test1/Patient_Record.json test1/SQL_CGSURG83.txt test1/Data_dictionary_CGSURG83.json --figsize 16 12
```

#### 4. Generate Policy Rule Graph
```bash
python generate_policy_rule_kg.py --sql test1/SQL_CGSURG83.txt --data-dict test1/Data_dictionary_CGSURG83.json --plot-path policy_rules.png
```

## 📊 Example: Bariatric Surgery Policy Analysis

The `test1/` directory contains a complete example analyzing bariatric surgery eligibility criteria:

### Sample Data Files

1. **Patient Record** (`Patient_Record.json`):
   - Complete patient profile with demographics, medical history, and conditions
   - Example: 44-year-old male with BMI 40.8, diabetes, hypertension

2. **SQL Policy** (`SQL_CGSURG83.txt`):
   - Complex eligibility criteria for bariatric surgery
   - Includes BMI requirements, comorbidity conditions, and procedural requirements

3. **Data Dictionary** (`Data_dictionary_CGSURG83.json`):
   - Field definitions and descriptions for all policy variables
   - Organized by sections: Demographics, Eligibility, Program Requirements, etc.

4. **Policy Rules** (`Policy_CGSURG83.json`):
   - Structured representation of policy restrictions
   - Machine-readable format for rule evaluation

### Generated Visualizations

The example generates several types of knowledge graphs:

1. **Policy Knowledge Graph**: Shows the complete policy structure with conditions and logical operators
2. **Patient Knowledge Graph**: Visualizes patient data and relationships
3. **Patient Rule Evaluation**: Shows how a specific patient measures against policy criteria
4. **Policy Rule Graph**: Displays policy rules organized by category

## 🛠️ Tools and Features

### 1. Knowledge Graph Generator (`generate_kg.py`)

**Purpose**: Converts SQL-based medical policies into structured knowledge graphs

**Key Features**:
- Parses complex SQL WHERE clauses
- Extracts logical operators (AND, OR) and conditions
- Maps medical codes to descriptions
- Supports patient data integration
- Multiple visualization layouts

**Usage**:
```bash
python generate_kg.py --sql <sql_file> --codes <code_dict> [options]
```

**Options**:
- `--patient-data`: Include patient data in the graph
- `--plot-path`: Save visualization to file
- `--show-plot`: Display interactive plot
- `--policy-only`: Show only policy nodes (exclude patient data)
- `--scatter-layout`: Use circular scatter layout

### 2. Patient Knowledge Graph Visualizer (`patient_kg.py`)

**Purpose**: Creates knowledge graphs from patient data in various JSON formats

**Key Features**:
- Auto-detects data structure (patient records, policies, data dictionaries)
- Multiple visualization layouts (spring, circular, hierarchical)
- Interactive Plotly visualizations
- Color-coded node types
- Flexible input format support

**Usage**:
```bash
python patient_kg.py <input_file> [options]
```

**Options**:
- `--layout`: Choose layout algorithm (spring, circular, hierarchical)
- `--interactive`: Create interactive Plotly visualization
- `--figsize`: Set figure dimensions
- `--output-file`: Custom output filename

### 3. Patient Rule Evaluator (`patient_rule_kg.py`)

**Purpose**: Evaluates patient data against policy rules and visualizes compliance

**Key Features**:
- Parses SQL conditions into evaluable rules
- Compares patient data against policy criteria
- Color-codes met/unmet conditions
- Detailed evaluation summary
- Visual rule compliance dashboard

**Usage**:
```bash
python patient_rule_kg.py <patient_file> <sql_file> <data_dict_file> [options]
```

**Options**:
- `--layout`: Graph layout (spring, circular)
- `--figsize`: Figure dimensions
- `--output-file`: Custom output filename

### 4. Policy Rule Generator (`generate_policy_rule_kg.py`)

**Purpose**: Creates knowledge graphs focused on policy rule structure

**Key Features**:
- Groups conditions by category (demographics, eligibility, requirements)
- Hierarchical rule organization
- Policy-centered visualization
- JSON export for further analysis

**Usage**:
```bash
python generate_policy_rule_kg.py --sql <sql_file> --data-dict <data_dict> [options]
```

## 📈 Visualization Types

### 1. Static Visualizations (Matplotlib)
- High-quality PNG output
- Customizable layouts and colors
- Legend and labeling
- Publication-ready figures

### 2. Interactive Visualizations (Plotly)
- Hover information
- Zoom and pan capabilities
- Dynamic filtering
- Web-ready HTML output

### 3. Layout Algorithms
- **Spring Layout**: Natural, force-directed positioning
- **Circular Layout**: Organized circular arrangement
- **Hierarchical Layout**: Tree-like structure (requires Graphviz)

## 🎨 Color Schemes

The tools use consistent color coding:

- **Patient Nodes**: Red (#FF6B6B)
- **Policy Nodes**: Teal (#4ECDC4)
- **Condition Groups**: Blue (#45B7D1)
- **Met Conditions**: Teal (#4ECDC4)
- **Unmet Conditions**: Red (#FF6B6B)
- **Data Fields**: Mint (#98D8C8)
- **Procedures**: Green (#96CEB4)
- **Diagnoses**: Yellow (#FFEAA7)

## 📋 Data Format Requirements

### Patient Data Format
```json
{
  "patient": {
    "name": "Patient Name",
    "age": 44,
    "mrn": "123456"
  },
  "vital_signs": {
    "bmi": 40.8
  },
  "medical_conditions": ["condition1", "condition2"]
}
```

### SQL Policy Format
```sql
SELECT * FROM patients
WHERE patient_age >= 18
  AND patient_bmi >= 40
  AND comorbidity IN ('diabetes', 'hypertension')
  AND medical_clearance = TRUE;
```

### Data Dictionary Format
```json
[
  {
    "name": "patient_age",
    "type": "integer",
    "description": "Patient age in years",
    "section": "Demographics"
  }
]
```

## 🔧 Advanced Usage

### Custom Code Dictionaries
Create custom code dictionaries for medical terminology:
```json
{
  "ICD10_Diagnosis": {
    "E66.01": "Morbid obesity due to excess calories",
    "E66.09": "Other obesity due to excess calories"
  },
  "CPT": {
    "43644": "Laparoscopy, surgical, gastric restrictive procedure"
  }
}
```

### Batch Processing
Process multiple patients or policies:
```bash
for patient in patients/*.json; do
  python patient_rule_kg.py "$patient" policy.sql data_dict.json
done
```

### Integration with Medical Systems
The tools can be integrated with EHR systems by:
1. Converting patient data to the required JSON format
2. Mapping medical codes to the code dictionary
3. Automating policy evaluation workflows

## 📊 Example Outputs

The `test1/` directory contains example outputs:

- `patient_kg_spring_15x10.png`: Patient data visualization
- `patient_rule_kg.png`: Patient vs policy evaluation
- `policy_rule_kg.png`: Policy rule structure
- `policy_rule_kg_nodes.json`: Structured policy data
- `policy_rule_kg_edges.json`: Policy relationships

## 🐛 Troubleshooting

### Common Issues

1. **Missing Dependencies**: Install all requirements with `pip install -r requirements.txt`
2. **File Not Found**: Ensure all input files exist and paths are correct
3. **JSON Format Errors**: Validate JSON files before processing
4. **Memory Issues**: For large datasets, consider processing in batches

### Debug Mode
Add `--verbose` flag to most tools for detailed output:
```bash
python generate_kg.py --sql policy.sql --codes codes.json --verbose
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- NetworkX for graph algorithms
- Matplotlib and Plotly for visualizations
- The medical informatics community for policy data standards

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Review example files in `test1/`
3. Open an issue on GitHub

---

**Note**: This tool is designed for research and educational purposes. Always consult with medical professionals for actual clinical decision-making.
