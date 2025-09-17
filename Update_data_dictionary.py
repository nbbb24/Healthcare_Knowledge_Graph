import json
import re
import argparse
from transformers import pipeline
from DataField import DataField
from Policy import Policy
from Restriction import Restriction


# ----------------------
# Step 1: Load & Save Data Dictionary
# ----------------------
def load_data_dictionary(path="Data_dictionary.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data_dictionary(dictionary, path="Data_dictionary.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, indent=2)


# ----------------------
# Step 2: Load Policy Text
# ----------------------
def load_policy_text(policy_input):
    """
    Load policy text from either a raw string or a .txt file.
    """
    if isinstance(policy_input, str) and policy_input.endswith(".txt"):
        with open(policy_input, "r", encoding="utf-8") as f:
            return f.read()
    return policy_input


# ----------------------
# Step 3: NLP Extraction (BERT + Regex)
# ----------------------
ner_model = pipeline("ner", model="dslim/bert-base-NER")

def extract_conditions_from_text(policy_text):
    """
    Extract restrictions from raw policy text.
    Uses regex + BERT (NER) as a helper for named entities.
    Returns a list of Restriction objects.
    """
    restrictions = []

    # Regex: age condition
    age_pattern = re.search(r"(\d+)\s*(?:years|year)?\s*or older", policy_text, re.IGNORECASE)
    if age_pattern:
        age_val = age_pattern.group(1)
        restrictions.append(
            Restriction(
                condition_text=f"Age ≥ {age_val}",
                field_name="patient_age",
                rule=f"patient_age >= {age_val}"
            )
        )

    # Regex: BMI ≥ 40
    if "BMI" in policy_text and "40" in policy_text:
        restrictions.append(
            Restriction(
                condition_text="BMI ≥ 40",
                field_name="patient_bmi",
                rule="patient_bmi >= 40"
            )
        )

    # Regex: BMI ≥ 35 with comorbidity
    if "BMI" in policy_text and "35" in policy_text and "comorbidity" in policy_text.lower():
        restrictions.append(
            Restriction(
                condition_text="BMI ≥ 35 with comorbidity",
                field_name="patient_bmi",
                rule="patient_bmi >= 35 AND comorbidity_flag = 1"
            )
        )

    # Regex: program duration (e.g., 6–12 months)
    duration_pattern = re.search(r"(\d+)[–-](\d+)\s*months", policy_text, re.IGNORECASE)
    if duration_pattern:
        low, high = duration_pattern.groups()
        restrictions.append(
            Restriction(
                condition_text=f"Must complete {low}-{high} months program",
                field_name="program_duration_months",
                rule=f"program_duration_months BETWEEN {low} AND {high}"
            )
        )

    return restrictions


# ----------------------
# Step 4: Update Dictionary
# ----------------------
def update_data_dictionary(dictionary, restrictions):
    """
    Update dictionary rules based on extracted restrictions.
    """
    for r in restrictions:
        if r.field_name == "patient_age":
            dictionary["Demographics"]["patient_age"]["rule"] = r.rule
        elif r.field_name == "patient_bmi":
            dictionary["Anthropometrics"]["patient_bmi"]["rule"] = r.rule
        elif r.field_name == "program_duration_months":
            dictionary["Documentation"]["program_duration_months"]["rule"] = r.rule
        elif r.field_name == "comorbidity_flag":
            dictionary["Diagnosis"]["comorbidity_flag"]["rule"] = r.rule
    return dictionary


# ----------------------
# Step 5: Build Policy
# ----------------------
def build_policy(policy_name, guideline_number, raw_text, restrictions):
    policy = Policy(name=policy_name, guideline_number=guideline_number, raw_text=raw_text)
    for r in restrictions:
        policy.add_restriction(
            condition=r.condition_text,
            rule=r.rule,
            codes=r.codes,
            logic=r.logic
        )
    return policy


# ----------------------
# Step 6: Run Full Pipeline
# ----------------------
def run_pipeline(policy_input, policy_name="New Policy", guideline_number="TEMP-001", dict_path="Data_dictionary.json", policy_out="policies.json"):
    # Step 1: Load policy text (raw string or .txt file)
    policy_text = load_policy_text(policy_input)

    # Step 2: Load dictionary
    dictionary = load_data_dictionary(dict_path)

    # Step 3: Extract restrictions
    restrictions = extract_conditions_from_text(policy_text)

    # Step 4: Update dictionary
    updated_dict = update_data_dictionary(dictionary, restrictions)
    save_data_dictionary(updated_dict, dict_path)

    # Step 5: Build policy
    policy = build_policy(policy_name, guideline_number, policy_text, restrictions)

    # Step 6: Export policy JSON
    with open(policy_out, "w", encoding="utf-8") as f:
        json.dump(policy.to_dict(), f, indent=2)

    # Step 7: Print SQL-like expression
    print("Generated SQL:", policy.to_sql())
    return policy


# ----------------------
# Main for Debugging
# ----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run policy extraction and update data dictionary.")
    parser.add_argument("--input", type=str, required=True, help="Policy text or path to .txt file")
    parser.add_argument("--name", type=str, default="New Policy", help="Policy name")
    parser.add_argument("--id", type=str, default="TEMP-001", help="Guideline number")
    parser.add_argument("--dict", type=str, default="Data_dictionary.json", help="Path to data dictionary JSON")
    parser.add_argument("--out", type=str, default="policies.json", help="Path to output policy JSON")

    args = parser.parse_args()

    run_pipeline(
        policy_input=args.input,
        policy_name=args.name,
        guideline_number=args.id,
        dict_path=args.dict,
        policy_out=args.out
    )