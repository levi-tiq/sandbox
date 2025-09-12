#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from enhanced_batch_extractor import EnhancedSOC2Extractor

def test_bullet_parsing():
    """Test the fixed bullet point parsing"""
    
    extractor = EnhancedSOC2Extractor()
    
    # The problematic text from Elbe report
    test_text = "Inquired to determine management's standards for integrity and ethical values, which are outlined in the entity's code of conduct. The organization comprehends these expectations, including outsourced service providers and business partners Inspected the most current code of conduct and two (2) samples of executed service agreements used in the scope of this engagement concerning expected standards of conduct, and the most current employee confidentiality policy."
    
    print("🔍 Testing bullet point parsing fix:")
    print("=" * 60)
    print(f"\nOriginal text:")
    print(f"{test_text}")
    
    parsed_tests = extractor.parse_tests_applied(test_text)
    
    print(f"\n✅ Parsed into {len(parsed_tests)} bullet points:")
    for i, test in enumerate(parsed_tests, 1):
        print(f"\n  {i}. {test}")
    
    # Test with some other examples
    test_cases = [
        # Case 1: Newline separated (should work already)
        "Inquired to determine the process.\n\nInspected the documentation.",
        
        # Case 2: No space between sentence and verb (like Elbe issue)
        "Inquired to determine the security measures in place for data protection Inspected the security policies and procedures.",
        
        # Case 3: Multiple verbs without clear separation
        "Inquired about the backup procedures Reviewed the backup logs Tested the restore process Observed the monitoring system.",
        
        # Case 4: Single test (should remain as one)
        "Inquired to determine that the organization has proper controls in place."
    ]
    
    print(f"\n" + "=" * 60)
    print("🧪 Additional test cases:")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {test_case[:100]}{'...' if len(test_case) > 100 else ''}")
        
        parsed = extractor.parse_tests_applied(test_case)
        print(f"Output: {len(parsed)} bullet points")
        
        for j, bullet in enumerate(parsed, 1):
            print(f"  {j}. {bullet[:80]}{'...' if len(bullet) > 80 else ''}")

if __name__ == "__main__":
    test_bullet_parsing()