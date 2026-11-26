
## Key Constraints
1. **Private by design**: No external APIs or telemetry

## Agent Edit Rules

### Always Read Before Edit
The `Edit` tool will **fail** if you attempt to modify a file without first reading it. Always call `Read` on the target file before any `Edit` operation. This ensures you have the exact content for `oldString` matching.

### Edit Tool Usage
The `Edit` tool requires an **exact string match** of the text to replace. Follow these steps:

1. **Read the file first** to get the exact content.
2. **Copy the exact text** from the `Read` output (including whitespace, indentation, and line endings).
3. **Use that exact text** as the `oldString` parameter.
4. **Provide the new text** as the `newString` parameter.

**Example of a correct Edit call:**
```json
{
  "filePath": "/home/m247/workspace/voice-chat/llm.py",
  "oldString": "    if memories:\n        recent_history = \"\\n\".join(...)\n        candidates = filter_facts_by_context(memories, user_text, recent_history)",
  "newString": "    if memories:\n        logger.info(f\"[OLLAMA] Starting memory filtering...\")\n        recent_history = \"\\n\".join(...)\n        candidates = filter_facts_by_context(memories, user_text, recent_history)"
}
```

**Common mistakes to avoid:**
- Guessing the content instead of reading it first.
- Including line number prefixes from the `Read` output (e.g., `178: `).
- Using partial or truncated strings that don't match exactly.
- Forgetting that `oldString` must be unique in the file (use more context if needed).

## Mandatory Verification Protocol
Before marking any task as "completed", the agent MUST:
1. **Programmatic Proof**: Write and run a standalone Python script or CURL command that proves the logic works against real world samples (e.g., specific message IDs).
2. **Log Audit**: Restart the server (`./service.sh restart`) and tail `server.log` to confirm no errors occur during the first execution of the new feature.
3. **Regression Check**: Verify that new changes didn't break existing core functionality (e.g., if adding a math symbol, ensure arrows still work).
4. **Evidence**: Provide the output of these tests in the final response.

