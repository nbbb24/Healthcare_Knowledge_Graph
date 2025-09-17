class Policy:
    def __init__(self, name, guideline_number=None, description=None, raw_text=None):
        self.name = name
        self.guideline_number = guideline_number
        self.description = description
        self.raw_text = raw_text           # store original policy text
        self.restrictions = []             # list of dicts

    def add_restriction(self, condition, rule, codes=None, logic="OR"):
        self.restrictions.append({
            "condition": condition,   # natural language condition
            "rule": rule,             # computable SQL-like logic
            "codes": codes or [],     # CPT/ICD codes
            "logic": logic            # "AND" or "OR"
        })

    def to_sql(self):
        if not self.restrictions:
            return ""
        sql_clauses = [f"({r['rule']})" for r in self.restrictions]
        # default join is OR, but can be extended per restriction["logic"]
        return " OR ".join(sql_clauses)

    def to_dict(self):
        return {
            "name": self.name,
            "guideline_number": self.guideline_number,
            "description": self.description,
            "raw_text": self.raw_text,
            "restrictions": self.restrictions
        }

    @classmethod
    def from_dict(cls, data):
        policy = cls(
            name=data.get("name"),
            guideline_number=data.get("guideline_number"),
            description=data.get("description"),
            raw_text=data.get("raw_text")
        )
        for r in data.get("restrictions", []):
            policy.add_restriction(
                condition=r["condition"],
                rule=r["rule"],
                codes=r.get("codes", []),
                logic=r.get("logic", "OR")
            )
        return policy