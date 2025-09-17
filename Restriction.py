class Restriction:
    def __init__(self, condition_text, field_name=None, rule=None, codes=None, logic="AND"):
        """
        A Restriction represents a single atomic condition extracted from a policy.
        It acts as a bridge between the raw text (policy language) and the computable rule (SQL-like).

        Args:
            condition_text (str): Original condition text from the policy (e.g., "BMI ≥35 with comorbidity")
            field_name (str): Name of the related DataField (e.g., "patient_bmi")
            rule (str): Computable SQL-like rule (e.g., "patient_bmi >= 35 AND comorbidity_flag = 1")
            codes (list): Related CPT/ICD codes, if any
            logic (str): Logical operator for combining with other restrictions ("AND" or "OR")
        """
        self.condition_text = condition_text
        self.field_name = field_name
        self.rule = rule
        self.codes = codes or []
        self.logic = logic

    def to_dict(self):
        """
        Convert the restriction to a dictionary representation (for JSON export).
        """
        return {
            "condition_text": self.condition_text,
            "field_name": self.field_name,
            "rule": self.rule,
            "codes": self.codes,
            "logic": self.logic
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a Restriction instance from a dictionary (JSON import).
        """
        return cls(
            condition_text=data.get("condition_text"),
            field_name=data.get("field_name"),
            rule=data.get("rule"),
            codes=data.get("codes"),
            logic=data.get("logic", "AND")
        )