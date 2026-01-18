#!/usr/bin/env python3
"""Simple test script to verify two sum problem execution."""

import json
import urllib.request
import urllib.error

API_URL = "http://localhost:8000"

# Two Sum solution
TEST_CODE_PYTHON = """
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
        print("Please ensure demo user exists or create one first")
        return None

def test_code_execution(token, language, code):
    """Test code execution for the two sum problem."""
    data = json.dumps({
        "session_id": "test-session-123",
        "code": code,
        "language": language
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
            print(f"\n{language.upper()} Test Results:")
            print(f"All Passed: {result.get('all_passed')}")
            print(f"Total Time: {result.get('total_time_ms')}ms")

            for test_result in result.get('results', []):
                status = "✅" if test_result['passed'] else "❌"
                print(f"  Test Case {test_result['test_case']}: {status}")
                if not test_result.get('hidden'):
                    print(f"    Expected: {test_result.get('expected')}")
                    print(f"    Got: {test_result.get('output')}")
                if test_result.get('error'):
                    print(f"    Error: {test_result['error']}")

            if result.get('stderr'):
                print(f"  Stderr: {result['stderr']}")

            return result.get('all_passed')
    except urllib.error.HTTPError as e:
        print(f"{language.upper()} execution failed: {e.code}")
        print(e.read().decode('utf-8'))
        return False

def main():
    print("Testing Two Sum Problem Execution")
    print("=" * 40)

    # Login first
    token = test_login()
    if not token:
        print("Failed to authenticate. Exiting.")
        return

    print(f"Successfully authenticated")

    # Test Python execution
    python_passed = test_code_execution(token, "python", TEST_CODE_PYTHON)

    print("\n" + "=" * 40)
    print("Summary:")
    print(f"Python: {'✅ PASSED' if python_passed else '❌ FAILED'}")

    if python_passed:
        print("\n🎉 Python test passed! The code execution is working correctly.")
    else:
        print("\n⚠️ Python test failed. Please check the implementation.")

if __name__ == "__main__":
    main()