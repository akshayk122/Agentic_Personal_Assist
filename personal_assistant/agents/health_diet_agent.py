import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
import nest_asyncio
import sys

# Add parent directories to path and other env variable
load_dotenv()

from utils.gemini_config import get_llm
from mcp_tools.health_diet_tools import (
    add_health_goal, update_health_goal, get_health_goals,
    add_food_log, get_food_log
)
nest_asyncio.apply()

llm = get_llm()

class HealthDietAgentTool(BaseTool):
    name: str = "health_diet_agent"
    description: str = "Show users their health and diet summary."
    def _run(self, query: str) -> str:
        return get_food_log()

class AddHealthGoalTool(BaseTool):
    name: str = "add_health_goal"
    description: str = "Add a new health goal (weight, calories, etc.) with optional daily calorie goal"
    def _run(self, goal_type: str, target_value: float, description: str = None, daily_calorie_goal: int = None) -> str:
        return add_health_goal(goal_type, target_value, description, daily_calorie_goal)

class UpdateHealthGoalTool(BaseTool):
    name: str = "update_health_goal"
    description: str = "Update an existing health goal"
    def _run(self, goal_id: str, target_value: float = None, current_value: float = None, description: str = None) -> str:
        return update_health_goal(goal_id, target_value, current_value, description)

class AddFoodLogTool(BaseTool):
    name: str = "add_food_log"
    description: str = "Add a food item to your daily log"
    def _run(self, meal_type: str, food_item: str, calories: int = None) -> str:
        return add_food_log(meal_type, food_item, calories)

class GetFoodLogTool(BaseTool):
    name: str = "get_food_log"
    description: str = "Get today's food log"
    def _run(self) -> str:
        return get_food_log()

class GetHealthGoalsTool(BaseTool):
    name: str = "get_health_goals"
    description: str = "Get all active health goals"
    def _run(self) -> str:
        return get_health_goals()

health_diet_tools = [
    HealthDietAgentTool(),
    AddHealthGoalTool(),
    UpdateHealthGoalTool(),
    AddFoodLogTool(),
    GetFoodLogTool(),
    GetHealthGoalsTool()
]

class HealthDietAgent:
    def __init__(self):
        self.agent = Agent(
            role="Health & Diet Manager",
            goal="Help users track their health goals and food logging",
            backstory="""Health & Diet Assistant

Manages basic health goal tracking and food logging.

## Core Functions
-  Health Goals : Set and update health goals (weight, calories, etc.)
-  Daily Calorie Goals : Set daily calorie intake targets
-  Food Logging : Log daily meals and track calories
-  Progress Tracking : Show progress against daily calorie goals
-  Simple Tracking : Easy-to-use health and diet management

## Response Formatting
-  Simple Formatting : Clear, easy-to-read responses
-  Direct Language : Provide straightforward answers
-  Success Indicators : Use clear success/error messages
-  Data Presentation : Show totals and summaries clearly
-  Privacy Focus : Maintain health data confidentiality

## Output Formatting Standards
-  Goal Management : Show goal type, target, and current values
-  Food Logging : Display meals by type with calorie totals
-  Daily Summaries : Show total calories for the day
-  Calorie Progress : Display progress against daily calorie goals
-  Success Messages : Confirm actions with clear feedback

## Professional Response Templates
-  Success : "[Action] completed successfully. [Details]"
-  Error : "[Action] failed: [Error]"
-  Information : "[Information type]: [Details]"
-  Summary : "[Summary type]: [Key data]"
""",
            llm=llm,
            tools=health_diet_tools,
            verbose=False,
            allow_delegation=False
        )

    async def handle(self, query: str) -> str:
        # Dynamically set the task description based on the query intent
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["add", "set", "create"]) and any(word in query_lower for word in ["goal", "target"]):
            task_description = (
                f"If the user wants to add a health goal, use the add_health_goal tool with the appropriate parameters extracted from: '{query}'. "
                "Otherwise, process the request as a general health query."
            )
        elif any(word in query_lower for word in ["update", "change", "modify"]) and any(word in query_lower for word in ["goal"]):
            task_description = (
                f"If the user wants to update a health goal, use the update_health_goal tool with the appropriate parameters extracted from: '{query}'. "
                "Otherwise, process the request as a general health query."
            )
        elif any(word in query_lower for word in ["add", "log", "ate", "eat", "food", "meal"]):
            task_description = (
                f"If the user wants to log food, use the add_food_log tool with the appropriate parameters extracted from: '{query}'. "
                "Otherwise, process the request as a general diet query."
            )
        elif any(word in query_lower for word in ["show", "view", "see", "what", "today"]) and any(word in query_lower for word in ["food", "ate", "eat", "meal"]):
            task_description = (
                f"If the user wants to see their food log, use the get_food_log tool. "
                "Otherwise, process the request as a general diet query."
            )
        elif any(word in query_lower for word in ["show", "view", "see", "list", "get"]) and any(word in query_lower for word in ["goal", "goals"]):
            task_description = (
                f"If the user wants to see their health goals, use the get_health_goals tool. "
                "Otherwise, process the request as a general health query."
            )
        else:
            task_description = (
                f"Process this health and diet-related request: '{query}' and return the result in a simple, clear manner."
            )

        task = Task(
            description=task_description,
            expected_output="A clear, simple response to the user's health and diet request.",
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
