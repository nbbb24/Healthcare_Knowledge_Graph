import json
import argparse
import os
import re
from typing import List, Dict, Any, Optional

# Import your existing classes
from Policy import Policy
from Restriction import Restriction
from DataField import DataField

# ----------------------
# Hugging Face Model Configuration
# ----------------------
class HuggingFaceConfig:
    """Configuration for Hugging Face models"""
    
    # Available models for different tasks
    QA_MODELS = [
        "distilbert-base-cased-distilled-squad",
        "bert-large-uncased-whole-word-masking-finetuned-squad",
        "roberta-base-squad2"
    ]
    
    NER_MODELS = [
        "dbmdz/bert-large-cased-finetuned-conll03-english",
        "dslim/bert-base-NER"
    ]
    
    TEXT_GENERATION_MODELS = [
        "microsoft/DialoGPT-medium",
        "gpt2",
        "distilgpt2"
    ]
    
    CLASSIFICATION_MODELS = [
        "bert-base-uncased",
        "roberta-base",
        "distilbert-base-uncased"
    ]


# ----------------------
# Base Extractor Class
# ----------------------
class BaseExtractor:
    """Base class for all extraction methods"""
    
    def extract_restrictions(self, policy_text: str) -> List[Restriction]:
        """Extract restrictions from policy text"""
        raise NotImplementedError("Subclasses must implement extract_restrictions")
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\-\.,;:()[\]{}]', ' ', text)
        return text.strip()


# ----------------------
# Question-Answering Based Extractor
# ----------------------
class QAExtractor(BaseExtractor):
    """Question-Answering based extraction using Hugging Face transformers"""
    
    def __init__(self, model_name: str = None):
        try:
            from transformers import pipeline
        except ImportError:
            raise ImportError("Please install transformers: pip install transformers torch")
        
        self.model_name = model_name or HuggingFaceConfig.QA_MODELS[0]
        self.qa_pipeline = pipeline(
            "question-answering",
            model=self.model_name,
            tokenizer=self.model_name
        )
    
    def extract_restrictions(self, policy_text: str) -> List[Restriction]:
        """Extract restrictions using question-answering approach"""
        
        processed_text = self._preprocess_text(policy_text)
        
        # Define questions to extract different components
        questions = [
            "What fields or attributes are mentioned in this policy?",
            "What are the restrictions or rules specified?",
            "What conditions must be satisfied?",
            "What codes or identifiers are referenced?",
            "What logical operations are used?"
        ]
        
        # Extract information using Q&A
        field_names = self._extract_with_question(processed_text, questions[0])
        rules = self._extract_with_question(processed_text, questions[1])
        conditions = self._extract_with_question(processed_text, questions[2])
        codes = self._extract_with_question(processed_text, questions[3])
        logic_ops = self._extract_with_question(processed_text, questions[4])
        
        # Parse extracted information into structured format
        restrictions = self._create_restrictions_from_extracted_data(
            field_names, rules, conditions, codes, logic_ops
        )
        
        return restrictions
    
    def _extract_with_question(self, text: str, question: str) -> List[str]:
        """Extract information using a specific question"""
        try:
            # Split text into chunks if too long (BERT has token limits)
            max_length = 400  # Conservative limit for most BERT models
            chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
            
            answers = []
            for chunk in chunks:
                if len(chunk.strip()) < 10:  # Skip very short chunks
                    continue
                    
                result = self.qa_pipeline(question=question, context=chunk)
                if result['answer'] and result['score'] > 0.1:  # Filter low-confidence answers
                    answers.append(result['answer'])
            
            return self._parse_answers(answers)
        
        except Exception as e:
            print(f"Error in Q&A extraction: {e}")
            return []
    
    def _parse_answers(self, answers: List[str]) -> List[str]:
        """Parse and clean extracted answers"""
        parsed = []
        for answer in answers:
            # Split by common delimiters
            items = re.split(r'[,;]|and|or', answer.lower())
            for item in items:
                cleaned = item.strip()
                if len(cleaned) > 2:  # Filter very short items
                    parsed.append(cleaned)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_parsed = []
        for item in parsed:
            if item not in seen:
                seen.add(item)
                unique_parsed.append(item)
        
        return unique_parsed
    
    def _create_restrictions_from_extracted_data(self, field_names, rules, conditions, codes, logic_ops):
        """Create Restriction objects from extracted data"""
        restrictions = []
        
        # Determine the maximum length to iterate over
        max_len = max(len(field_names), len(rules), len(conditions), 1)
        
        for i in range(max_len):
            field_name = field_names[i] if i < len(field_names) else f"extracted_field_{i}"
            rule = rules[i] if i < len(rules) else ""
            condition = conditions[i] if i < len(conditions) else ""
            code_list = [codes[i]] if i < len(codes) and codes[i] else []
            logic = logic_ops[i] if i < len(logic_ops) else "AND"
            
            # Only create restriction if we have meaningful content
            if field_name or rule or condition:
                # Use the correct parameter order for Restriction class
                restriction = Restriction(
                    condition_text=condition,
                    field_name=field_name,
                    rule=rule,
                    codes=code_list,
                    logic=self._normalize_logic(logic)
                )
                restrictions.append(restriction)
        
        return restrictions
    
    def _normalize_logic(self, logic_text: str) -> str:
        """Normalize logic operators"""
        logic_lower = logic_text.lower().strip()
        if any(word in logic_lower for word in ['and', '&', '&&']):
            return "AND"
        elif any(word in logic_lower for word in ['or', '|', '||']):
            return "OR"
        elif any(word in logic_lower for word in ['not', '!', 'except']):
            return "NOT"
        else:
            return "AND"  # Default


# ----------------------
# Named Entity Recognition Based Extractor
# ----------------------
class NERExtractor(BaseExtractor):
    """Named Entity Recognition based extraction"""
    
    def __init__(self, model_name: str = None):
        try:
            from transformers import pipeline
        except ImportError:
            raise ImportError("Please install transformers: pip install transformers torch")
        
        self.model_name = model_name or HuggingFaceConfig.NER_MODELS[0]
        self.ner_pipeline = pipeline(
            "ner",
            model=self.model_name,
            tokenizer=self.model_name,
            aggregation_strategy="simple"
        )
    
    def extract_restrictions(self, policy_text: str) -> List[Restriction]:
        """Extract restrictions using Named Entity Recognition"""
        
        processed_text = self._preprocess_text(policy_text)
        
        # Extract entities
        entities = self.ner_pipeline(processed_text)
        
        # Group entities by type
        field_names = []
        rules = []
        conditions = []
        
        for entity in entities:
            entity_text = entity['word'].replace('##', '')  # Clean BERT subword tokens
            entity_label = entity['entity_group']
            
            if entity['score'] > 0.5:  # Filter low-confidence entities
                if entity_label in ['MISC', 'ORG']:  # Likely field names or system names
                    field_names.append(entity_text)
                elif entity_label in ['PER', 'LOC']:  # Could be conditions or rules
                    conditions.append(entity_text)
        
        # Extract rules using pattern matching
        rules = self._extract_rules_with_patterns(processed_text)
        
        # Create restrictions
        restrictions = []
        max_len = max(len(field_names), len(rules), len(conditions), 1)
        
        for i in range(max_len):
            field_name = field_names[i] if i < len(field_names) else f"ner_field_{i}"
            rule = rules[i] if i < len(rules) else ""
            condition = conditions[i] if i < len(conditions) else ""
            
            if field_name or rule or condition:
                # Use the correct parameter order for Restriction class
                restriction = Restriction(
                    condition_text=condition,
                    field_name=field_name,
                    rule=rule,
                    codes=[],
                    logic="AND"
                )
                restrictions.append(restriction)
        
        return restrictions
    
    def _extract_rules_with_patterns(self, text: str) -> List[str]:
        """Extract rules using regex patterns"""
        patterns = [
            r'must\s+([^.]+)',
            r'shall\s+([^.]+)',
            r'should\s+([^.]+)',
            r'required\s+to\s+([^.]+)',
            r'cannot\s+([^.]+)',
            r'prohibited\s+([^.]+)',
        ]
        
        rules = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            rules.extend(matches)
        
        return [rule.strip() for rule in rules if len(rule.strip()) > 5]


# ----------------------
# Text Generation Based Extractor
# ----------------------
class TextGenerationExtractor(BaseExtractor):
    """Text generation based extraction using smaller generative models"""
    
    def __init__(self, model_name: str = None):
        try:
            from transformers import pipeline
        except ImportError:
            raise ImportError("Please install transformers: pip install transformers torch")
        
        self.model_name = model_name or HuggingFaceConfig.TEXT_GENERATION_MODELS[2]  # Use distilgpt2 as default
        self.generator = pipeline(
            "text-generation",
            model=self.model_name,
            tokenizer=self.model_name,
            max_length=200,
            num_return_sequences=1,
            do_sample=True,
            temperature=0.7
        )
    
    def extract_restrictions(self, policy_text: str) -> List[Restriction]:
        """Extract restrictions using text generation prompting"""
        
        processed_text = self._preprocess_text(policy_text)
        
        # Create prompts for extraction
        prompts = [
            f"Policy text: {processed_text[:200]}...\nField names mentioned:",
            f"Policy text: {processed_text[:200]}...\nRules specified:",
            f"Policy text: {processed_text[:200]}...\nConditions required:"
        ]
        
        extracted_data = []
        for prompt in prompts:
            try:
                result = self.generator(prompt, max_length=len(prompt) + 100, pad_token_id=50256)
                generated_text = result[0]['generated_text']
                # Extract only the generated part
                generated_part = generated_text[len(prompt):].strip()
                extracted_data.append(generated_part)
            except Exception as e:
                print(f"Error in text generation: {e}")
                extracted_data.append("")
        
        # Parse generated data into restrictions
        restrictions = self._parse_generated_data(extracted_data)
        
        return restrictions
    
    def _parse_generated_data(self, generated_data: List[str]) -> List[Restriction]:
        """Parse generated text into structured restrictions"""
        restrictions = []
        
        field_names = self._extract_items_from_generated(generated_data[0]) if len(generated_data) > 0 else []
        rules = self._extract_items_from_generated(generated_data[1]) if len(generated_data) > 1 else []
        conditions = self._extract_items_from_generated(generated_data[2]) if len(generated_data) > 2 else []
        
        max_len = max(len(field_names), len(rules), len(conditions), 1)
        
        for i in range(max_len):
            field_name = field_names[i] if i < len(field_names) else f"gen_field_{i}"
            rule = rules[i] if i < len(rules) else ""
            condition = conditions[i] if i < len(conditions) else ""
            
            if field_name or rule or condition:
                # Use the correct parameter order for Restriction class
                restriction = Restriction(
                    condition_text=condition,
                    field_name=field_name,
                    rule=rule,
                    codes=[],
                    logic="AND"
                )
                restrictions.append(restriction)
        
        return restrictions
    
    def _extract_items_from_generated(self, generated_text: str) -> List[str]:
        """Extract items from generated text"""
        if not generated_text:
            return []
        
        # Split by common delimiters
        items = re.split(r'[,\n]', generated_text)
        cleaned_items = []
        
        for item in items:
            cleaned = item.strip()
            # Filter out incomplete or very short items
            if len(cleaned) > 3 and not cleaned.startswith(('...', 'The', 'This')):
                cleaned_items.append(cleaned)
        
        return cleaned_items[:5]  # Limit to avoid noise


# ----------------------
# Hybrid Extractor (Combines Multiple Approaches)
# ----------------------
class HybridExtractor(BaseExtractor):
    """Combines multiple extraction approaches for better results"""
    
    def __init__(self, use_qa=True, use_ner=True, use_generation=False):
        self.extractors = []
        
        if use_qa:
            try:
                self.extractors.append(("QA", QAExtractor()))
            except Exception as e:
                print(f"Warning: Could not initialize QA extractor: {e}")
        
        if use_ner:
            try:
                self.extractors.append(("NER", NERExtractor()))
            except Exception as e:
                print(f"Warning: Could not initialize NER extractor: {e}")
        
        if use_generation:
            try:
                self.extractors.append(("Generation", TextGenerationExtractor()))
            except Exception as e:
                print(f"Warning: Could not initialize Generation extractor: {e}")
        
        if not self.extractors:
            raise RuntimeError("No extractors could be initialized")
    
    def extract_restrictions(self, policy_text: str) -> List[Restriction]:
        """Extract restrictions using multiple approaches and combine results"""
        
        all_restrictions = []
        
        for name, extractor in self.extractors:
            try:
                print(f"Running {name} extractor...")
                restrictions = extractor.extract_restrictions(policy_text)
                all_restrictions.extend(restrictions)
                print(f"{name} extractor found {len(restrictions)} restrictions")
            except Exception as e:
                print(f"Error with {name} extractor: {e}")
        
        # Merge and deduplicate restrictions
        merged_restrictions = self._merge_restrictions(all_restrictions)
        
        return merged_restrictions
    
    def _merge_restrictions(self, restrictions: List[Restriction]) -> List[Restriction]:
        """Merge similar restrictions and remove duplicates"""
        if not restrictions:
            return []
        
        merged = []
        seen_fields = set()
        
        for restriction in restrictions:
            # Use field name as primary key for deduplication
            if restriction.field_name not in seen_fields:
                merged.append(restriction)
                seen_fields.add(restriction.field_name)
            else:
                # Find existing restriction with same field name and enhance it
                for existing in merged:
                    if existing.field_name == restriction.field_name:
                        # Combine rules and conditions
                        if restriction.rule and restriction.rule not in existing.rule:
                            existing.rule += f" {restriction.rule}"
                        if restriction.condition_text and restriction.condition_text not in existing.condition_text:
                            existing.condition_text += f" {restriction.condition_text}"
                        # Combine codes
                        for code in restriction.codes:
                            if code not in existing.codes:
                                existing.codes.append(code)
                        break
        
        return merged


# ----------------------
# Extractor Factory
# ----------------------
class ExtractorFactory:
    """Factory class to create different types of extractors"""
    
    @staticmethod
    def create_extractor(extractor_type: str, **kwargs) -> BaseExtractor:
        """Create an extractor based on type"""
        
        extractor_type = extractor_type.lower()
        
        if extractor_type == "qa":
            return QAExtractor(**kwargs)
        elif extractor_type == "ner":
            return NERExtractor(**kwargs)
        elif extractor_type == "generation":
            return TextGenerationExtractor(**kwargs)
        elif extractor_type == "hybrid":
            return HybridExtractor(**kwargs)
        else:
            raise ValueError(f"Unknown extractor type: {extractor_type}. Available: qa, ner, generation, hybrid")


# ----------------------
# Utility Functions
# ----------------------
def load_data_dictionary(path="Data_dictionary.json"):
    """Load data dictionary from JSON file and convert to DataField objects"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # If data is list of dicts, convert to DataField objects
    if isinstance(data, list):
        return [DataField.from_dict(item) if isinstance(item, dict) else item for item in data]
    return data

def save_data_dictionary(dictionary, path="Data_dictionary.json"):
    """Save data dictionary to JSON file"""
    # Convert DataField objects to dictionaries if needed
    if dictionary and hasattr(dictionary[0], 'to_dict'):
        dict_data = [field.to_dict() for field in dictionary]
    else:
        dict_data = dictionary
        
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dict_data, f, indent=2)

def load_policy_text(policy_input):
    """Load policy text from either a raw string or a .txt file"""
    if isinstance(policy_input, str) and policy_input.endswith(".txt"):
        with open(policy_input, "r", encoding="utf-8") as f:
            return f.read()
    return policy_input

def update_data_dictionary(dictionary, restrictions):
    """Update dictionary rules based on restrictions"""
    # Handle both DataField objects and plain dictionaries
    if dictionary and hasattr(dictionary[0], 'name'):
        # Working with DataField objects
        dict_by_field = {field.name: field for field in dictionary}
        
        for r in restrictions:
            if r.field_name in dict_by_field:
                dict_by_field[r.field_name].rule = r.rule
        
        return list(dict_by_field.values())
    else:
        # Working with plain dictionaries (backward compatibility)
        dict_by_field = {f["name"]: f for f in dictionary}
        
        for r in restrictions:
            if r.field_name in dict_by_field:
                dict_by_field[r.field_name]["rule"] = r.rule
        
        return list(dict_by_field.values())

def build_policy(policy_name, guideline_number, raw_text, restrictions):
    """Build Policy object from extracted restrictions"""
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
# Main Pipeline
# ----------------------
def run_pipeline(policy_input, policy_name="New Policy", guideline_number="TEMP-001",
                 dict_path="Data_dictionary.json", policy_out="policies.json", 
                 extractor_type="hybrid", dev=False, **extractor_kwargs):
    """
    Run the policy extraction pipeline using Hugging Face models
    
    Args:
        policy_input: Policy text or file path
        policy_name: Name for the policy
        guideline_number: Policy identifier
        dict_path: Path to data dictionary
        policy_out: Output path for policies
        extractor_type: Type of extractor to use (qa, ner, generation, hybrid)
        dev: Development mode flag
        extractor_kwargs: Additional arguments for the extractor
    """
    
    print(f"Starting policy extraction pipeline with {extractor_type.upper()} extractor...")
    
    # Step 1: Load policy text
    policy_text = load_policy_text(policy_input)
    print(f"Loaded policy text ({len(policy_text)} characters)")
    
    # Step 2: Load dictionary
    dictionary = load_data_dictionary(dict_path)
    print(f"Loaded data dictionary with {len(dictionary)} fields")
    
    # Step 3: Create and use extractor
    try:
        extractor = ExtractorFactory.create_extractor(extractor_type, **extractor_kwargs)
        restrictions = extractor.extract_restrictions(policy_text)
        print(f"Extracted {len(restrictions)} restrictions")
    except Exception as e:
        print(f"Error with {extractor_type} extractor: {e}")
        print("Using empty restrictions list...")
        restrictions = []
    
    # Step 4: Update dictionary
    updated_dict = update_data_dictionary(dictionary, restrictions)
    
    # Step 5: Build policy
    policy = build_policy(policy_name, guideline_number, policy_text, restrictions)
    
    if dev:
        print(f"\n🔎 Development Mode: Using {extractor_type.upper()} extractor")
        print("\n--- Extracted Restrictions ---")
        for i, r in enumerate(restrictions):
            print(f"{i+1}. Field: {r.field_name}")
            print(f"   Rule: {r.rule}")
            print(f"   Condition: {r.condition_text}")
            print(f"   Logic: {r.logic}")
            print()
        
        print("--- Updated Data Dictionary ---")
        print(json.dumps(updated_dict[:3], indent=2))  # Show first 3 entries
        print("...")
        
        print("--- Policy Summary ---")
        print(json.dumps(policy.to_dict(), indent=2))
    else:
        # Save updated dictionary
        save_data_dictionary(updated_dict, dict_path)
        
        # Save policy JSON (append mode)
        try:
            with open(policy_out, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = [existing]
        except FileNotFoundError:
            existing = []
        
        existing.append(policy.to_dict())
        with open(policy_out, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        
        print(f"✅ Policy '{policy_name}' saved with {len(restrictions)} restrictions")
        print(f"   Data dictionary updated: {dict_path}")
        print(f"   Policy saved to: {policy_out}")
    
    return policy


# ----------------------
# Command Line Interface
# ----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Policy extraction using Hugging Face transformers models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available extractor types:
  qa          - Question-Answering based extraction (recommended)
  ner         - Named Entity Recognition based extraction
  generation  - Text generation based extraction
  hybrid      - Combines multiple approaches (default, best results)

Examples:
  python policy_extraction.py --input policy.txt --extractor qa
  python policy_extraction.py --input policy.txt --extractor hybrid --dev
  python policy_extraction.py --input "Policy text here" --extractor ner --model dslim/bert-base-NER
        """
    )
    
    parser.add_argument("--input", type=str, required=True, 
                       help="Policy text or path to .txt file")
    parser.add_argument("--name", type=str, default="New Policy", 
                       help="Policy name")
    parser.add_argument("--id", type=str, default="TEMP-001", 
                       help="Guideline number")
    parser.add_argument("--dict", type=str, default="Data_dictionary.json", 
                       help="Path to data dictionary JSON")
    parser.add_argument("--out", type=str, default="policies.json", 
                       help="Path to output policy JSON")
    parser.add_argument("--dev", action="store_true", 
                       help="Development mode: print results without saving")
    
    # Extractor options
    parser.add_argument("--extractor", type=str, 
                       choices=["qa", "ner", "generation", "hybrid"], 
                       default="hybrid", 
                       help="Choose extraction method")
    parser.add_argument("--model", type=str, 
                       help="Specific Hugging Face model to use (optional)")
    
    args = parser.parse_args()
    
    # Prepare extractor arguments
    extractor_kwargs = {}
    if args.model:
        extractor_kwargs["model_name"] = args.model
    
    # Run the pipeline
    try:
        run_pipeline(
            policy_input=args.input,
            policy_name=args.name,
            guideline_number=args.id,
            dict_path=args.dict,
            policy_out=args.out,
            extractor_type=args.extractor,
            dev=args.dev,
            **extractor_kwargs
        )
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        print("Please check your input and try again")