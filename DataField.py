from typing import Any, List, Optional

class DataField:
    def __init__(self, name: str, field_type: str, description: Optional[str] = None, 
                 rule: Optional[str] = None, values: Optional[List[Any]] = None, 
                 examples: Optional[List[Any]] = None, section: Optional[str] = None):
        self.name = name
        self.field_type = field_type
        self.description = description
        self.rule = rule
        self.values = values
        self.examples = examples
        self.section = section

    def to_dict(self) -> dict:
        """Convert DataField to dictionary representation"""
        return {
            "name": self.name,
            "type": self.field_type,
            "description": self.description,
            "rule": self.rule,
            "values": self.values,
            "examples": self.examples,
            "section": self.section
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DataField':
        """Create DataField from dictionary"""
        return cls(
            name=data.get("name"),
            field_type=data.get("type"),
            description=data.get("description"),
            rule=data.get("rule"),
            values=data.get("values"),
            examples=data.get("examples"),
            section=data.get("section")
        )

    def __str__(self) -> str:
        """String representation of the field"""
        desc = f" - {self.description}" if self.description else ""
        rule_str = f" (Rule: {self.rule})" if self.rule else ""
        return f"{self.name} ({self.field_type}){desc}{rule_str}"

    def __repr__(self) -> str:
        return f"DataField(name='{self.name}', field_type='{self.field_type}')"


# Factory function to create all bariatric surgery fields matching Data_dictionary.json
def create_bariatric_fields() -> List[DataField]:
    """Create all DataField instances for bariatric surgery data"""
    return [
        DataField("patient_id", "string", "Unique patient identifier", section="Demographics"),
        DataField("date_of_birth", "date", "Patient date of birth", section="Demographics"),
        DataField("patient_age", "integer", rule="Derived from date_of_birth and date_of_service, must be >= 18 at time of surgery", section="Demographics"),
        DataField("sex", "enum", "Patient sex", values=["M", "F", "Other"], section="Demographics"),
        DataField("encounter_id", "string", "Encounter or surgery event ID", section="Encounter"),
        DataField("date_of_service", "date", "Date of surgery or evaluation", section="Encounter"),
        DataField("provider_type", "string", "Type of provider (e.g., Bariatric Surgeon)", section="Encounter"),
        DataField("patient_bmi", "float", rule=">= 40 OR >= 35 with comorbidity", section="Anthropometrics"),
        DataField("patient_weight", "float", "Current weight in kilograms or pounds", section="Anthropometrics"),
        DataField("patient_height", "float", "Height in centimeters or inches", section="Anthropometrics"),
        DataField("diagnosis_code", "ICD-10", "Relevant ICD-10 diagnosis codes for obesity and related conditions", 
                 examples=["E66.01", "E66.09", "E66.1", "E66.2", "E66.3", "E66.8", "E66.811", "E66.812", "E66.813", 
                          "E66.89", "E66.9", "E88.82", "Z68.20", "Z68.29", "Z68.30", "Z68.34", "Z68.35", "Z68.39", 
                          "Z68.41", "Z68.45", "Z68.51", "Z68.56", "Z98.84"], section="Diagnosis"),
        DataField("comorbidity_conditions", "array", "Comorbid conditions relevant to bariatric surgery", 
                 values=["diabetes", "hypertension", "cardiomyopathy", "cardiovascular", "sleep_apnea", "pickwickian"], section="Diagnosis"),
        DataField("comorbidity_flag", "boolean", rule="True if patient has at least one qualifying comorbidity", section="Diagnosis"),
        DataField("procedure_code", "CPT/ICD-10-PCS", "Bariatric surgery procedure codes considered in policy", 
                 examples=["43644", "43770", "43775", "43842", "43845", "43846", "43290", "43291", "43632", "43633", 
                          "43645", "43659", "43771", "43772", "43773", "43774", "43843", "43847", "43848", "43886", 
                          "43887", "43888", "43999"], section="Procedure"),
        DataField("surgical_procedure_type", "enum", "Categorized type of surgical procedure", 
                 values=["biliopancreatic", "gastric_banding", "roux_en_y", "sleeve_gastrectomy", "vertical_banded"], section="Procedure"),
        DataField("revision_flag", "boolean", "Indicates whether procedure is a revision/reoperation", section="Procedure"),
        DataField("weight_loss_program_flag", "boolean", "Evidence of participation in structured weight loss program", section="Documentation"),
        DataField("program_duration_months", "integer", rule="Typically 6–12 months continuous participation", section="Documentation"),
        DataField("conservative_therapy_flag", "boolean", "Attempted conservative therapy (diet, exercise, behavior modification)", section="Documentation"),
        DataField("medical_evaluation_flag", "boolean", "Pre-operative medical evaluation completed", section="Documentation"),
        DataField("mental_health_evaluation_flag", "boolean", "Pre-operative psychological/psychiatric evaluation completed", section="Documentation"),
        DataField("preoperative_education_flag", "boolean", "Completed education on risks, benefits, and follow-up requirements", section="Documentation"),
        DataField("treatment_plan_flag", "boolean", "Presence of comprehensive treatment plan covering pre- and post-operative care", section="Documentation"),
        DataField("reoperation_flag", "boolean", "Indicates whether this is a revision surgery", section="Reoperation"),
        DataField("surgical_complications", "array", "Surgical complications prompting reoperation", 
                 values=["erosion", "fistula", "gerd", "leakage", "obstruction", "stricture"], section="Reoperation"),
        DataField("reoperation_reason", "string", "Reason for reoperation", section="Reoperation"),
        DataField("medical_necessity_flag", "boolean", "Indicates whether surgery meets policy criteria for medical necessity", section="Coverage")
    ]


def generate_data_dictionary() -> List[dict]:
    """Generate the data dictionary in the target JSON format"""
    fields = create_bariatric_fields()
    return [field.to_dict() for field in fields]