import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
import nest_asyncio
import sys
from utils.gemini_config import get_llm
from mcp_tools.notes_tool import list_notes, add_note, update_note, delete_note

load_dotenv()

from utils.gemini_config import get_llm
nest_asyncio.apply()

llm = get_llm()

class NotesAgentTool(BaseTool):
    name: str = "notes_agent"
    description: str = "Show users their notes in a structured way."
    def _run(self, query: str) -> str:
        return list_notes(query)

class AddNoteTool(BaseTool):
    name: str = "add_note"
    description: str = "Add a new note to your notes database."
    def _run(self, content: str, is_completed: bool = False) -> str:
        return add_note(content, is_completed)

class UpdateNoteTool(BaseTool):
    name: str = "update_note"
    description: str = "Update a note's content or completion status."
    def _run(self, note_id: str, content: str = None, is_completed: bool = None) -> str:
        return update_note(note_id, content, is_completed)
    
class DeleteNoteTool(BaseTool):
    name: str = "delete_note"
    description: str = "Delete a note from your notes database."
    def _run(self, note_id: str) -> str:
        return delete_note(note_id)

notes_tools = [
    NotesAgentTool(),
    AddNoteTool(),
    UpdateNoteTool(),
    DeleteNoteTool()
]

class NotesAgent:
    def __init__(self):
        self.agent = Agent(
            role="Notes Manager",
            goal="Help users manage their notes (add, list, delete, update)",
            backstory="""Smart Notes Assistant

Manages personal notes with clear, organized responses.

## Core Functions
-  Add Notes : Create new notes with content and completion status
-  View Notes : List and search notes with filtering options
-  Update Notes : Modify content or mark as completed/pending
-  Delete Notes : Remove notes with confirmation

## Response Style
-  Professional Formatting : Use clear headers, bullet points, structured layouts
-  Concise Language : Provide direct, actionable responses
-  Status Indicators : Use ✓ Success, Warning, Error
-  Data Presentation : Present notes in organized lists with proper spacing
-  Action Confirmation : Provide clear confirmation messages
-  Error Handling : Give helpful error messages with suggestions
-  Privacy Focus : Maintain strict confidentiality

## Output Formatting Standards
-  Note Lists : Numbered lists with headers and timestamps
-  Status Updates : Include completion status and modified dates
-  Action Results : Provide confirmation with note ID and details
-  Error Messages : Include error codes and resolution steps
-  Empty States : Handle empty lists with helpful guidance
-  Search Results : Highlight matching content with context

## Structured Response Templates
-  Success : "[Operation] completed successfully. [Details]"
-  Error : "[Operation] failed: [Error]. [Suggestion]"
-  Information : "[Information type]: [Details]"
-  Warning : "[Warning message]. [Recommendation]"
""",
            llm=llm,
            tools=notes_tools,
            verbose=False,
            allow_delegation=False
        )

    async def handle(self, query: str) -> str:
        # Dynamically set the task description based on the query intent
        query_lower = query.lower()
        if any(word in query_lower for word in ["add", "create", "new note"]):
            task_description = (
                f"If the user wants to add a note, use the add_note tool with the note content extracted from: '{query}'. "
                "Otherwise, process the request as a note management query."
            )
        else:
            task_description = (
                f"Process this note-related request: '{query}' and return the result in the most professional and concise manner."
            )

        task = Task(
            description=task_description,
            expected_output="A clear, actionable response to the user's note management request in a professional and concise manner.",
            agent=self.agent,
            verbose=False
        )
        # Create and run the Crew
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=False
        )
        result = await crew.kickoff_async()
        return str(result)
    
