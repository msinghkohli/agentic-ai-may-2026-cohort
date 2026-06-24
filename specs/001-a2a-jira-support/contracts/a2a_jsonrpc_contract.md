# A2A JSON-RPC 2.0 Contract Specification

This contract defines the JSON-RPC interface exposed by the Jira Management A2A Server.

## Endpoint

- **URL**: `http://localhost:8001/`
- **Method**: `POST`
- **Headers**:
  - `Content-Type: application/json`
  - `Authorization: Bearer OrangeJiraToken`

---

## 1. `message/send` Request

Submits a new query task to the Jira Management agent.

### Schema (JSON-RPC)

```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "id": "request-id-123",
  "params": {
    "id": "task-uuid-456",
    "message": {
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "What is the status of ticket TIME-123?"
        }
      ]
    }
  }
}
```

---

## 2. Response (Synchronous/Completed)

Returns the final task state and the query results inside a structured artifact.

### Schema (JSON-RPC)

```json
{
  "jsonrpc": "2.0",
  "id": "request-id-123",
  "result": {
    "id": "task-uuid-456",
    "status": {
      "state": "completed",
      "timestamp": "2026-06-24T12:00:00Z"
    },
    "artifacts": [
      {
        "artifactId": "artifact-uuid-789",
        "name": "jira_status_report",
        "parts": [
          {
            "kind": "text",
            "text": "Ticket TIME-123: 'Implement user checkout' is currently 'In Progress'. Assigned to: John Doe. Priority: High."
          }
        ]
      }
    ]
  }
}
```

---

## 3. `tasks/get` Request

Used to poll for status of a previously submitted task.

### Schema (JSON-RPC)

```json
{
  "jsonrpc": "2.0",
  "method": "tasks/get",
  "id": "request-id-124",
  "params": {
    "id": "task-uuid-456"
  }
}
```
