#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from smt_planning.smt.cask_to_smt import CaskadePlanner

def limited_test():
    """Limited test to debug the solution exclusion"""
    print("=== Limited Test ===")
    
    planner = CaskadePlanner("http://example.org/ontologies/requiredLocalFillTime#Sim_Req")
    planner.with_endpoint_query_handler("http://localhost:7200/repositories/testdb")
    
    # Test with very limited scope to capture debug output
    result = planner.cask_to_smt(3, find_all_solutions=True)
    
    print(f"Final result type: {result.result_type}")
    if hasattr(result, 'plans') and result.plans:
        print(f"Total plans found: {len(result.plans)}")
    elif hasattr(result, 'plan') and result.plan:
        print("Single plan found")
    else:
        print("No plans found")

if __name__ == "__main__":
    try:
        limited_test()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()