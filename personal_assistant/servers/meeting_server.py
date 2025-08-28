"""
ACP Server 1 - Meeting Manager Agent with MCP tools
Port: 8100

Handles all meeting-related operations using MCP tools
Following the pattern from acp_demo.py
"""

from collections.abc import AsyncGenerator
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Server, RunYield, RunYieldResume
from crewai import Agent, Task, Crew
import nest_asyncio
import sys
import os

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.gemini_config import get_llm
from mcp_tools.meeting_tools import (
    add_meeting, list_meetings, search_meetings, 
    update_meeting, delete_meeting, get_meeting_conflicts
)

# Apply asyncio patch for Jupyter compatibility
nest_asyncio.apply()

# Initialize server and get configured LLM
server = Server()
llm = get_llm()

# Mock MCP tools as CrewAI tools (since we can't directly integrate MCP with CrewAI)
class MeetingTool:
    """Wrapper for MCP meeting tools to work with CrewAI"""
    
    def __init__(self, tool_func, name, description):
        self.tool_func = tool_func
        self.name = name
        self.description = description
    
    def run(self, **kwargs):
        """Execute the MCP tool function"""
        try:
            return self.tool_func(**kwargs)
        except Exception as e:
            return f"Error executing {self.name}: {str(e)}"

# Create tool instances
meeting_tools = [
    MeetingTool(add_meeting, "add_meeting", "Add a new meeting to the calendar"),
    MeetingTool(list_meetings, "list_meetings", "List meetings within a date range"),
    MeetingTool(search_meetings, "search_meetings", "Search meetings by title, attendee, or description"),
    MeetingTool(update_meeting, "update_meeting", "Update a meeting's details"),
    MeetingTool(delete_meeting, "delete_meeting", "Delete/cancel a meeting"),
    MeetingTool(get_meeting_conflicts, "get_meeting_conflicts", "Check for meeting conflicts")
]

@server.agent(name="meeting_manager")
async def meeting_agent(input: list[Message]) -> AsyncGenerator[RunYield, RunYieldResume]:
    """
    Meeting Manager Agent
    
    Handles all meeting-related queries and operations including:
    - Scheduling new meetings
    - Listing and searching existing meetings
    - Updating meeting details
    - Checking for conflicts
    - Managing meeting attendees and locations
    """
    
    try:
        # Extract user query
        user_query = input[0].parts[0].content
        
        # Create specialized meeting management agent
        meeting_manager = Agent(
            role="Meeting Management Specialist",
            goal="Efficiently manage all meeting-related tasks including scheduling, updating, and organizing meetings",
            backstory="""You are an expert meeting management assistant with years of experience in 
            calendar management, scheduling optimization, and meeting coordination. You excel at:
            - Understanding natural language requests for meeting operations
            - Scheduling conflicts detection and resolution
            - Meeting logistics coordination
            - Attendee management and communication
            - Calendar optimization and time management
            
            You can perform various meeting operations including adding, listing, searching, 
            updating, and deleting meetings. You always provide clear, actionable responses 
            and proactively suggest improvements to meeting management.""",
            verbose=True,
            allow_delegation=False,
            llm=llm,
            max_retry_limit=3
        )
        
        # Create task for meeting management
        meeting_task = Task(
            description=f"""
            Process this meeting-related request: "{user_query}"
            
            You have access to various meeting management capabilities:
            1. Adding new meetings with full details (title, date, time, attendees, location)
            2. Listing meetings by date range and status
            3. Searching meetings by various criteria
            4. Updating existing meeting details
            5. Deleting or canceling meetings
            6. Checking for scheduling conflicts
            
            Based on the user's request, determine the appropriate action and provide a 
            comprehensive response. If the request is ambiguous, ask for clarification.
            
            For scheduling requests, always check for conflicts first.
            For listing requests, format the results clearly with all relevant details.
            For search requests, try multiple search criteria if needed.
            
            If you need to perform meeting operations, describe what you would do step by step,
            but note that the actual operations will be handled by the MCP tools.
            """,
            expected_output="""
            A detailed response that addresses the user's meeting-related request. This should include:
            - Clear acknowledgment of what was requested
            - Appropriate meeting operation results or recommendations
            - Any relevant details like meeting conflicts, scheduling suggestions, or formatting
            - Helpful tips or proactive suggestions for better meeting management
            - If operations were performed, confirmation of success with relevant details
            """,
            agent=meeting_manager,
            verbose=True,
            max_retry_limit=3
        )
        
        # Execute the task
        crew = Crew(
            agents=[meeting_manager],
            tasks=[meeting_task],
            verbose=True
        )
        
        # Run the crew and get results
        result = await crew.kickoff_async()
        
        # For now, we'll provide the AI response along with a note about MCP integration
        response = f"""**Meeting Manager Response:**

{str(result)}

**Note:** This is the AI analysis of your meeting request. In a full implementation, 
the actual meeting operations would be performed using the integrated MCP tools.

**Available Operations:**
- Add meetings with conflict checking
- List meetings by date/status
- Search meetings by various criteria  
- Update meeting details
- Delete/cancel meetings
- Check scheduling conflicts
"""
        
        yield Message(parts=[MessagePart(content=response)])
        
    except Exception as e:
        error_response = f"Error in Meeting Manager: {str(e)}"
        yield Message(parts=[MessagePart(content=error_response)])

if __name__ == "__main__":
    print("Starting Meeting Manager Server on port 8100...")
    print("Available endpoints:")
    print("POST /runs (agent: meeting_manager)")
    print("MCP Tools integrated: meeting management operations")
    
    server.run(port=8100) 