"""
ACP Server 3 - Personal Assistant Orchestrator 
Port: 8300

Coordinates between Meeting Manager, Expense Tracker, Notes, and Health/Diet agents
Following the pattern from acp_demo.py
"""

import logging
import os
import re
from collections.abc import AsyncGenerator
from acp_sdk.models import Message, MessagePart
from acp_sdk.server import Server, RunYield, RunYieldResume
from acp_sdk.client import Client
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
import nest_asyncio
import sys
import os
import asyncio
from agents.notes_agents import NotesAgent
from agents.health_diet_agent import HealthDietAgent

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.gemini_config import get_llm

# Apply asyncio patch for Jupyter compatibility
nest_asyncio.apply()

# Initialize server and get configured LLM
server = Server()
llm = get_llm()

def extract_user_id_from_query(query: str) -> str:
    """Extract user_id from query using various patterns"""
    # Pattern 1: "for user: user123" or "user: user123"
    user_pattern1 = r'(?:for\s+)?user\s*:\s*([a-zA-Z0-9_-]+)'
    match = re.search(user_pattern1, query, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 2: "user123's expenses" or "user123 expenses"
    user_pattern2 = r'([a-zA-Z0-9_-]+)\'?s?\s+(?:expenses?|spending|costs?)'
    match = re.search(user_pattern2, query, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 3: "my expenses as user123" or "expenses for user123"
    user_pattern3 = r'(?:my\s+)?expenses?\s+(?:as\s+|for\s+)([a-zA-Z0-9_-]+)'
    match = re.search(user_pattern3, query, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return os.getenv('USER_ID', 'default_user')


class QueryExpenseAgentTool(BaseTool):
    name: str = "query_expense_agent"
    description: str = "Query the expense tracking agent for financial management tasks"
    
    async def _run(self, query: str, user_id: str = "") -> str:
        try:
            # Add user_id to the query if provided
            if user_id and user_id != os.getenv('USER_ID', 'default_user'):
                if "for user:" not in query.lower() and "user:" not in query.lower():
                    query = f"{query} for user: {user_id}"
            
            print(f"[Orchestrator] Sending expense query: {query}")
            
            async with Client(base_url="http://localhost:8200") as client:
                run = await client.run_sync(
                    agent="expense_tracker", 
                    input=[
                        Message(parts=[MessagePart(content=query, content_type="text/plain")]),
                        Message(parts=[MessagePart(content=user_id, content_type="text/plain")])
                        ]
                )
                return run.output[0].parts[0].content
        except Exception as e:
            return f"Unable to contact Expense Tracker: {str(e)}"

class QueryNotesAgentTool(BaseTool):
    name: str = "query_notes_agent"
    description: str = "Query the notes agent for note-taking tasks"
    
    async def _run(self, query: str) -> str:
        try:
            return await NotesAgent().handle(query)
        except Exception as e:
            return f"Unable to contact Notes Agent: {str(e)}"
        
class QueryHealthDietAgentTool(BaseTool):
    name: str = "query_health_diet_agent"
    description: str = "Query the health and diet agent for health and diet related tasks"
    
    async def _run(self, query: str) -> str:
        return await HealthDietAgent().handle(query)

# Initialize tools
orchestrator_tools = [
    # QueryMeetingAgentTool(),
    QueryExpenseAgentTool(),
    QueryNotesAgentTool(),
    QueryHealthDietAgentTool()
]

@server.agent(
    name="personal_assistant",
    description="""Personal Assistant Orchestrator

Coordinates Expense Tracker, Notes, and Health/Diet agents to provide intelligent responses.
## Core Capabilities
- Expense Tracking: Record, categorize, analyze expenses  
- Notes Management: Create, search, organize notes
- Health & Diet: Track goals, log food, monitor progress
- Integrated Services: Handle multi-agent queries


## Query Routing
- Expense queries → Expense Tracker (expense, spend, money, budget)
- Notes queries → Notes Agent (note, search, organize)
- Health and Diet queries → Health and Diet Agent (health, diet, fitness, nutrition, weight, exercise, meal, calorie, workout, food, goal, ate, eat, target, daily)
- Combined queries → Multiple agents as needed

## Response Processing
- Filter data based on user criteria (time periods, categories, status)
- Consolidate duplicate entries and group related items
- Provide formatted summaries with totals and breakdowns
- Present refined results instead of raw data"""
)
async def orchestrator_agent(input: list[Message]) -> AsyncGenerator[RunYield, RunYieldResume]:
    try:
        # Extract user query and user_id
        user_query = input[0].parts[0].content
        user_id = input[1].parts[0].content
        #extracted_user_id = extract_user_id_from_query(user_query)
        extracted_user_id = user_id
        
        
        print(f"[Orchestrator] Query: {user_query}")
        print(f"[Orchestrator] Extracted user_id: {extracted_user_id}")
        
        # Create the orchestrator agent
        coordinator = Agent(
            role="Personal Assistant Coordinator",
            goal="Route queries to appropriate specialized agents and coordinate their responses",
            backstory="""Expert Personal Assistant Coordinator

Coordinates between specialized agents for personal and professional task management.

## Core Responsibilities
- Analyze user queries and route to appropriate agents
- Process and refine agent responses based on user intent
- Handle errors gracefully and provide helpful alternatives
- Extract and pass user_id to ensure data isolation


## Operating Rules
- Use single agent for specific queries (meeting → Meeting Manager - DISABLED, expense → Expense Tracker, notes → Notes Agent, health → Health/Diet Agent)
- Use multiple agents only when explicitly needed
- Choose exactly ONE tool per task, never retry with different tools
- Always pass user_id to expense queries

## Query Classification
- **Expense queries**: expense, spend, cost, money, budget  
- **Notes queries**: note, search, organize, complete
- **Health and Diet queries**: health, diet, fitness, nutrition, weight, exercise, meal, calorie, workout, food, goal, ate, eat, target
- **Combined queries**: Explicitly asks for multiple types of info

## Response Processing
- Filter data based on user criteria (time periods, categories, status)
- Consolidate duplicate entries and group related items
- Provide formatted summaries with totals and breakdowns
- Present refined results instead of raw data
- Always include user context in responses

## POLITE REDIRECTION FOR UNSUPPORTED QUERIES:
If users ask about anything other than the three supported services, respond politely:
"I'm here to help you with three main areas: Expense Tracking, Health & Diet Management, and Notes Management. I can't assist with [their request], but I'd be happy to help with any of these services. What would you like to know about?""",
            llm=llm,
            tools=orchestrator_tools,
            allow_delegation=False,
            verbose=True
        )
        task = Task(
            description=f"""Route this query to the appropriate agent(s) and process the response intelligently: {user_query}

GREETING-ONLY QUERIES:
If the user query is just a simple greeting (hi, hello, hey, good morning, etc.) or general question about capabilities:
- DO NOT call any tools or agents
- DO NOT provide sample data or examples
- ONLY respond with a warm greeting and brief service overview
- Example response: "Hello! I'm your personal assistant. I can help you with three main areas: Expense Tracking, Health & Diet Management, and Notes Management. What would you like to work on today?"

SPECIFIC TASK QUERIES:
Only call tools/agents when user asks for specific actions like:
- Adding/viewing/Deleting expenses
- Creating/searching notes  
- Logging food or health goals

IMPORTANT: 
- use user_id: {extracted_user_id}
- Pass user_id to expense queries
- Ensure user data isolation
- MEETING SERVER IS DISABLED - Do NOT respond with meeting information
- Available services: Expense Tracking, Notes Management, Health & Diet

UNSUPPORTED QUERIES:
If the user asks about ANYTHING other than expenses, health/diet, or notes, respond politely:
"I'm here to help you with three main areas: Expense Tracking, Health & Diet Management, and Notes Management. I can't assist with [their request], but I'd be happy to help with any of these services. What would you like to know about?"

SUPPORTED SERVICES ONLY:
- Expense Tracking: Record, categorize, analyze expenses
- Notes Management: Create, search, organize notes  
- Health & Diet: Track goals, log food, monitor progress

- After receiving the agent response, analyze the user's intent and:
1. Filter the data based on user criteria (e.g., "last month", "food expenses", "completed notes")
2. Consolidate duplicate or similar entries
3. Group related items intelligently
4. Calculate totals and summaries
5. Present the refined, filtered result instead of raw data
6. Always include user context in responses

User ID Context: {extracted_user_id}""",
            expected_output="Intelligently filtered and processed response based on user criteria with user_id context, not raw agent data",
            agent=coordinator,
            verbose=True
        )

        # Create and run the crew
        crew = Crew(
            agents=[coordinator],
            tasks=[task],
            verbose=True
        )

        # Execute the task and get result
        result = await crew.kickoff_async()
        
        # Return the result
        yield Message(parts=[MessagePart(content=str(result))])
            
    except Exception as e:
        error_response = f"Error in Personal Assistant Orchestrator: {str(e)}"
        yield Message(parts=[MessagePart(content=error_response)])

if __name__ == "__main__":
    print("Personal Assistant Orchestrator Agent is running on port 8300...")
    
    server.run(port=8300) 