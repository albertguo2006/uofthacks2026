"""
Correct solution format for the Two Sum problem in SkillPulse

The sandbox system passes a single dictionary argument containing all input data.
You need to extract the individual values from this dictionary.
"""

# ❌ INCORRECT - This will cause the error you're seeing:
def two_sum_wrong(nums, target):
    """This expects two separate arguments - WON'T WORK"""
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []


# ✅ CORRECT - Option 1: Using the function name 'solution'
def solution(data):
    """
    The sandbox passes a dictionary with 'nums' and 'target' keys.
    Extract them from the data parameter.
    """
    nums = data['nums']
    target = data['target']

    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []


# ✅ CORRECT - Option 2: Using the function name 'two_sum'
def two_sum(data):
    """
    Alternative using two_sum as the function name.
    Still needs to accept a single dictionary parameter.
    """
    nums = data['nums']
    target = data['target']

    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []


# ✅ CORRECT - Option 3: Using the function name 'twoSum' (camelCase)
def twoSum(data):
    """
    Another alternative using camelCase naming.
    """
    nums = data['nums']
    target = data['target']

    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []


# For JavaScript, the correct format would be:
"""
// ✅ CORRECT JavaScript solution:
function solution(data) {
    const { nums, target } = data;  // Destructure the input

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

// Or using arrow function:
const solution = (data) => {
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
};
"""

# Test locally to verify the format:
if __name__ == "__main__":
    # This is how the sandbox calls your function:
    test_input = {
        "nums": [2, 7, 11, 15],
        "target": 9
    }

    # Test all correct versions
    print("Testing solution():", solution(test_input))  # Should return [0, 1]
    print("Testing two_sum():", two_sum(test_input))   # Should return [0, 1]
    print("Testing twoSum():", twoSum(test_input))      # Should return [0, 1]

    # This would fail in the sandbox:
    try:
        result = two_sum_wrong(test_input)  # Missing second argument!
    except TypeError as e:
        print(f"\nError with incorrect function: {e}")
        print("This is the error you're seeing!")