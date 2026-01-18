#!/usr/bin/env python3
"""Test script to verify two sum problem execution."""

import asyncio
import httpx
import json

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

TEST_CODE_JAVASCRIPT = """
function solution(data) {
    const { nums, target } = data;
    const seen = {};
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (complement in seen) {
            return [seen[complement], i];
        }
        seen[nums[i]] = i;
    }
    return [];
}
"""

async def test_login():
    """Login to get auth token."""
    async with httpx.AsyncClient() as client:
        # Try to login with test credentials
        response = await client.post(
            f"{API_URL}/auth/login",
            json={
                "username": "demo",
                "password": "demo123"
            }
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"Login failed: {response.status_code}")
            print("Please ensure demo user exists or create one first")
            return None

async def test_code_execution(token: str, language: str, code: str):
    """Test code execution for the two sum problem."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}

        # Run the code
        response = await client.post(
            f"{API_URL}/tasks/proctored-two-sum/run",
            headers=headers,
            json={
                "session_id": "test-session-123",
                "code": code,
                "language": language
            }
        )

        if response.status_code == 200:
            result = response.json()
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
        else:
            print(f"{language.upper()} execution failed: {response.status_code}")
            print(response.text)
            return False

async def main():
    print("Testing Two Sum Problem Execution")
    print("=" * 40)

    # Login first
    token = await test_login()
    if not token:
        print("Failed to authenticate. Exiting.")
        return

    print(f"Successfully authenticated")

    # Test Python execution
    python_passed = await test_code_execution(token, "python", TEST_CODE_PYTHON)

    # Test JavaScript execution
    js_passed = await test_code_execution(token, "javascript", TEST_CODE_JAVASCRIPT)

    print("\n" + "=" * 40)
    print("Summary:")
    print(f"Python: {'✅ PASSED' if python_passed else '❌ FAILED'}")
    print(f"JavaScript: {'✅ PASSED' if js_passed else '❌ FAILED'}")

    if python_passed and js_passed:
        print("\n🎉 All tests passed! The code execution is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(main())