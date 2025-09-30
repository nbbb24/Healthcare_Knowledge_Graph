# Medical Policy Knowledge Graph Generator

A Python toolkit for generating and visualizing knowledge graphs from medical policies and patient data. This project focuses on bariatric surgery policies and creates visualizations to understand complex medical decision rules.

## 📁 Project Structure

```
├── patient_kg.py               # Patient data knowledge graph visualizer
├── patient_rule_kg.py          # Patient vs policy rule evaluator
├── generate_policy_rule_kg.py  # Policy rule knowledge graph generator
├── DataField.py                # Data field processing utilities
├── Policy.py                   # Policy processing utilities
├── test1/                      # Example data and outputs
│   ├── Patient_data_dictionary/ # Patient data dictionaries for multiple patients
│   ├── Patient_KG/             # Generated patient knowledge graphs
│   ├── Patient_Rule_KG/        # Generated patient rule knowledge graphs
│   └── Policy_CGSURG83/        # Policy data and generated visualizations
├── scripts/                    # Shell scripts for batch processing
├── prompts/                    # Prompt templates for data processing
└── requirements.txt            # Python dependencies
```

## 🐍 Python Files

### 1. `patient_kg.py`
Creates knowledge graphs from patient data in various JSON formats.

**Features:**
- Auto-detects data structure (patient records, policies, data dictionaries)
- Multiple visualization layouts (spring, circular, hierarchical)
- Interactive Plotly visualizations
- Color-coded node types

**Usage:**
```bash
python patient_kg.py test1/Patient_Record1.json --layout spring --figsize 15 10
```

### 2. `patient_rule_kg.py`
Evaluates patient data against policy rules and visualizes compliance.

**Features:**
- Parses SQL conditions into evaluable rules
- Compares patient data against policy criteria
- Color-codes met/unmet conditions
- Detailed evaluation summary

**Usage:**
```bash
python patient_rule_kg.py test1/Patient_Record1.json test1/Policy_CGSURG83/SQL_CGSURG83.txt test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json --figsize 16 12
```

### 3. `generate_policy_rule_kg.py`
Creates knowledge graphs focused on policy rule structure.

**Features:**
- Groups conditions by category (demographics, eligibility, requirements)
- Hierarchical rule organization
- Policy-centered visualization
- JSON export for further analysis

**Usage:**
```bash
python generate_policy_rule_kg.py --sql test1/Policy_CGSURG83/SQL_CGSURG83.txt --data-dict test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json --plot-path policy_rules.png
```

### 4. `DataField.py`
Data field processing utilities for extracting and structuring medical data fields.

### 5. `Policy.py`
Policy processing utilities for parsing and analyzing medical policies.

## 🚀 Automation Scripts

The `scripts/` directory contains shell scripts for batch processing multiple patients:

### `generate_all_patient_kgs.sh`
Generates patient knowledge graphs for all patients in the test1 dataset.

**Usage:**
```bash
chmod +x scripts/generate_all_patient_kgs.sh
./scripts/generate_all_patient_kgs.sh
```

### `generate_all_patient_rule_kgs.sh`
Generates patient rule knowledge graphs for all patients against policy rules.

**Usage:**
```bash
chmod +x scripts/generate_all_patient_rule_kgs.sh
./scripts/generate_all_patient_rule_kgs.sh
```

### `plot_patient_kg.sh`, `plot_patient_rule_kg.sh`, `plot_policy_rule_kg.sh`
Individual plotting scripts for specific visualizations.

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

1. **Patient Records** (`Patient_data_dictionary/`):
   - Multiple patient profiles with complete medical data
   - Patient 200001: 44-year-old male (Robert Chen) with BMI 40.8, diabetes and hypertension
   - Additional patients (200002-200006, 445789123) with varied medical profiles
   - Medical history, medications, and assessment plans

2. **SQL Policy** (`Policy_CGSURG83/SQL_CGSURG83.txt`):
   - Complex eligibility criteria for bariatric surgery
   - BMI requirements (≥40 or ≥35 with comorbidities)
   - Program requirements and procedural codes

3. **Data Dictionary** (`Policy_CGSURG83/Data_dictionary_CGSURG83.json`):
   - Field definitions for all policy variables
   - Organized by sections: Demographics, Eligibility, Program Requirements, etc.

4. **Policy Rules** (`Policy_CGSURG83/Policy_CGSURG83.json`):
   - Structured representation of policy restrictions
   - Machine-readable format for rule evaluation

### Generated Knowledge Graph Visualizations

The example generates multiple knowledge graphs for each patient:

#### 1. Patient Knowledge Graphs (`Patient_KG/patient_kg_*.png`)
Shows individual patient data structures with:
- Patient information at the center
- Medical conditions, vital signs, and medications as connected nodes
- Color-coded by data type (demographics, medical conditions, etc.)
- Generated for each patient (200001-200006, 445789123)

#### 2. Policy Rule Graph (`Policy_CGSURG83/policy_rule_kg.png`)
Displays the policy rule structure:
- Policy at the center
- Rule groups organized by category
- Individual conditions and their relationships
- Hierarchical organization of eligibility criteria

#### 3. Patient Rule Evaluations (`Patient_Rule_KG/patient_rule_kg_*.png`)
Evaluates how each patient measures against policy criteria:
- Patient at the center
- Policy rules grouped by category (demographics, eligibility, requirements)
- Green edges for met conditions, red edges for unmet conditions
- Visual compliance dashboard for each patient

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
python generate_policy_rule_kg.py --sql test1/Policy_CGSURG83/SQL_CGSURG83.txt --data-dict test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json --plot-path test1/Policy_CGSURG83/policy_rule_kg.png
```

#### Phase 2: Patient Processing
```bash
# Step 1: Generate patient knowledge graph
python patient_kg.py test1/Patient_Record1.json --layout spring --figsize 15 10

# Step 2: Evaluate patient against policy rules
python patient_rule_kg.py test1/Patient_Record1.json test1/Policy_CGSURG83/SQL_CGSURG83.txt test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json --figsize 16 12
```

### Quick Start (Using Pre-processed Data)

To generate all visualizations for the test1 example using the pre-processed data:

```bash
# Option 1: Generate for individual patient
python patient_kg.py test1/Patient_Record1.json --layout spring --figsize 15 10
python patient_rule_kg.py test1/Patient_Record1.json test1/Policy_CGSURG83/SQL_CGSURG83.txt test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json --figsize 16 12

# Option 2: Generate for all patients using automation scripts
chmod +x scripts/generate_all_patient_kgs.sh
chmod +x scripts/generate_all_patient_rule_kgs.sh
./scripts/generate_all_patient_kgs.sh
./scripts/generate_all_patient_rule_kgs.sh

# 3. Generate policy rule graph
python generate_policy_rule_kg.py --sql test1/Policy_CGSURG83/SQL_CGSURG83.txt --data-dict test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json --plot-path test1/Policy_CGSURG83/policy_rule_kg.png
```

## 🚀 Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the test1 example:
```bash
# Generate for individual patient
python patient_kg.py test1/Patient_Record1.json
python patient_rule_kg.py test1/Patient_Record1.json test1/Policy_CGSURG83/SQL_CGSURG83.txt test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json
python generate_policy_rule_kg.py --sql test1/Policy_CGSURG83/SQL_CGSURG83.txt --data-dict test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json

# Or generate for all patients at once
chmod +x scripts/generate_all_patient_kgs.sh scripts/generate_all_patient_rule_kgs.sh
./scripts/generate_all_patient_kgs.sh
./scripts/generate_all_patient_rule_kgs.sh
```
