# COPY AND PASTE THIS EXACT CODE INTO THE EDITOR:

def two_sum(data):
    # Extract nums and target from the data dictionary
    nums = data['nums']
    target = data['target']

    # Solution logic
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []