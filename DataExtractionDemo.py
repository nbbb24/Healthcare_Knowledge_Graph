import os
import re
import csv
import json
import requests
import docx
import fitz  # PyMuPDF for PDF parsing
from datetime import datetime
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup


class Tools:
    def __init__(self):
        pass

    def get_current_time(self) -> str:
        """
        Get the current time in a more human-readable format.
        """
        now = datetime.now()
        current_time = now.strftime("%I:%M:%S %p")
        current_date = now.strftime("%A, %B %d, %Y")
        return f"Current Date and Time = {current_date}, {current_time}"

    def _clean_text(self, text: str) -> str:
        """Normalize whitespace, bullet markers, and unicode quirks."""
        if not text:
            return ""
        # Replace fancy dashes
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove repeated punctuation spacing
        text = re.sub(r"\s+([,.;:])", r"\1", text)
        return text.strip()

    def extract_text_from_file(
        self,
        file_path: str = Field(..., description="Path to the document (.docx, .pdf, .txt)"),
    ) -> str:
        """
        Extract text content from Word, PDF, or TXT file.
        """
        if file_path.endswith(".docx"):
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return self._clean_text(text)
        elif file_path.endswith(".pdf"):
            text = ""
            with fitz.open(file_path) as pdf:
                for page in pdf:
                    text += page.get_text()
            return self._clean_text(text)
        elif file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                return self._clean_text(f.read())
        else:
            raise ValueError("Unsupported file format. Use .docx, .pdf, or .txt")

    def extract_text_from_url(
        self,
        url: str = Field(..., description="URL pointing to a policy document (HTML or text)."),
    ) -> str:
        """
        Download and extract text from a URL, stripping HTML noise.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (PolicyExtractionBot/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()
        if "html" in content_type or response.text.lstrip().startswith("<"):
            soup = BeautifulSoup(response.text, "html.parser")
            # Remove script/style/nav
            for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
                tag.decompose()
            text = soup.get_text(" ")
            return self._clean_text(text)
        else:
            return self._clean_text(response.text)

    def extract_policy_fields(
        self,
        text: str = Field(..., description="Raw policy text to extract fields from."),
    ):
        """
        Extract comprehensive fields from policy text for claims/patient records:
        Demographics, clinical criteria, procedures, documentation requirements, etc.
        Returns a list of (Field, Type, Example/Rule) tuples without duplicates.
        """
        text = self._clean_text(text)

        fields = []
        added = set()

        def add(field: str, ftype: str, desc: str):
            key = (field, ftype, desc)
            if key not in added:
                fields.append(key)
                added.add(key)

        # Demographics
        if re.search(r"\bage\b|\b18 years\b", text, re.IGNORECASE):
            add("patient_age", "integer", ">= 18 years")

        # Clinical Measurements
        if re.search(r"\bBMI\b|body\s*mass\s*index", text, re.IGNORECASE):
            add("patient_bmi", "float", ">= 40 OR >= 35 with comorbidity")

        # Weight and measurements
        if re.search(r"\bweight\b|\bkg\b|\bpounds\b", text, re.IGNORECASE):
            add("patient_weight", "float", "Current weight in kg/lbs")

        # CPT codes (procedure codes) - restrict to bariatric range 43xxx
        cpt_codes = sorted(set(re.findall(r"\b(43[0-9]{3})\b", text)))
        if cpt_codes:
            add("procedure_code", "string", ", ".join(cpt_codes))

        # ICD-10 codes (diagnosis codes) - exclude 'U' block, enforce max length
        icd_codes = set(re.findall(r"\b([A-TV-Z][0-9]{2}(?:\.[0-9A-TV-Z]{1,4})?)\b", text))
        if icd_codes:
            add("diagnosis_code", "string", ", ".join(sorted(icd_codes)))

        # Comorbidity conditions
        comorbidities = []
        comorbidity_patterns = {
            "diabetes": r"diabetes\s*mellitus|\bdiabetes\b",
            "cardiovascular": r"cardiovascular\s*disease|heart\s*disease",
            "hypertension": r"\bhypertension\b|high\s*blood\s*pressure",
            "sleep_apnea": r"sleep\s*apnea|obstructive\s*sleep",
            "cardiomyopathy": r"\bcardiomyopathy\b",
            "pickwickian": r"pickwickian\s*syndrome",
        }
        for condition, pattern in comorbidity_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                comorbidities.append(condition)
        if comorbidities:
            add("comorbidity_conditions", "array", ", ".join(sorted(set(comorbidities))))

        # Surgical procedures (keyword types)
        procedures = []
        procedure_patterns = {
            "roux_en_y": r"roux[-\s]?en[-\s]?y|gastric\s*bypass",
            "sleeve_gastrectomy": r"sleeve\s*gastrectomy",
            "gastric_banding": r"gastric\s*band|adjustable\s*gastric",
            "biliopancreatic": r"biliopancreatic\s*bypass",
            "vertical_banded": r"vertical\s*banded\s*gastroplasty",
        }
        for procedure, pattern in procedure_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                procedures.append(procedure)
        if procedures:
            add("surgical_procedure_type", "string", ", ".join(sorted(set(procedures))))

        # Documentation requirements
        doc_patterns = {
            "weight_loss_program": r"weight\s*loss\s*program|past\s*participation",
            "medical_evaluation": r"medical.*evaluation|pre[-\s]?operative.*medical",
            "mental_health_evaluation": r"mental\s*health\s*evaluation|psychiatric",
            "preoperative_education": r"pre[-\s]?operative\s*education|patient\s*education",
            "treatment_plan": r"treatment\s*plan",
            "conservative_therapy": r"conservative\s*medical\s*therapy|lifestyle\s*intervention",
        }
        for requirement, pattern in doc_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                add(f"{requirement}_flag", "boolean", "Required documentation")

        # Service dates and timing
        if re.search(r"date\s*of\s*service|service\s*date", text, re.IGNORECASE):
            add("date_of_service", "date", "YYYY-MM-DD format")
        if re.search(r"coverage\s*period|effective\s*date", text, re.IGNORECASE):
            add("coverage_period", "date_range", "Policy effective dates")

        # Reoperation criteria
        if re.search(r"reoperation|revision|conversion", text, re.IGNORECASE):
            add("reoperation_flag", "boolean", "Indicates revision surgery")

        # Complications
        complications = []
        complication_patterns = {
            "fistula": r"\bfistula\b",
            "obstruction": r"\bobstruction\b",
            "erosion": r"\berosion\b",
            "leakage": r"\bleakage\b|\bdisruption\b",
            "stricture": r"\bstricture\b",
            "gerd": r"gastroesophageal\s*reflux|\bGERD\b",
        }
        for complication, pattern in complication_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                complications.append(complication)
        if complications:
            add("surgical_complications", "array", ", ".join(sorted(set(complications))))

        # Authorization and approval
        if re.search(r"medically\s*necessary|medical\s*necessity", text, re.IGNORECASE):
            add("medical_necessity_flag", "boolean", "Required for coverage")
        if re.search(r"prior\s*authorization|pre[-\s]?authorization", text, re.IGNORECASE):
            add("prior_authorization_flag", "boolean", "Required before service")

        return fields

    def save_to_csv(
        self,
        fields: list = Field(..., description="List of tuples: (Field, Type, Example/Rule)."),
        output_file: str = Field("policy_fields.csv", description="Output CSV file name."),
    ) -> str:
        """
        Save extracted fields to a CSV file.
        """
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Field", "Type", "Example/Rule"])
            # Sort by field name for stability
            for row in sorted(fields, key=lambda x: (x[0], x[1])):
                writer.writerow(row)
        return f"✅ Saved extracted fields to {output_file}"

    def save_to_json(
        self,
        fields: list = Field(..., description="List of tuples: (Field, Type, Example/Rule)."),
        output_file: str = Field("policy_fields.json", description="Output JSON file name."),
    ) -> str:
        """
        Save extracted fields to a JSON file.
        """
        data = [
            {"field": f, "type": t, "example_or_rule": d}
            for f, t, d in fields
        ]
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return f"✅ Saved extracted fields to {output_file}"


# ---------------------- Example Usage ----------------------
if __name__ == "__main__":
    tools = Tools()

    # Example: local policy file
    try:
        # Prefer URL if provided via env var or edit below
        policy_url = os.environ.get("POLICY_URL", "")
        if policy_url:
            text = tools.extract_text_from_url(policy_url)
            source_label = policy_url
        else:
            text = tools.extract_text_from_file("policy1.txt")
            source_label = "policy1.txt"
        fields = tools.extract_policy_fields(text)
        print(f"✅ Extracted {len(fields)} data fields from {source_label}")
        print(tools.save_to_csv(fields, "bariatric_policy_fields.csv"))
        print(tools.save_to_json(fields, "bariatric_policy_fields.json"))
        
        # Display extracted fields
        print("\n📋 Extracted Data Fields:")
        for field_name, field_type, description in fields:
            print(f"  • {field_name} ({field_type}): {description}")
            
    except Exception as e:
        print(f"❌ Error processing local file: {e}")

    # # Example: from URL (if HTML policy page)
    # text = tools.extract_text_from_url("https://www.anthem.com/medpolicies/abc/active/gl_pw_d085821.html")
    # fields = tools.extract_policy_fields(text)
    # print(tools.save_to_csv(fields, "policy_fields_from_url.csv"))
