class DataField:
    def __init__(self, name, field_type, description=None, rule=None, values=None, examples=None):
        self.name = name
        self.field_type = field_type
        self.description = description
        self.rule = rule                  # e.g., ">= 40 OR >= 35 with comorbidity"
        self.values = values or []        # fix: add default
        self.examples = examples or []    # e.g., ICD or CPT codes

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.field_type,
            "description": self.description,
            "rule": self.rule,
            "values": self.values,
            "examples": self.examples
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name"),
            field_type=data.get("type"),
            description=data.get("description"),
            rule=data.get("rule"),
            values=data.get("values"),
            examples=data.get("examples")
        )