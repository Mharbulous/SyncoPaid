# TDD Execution

Execute tasks in batches of 3, following strict RED-GREEN-COMMIT cycle.

## Batch Execution

### Before Starting Batch

```python
python -c "
import json

state_file = '.claude/skills/story-execution/temp-CI-notes.json'
with open(state_file) as f:
    state = json.load(f)

batch_num = state.get('current_batch', 0) + 1
start_idx = (batch_num - 1) * 3
end_idx = min(start_idx + 3, state['total_tasks'])

# Mark batch as in progress
if len(state.get('batches', [])) < batch_num:
    state['batches'].append({
        'batch': batch_num,
        'task_range': [start_idx + 1, end_idx],
        'status': 'in_progress',
        'commits': []
    })
else:
    state['batches'][batch_num - 1]['status'] = 'in_progress'

state['current_batch'] = batch_num

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2)

print(f'Starting batch {batch_num}: tasks {start_idx + 1}-{end_idx}')
"
```

## TDD Cycle per Task

### RED: Write Failing Test

1. Write the test as specified in the plan
2. Run the test suite
3. **Verify the new test FAILS** for the expected reason

```bash
# Run tests
python -m pytest tests/ -v --tb=short
```

**If test passes:** STOP. Feature may already exist. Document and continue to next task.

### GREEN: Minimal Implementation

1. Write the minimal code to make the test pass
2. Follow plan implementation steps exactly
3. Run the test suite again

```bash
python -m pytest tests/ -v --tb=short
```

**If test fails:** Debug and fix. Do not proceed until test passes.

### COMMIT: Stage and Commit

```bash
# Stage changes
git add -A

# Commit with story ID
git commit -m "feat: [task description]

Story: [STORY_ID]
Task: [TASK_NUMBER] of [TOTAL_TASKS]"
```

### Update Task Status

```python
python -c "
import json, subprocess

state_file = '.claude/skills/story-execution/temp-CI-notes.json'
with open(state_file) as f:
    state = json.load(f)

task_idx = 0  # Replace with actual task index
commit_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()[:7]

# Update task
state['tasks'][task_idx]['status'] = 'completed'
state['tasks'][task_idx]['notes'] = f'Commit: {commit_hash}'

# Add commit to batch
batch_idx = state['current_batch'] - 1
state['batches'][batch_idx]['commits'].append(commit_hash)

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2)

print(f'Task {task_idx + 1} completed: {commit_hash}')
"
```

## Batch Completion

After completing all tasks in batch:

```python
python -c "
import json

state_file = '.claude/skills/story-execution/temp-CI-notes.json'
with open(state_file) as f:
    state = json.load(f)

batch_idx = state['current_batch'] - 1

# Check all tasks in range completed
start = state['batches'][batch_idx]['task_range'][0] - 1
end = state['batches'][batch_idx]['task_range'][1]
all_completed = all(state['tasks'][i]['status'] == 'completed' for i in range(start, end))

state['batches'][batch_idx]['status'] = 'completed' if all_completed else 'failed'

# Check if more tasks remain
tasks_remaining = sum(1 for t in state['tasks'] if t['status'] == 'pending')
state['tasks_remaining'] = tasks_remaining

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2)

print(json.dumps({
    'batch': state['current_batch'],
    'status': state['batches'][batch_idx]['status'],
    'tasks_remaining': tasks_remaining
}, indent=2))
"
```

## When to Stop

Stop and set batch status to 'failed' when:
- Test should fail but passes (feature already exists)
- Test fails for wrong reason (wrong implementation path)
- Cannot find file/function mentioned in plan
- Repeated failures after 3 attempts
- Regression detected (existing tests fail)
