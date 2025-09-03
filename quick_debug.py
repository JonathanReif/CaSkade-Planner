#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from smt_planning.smt.cask_to_smt import CaskadePlanner

def quick_debug():
    """Quick debug to see variable names"""
    print("=== Quick Debug ===")
    
    planner = CaskadePlanner("http://example.org/ontologies/requiredLocalFillTime#Sim_Req")
    planner.with_endpoint_query_handler("http://localhost:7200/repositories/testdb")
    
    # Test with very limited scope - just find first solution and stop
    result = planner.cask_to_smt(3, find_all_solutions=False)  # Single solution first
    
    print(f"Result type: {result.result_type}")
    if hasattr(result, 'plan') and result.plan:
        print("Single plan found - stopping here to debug")

if __name__ == "__main__":
    try:
        quick_debug()
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()