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
├── Database/                   # Database management and filtering system
│   ├── create_database.py      # Creates SQLite database from data dictionary
│   ├── import_data.py          # Imports patient data from JSON files
│   ├── run_filter.py           # Executes SQL queries and exports results
│   ├── patient_data_filtered.csv # Filtered patient data results
│   ├── policy_CGSURG83.db      # SQLite database file
│   └── scripts/                # Database automation scripts
├── scripts/                    # Shell scripts for batch processing
├── prompts/                    # Prompt templates for data processing
└── requirements.txt            # Python dependencies
```

## 🐍 Python Files

### 1. `patient_kg.py`
Creates knowledge graphs from patient data in various JSON formats.

**Input:**
- Patient data dictionary JSON file (e.g., `Patient_data_dictionary_200001.json`)

**Output:**
- Patient knowledge graph PNG visualization (e.g., `patient_kg_200001.png`)

**Features:**
- Auto-detects data structure (patient records, policies, data dictionaries)
- Multiple visualization layouts (spring, circular, hierarchical)
- Interactive Plotly visualizations
- Color-coded node types

**Usage:**
```bash
python patient_kg.py test1/Patient_data_dictionary/Patient_data_dictionary_200001.json --output-file test1/Patient_KG/patient_kg_200001 --no-show
```

### 2. `patient_rule_kg.py`
Evaluates patient data against policy rules and visualizes compliance.

**Input:**
- Patient data dictionary JSON file (e.g., `Patient_data_dictionary_200001.json`)
- SQL policy file (e.g., `SQL_CGSURG83.txt`)
- Policy JSON file (e.g., `Policy_CGSURG83.json`)

**Output:**
- Patient rule knowledge graph PNG visualization (e.g., `patient_rule_kg_200001.png`)
- Compliance report JSON (e.g., `pat_200001_pol_CGSURG83.json`)

**Features:**
- Parses SQL conditions into evaluable rules
- Compares patient data against policy criteria
- Color-codes met/unmet conditions (green=met, red=not met, blue=logically met by OR)
- Detailed evaluation summary

**Usage:**
```bash
python patient_rule_kg.py test1/Patient_data_dictionary/Patient_data_dictionary_200001.json test1/Policy_CGSURG83/SQL_CGSURG83.txt test1/Policy_CGSURG83/Policy_CGSURG83.json --policy-id CGSURG83 --output-file test1/Patient_Rule_KG/patient_rule_kg_200001 --compliance-dir test1/Patient_Rule_KG --no-show
```

### 3. `generate_policy_rule_kg.py`
Creates knowledge graphs focused on policy rule structure.

**Input:**
- SQL policy file (e.g., `SQL_CGSURG83.txt`)
- Data dictionary JSON file (e.g., `Data_dictionary_CGSURG83.json`)

**Output:**
- Policy rule knowledge graph PNG visualization (e.g., `policy_rule_kg.png`)
- Policy rule nodes JSON (e.g., `policy_rule_kg_nodes.json`)
- Policy rule edges JSON (e.g., `policy_rule_kg_edges.json`)

**Features:**
- Groups conditions by category (demographics, eligibility, requirements)
- Hierarchical rule organization
- Policy-centered visualization
- JSON export for further analysis

**Usage:**
```bash
python generate_policy_rule_kg.py --sql test1/Policy_CGSURG83/SQL_CGSURG83.txt --data-dict test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json --output-dir test1/Policy_CGSURG83 --plot-path test1/Policy_CGSURG83/policy_rule_kg.png
```

### 4. `DataField.py`
Data field processing utilities for extracting and structuring medical data fields.

### 5. `Policy.py`
Policy processing utilities for parsing and analyzing medical policies.

## 🗄️ Database Management System

The `Database/` folder contains a complete database management system for storing, importing, and filtering patient data using SQLite. This system provides a structured approach to data management and enables efficient querying of patient records against policy criteria.

### Database Components

#### 1. `create_database.py`
Creates a SQLite database from a data dictionary JSON file.

**Features:**
- Automatically maps JSON field types to SQLite column types
- Creates tables based on data dictionary structure
- Supports custom table names and database file names

**Usage:**
```bash
python Database/create_database.py --database policy_CGSURG83.db --dictionary ../test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json --table patients
```

#### 2. `import_data.py`
Imports patient data from JSON files into the database.

**Features:**
- Batch imports all JSON files from a directory
- Handles patient data structure automatically
- Uses INSERT OR REPLACE for data updates
- Provides import status feedback

**Usage:**
```bash
python Database/import_data.py --database policy_CGSURG83.db --data-dir ../test1/Patient_data_dictionary --table patients
```

#### 3. `run_filter.py`
Executes SQL queries on the database and exports results in multiple formats.

**Features:**
- Supports table, CSV, and JSON output formats
- Can save results to files
- Handles complex SQL queries from policy files
- Provides formatted table output

**Usage:**
```bash
python Database/run_filter.py --database policy_CGSURG83.db --sql-file ../test1/Policy_CGSURG83/SQL_CGSURG83.txt --output csv --save patient_data_filtered.csv
```

### Database Automation Scripts

The `Database/scripts/` directory contains shell scripts for automated database operations:

#### `create_db.sh`
Creates the database and table structure:
```bash
python create_database.py --database policy_CGSURG83.db --dictionary ../test1/Policy_CGSURG83/Data_dictionary_CGSURG83.json --table patients
```

#### `import_data.sh`
Imports all patient data:
```bash
python import_data.py --database policy_CGSURG83.db --data-dir ../test1/Patient_data_dictionary --table patients
```

#### `run_filters.sh`
Runs policy filters and exports results:
```bash
python run_filter.py --database policy_CGSURG83.db --sql-file ../test1/Policy_CGSURG83/SQL_CGSURG83.txt --output csv --save patient_data_filtered.csv
```

### Database Workflow

1. **Create Database**: Use `create_database.py` to create the SQLite database structure
2. **Import Data**: Use `import_data.py` to load patient data from JSON files
3. **Run Filters**: Use `run_filter.py` to execute policy queries and export results

### Sample Database Results

The `patient_data_filtered.csv` file contains the results of running policy filters on the patient database. Here's a sample of the filtered data:

```csv
patient_id,patient_id,patient_age,patient_bmi,comorbidity_flag,weight_loss_program_history,conservative_therapy_attempt,preop_medical_clearance,preop_psych_clearance,preop_education_completed,treatment_plan_documented,procedure_code_CPT,procedure_code_ICD10PCS,diagnosis_code_ICD10
200001,200001,52,42.5,0,1,1,1,1,1,1,43644,0DV60ZZ,E66.01
200002,200002,39,36.4,1,1,1,1,1,1,1,43775,0DB60Z3,Z68.36
200005,200005,28,34.8,1,1,1,1,1,1,1,43770,0D160ZA,E66.2
```


## 🚀 Automation Scripts

The `scripts/` directory contains shell scripts for batch processing multiple patients:

### `generate_all_patient_kgs.sh`
Generates patient knowledge graphs for all patients in the test1 dataset.

**What it does:**
- Loops through all `Patient_data_dictionary_*.json` files in `test1/Patient_data_dictionary/`
- Extracts patient_id from each file
- Generates `patient_kg_<patient_ID>.png` for each patient in `test1/Patient_KG/`

**Usage:**
```bash
chmod +x scripts/generate_all_patient_kgs.sh
./scripts/generate_all_patient_kgs.sh
```

### `generate_all_patient_rule_kgs.sh`
Generates patient rule knowledge graphs for all patients against policy <policy_ID>

**What it does:**
- Loops through all `Patient_data_dictionary_*.json` files
- Evaluates each patient against <policy_ID> policy
- Generates `patient_rule_kg_<patient_ID>.png` and `pat_<patient_ID>_pol_<policy_ID>.json` for each patient in `test1/Patient_Rule_KG/`

**Usage:**
```bash
chmod +x scripts/generate_all_patient_rule_kgs.sh
./scripts/generate_all_patient_rule_kgs.sh
```

### `plot_policy_rule_kg.sh`
Generates the policy rule knowledge graph for policy <policy_ID>.

**What it does:**
- Generates `policy_rule_kg.png`, `policy_rule_kg_nodes.json`, and `policy_rule_kg_edges.json` in `test1/Policy_<policy_ID>/`

**Usage:**
```bash
chmod +x scripts/plot_policy_rule_kg.sh
./scripts/plot_policy_rule_kg.sh
```

## 📊 Data Processing Pipeline

This project follows a structured workflow for processing medical policies and patient data into knowledge graphs. Here's the detailed step-by-step process:

### Workflow Overview

```
Phase 1: Policy Processing (generate_policy_rule_kg.py)
Input: SQL_<policy_ID>.txt + Data_dictionary_<policy_ID>.json
         ↓
Output: policy_rule_kg.png + policy_rule_kg_nodes.json + policy_rule_kg_edges.json

Phase 2: Patient Knowledge Graph (patient_kg.py)
Input: Patient_data_dictionary_<ID>.json
         ↓
Output: patient_kg_<ID>.png

Phase 3: Patient Rule Evaluation (patient_rule_kg.py)
Input: Patient_data_dictionary_<ID>.json + SQL_<policy_ID>.txt + Policy_<policy_ID>.json
         ↓
Output: patient_rule_kg_<ID>.png + pat_<ID>_pol_<policy_ID>.json
```

### Phase 1: Policy Rule Knowledge Graph Generation

**Script**: `generate_policy_rule_kg.py`

**Input Files:**
- `SQL_<policy_ID>.txt`: SQL WHERE clause with policy eligibility criteria
- `Data_dictionary_<policy_ID>.json`: Field definitions for all policy variables

**Output Files:**
- `policy_rule_kg.png`: Visual knowledge graph of policy rules
- `policy_rule_kg_nodes.json`: Node data for the knowledge graph
- `policy_rule_kg_edges.json`: Edge data for the knowledge graph

**Process:**
1. Parse SQL WHERE clause to extract individual conditions
2. Match conditions with data dictionary to get field descriptions
3. Group conditions by type (demographics, eligibility, requirements, procedures, diagnosis)
4. Build hierarchical knowledge graph with policy at center
5. Generate visualization and export JSON data

**Visualization Features:**
- Policy node at the center (red)
- Condition group nodes (teal)
- Individual condition nodes (blue)
- Hierarchical organization showing rule relationships

### Phase 2: Patient Knowledge Graph Generation

**Script**: `patient_kg.py`

**Input Files:**
- `Patient_data_dictionary_<ID>.json`: Patient data dictionary with demographics, conditions, medications, etc.

**Output Files:**
- `patient_kg_<ID>.png`: Visual knowledge graph of patient data

**Process:**
1. Load patient data dictionary JSON
2. Auto-detect data structure
3. Build knowledge graph with patient at center
4. Generate visualization with color-coded nodes

**Visualization Features:**
- Patient node at the center (red)
- Attribute nodes connected to patient
- Color-coded by data type (demographics, medical conditions, etc.)
- Spring layout for optimal spacing

### Phase 3: Patient Rule Evaluation

**Script**: `patient_rule_kg.py`

**Input Files:**
- `Patient_data_dictionary_<ID>.json`: Patient data dictionary
- `SQL_<policy_ID>.txt`: SQL policy conditions
- `Policy_<policy_ID>.json`: Policy rules with descriptions

**Output Files:**
- `patient_rule_kg_<ID>.png`: Visual knowledge graph showing policy compliance
- `pat_<ID>_pol_<policy_ID>.json`: Compliance report with condition evaluation results

**Process:**
1. Load patient data and policy rules
2. Parse and evaluate each SQL condition against patient data
3. Apply logical operators (AND/OR) to determine overall compliance
4. Build knowledge graph showing evaluation results
5. Generate visualization and compliance report

**Visualization Features:**
- Patient node at the center (red)
- Condition group nodes (teal) organized by AND/OR logic
- Condition nodes color-coded by status:
  - Green: Condition met
  - Blue: Logically met by other OR condition
  - Red: Condition not met
- Edge colors indicate compliance status
- Overall policy compliance status displayed at top

## 📊 Example: Bariatric Surgery Policy Analysis (test1/)

The `test1/` directory contains a complete example analyzing bariatric surgery eligibility criteria, demonstrating the full pipeline described above.

### Input Data Files

1. **Patient Records** (`Patient_data_dictionary/`):
   - Multiple patient profiles with complete medical data
   - Patient <patient_ID>: 44-year-old male (Robert Chen) with BMI 40.8, diabetes and hypertension
   - Additional patients (200002-200006, 445789123) with varied medical profiles
   - Medical history, medications, and assessment plans

2. **SQL Policy** (`Policy_<policy_ID>/SQL_<policy_ID>.txt`):
   - Complex eligibility criteria for bariatric surgery
   - BMI requirements (≥40 or ≥35 with comorbidities)
   - Program requirements and procedural codes

3. **Data Dictionary** (`Policy_<policy_ID>/Data_dictionary_<policy_ID>.json`):
   - Field definitions for all policy variables
   - Organized by sections: Demographics, Eligibility, Program Requirements, etc.

4. **Policy Rules** (`Policy_<policy_ID>/Policy_<policy_ID>.json`):
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

#### 2. Policy Rule Graph (`Policy_<policy_ID>/policy_rule_kg.png`)
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

#### Phase 1: Generate Policy Rule Knowledge Graph
```bash
python generate_policy_rule_kg.py \
  --sql test1/Policy_<policy_ID>/SQL_<policy_ID>.txt \
  --data-dict test1/Policy_<policy_ID>/Data_dictionary_<policy_ID>.json \
  --output-dir test1/Policy_<policy_ID> \
  --plot-path test1/Policy_<policy_ID>/policy_rule_kg.png
```

#### Phase 2: Generate Patient Knowledge Graphs
```bash
# For a single patient
python patient_kg.py \
  test1/Patient_data_dictionary/Patient_data_dictionary_200001.json \
  --output-file test1/Patient_KG/patient_kg_200001 \
  --no-show

# For all patients using the automation script
chmod +x scripts/generate_all_patient_kgs.sh
./scripts/generate_all_patient_kgs.sh
```

#### Phase 3: Evaluate Patients Against Policy
```bash
# For a single patient
python patient_rule_kg.py \
  test1/Patient_data_dictionary/Patient_data_dictionary_200001.json \
  test1/Policy_<policy_ID>/SQL_<policy_ID>.txt \
  test1/Policy_<policy_ID>/Policy_<policy_ID>.json \
  --policy-id <policy_ID> \
  --output-file test1/Patient_Rule_KG/patient_rule_kg_200001 \
  --compliance-dir test1/Patient_Rule_KG \
  --no-show

# For all patients using the automation script
chmod +x scripts/generate_all_patient_rule_kgs.sh
./scripts/generate_all_patient_rule_kgs.sh
```

## 🚀 Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate all visualizations:
```bash
# Generate policy rule knowledge graph
chmod +x scripts/plot_policy_rule_kg.sh
./scripts/plot_policy_rule_kg.sh

# Generate patient knowledge graphs for all patients
chmod +x scripts/generate_all_patient_kgs.sh
./scripts/generate_all_patient_kgs.sh

# Generate patient rule evaluations for all patients
chmod +x scripts/generate_all_patient_rule_kgs.sh
./scripts/generate_all_patient_rule_kgs.sh
```

3. Or run for a single patient:
```bash
# Generate policy rule KG
python generate_policy_rule_kg.py \
  --sql test1/Policy_<policy_ID>/SQL_<policy_ID>.txt \
  --data-dict test1/Policy_<policy_ID>/Data_dictionary_<policy_ID>.json \
  --output-dir test1/Policy_<policy_ID>

# Generate patient KG
python patient_kg.py \
  test1/Patient_data_dictionary/Patient_data_dictionary_<patient_ID>.json \
  --output-file test1/Patient_KG/patient_kg_<patient_ID>

# Evaluate patient against policy
python patient_rule_kg.py \
  test1/Patient_data_dictionary/Patient_data_dictionary_<patient_ID>.json \
  test1/Policy_<policy_ID>/SQL_<policy_ID>.txt \
  test1/Policy_<policy_ID>/Policy_<policy_ID>.json \
  --policy-id <policy_ID> \
  --output-file test1/Patient_Rule_KG/patient_rule_kg_<patient_ID> \
  --compliance-dir test1/Patient_Rule_KG
```
