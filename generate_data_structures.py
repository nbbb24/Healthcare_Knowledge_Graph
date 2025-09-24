#!/usr/bin/env python3
"""
Pipeline utility to generate the target JSON data structures.

This script generates:
1. Data_dictionary.json - Schema definitions for all data fields
2. policies.json - Policy definitions with restrictions

Usage:
    python generate_data_structures.py
"""

import json
from DataField import generate_data_dictionary
from Policy import generate_policies


def main():
    """Generate both target JSON structures"""
    
    print("Generating Data Dictionary...")
    
    # Generate Data_dictionary.json
    data_dictionary = generate_data_dictionary()
    
    with open('Data_dictionary.json', 'w', encoding='utf-8') as f:
        json.dump(data_dictionary, f, indent=2)
    
    print(f"✓ Generated Data_dictionary.json with {len(data_dictionary)} fields")
    
    print("\nGenerating Policies...")
    
    # Generate policies.json
    policies = generate_policies()
    
    with open('policies.json', 'w', encoding='utf-8') as f:
        json.dump(policies, f, indent=2)
    
    print(f"✓ Generated policies.json with {len(policies)} policies")
    
    # Summary
    policy = policies[0]
    restrictions_count = len(policy.get('restrictions', []))
    print(f"  - Policy: {policy['name']}")
    print(f"  - Restrictions: {restrictions_count}")
    
    print("\n🎉 Pipeline completed successfully!")
    print("Generated files:")
    print("  - Data_dictionary.json")
    print("  - policies.json")


def validate_pipeline():
    """Validate that the generated structures match the expected format"""
    
    print("\nValidating generated structures...")
    
    # Check Data_dictionary.json
    try:
        with open('Data_dictionary.json', 'r') as f:
            data_dict = json.load(f)
        
        required_fields = ['name', 'type', 'description', 'rule', 'values', 'examples', 'section']
        
        for field in data_dict:
            for req_field in required_fields:
                if req_field not in field:
                    print(f"❌ Missing field '{req_field}' in data dictionary entry")
                    return False
        
        print(f"✓ Data_dictionary.json structure is valid ({len(data_dict)} fields)")
        
    except Exception as e:
        print(f"❌ Error validating Data_dictionary.json: {e}")
        return False
    
    # Check policies.json
    try:
        with open('policies.json', 'r') as f:
            policies = json.load(f)
        
        policy_required_fields = ['name', 'guideline_number', 'description', 'raw_text', 'restrictions']
        restriction_required_fields = ['condition', 'rule', 'codes', 'logic']
        
        for policy in policies:
            for req_field in policy_required_fields:
                if req_field not in policy:
                    print(f"❌ Missing field '{req_field}' in policy")
                    return False
            
            for restriction in policy.get('restrictions', []):
                for req_field in restriction_required_fields:
                    if req_field not in restriction:
                        print(f"❌ Missing field '{req_field}' in restriction")
                        return False
        
        print(f"✓ policies.json structure is valid ({len(policies)} policies)")
        
    except Exception as e:
        print(f"❌ Error validating policies.json: {e}")
        return False
    
    print("✅ All structures are valid!")
    return True


if __name__ == "__main__":
    main()
    validate_pipeline()