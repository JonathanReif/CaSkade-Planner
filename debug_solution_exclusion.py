#!/usr/bin/env python3
"""
Debug script to understand what's happening with solution exclusion
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from smt_planning.smt.cask_to_smt import CaskadePlanner

def test_with_debugging():
    """Test with debugging to see what variables are being used"""
    print("=== Debug Solution Exclusion ===")
    
    planner = CaskadePlanner("http://example.org/ontologies/requiredLocalFillTime#Sim_Req")
    planner.with_endpoint_query_handler("http://localhost:7200/repositories/testdb")
    
    # Let's find just the first few solutions with debugging
    result = planner.cask_to_smt(5, find_all_solutions=True)  # Limited to prevent infinite loop
    
    print(f"\nResult type: {result.result_type}")
    if hasattr(result, 'plans') and result.plans:
        print(f"Number of plans found: {len(result.plans)}")
        
        # Show first few plans for comparison
        for i, plan in enumerate(result.plans[:3]):
            print(f"\n--- Plan {i+1} ---")
            print(f"Plan length: {plan.plan_length}")
            print(f"Total duration: {plan.total_duration}")
            for step in plan.plan_steps:
                print(f"  Step {step.step_number}:")
                for cap_app in step.capability_appearances:
                    print(f"    Capability: {cap_app.capability_iri}")
    
    return result

if __name__ == "__main__":
    try:
        result = test_with_debugging()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()