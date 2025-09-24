import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ExtractedCriterion:
    field_name: str
    operator: str
    value: Any
    description: str
    logic: str = "AND"

class GenericPolicyParser:
    def __init__(self):
        # Pattern templates that work for any medical policy
        self.age_patterns = [
            r'(?:age|years?)\s+(?:of\s+)?(\d+)\s+(?:years?\s+)?(?:or\s+)?(?:older|greater)',
            r'(\d+)\s+years?\s+(?:of\s+age\s+)?or\s+(?:older|above)',
            r'individual\s+is\s+age\s+(\d+)'
        ]
        
        self.bmi_patterns = [
            r'BMI\s+(?:of\s+)?(\d+(?:\.\d+)?)\s+(?:kg/m2\s+)?or\s+(?:greater|higher)',
            r'body\s+mass\s+index.*?(\d+(?:\.\d+)?)',
            r'BMI\s+≥\s*(\d+(?:\.\d+)?)'
        ]
        
        self.procedure_patterns = [
            r'(?:CPT|procedure)\s+(?:code[s]?)?\s*:?\s*((?:\d{5}(?:\s*,\s*)?)+)',
            r'following\s+procedures?\s*:?\s*((?:\d{5}(?:\s*,\s*)?)+)',
            r'recommended\s+surgery\s+is\s+one\s+of.*?((?:\d{5}(?:\s*,\s*)?)+)'
        ]
        
        self.documentation_patterns = [
            r'(medical\s+evaluation)',
            r'(mental\s+health\s+evaluation)',
            r'(weight\s+loss\s+program)',
            r'(pre-operative\s+education)',
            r'(treatment\s+plan)'
        ]
    
    def parse_policy_text(self, policy_text: str, policy_name: str) -> Dict[str, Any]:
        """Extract criteria from any medical policy text"""
        criteria = []
        
        # Extract age requirements
        age_criteria = self._extract_age_requirements(policy_text)
        if age_criteria:
            criteria.extend(age_criteria)
        
        # Extract BMI requirements
        bmi_criteria = self._extract_bmi_requirements(policy_text)
        if bmi_criteria:
            criteria.extend(bmi_criteria)
        
        # Extract procedure codes
        procedure_criteria = self._extract_procedure_requirements(policy_text)
        if procedure_criteria:
            criteria.extend(procedure_criteria)
        
        # Extract documentation requirements
        doc_criteria = self._extract_documentation_requirements(policy_text)
        if doc_criteria:
            criteria.extend(doc_criteria)
        
        return {
            "policy_name": policy_name,
            "criteria": criteria,
            "total_criteria": len(criteria)
        }
    
    def _extract_age_requirements(self, text: str) -> List[ExtractedCriterion]:
        criteria = []
        text_lower = text.lower()
        
        for pattern in self.age_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                age_threshold = int(match.group(1))
                criteria.append(ExtractedCriterion(
                    field_name="patient_age",
                    operator=">=",
                    value=age_threshold,
                    description=f"Patient must be {age_threshold} years or older"
                ))
        
        return criteria
    
    def _extract_bmi_requirements(self, text: str) -> List[ExtractedCriterion]:
        criteria = []
        text_lower = text.lower()
        
        # Look for BMI >= 40 patterns
        bmi_40_pattern = r'bmi.*?(\d+(?:\.\d+)?)\s+or\s+greater'
        matches = re.finditer(bmi_40_pattern, text_lower)
        for match in matches:
            bmi_value = float(match.group(1))
            if bmi_value >= 35:  # Only capture significant BMI thresholds
                criteria.append(ExtractedCriterion(
                    field_name="patient_bmi",
                    operator=">=",
                    value=bmi_value,
                    description=f"BMI must be {bmi_value} or greater"
                ))
        
        # Look for BMI with comorbidity patterns
        comorbid_pattern = r'bmi.*?(\d+(?:\.\d+)?)\s+.*?(?:with|comorbid|condition)'
        matches = re.finditer(comorbid_pattern, text_lower)
        for match in matches:
            bmi_value = float(match.group(1))
            criteria.append(ExtractedCriterion(
                field_name="bmi_with_comorbidity",
                operator="composite",
                value={"bmi_threshold": bmi_value, "requires_comorbidity": True},
                description=f"BMI {bmi_value} or greater with qualifying comorbidity"
            ))
        
        return criteria
    
    def _extract_procedure_requirements(self, text: str) -> List[ExtractedCriterion]:
        criteria = []
        
        # Extract CPT codes
        cpt_matches = re.finditer(r'\b(\d{5})\b', text)
        cpt_codes = list(set([match.group(1) for match in cpt_matches]))
        
        if cpt_codes:
            criteria.append(ExtractedCriterion(
                field_name="procedure_code",
                operator="in",
                value=cpt_codes,
                description=f"Procedure must be one of approved codes: {', '.join(cpt_codes[:5])}..."
            ))
        
        return criteria
    
    def _extract_documentation_requirements(self, text: str) -> List[ExtractedCriterion]:
        criteria = []
        text_lower = text.lower()
        
        doc_requirements = {
            "weight_loss_program": ["weight loss program", "weight reduction program"],
            "medical_evaluation": ["medical evaluation", "medical clearance"],
            "mental_health_evaluation": ["mental health evaluation", "psychological evaluation", "psychiatric evaluation"],
            "preoperative_education": ["pre-operative education", "preoperative education", "patient education"],
            "treatment_plan": ["treatment plan", "care plan"],
            "conservative_therapy": ["conservative therapy", "conservative treatment", "medical therapy"]
        }
        
        for field_name, search_terms in doc_requirements.items():
            for term in search_terms:
                if term in text_lower:
                    criteria.append(ExtractedCriterion(
                        field_name=f"{field_name}_flag",
                        operator="==",
                        value=True,
                        description=f"Must complete {term.replace('_', ' ')}"
                    ))
                    break  # Only add once per field
        
        return criteria

# Example usage showing flexibility
class PolicyFactory:
    def __init__(self):
        self.parser = GenericPolicyParser()
    
    def create_policy_from_text(self, policy_text: str, policy_name: str):
        """Create a policy object from any medical policy text"""
        extracted_data = self.parser.parse_policy_text(policy_text, policy_name)
        
        # Convert to your existing Policy class format
        from your_existing_code import Policy  # Import your Policy class
        
        policy = Policy(
            name=extracted_data["policy_name"],
            description=f"Auto-generated policy with {extracted_data['total_criteria']} criteria"
        )
        
        for criterion in extracted_data["criteria"]:
            # Convert extracted criteria to restriction format
            rule = self._criterion_to_rule(criterion)
            policy.add_restriction(
                condition=criterion.description,
                rule=rule,
                codes=criterion.value if criterion.operator == "in" else [],
                logic=criterion.logic
            )
        
        return policy
    
    def _criterion_to_rule(self, criterion: ExtractedCriterion) -> str:
        """Convert extracted criterion to computable rule"""
        if criterion.operator == ">=":
            return f"{criterion.field_name} >= {criterion.value}"
        elif criterion.operator == "==":
            return f"{criterion.field_name} == {criterion.value}"
        elif criterion.operator == "in":
            codes_str = str(criterion.value).replace("'", '"')
            return f"{criterion.field_name} in {codes_str}"
        elif criterion.operator == "composite":
            # Handle complex BMI + comorbidity rules
            bmi_threshold = criterion.value["bmi_threshold"]
            return f"(patient_bmi >= 40) OR (patient_bmi >= {bmi_threshold} AND comorbidity_flag == True)"
        else:
            return f"{criterion.field_name} {criterion.operator} {criterion.value}"

# Test with different policy types
def test_parser_flexibility():
    parser = GenericPolicyParser()
    factory = PolicyFactory()
    
    # Test with bariatric surgery text
    bariatric_text = """
    Gastric bypass procedures are considered medically necessary when all of the following criteria are met:
    Individual is age 18 years or older; BMI of 40 or greater, or 35 or greater with comorbidity;
    Past participation in a weight loss program; Pre-operative medical and mental health evaluations;
    """
    
    # Test with a different policy type
    cardiac_text = """
    Cardiac surgery is considered medically necessary when: 
    Patient is age 21 years or older; BMI of 45 or greater;
    Medical evaluation completed; Treatment plan established;
    """
    
    bariatric_policy = factory.create_policy_from_text(bariatric_text, "Bariatric Surgery")
    cardiac_policy = factory.create_policy_from_text(cardiac_text, "Cardiac Surgery")
    
    print(f"Bariatric policy has {len(bariatric_policy.restrictions)} restrictions")
    print(f"Cardiac policy has {len(cardiac_policy.restrictions)} restrictions")
    
    return bariatric_policy, cardiac_policy

if __name__ == "__main__":
    test_parser_flexibility()