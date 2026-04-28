import base64
import os
from crewai import Agent, Crew, Task, LLM, Process
from crewai_tools import MCPServerAdapter
from . import bedrock_patches  # noqa: F401 — applies Bedrock monkey-patches on import

def _filter_tools(all_tools, tool_names: set):
    return [t for t in all_tools if t.name in tool_names]


def create_crew():
    atlassian_email = os.environ["ATLASSIAN_EMAIL"]
    atlassian_api_key = os.environ["ATLASSIAN_API_KEY"]
    atlassian_token = base64.b64encode(f"{atlassian_email}:{atlassian_api_key}".encode()).decode()
    server_params = {
        "url": "https://mcp.atlassian.com/v1/mcp",
        "transport": "streamable-http",
        "headers": {"Authorization": f"Basic {atlassian_token}"},
    }

    all_tools = MCPServerAdapter(server_params).tools
    llm = LLM(model=os.environ["LARGE_MODEL_ID"])



    confluence_reader = Agent(
        role="Confluence Reader",
        goal="Read and extract structured information from Confluence pages and spaces.",
        backstory=(
            "You are a specialist in navigating Confluence. You retrieve page content, "
            "descendants, comments, and search results accurately and completely. " 
            " When fetching the content from a confluence page, you prefer the markdown format"
        ),
        llm=llm,
        tools=_filter_tools(all_tools, {
            "get_confluence_page",
            "get_confluence_page_descendants",
            "get_confluence_page_footer_comments",
            "get_confluence_page_inline_comments",
            "get_confluence_comment_children",
            "get_confluence_spaces",
            "get_pages_in_confluence_space",
            "search_confluence_using_cql",
        }),
        allow_delegation=False,
    )

    jira_issue_reader = Agent(
        role="Jira Issue Reader",
        goal="Read and search Jira issues to retrieve their details, fields, and relationships.",
        backstory=(
            "You are an expert at querying Jira issues and performing JQL searches to find "
            "relevant issues and understand their current state."
        ),
        llm=llm,
        tools=_filter_tools(all_tools, {
            "get_jira_issue",
            "get_jira_issue_remote_issue_links",
            "search_jira_issues_using_jql",
            "get_visible_jira_projects",
            "get_jira_project_issue_types_metadata",
            "get_jira_issue_type_meta_with_fields",
        }),
        allow_delegation=False,
    )

    jira_issue_creator = Agent(
        role="Jira Issue Creator",
        goal="Create new Jira issues including epics, stories, tasks, and sub-tasks with correct fields and dependency links.",
        backstory=(
            "You are an expert at creating well-structured Jira issues with the correct issue types, "
            "project metadata, and inter-issue dependency links."
        ),
        llm=llm,
        tools=_filter_tools(all_tools, {
            "create_jira_issue",
            "create_issue_link",
            "get_visible_jira_projects",
            "get_jira_project_issue_types_metadata",
            "get_jira_issue_type_meta_with_fields",
            "get_issue_link_types",
            "lookup_jira_account_id",
        }),
        allow_delegation=False,
    )

    jira_issue_updater = Agent(
        role="Jira Issue Updater",
        goal="Update existing Jira issues by editing fields, transitioning status, and adding comments.",
        backstory=(
            "You are an expert at modifying Jira issues, transitioning them through workflows, "
            "and adding structured comments and worklogs."
        ),
        llm=llm,
        tools=_filter_tools(all_tools, {
            "edit_jira_issue",
            "transition_jira_issue",
            "get_transitions_for_jira_issue",
            "add_comment_to_jira_issue",
            "add_worklog_to_jira_issue",
            "get_jira_issue_type_meta_with_fields",
            "lookup_jira_account_id",
        }),
        allow_delegation=False,
    )

    # The Atlassian MCP server does not expose a deleteJiraIssue tool.
    # This agent transitions issues to their terminal state (Cancelled/Done) as the closest equivalent.
    jira_issue_deleter = Agent(
        role="Jira Issue Deleter",
        goal="Cancel or close Jira issues by transitioning them to a terminal workflow state.",
        backstory=(
            "You handle removal of Jira issues. Since the MCP server does not expose a direct "
            "delete API, you transition issues to their Cancelled or Done state to effectively retire them."
        ),
        llm=llm,
        tools=_filter_tools(all_tools, {
            "get_jira_issue",
            "get_transitions_for_jira_issue",
            "transition_jira_issue",
        }),
        allow_delegation=False,
    )

    jira_manager = Agent(
        role="Jira Project Manager",
        goal=(
            "Manage Jira projects by orchestrating specialised agents to create and organise epics, "
            "tasks, and sub-tasks from requirements. Ensure proper dependency tracking, design phase "
            "checks for enhancements, and a security review task for every enhancement."
        ),
        backstory=(
            "You are a seasoned Jira Project Manager with deep expertise in agile project management "
            "and software delivery. You translate requirements into well-structured Jira epics and tasks "
            "with clear acceptance criteria and dependencies. For enhancements, you assess whether a "
            "design phase is needed (architectural changes, new integrations, significant UX work) and "
            "enforce that a security review task is always created. You delegate all reading, creating, "
            "updating, and cancelling work to the appropriate specialised sub-agents.\n\n"
            "Available coworkers (use the exact role name when delegating):\n"
            "- 'Confluence Reader': reads Confluence pages, spaces, and search results\n"
            "- 'Jira Issue Reader': reads and searches Jira issues via JQL\n"
            "- 'Jira Issue Creator': creates new epics, stories, tasks, sub-tasks, and issue links\n"
            "- 'Jira Issue Updater': edits fields, transitions status, and adds comments to issues\n"
            "- 'Jira Issue Deleter': cancels or closes issues by transitioning to a terminal state\n\n"
            "When using the 'Delegate work to coworker' or 'Ask question to coworker' tools you MUST "
            "always provide all three required arguments: coworker (exact role name from the list above), "
            "task or question (a clear and specific request), and context (all background info the "
            "coworker needs to complete the request, such as URLs, issue IDs, and project keys)."
        ),
        llm=llm,
        allow_delegation=True,
    )

    jira_task = Task(
        description=(
            "Perform the following Jira management action:\n"
            "{jira_request}\n\n"
            "Important guidelines:\n"
            "- For enhancements: assess whether a design phase is required (architectural "
            "  impact, new integrations, significant UI/UX changes). If yes, create a design task.\n"
            "- For enhancements: always create a security review task.\n"
            "- Model task dependencies accurately (e.g., design before implementation, "
            "  security review before QA).\n"
            "- Provide a clear summary of all created items with their IDs and relationships."
        ),
        expected_output=(
            "A structured summary of all Jira items created, including:\n"
            "- Epic: ID, summary, description\n"
            "- Tasks: ID, summary, type, dependencies\n"
            "- Any design or security review tasks added for enhancements"
        ),
    )

    return Crew(
        agents=[confluence_reader, jira_issue_reader, jira_issue_creator, jira_issue_updater, jira_issue_deleter],
        tasks=[jira_task],
        manager_agent=jira_manager,
        process=Process.hierarchical,
        verbose=True,
    )
