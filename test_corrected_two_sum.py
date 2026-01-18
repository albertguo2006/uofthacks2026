#!/usr/bin/env python3
"""Test script with the CORRECTED two sum solution format."""

import json
import urllib.request
import urllib.error

API_URL = "http://localhost:8000"

# ✅ CORRECT Solution - accepts a single dictionary parameter
CORRECT_SOLUTION_PYTHON = """
def solution(data):
    nums = data['nums']
    target = data['target']

    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""

# Alternative correct version using two_sum name
CORRECT_TWO_SUM_PYTHON = """
def two_sum(data):
    nums = data['nums']
    target = data['target']

    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""

def test_login():
    """Login to get auth token."""
    data = json.dumps({
        "email": "demo@example.com",
        "password": "demo1234"
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{API_URL}/auth/login",
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("access_token")
    except urllib.error.HTTPError as e:
        print(f"Login failed: {e.code}")
        return None

def test_code_execution(token, code, test_name):
    """Test code execution for the two sum problem."""
    data = json.dumps({
        "session_id": "test-corrected-123",
        "code": code,
        "language": "python"
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{API_URL}/tasks/proctored-two-sum/run",
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"\n{test_name} Results:")
            print(f"✅ All Tests Passed: {result.get('all_passed')}")

            for test_result in result.get('results', []):
                status = "✅" if test_result['passed'] else "❌"
                print(f"  Test Case {test_result['test_case']}: {status}")
                if not test_result['passed'] and test_result.get('error'):
                    print(f"    Error: {test_result['error']}")

            return result.get('all_passed')
    except urllib.error.HTTPError as e:
        print(f"{test_name} failed: {e.code}")
        error_content = e.read().decode('utf-8')
        print(f"Error: {error_content}")
        return False

def main():
    print("=" * 60)
    print("Testing CORRECTED Two Sum Solution Format")
    print("=" * 60)

    # Login first
    token = test_login()
    if not token:
        print("Failed to authenticate.")
        return

    print("✅ Successfully authenticated")

    # Test with 'solution' function name
    print("\n" + "-" * 40)
    solution_passed = test_code_execution(
        token,
        CORRECT_SOLUTION_PYTHON,
        "Using 'solution' function"
    )

    # Test with 'two_sum' function name
    print("\n" + "-" * 40)
    two_sum_passed = test_code_execution(
        token,
        CORRECT_TWO_SUM_PYTHON,
        "Using 'two_sum' function"
    )

    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"  solution(): {'✅ PASSED' if solution_passed else '❌ FAILED'}")
    print(f"  two_sum():  {'✅ PASSED' if two_sum_passed else '❌ FAILED'}")

    if solution_passed and two_sum_passed:
        print("\n🎉 Both function formats work correctly!")
        print("\nRemember: Your function must accept a single 'data' parameter")
        print("and extract 'nums' and 'target' from it.")
    else:
        print("\n⚠️ Some tests failed. Check the implementation.")

if __name__ == "__main__":
    main()