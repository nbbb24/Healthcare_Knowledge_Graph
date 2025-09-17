import requests
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import re
from bs4 import BeautifulSoup

class BioBERTEntityExtractor:
    def __init__(self):
        # Use the correct BioBERT model that exists
        model_name = "dmis-lab/biobert-base-cased-v1.1"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # For NER, use a model that actually exists and is designed for medical text
        self.ner_pipeline = pipeline("ner", 
                                   model="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext", 
                                   tokenizer="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
                                   aggregation_strategy="simple")
    
    def load_medical_policy(self, file_path):
        """Load medical policy content from local file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            return text
        except Exception as e:
            print(f"Error loading file: {e}")
            return None
    
    def preprocess_text(self, text):
        """Clean and preprocess medical text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove non-alphanumeric characters except basic punctuation
        text = re.sub(r'[^\w\s.,;:()\-]', '', text)
        return text.strip()
    
    def extract_entities(self, text):
        """Extract medical entities using BioBERT-based model"""
        if not text:
            return []
        
        # Split text into manageable chunks (transformers have token limits)
        max_length = 512
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        all_entities = []
        
        for chunk in chunks:
            if len(chunk.strip()) > 0:
                try:
                    entities = self.ner_pipeline(chunk)
                    all_entities.extend(entities)
                except Exception as e:
                    print(f"Error processing chunk: {e}")
                    continue
        
        return all_entities
    
    def filter_medical_entities(self, entities):
        """Filter and categorize medical entities"""
        medical_keywords = [
            'surgery', 'procedure', 'treatment', 'therapy', 'diagnosis',
            'disease', 'condition', 'symptom', 'medication', 'drug',
            'gastric', 'bypass', 'obesity', 'bmi', 'diabetes', 'hypertension',
            'cardiovascular', 'bariatric', 'laparoscopic', 'endoscopic'
        ]
        
        filtered_entities = []
        seen_entities = set()
        
        for entity in entities:
            entity_text = entity['word'].lower().strip()
            
            # Remove duplicates and filter relevant entities
            if entity_text not in seen_entities and len(entity_text) > 2:
                if any(keyword in entity_text for keyword in medical_keywords) or entity['label'] in ['MISC', 'ORG']:
                    filtered_entities.append(entity)
                    seen_entities.add(entity_text)
        
        return filtered_entities
    
    def categorize_entities(self, entities):
        """Categorize extracted entities by medical type"""
        categories = {
            'procedures': [],
            'conditions': [],
            'medications': [],
            'body_parts': [],
            'measurements': [],
            'other': []
        }
        
        procedure_keywords = ['surgery', 'bypass', 'procedure', 'treatment', 'therapy', 'plication', 'banding']
        condition_keywords = ['obesity', 'diabetes', 'hypertension', 'cardiovascular', 'disease', 'disorder']
        body_keywords = ['gastric', 'duodenal', 'intestinal', 'stomach', 'vagus']
        measurement_keywords = ['bmi', 'weight', 'kg', 'pounds', 'index']
        
        for entity in entities:
            entity_text = entity['word'].lower()
            categorized = False
            
            for keyword in procedure_keywords:
                if keyword in entity_text:
                    categories['procedures'].append(entity)
                    categorized = True
                    break
            
            if not categorized:
                for keyword in condition_keywords:
                    if keyword in entity_text:
                        categories['conditions'].append(entity)
                        categorized = True
                        break
            
            if not categorized:
                for keyword in body_keywords:
                    if keyword in entity_text:
                        categories['body_parts'].append(entity)
                        categorized = True
                        break
            
            if not categorized:
                for keyword in measurement_keywords:
                    if keyword in entity_text:
                        categories['measurements'].append(entity)
                        categorized = True
                        break
            
            if not categorized:
                categories['other'].append(entity)
        
        return categories

def main():
    extractor = BioBERTEntityExtractor()
    
    # Load medical policy from local file
    file_path = "policy1.txt"
    
    print("Loading medical policy content from local file...")
    text = extractor.load_medical_policy(file_path)
    
    if text:
        print("Preprocessing text...")
        clean_text = extractor.preprocess_text(text)
        
        print("Extracting medical entities...")
        entities = extractor.extract_entities(clean_text)
        
        print("Filtering medical entities...")
        filtered_entities = extractor.filter_medical_entities(entities)
        
        print("Categorizing entities...")
        categorized = extractor.categorize_entities(filtered_entities)
        
        print("\n=== EXTRACTED MEDICAL ENTITIES ===")
        for category, entity_list in categorized.items():
            if entity_list:
                print(f"\n{category.upper()}:")
                for entity in entity_list[:10]:  # Limit to top 10 per category
                    print(f"  - {entity['word']} (confidence: {entity['score']:.2f})")
        
        print(f"\nTotal entities found: {len(filtered_entities)}")
    else:
        print("Failed to fetch medical policy content.")

if __name__ == "__main__":
    main()