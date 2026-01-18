# Correct Solution Format for SkillPulse Coding Tasks

## The Problem

You're getting this error:
```
TypeError: two_sum() missing 1 required positional argument: 'target'
```

This happens because the sandbox system passes **a single dictionary** containing all input data, not separate arguments.

## ❌ INCORRECT Format

```python
def two_sum(nums, target):  # Expects two separate arguments
    # Your solution...
```

## ✅ CORRECT Format

Your function must accept a single `data` parameter (a dictionary) and extract the values from it:

### Python Solutions

```python
# Option 1: Using 'solution' (recommended)
def solution(data):
    nums = data['nums']
    target = data['target']

    # Your solution logic here
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Option 2: Using 'two_sum'
def two_sum(data):  # Note: single parameter!
    nums = data['nums']
    target = data['target']

    # Your solution logic here

# Option 3: Using 'twoSum' (camelCase)
def twoSum(data):
    nums = data['nums']
    target = data['target']

    # Your solution logic here
```

### JavaScript Solutions

```javascript
// Option 1: Using 'solution' (recommended)
function solution(data) {
    const { nums, target } = data;  // Destructure the input

    // Your solution logic here
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

// Option 2: Using arrow function
const solution = (data) => {
    const { nums, target } = data;

    // Your solution logic here
};
```

## Key Points

1. **Single Parameter**: Your function must accept exactly ONE parameter (the data dictionary)
2. **Extract Values**: Extract `nums` and `target` from the data dictionary inside your function
3. **Supported Function Names**:
   - `solution` (recommended)
   - `two_sum` or `twoSum`
   - `main`

## Test Input Format

The sandbox calls your function like this:
```python
input_data = {
    "nums": [2, 7, 11, 15],
    "target": 9
}
result = solution(input_data)  # or two_sum(input_data)
```

## Quick Fix

Just change your function signature from:
```python
def two_sum(nums, target):
```

To:
```python
def two_sum(data):
    nums = data['nums']
    target = data['target']
```

That's it! Your solution will now work correctly in the SkillPulse sandbox.