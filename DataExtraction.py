"""
Data Extraction Module - Step 1
===============================

This module handles extracting structured criteria from natural language medical policy text.
It uses NLP and regex patterns to identify age requirements, BMI thresholds, procedure codes,
diagnosis codes, and documentation requirements.

Author: Policy Automation Pipeline
Date: 2025
"""

import re
import os
try:
    import spacy  # Optional; extractor works without spaCy
except Exception:  # ModuleNotFoundError or other import issues
    spacy = None
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtractedCriterion:
    """Structured representation of a policy criterion"""
    id: str
    type: str  # 'age', 'bmi', 'procedure', 'diagnosis', 'documentation', 'temporal'
    field: str
    operator: Optional[str] = None
    value: Any = None
    description: str = ""
    confidence: float = 1.0
    source_text: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class PolicyTextExtractor:
    """
    Extracts structured criteria from natural language policy text.
    
    Uses a combination of regex patterns, NLP models, and domain-specific
    knowledge to identify and structure policy requirements.
    """
    
    def __init__(self, use_medical_nlp: bool = True):
        """
        Initialize the extractor with optional medical NLP models.
        
        Args:
            use_medical_nlp: Whether to use specialized medical NLP models
        """
        self.use_medical_nlp = use_medical_nlp
        self._load_nlp_models()
        self._initialize_patterns()
        
        # Statistics tracking
        self.extraction_stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'extraction_types': {}
        }
    
    def _load_nlp_models(self):
        """Load NLP models for text processing"""
        try:
            if spacy is None:
                raise OSError("spaCy not installed")
            if self.use_medical_nlp:
                # Try to load medical spaCy model
                self.nlp = spacy.load("en_core_sci_md")
                logger.info("Loaded medical NLP model: en_core_sci_md")
            else:
                raise OSError("Medical model not requested")
                
        except OSError:
            # Fallback to standard English model
            try:
                if spacy is None:
                    raise OSError("spaCy not available")
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded standard NLP model: en_core_web_sm")
            except OSError:
                logger.warning("No spaCy models available. Text processing will be limited.")
                self.nlp = None
    
    def _initialize_patterns(self):
        """Initialize regex patterns for different types of criteria"""
        self.extraction_patterns = {
            'age': [
                r'(?:patient\s+must\s+be\s+)?(\d+)\s+years?\s+(?:of\s+age\s+)?or\s+older',
                r'age\s*(?:≥|>=|greater\s+than\s+or\s+equal\s+to)\s*(\d+)',
                r'(?:minimum\s+)?age\s*:\s*(\d+)',
                r'(?:patients?\s+)?(?:aged?\s+)?(\d+)\s*\+',
                r'(\d+)\s+years?\s+and\s+above'
            ],
            'bmi': [
                r'BMI\s*(?:≥|>=)\s*(\d+(?:\.\d+)?)',
                r'body\s+mass\s+index\s*(?:≥|>=)\s*(\d+(?:\.\d+)?)',
                r'BMI\s*(?:≥|>=)\s*(\d+(?:\.\d+)?)\s+(?:with|and)\s+(.+?)(?:\.|,|;|$)',
                r'BMI\s+of\s+(\d+(?:\.\d+)?)\s+or\s+(?:higher|greater)',
                r'BMI\s*(?:≤|<=)\s*(\d+(?:\.\d+)?)'  # Upper limits
            ],
            'procedure_codes': [
                r'CPT\s+codes?\s*:?\s*((?:\d{5}(?:\s*,\s*)?)+)',
                r'procedure\s+codes?\s*:?\s*((?:\d{5}(?:\s*,\s*)?)+)',
                r'(\d{5})\s*\([^)]+\)',  # Code with description
                r'codes?\s*(?:\d{5}(?:\s*,\s*\d{5})*)',
                r'following\s+procedures?\s*:?\s*((?:\d{5}(?:\s*,\s*)?)+)'
            ],
            'diagnosis_codes': [
                r'ICD(?:-?10)?\s+codes?\s*:?\s*((?:[A-Z]\d{2}\.?\d*(?:\s*,\s*)?)+)',
                r'([A-Z]\d{2}\.?\d*)\s*\([^)]+\)',  # ICD with description
                r'diagnosis\s+codes?\s*:?\s*((?:[A-Z]\d{2}\.?\d*(?:\s*,\s*)?)+)',
                r'([A-Z]\d{2}\.?\d*)(?:\s*-\s*[A-Z]\d{2}\.?\d*)?',  # Range of codes
                r'ICD-10\s*:?\s*([A-Z]\d{2}\.?\d*(?:\s*,\s*[A-Z]\d{2}\.?\d*)*)'
            ],
            'documentation': [
                r'evidence\s+of\s+(.+?)(?:\s+\((\d+)[-–](\d+)\s+months?\))?',
                r'pre-?operative\s+(.+?)\s+evaluation',
                r'documentation\s+(?:of\s+)?(.+?)(?:\.|,|;|must|required)',
                r'patient\s+(?:must\s+)?(?:have\s+)?received\s+(.+?)(?:\.|,|;)',
                r'(?:completion\s+of|completed)\s+(.+?)(?:\.|,|;)',
                r'required\s*:?\s*(.+?)(?:\.|,|;|$)'
            ],
            'temporal': [
                r'(\d+)[-–](\d+)\s+months?',
                r'within\s+(\d+)\s+(?:days?|weeks?|months?|years?)',
                r'(?:during|within)\s+(?:the\s+)?(.+?)\s+period',
                r'coverage\s+period',
                r'date\s+of\s+service'
            ],
            'exclusions': [
                r'not\s+covered',
                r'excluded?',
                r'contraindicated',
                r'not\s+medically\s+necessary'
            ]
        }
        
        # Compile patterns for better performance
        self.compiled_patterns = {}
        for category, patterns in self.extraction_patterns.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                for pattern in patterns
            ]
    
    def extract_criteria(self, policy_text: str, policy_name: str) -> List[ExtractedCriterion]:
        """
        Extract all criteria from policy text.
        
        Args:
            policy_text: Raw policy text to analyze
            policy_name: Name of the policy for ID generation
            
        Returns:
            List of extracted criteria with structured data
        """
        logger.info(f"Starting extraction for policy: {policy_name}")
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(policy_text)
        
        # Extract different types of criteria
        all_criteria = []
        
        # Age criteria
        age_criteria = self._extract_age_criteria(cleaned_text)
        all_criteria.extend(age_criteria)
        
        # BMI criteria
        bmi_criteria = self._extract_bmi_criteria(cleaned_text)
        all_criteria.extend(bmi_criteria)
        
        # Procedure criteria
        procedure_criteria = self._extract_procedure_criteria(cleaned_text)
        all_criteria.extend(procedure_criteria)
        
        # Diagnosis criteria
        diagnosis_criteria = self._extract_diagnosis_criteria(cleaned_text)
        all_criteria.extend(diagnosis_criteria)
        
        # Documentation criteria
        doc_criteria = self._extract_documentation_criteria(cleaned_text)
        all_criteria.extend(doc_criteria)
        
        # Temporal criteria
        temporal_criteria = self._extract_temporal_criteria(cleaned_text)
        all_criteria.extend(temporal_criteria)
        
        # Assign unique IDs and add metadata
        for i, criterion in enumerate(all_criteria):
            criterion.id = f"{policy_name.lower()}_{criterion.type}_{i}"
            criterion.metadata['extraction_timestamp'] = datetime.now().isoformat()
            criterion.metadata['policy_name'] = policy_name
        
        # Update statistics
        self._update_extraction_stats(all_criteria)
        
        logger.info(f"Extracted {len(all_criteria)} criteria from {policy_name}")
        return all_criteria
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize policy text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize operators
        text = text.replace('≥', '>=').replace('≤', '<=')
        text = text.replace('greater than or equal to', '>=')
        text = text.replace('less than or equal to', '<=')
        
        # Normalize bullet points and lists
        text = re.sub(r'^[\s]*[-•*]\s+', '', text, flags=re.MULTILINE)
        
        # Remove extra punctuation
        text = re.sub(r'\s+([,.;:])', r'\1', text)
        
        # Normalize common medical abbreviations
        abbreviations = {
            'pts?': 'patient',
            'pt\.': 'patient',
            'yrs?': 'years',
            'yr\.': 'year',
            'mos?': 'months',
            'mo\.': 'month'
        }
        
        for abbrev, full_form in abbreviations.items():
            text = re.sub(abbrev, full_form, text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _extract_age_criteria(self, text: str) -> List[ExtractedCriterion]:
        """Extract age-related criteria"""
        criteria = []
        
        for pattern in self.compiled_patterns['age']:
            matches = pattern.finditer(text)
            for match in matches:
                try:
                    age_value = int(match.group(1))
                    
                    # Determine operator based on context
                    operator = ">=" if "or older" in match.group(0).lower() else ">="
                    
                    criterion = ExtractedCriterion(
                        id="",  # Will be set later
                        type="age",
                        field="patient_age",
                        operator=operator,
                        value=age_value,
                        description=f"Patient must be {age_value} years or older",
                        source_text=match.group(0).strip(),
                        confidence=0.95,
                        metadata={
                            'pattern_used': pattern.pattern,
                            'match_position': match.span()
                        }
                    )
                    criteria.append(criterion)
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing age criterion: {e}")
                    continue
        
        # Remove duplicates
        return self._deduplicate_criteria(criteria)
    
    def _extract_bmi_criteria(self, text: str) -> List[ExtractedCriterion]:
        """Extract BMI-related criteria"""
        criteria = []
        
        for pattern in self.compiled_patterns['bmi']:
            matches = pattern.finditer(text)
            for match in matches:
                try:
                    bmi_value = float(match.group(1))
                    
                    # Check for operator in the pattern
                    operator = ">=" if ">=" in match.group(0) else ">="
                    if "<=" in match.group(0):
                        operator = "<="
                    
                    # Check for comorbidity requirements
                    comorbidity_text = ""
                    if len(match.groups()) > 1 and match.group(2):
                        comorbidity_text = match.group(2).strip()
                    
                    description = f"BMI {operator} {bmi_value}"
                    if comorbidity_text:
                        description += f" with {comorbidity_text}"
                    
                    criterion = ExtractedCriterion(
                        id="",
                        type="bmi",
                        field="patient_bmi",
                        operator=operator,
                        value=bmi_value,
                        description=description,
                        source_text=match.group(0).strip(),
                        confidence=0.9,
                        metadata={
                            'comorbidity_requirement': comorbidity_text,
                            'pattern_used': pattern.pattern
                        }
                    )
                    criteria.append(criterion)
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing BMI criterion: {e}")
                    continue
        
        return self._deduplicate_criteria(criteria)
    
    def _extract_procedure_criteria(self, text: str) -> List[ExtractedCriterion]:
        """Extract procedure code criteria"""
        all_codes = set()
        source_texts = []
        
        for pattern in self.compiled_patterns['procedure_codes']:
            matches = pattern.finditer(text)
            for match in matches:
                # Extract individual CPT codes
                codes_text = match.group(0)
                codes = re.findall(r'\d{5}', codes_text)
                all_codes.update(codes)
                source_texts.append(match.group(0).strip())
        
        if all_codes:
            criterion = ExtractedCriterion(
                id="",
                type="procedure",
                field="procedure_code",
                operator="in",
                value=sorted(list(all_codes)),
                description=f"Procedure must be one of: {', '.join(sorted(all_codes))}",
                source_text="; ".join(source_texts),
                confidence=0.95,
                metadata={
                    'code_count': len(all_codes),
                    'code_system': 'CPT'
                }
            )
            return [criterion]
        
        return []
    
    def _extract_diagnosis_criteria(self, text: str) -> List[ExtractedCriterion]:
        """Extract diagnosis code criteria"""
        all_codes = set()
        source_texts = []
        
        for pattern in self.compiled_patterns['diagnosis_codes']:
            matches = pattern.finditer(text)
            for match in matches:
                # Extract ICD-10 codes
                codes_text = match.group(0)
                codes = re.findall(r'[A-Z]\d{2}\.?\d*', codes_text)
                all_codes.update(codes)
                source_texts.append(match.group(0).strip())
        
        if all_codes:
            criterion = ExtractedCriterion(
                id="",
                type="diagnosis",
                field="diagnosis_codes",
                operator="contains_any",
                value=sorted(list(all_codes)),
                description=f"Must have qualifying diagnosis: {', '.join(sorted(all_codes))}",
                source_text="; ".join(source_texts),
                confidence=0.9,
                metadata={
                    'code_count': len(all_codes),
                    'code_system': 'ICD-10'
                }
            )
            return [criterion]
        
        return []
    
    def _extract_documentation_criteria(self, text: str) -> List[ExtractedCriterion]:
        """Extract documentation requirements"""
        criteria = []
        
        for pattern in self.compiled_patterns['documentation']:
            matches = pattern.finditer(text)
            for match in matches:
                try:
                    doc_type = match.group(1).strip().lower()
                    
                    # Skip if it's too generic
                    if len(doc_type) < 3 or doc_type in ['the', 'and', 'or', 'a']:
                        continue
                    
                    # Create field name from documentation type
                    field_name = f"documentation_{re.sub(r'[^a-zA-Z0-9]', '_', doc_type)}"
                    
                    # Check for duration requirements
                    duration_info = ""
                    if len(match.groups()) >= 3:
                        min_months = match.group(2)
                        max_months = match.group(3)
                        if min_months and max_months:
                            duration_info = f" ({min_months}-{max_months} months)"
                    
                    criterion = ExtractedCriterion(
                        id="",
                        type="documentation",
                        field=field_name,
                        operator="==",
                        value=True,
                        description=f"Required: {doc_type.title()}{duration_info}",
                        source_text=match.group(0).strip(),
                        confidence=0.8,
                        metadata={
                            'document_type': doc_type,
                            'duration_requirement': duration_info
                        }
                    )
                    criteria.append(criterion)
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing documentation criterion: {e}")
                    continue
        
        return self._deduplicate_criteria(criteria)
    
    def _extract_temporal_criteria(self, text: str) -> List[ExtractedCriterion]:
        """Extract temporal/timing requirements"""
        criteria = []
        
        for pattern in self.compiled_patterns['temporal']:
            matches = pattern.finditer(text)
            for match in matches:
                try:
                    criterion = ExtractedCriterion(
                        id="",
                        type="temporal",
                        field="temporal_requirement",
                        operator="within",
                        value=match.group(0).strip(),
                        description=f"Timing requirement: {match.group(0).strip()}",
                        source_text=match.group(0).strip(),
                        confidence=0.7,
                        metadata={
                            'temporal_type': 'duration' if 'month' in match.group(0) else 'period'
                        }
                    )
                    criteria.append(criterion)
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing temporal criterion: {e}")
                    continue
        
        return self._deduplicate_criteria(criteria)
    
    def _deduplicate_criteria(self, criteria: List[ExtractedCriterion]) -> List[ExtractedCriterion]:
        """Remove duplicate criteria based on type, field, and value"""
        seen = set()
        unique_criteria = []
        
        for criterion in criteria:
            # Create a signature for deduplication
            signature = (criterion.type, criterion.field, str(criterion.value))
            
            if signature not in seen:
                seen.add(signature)
                unique_criteria.append(criterion)
        
        return unique_criteria
    
    def _update_extraction_stats(self, criteria: List[ExtractedCriterion]):
        """Update extraction statistics"""
        self.extraction_stats['total_extractions'] += 1
        self.extraction_stats['successful_extractions'] += len(criteria)
        
        for criterion in criteria:
            criterion_type = criterion.type
            if criterion_type not in self.extraction_stats['extraction_types']:
                self.extraction_stats['extraction_types'][criterion_type] = 0
            self.extraction_stats['extraction_types'][criterion_type] += 1
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics"""
        return self.extraction_stats.copy()
    
    def extract_from_file(self, file_path: str, policy_name: Optional[str] = None) -> List[ExtractedCriterion]:
        """
        Extract criteria from a text file.
        
        Args:
            file_path: Path to the text file containing policy text
            policy_name: Name of the policy (if None, uses filename without extension)
            
        Returns:
            List of extracted criteria with structured data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file
        """
        # Validate file path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Policy file not found: {file_path}")
        
        # Generate policy name from filename if not provided
        if policy_name is None:
            policy_name = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as file:
                policy_text = file.read()
            
            logger.info(f"Successfully read policy file: {file_path}")
            logger.info(f"File size: {len(policy_text)} characters")
            
            # Extract criteria using existing method
            return self.extract_criteria(policy_text, policy_name)
            
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    policy_text = file.read()
                logger.warning(f"Read file with latin-1 encoding: {file_path}")
                return self.extract_criteria(policy_text, policy_name)
            except Exception as e:
                raise IOError(f"Error reading file {file_path}: {e}")
        except Exception as e:
            raise IOError(f"Error reading file {file_path}: {e}")
    
    def extract_from_multiple_files(self, file_paths: List[str]) -> Dict[str, List[ExtractedCriterion]]:
        """
        Extract criteria from multiple text files.
        
        Args:
            file_paths: List of paths to text files containing policy text
            
        Returns:
            Dictionary mapping policy names to their extracted criteria lists
        """
        results = {}
        
        for file_path in file_paths:
            try:
                policy_name = os.path.splitext(os.path.basename(file_path))[0]
                criteria = self.extract_from_file(file_path, policy_name)
                results[policy_name] = criteria
                logger.info(f"Successfully processed: {file_path} ({len(criteria)} criteria)")
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results[os.path.basename(file_path)] = []
        
        return results
    
    def extract_from_directory(self, directory_path: str, file_pattern: str = "*.txt") -> Dict[str, List[ExtractedCriterion]]:
        """
        Extract criteria from all matching files in a directory.
        
        Args:
            directory_path: Directory path
            file_pattern: File matching pattern, defaults to "*.txt"
            
        Returns:
            Dictionary mapping policy names to their extracted criteria lists
        """
        import glob
        
        # Build search pattern
        search_pattern = os.path.join(directory_path, file_pattern)
        file_paths = glob.glob(search_pattern)
        
        if not file_paths:
            logger.warning(f"No files matching {file_pattern} found in directory {directory_path}")
            return {}
        
        logger.info(f"Found {len(file_paths)} files in directory {directory_path}")
        return self.extract_from_multiple_files(file_paths)
    
    def print_extraction_summary(self, criteria: List[ExtractedCriterion], policy_name: str = "Policy"):
        """
        Print detailed summary of extraction results.
        
        Args:
            criteria: List of extracted criteria
            policy_name: Name of the policy
        """
        print(f"\n{'='*60}")
        print(f"Policy Criteria Extraction Results: {policy_name}")
        print(f"{'='*60}")
        print(f"Total extracted criteria: {len(criteria)}")
        
        # Group by type for display
        type_groups = {}
        for criterion in criteria:
            if criterion.type not in type_groups:
                type_groups[criterion.type] = []
            type_groups[criterion.type].append(criterion)
        
        for criterion_type, type_criteria in type_groups.items():
            print(f"\n{criterion_type.upper()} Criteria ({len(type_criteria)} items):")
            print("-" * 40)
            for i, criterion in enumerate(type_criteria, 1):
                print(f"{i:2d}. {criterion.description}")
                print(f"    Field: {criterion.field}")
                print(f"    Operator: {criterion.operator}")
                print(f"    Value: {criterion.value}")
                print(f"    Confidence: {criterion.confidence:.2f}")
                if criterion.source_text:
                    print(f"    Source: {criterion.source_text[:100]}{'...' if len(criterion.source_text) > 100 else ''}")
                print()
    
    def save_results_to_file(self, criteria: List[ExtractedCriterion], output_file: str, policy_name: str = "Policy"):
        """
        Save extraction results to a file.
        
        Args:
            criteria: List of extracted criteria
            output_file: Output file path
            policy_name: Name of the policy
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Policy Criteria Extraction Results: {policy_name}\n")
                f.write("="*60 + "\n")
                f.write(f"Extraction time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total extracted criteria: {len(criteria)}\n\n")
                
                # Group by type for saving
                type_groups = {}
                for criterion in criteria:
                    if criterion.type not in type_groups:
                        type_groups[criterion.type] = []
                    type_groups[criterion.type].append(criterion)
                
                for criterion_type, type_criteria in type_groups.items():
                    f.write(f"{criterion_type.upper()} Criteria ({len(type_criteria)} items):\n")
                    f.write("-" * 40 + "\n")
                    for i, criterion in enumerate(type_criteria, 1):
                        f.write(f"{i:2d}. {criterion.description}\n")
                        f.write(f"    Field: {criterion.field}\n")
                        f.write(f"    Operator: {criterion.operator}\n")
                        f.write(f"    Value: {criterion.value}\n")
                        f.write(f"    Confidence: {criterion.confidence:.2f}\n")
                        if criterion.source_text:
                            f.write(f"    Source: {criterion.source_text}\n")
                        f.write("\n")
            
            logger.info(f"Results saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise
    
    def validate_extracted_criteria(self, criteria: List[ExtractedCriterion]) -> Dict[str, Any]:
        """Validate extracted criteria for completeness and accuracy"""
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'completeness_score': 0.0
        }
        
        # Check for essential criteria types
        essential_types = ['age', 'procedure']
        found_types = {c.type for c in criteria}
        
        for essential_type in essential_types:
            if essential_type not in found_types:
                validation_results['warnings'].append(
                    f"Missing essential criterion type: {essential_type}"
                )
        
        # Check confidence scores
        low_confidence_criteria = [c for c in criteria if c.confidence < 0.7]
        if low_confidence_criteria:
            validation_results['warnings'].append(
                f"Found {len(low_confidence_criteria)} criteria with low confidence"
            )
        
        # Calculate completeness score
        expected_types = ['age', 'bmi', 'procedure', 'diagnosis', 'documentation']
        completeness_score = len(found_types.intersection(expected_types)) / len(expected_types)
        validation_results['completeness_score'] = completeness_score
        
        return validation_results

# Example usage and testing
if __name__ == "__main__":
    # Initialize extractor
    extractor = PolicyTextExtractor()
    
    # ===========================================
    # CONFIGURE YOUR FILE PATH HERE
    # ===========================================
    file_path = "policy1.txt"  # Change this to your file path
    policy_name = "BariatricSurgery"  # Optional: specify policy name
    
    print("Medical Policy Criteria Extraction Tool")
    print("="*50)
    
    try:
        # Extract criteria from file
        print(f"Processing file: {file_path}")
        criteria = extractor.extract_from_file(file_path, policy_name)
        
        if not criteria:
            print("No criteria extracted from the file.")
        else:
            # Print detailed summary
            extractor.print_extraction_summary(criteria, policy_name)
            
            # Save results to file
            output_file = f"{policy_name}_extraction_results.txt"
            extractor.save_results_to_file(criteria, output_file, policy_name)
            print(f"\nResults saved to: {output_file}")
            
            # Validation
            print(f"\nValidation Results:")
            validation = extractor.validate_extracted_criteria(criteria)
            print(f"- Valid: {validation['valid']}")
            print(f"- Completeness: {validation['completeness_score']:.1%}")
            print(f"- Warnings: {len(validation['warnings'])}")
            if validation['warnings']:
                print("Warning details:")
                for warning in validation['warnings']:
                    print(f"  - {warning}")
            
            # Statistics
            print(f"\nExtraction Statistics:")
            stats = extractor.get_extraction_stats()
            print(f"- Total extractions: {stats['total_extractions']}")
            print(f"- Successful extractions: {stats['successful_extractions']}")
            print("- Extraction type distribution:")
            for criterion_type, count in stats['extraction_types'].items():
                print(f"  - {criterion_type}: {count}")
    
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        print("Please check the file path and try again.")
    except Exception as e:
        print(f"Error processing file: {e}")
    
    print("\n" + "="*50)
    print("Extraction completed!")
