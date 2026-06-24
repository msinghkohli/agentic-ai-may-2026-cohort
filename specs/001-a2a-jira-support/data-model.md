# Data Model: A2A Jira Support Agents

## 1. PageIndex Tree Indexes

`pageindex-open` builds a hierarchical index representing the structure of the document. These are stored locally as markdown files:
- **Location**: `session7/2.a2a_jira_support/data/indexes/`
- **Files**:
  - `repair_service_policy_index.json` (cached structure)
  - `product_lineup_specifications_index.json` (cached structure)

---

## 2. Pydantic Models for Structured Interface

### JiraIssueStatus (Pydantic Model)
Represents the status information retrieved from the Jira Management agent over A2A:

```python
from pydantic import BaseModel, Field

class JiraIssueStatus(BaseModel):
    ticket_id: str = Field(..., description="The unique Jira ticket identifier, e.g., TIME-123")
    summary: str = Field(..., description="Brief summary of the issue")
    status: str = Field(..., description="Current workflow state, e.g., To Do, In Progress, Done")
    assignee: str = Field(..., description="Name or ID of the assignee, or Unassigned")
    priority: str = Field(..., description="Priority level, e.g., High, Medium, Low")
```

### SupportChatHistory (Session State Model)
Maintains conversation history for multi-turn chat in the Streamlit UI:

```python
from pydantic import BaseModel
from typing import List, Literal

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class SupportChatHistory(BaseModel):
    session_id: str
    messages: List[ChatMessage]
```
