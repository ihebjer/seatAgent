#!/usr/bin/env python3
"""
Test script to verify motor control tool calls work properly
"""

import requests
import json

# Configuration
APP_URL = "http://localhost:5050/query"

def test_motor_call(query, expected_tool=None):
    """Test a motor control query"""
    print(f"\n{'='*50}")
    print(f"Testing: {query}")
    print(f"Expected tool: {expected_tool}")
    print(f"{'='*50}")
    
    try:
        response = requests.post(APP_URL, json={"query": query})
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Check if we got a raw response (what we want for motor tools)
        if result.get("response_type") == "raw":
            print("✅ SUCCESS: Got raw response as expected")
            raw_response = result.get("raw_response", {})
            if expected_tool and result.get("tool_used") == expected_tool:
                print(f"✅ SUCCESS: Correct tool used ({expected_tool})")
            else:
                print(f"❌ ISSUE: Expected tool {expected_tool}, got {result.get('tool_used')}")
        elif result.get("response_type") == "natural":
            print("❌ ISSUE: Got natural language response instead of raw response")
        else:
            print(f"❌ ISSUE: Unexpected response type: {result.get('response_type')}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def main():
    """Run test cases"""
    print("Testing Motor Control Tool Calls")
    print("Make sure your app.py server is running on localhost:5050")
    
    # Test cases
    test_cases = [
        ("move track forward", "move_track_forward"),
        ("move track backward", "move_track_backward"),
        ("move backrest forward", "move_backrest_forward"),
        ("move height backward", "move_height_backward"),
        ("adjust thermal to 7", "adjust_thermal"),
        ("set ventilation to 3", "adjust_ventilation"),
    ]
    
    for query, expected_tool in test_cases:
        test_motor_call(query, expected_tool)
    
    print(f"\n{'='*50}")
    print("Test completed!")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()