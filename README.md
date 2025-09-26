# Medical Policy Knowledge Graph Generator

A Python toolkit for generating and visualizing knowledge graphs from medical policies and patient data. This project focuses on bariatric surgery policies and creates visualizations to understand complex medical decision rules.

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
│   ├── patient_kg_spring_15x10.png    # Generated patient KG
│   ├── patient_rule_kg.png            # Generated patient rule KG
│   └── policy_rule_kg.png             # Generated policy rule KG
├── scripts/                    # Shell scripts for easy execution
└── requirements.txt            # Python dependencies
```

## 🐍 Python Files

### 1. `generate_kg.py`
Main knowledge graph generator that converts SQL-based medical policies into structured knowledge graphs.

**Features:**
- Parses complex SQL WHERE clauses
- Extracts logical operators (AND, OR) and conditions
- Maps medical codes to descriptions
- Supports patient data integration
- Multiple visualization layouts

**Usage:**
```bash
python generate_kg.py --sql test1/SQL_CGSURG83.txt --codes test1/Data_dictionary_CGSURG83.json --plot-path policy_kg.png --show-plot
```

### 2. `patient_kg.py`
Creates knowledge graphs from patient data in various JSON formats.

**Features:**
- Auto-detects data structure (patient records, policies, data dictionaries)
- Multiple visualization layouts (spring, circular, hierarchical)
- Interactive Plotly visualizations
- Color-coded node types

**Usage:**
```bash
python patient_kg.py test1/Patient_Record.json --layout spring --figsize 15 10
```

### 3. `patient_rule_kg.py`
Evaluates patient data against policy rules and visualizes compliance.

**Features:**
- Parses SQL conditions into evaluable rules
- Compares patient data against policy criteria
- Color-codes met/unmet conditions
- Detailed evaluation summary

**Usage:**
```bash
python patient_rule_kg.py test1/Patient_Record.json test1/SQL_CGSURG83.txt test1/Data_dictionary_CGSURG83.json --figsize 16 12
```

### 4. `generate_policy_rule_kg.py`
Creates knowledge graphs focused on policy rule structure.

**Features:**
- Groups conditions by category (demographics, eligibility, requirements)
- Hierarchical rule organization
- Policy-centered visualization
- JSON export for further analysis

**Usage:**
```bash
python generate_policy_rule_kg.py --sql test1/SQL_CGSURG83.txt --data-dict test1/Data_dictionary_CGSURG83.json --plot-path policy_rules.png
```

## 📊 Data Processing Pipeline

This project follows a structured workflow for processing medical policies and patient data into knowledge graphs. Here's the detailed step-by-step process:

### Workflow Overview

```
Phase 1: Policy Processing
codes.txt + medical_policy.txt
         ↓
    data_dictionary.json
         ↓
    policy.json + code_dictionary.json
         ↓
       sql.txt
         ↓
   policy_rule_kg.png

Phase 2: Patient Processing
patient_record.json + data_dictionary.json
         ↓
    Patient Info Extraction
         ↓
    patient_kg.png + patient_rule_kg.png
```

### Phase 1: Policy Data Processing

#### Step 1: Input Files
- **`codes.txt`**: Contains medical codes and their descriptions
- **`medical_policy.txt`**: Raw medical policy text with eligibility criteria

#### Step 2: Data Dictionary Extraction
- **Output**: `data_dictionary.json`
- **Process**: Extract and structure field definitions from the medical policy
- **Purpose**: Creates a standardized schema for all policy variables
- **Structure**: Organized by sections (Demographics, Eligibility, Program Requirements, etc.)

#### Step 3: Policy Rule Extraction
- **Output**: `policy.json`
- **Process**: Parse the medical policy text into structured rule format
- **Purpose**: Converts human-readable policy into machine-readable rules
- **Features**: 
  - Logical operators (AND, OR)
  - Condition groupings
  - Hierarchical rule organization

#### Step 4: Code Dictionary Update
- **Output**: `code_dictionary.json` (updated)
- **Process**: Map medical codes to their descriptions and categories
- **Purpose**: Creates a comprehensive mapping for code interpretation

#### Step 5: SQL Conversion
- **Output**: `sql.txt`
- **Process**: Convert policy rules into SQL WHERE clauses
- **Purpose**: Enables database querying and rule evaluation
- **Features**: Complex logical conditions, parameterized queries

#### Step 6: Policy Rule Knowledge Graph
- **Output**: `policy_rule_kg.png`
- **Process**: Visualize policy rules as a knowledge graph
- **Purpose**: Understand policy structure and rule relationships
- **Features**: 
  - Policy at the center
  - Rule groups by category
  - Hierarchical organization

### Phase 2: Patient Data Processing

#### Step 1: Patient Data Input
- **Input**: `patient_record.json`
- **Content**: Complete patient profile including demographics, medical history, conditions, medications

#### Step 2: Patient Information Extraction
- **Process**: Extract patient information based on `data_dictionary.json`
- **Purpose**: Standardize patient data according to policy schema
- **Output**: Structured patient data ready for rule evaluation

#### Step 3: Patient Knowledge Graph Generation
- **Output**: `patient_kg.png`
- **Process**: Create knowledge graph from patient data
- **Purpose**: Visualize patient's medical profile and relationships
- **Features**:
  - Patient at the center
  - Medical conditions, vital signs, medications as connected nodes
  - Color-coded by data type

#### Step 4: Patient Rule Evaluation
- **Output**: `patient_rule_kg.png`
- **Process**: Evaluate patient data against policy rules
- **Purpose**: Determine policy compliance and eligibility
- **Features**:
  - Patient at the center
  - Policy rules grouped by category
  - Green edges for met conditions, red for unmet
  - Visual compliance dashboard

## 📊 Example: Bariatric Surgery Policy Analysis (test1/)

The `test1/` directory contains a complete example analyzing bariatric surgery eligibility criteria, demonstrating the full pipeline described above.

### Input Data Files

1. **Patient Record** (`Patient_Record.json`):
   - Complete patient profile: 44-year-old male (Robert Chen)
   - BMI: 40.8, with diabetes and hypertension
   - Medical history, medications, and assessment plan

2. **SQL Policy** (`SQL_CGSURG83.txt`):
   - Complex eligibility criteria for bariatric surgery
   - BMI requirements (≥40 or ≥35 with comorbidities)
   - Program requirements and procedural codes

3. **Data Dictionary** (`Data_dictionary_CGSURG83.json`):
   - Field definitions for all policy variables
   - Organized by sections: Demographics, Eligibility, Program Requirements, etc.

4. **Policy Rules** (`Policy_CGSURG83.json`):
   - Structured representation of policy restrictions
   - Machine-readable format for rule evaluation

### Generated Knowledge Graph Visualizations

The example generates three main types of knowledge graphs:

#### 1. Patient Knowledge Graph (`patient_kg_spring_15x10.png`)
Shows the patient data structure with:
- Patient information at the center
- Medical conditions, vital signs, and medications as connected nodes
- Color-coded by data type (demographics, medical conditions, etc.)

![Patient Knowledge Graph](test1/patient_kg_spring_15x10.png)

#### 2. Policy Rule Graph (`policy_rule_kg.png`)
Displays the policy rule structure:
- Policy at the center
- Rule groups organized by category
- Individual conditions and their relationships
- Hierarchical organization of eligibility criteria

![Policy Rule Graph](test1/policy_rule_kg.png)

#### 3. Patient Rule Evaluation (`patient_rule_kg.png`)
Evaluates how the patient measures against policy criteria:
- Patient at the center
- Policy rules grouped by category (demographics, eligibility, requirements)
- Green edges for met conditions, red edges for unmet conditions
- Visual compliance dashboard

![Patient Rule Evaluation](test1/patient_rule_kg.png)

### Complete Pipeline Example

Here's how to run the complete data processing pipeline using the test1 example:

#### Phase 1: Policy Processing (if starting from raw data)
```bash
# Step 1: Extract data dictionary from medical policy
# (This would typically use a script to parse medical_policy.txt)
# Output: data_dictionary.json

# Step 2: Extract policy rules and update code dictionary
# (This would parse the policy and create structured rules)
# Output: policy.json, code_dictionary.json

# Step 3: Convert policy to SQL
# (This would convert policy rules to SQL WHERE clauses)
# Output: sql.txt

# Step 4: Generate policy rule knowledge graph
python generate_policy_rule_kg.py --sql test1/SQL_CGSURG83.txt --data-dict test1/Data_dictionary_CGSURG83.json --plot-path test1/policy_rule_kg.png
```

#### Phase 2: Patient Processing
```bash
# Step 1: Generate patient knowledge graph
python patient_kg.py test1/Patient_Record.json --layout spring --figsize 15 10

# Step 2: Evaluate patient against policy rules
python patient_rule_kg.py test1/Patient_Record.json test1/SQL_CGSURG83.txt test1/Data_dictionary_CGSURG83.json --figsize 16 12
```

### Quick Start (Using Pre-processed Data)

To generate all visualizations for the test1 example using the pre-processed data:

```bash
# 1. Generate patient knowledge graph
python patient_kg.py test1/Patient_Record.json --layout spring --figsize 15 10

# 2. Evaluate patient against policy rules
python patient_rule_kg.py test1/Patient_Record.json test1/SQL_CGSURG83.txt test1/Data_dictionary_CGSURG83.json --figsize 16 12

# 3. Generate policy rule graph
python generate_policy_rule_kg.py --sql test1/SQL_CGSURG83.txt --data-dict test1/Data_dictionary_CGSURG83.json --plot-path test1/policy_rule_kg.png
```

## 🚀 Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the test1 example:
```bash
cd test1
python ../patient_kg.py Patient_Record.json
python ../patient_rule_kg.py Patient_Record.json SQL_CGSURG83.txt Data_dictionary_CGSURG83.json
python ../generate_policy_rule_kg.py --sql SQL_CGSURG83.txt --data-dict Data_dictionary_CGSURG83.json
```
