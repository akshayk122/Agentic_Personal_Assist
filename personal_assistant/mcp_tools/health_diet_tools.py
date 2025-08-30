"""
Simple Health and Diet Tools
Basic health goal tracking and food logging with Supabase integration
"""

from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, date
import uuid

from utils.supabase_config import supabase_manager

mcp = FastMCP()

# Fallback in-memory storage (if Supabase not available)
health_goals = {}
food_logs = []

@mcp.tool()
def add_health_goal(
    goal_type: str,
    target_value: float,
    description: str = None,
    daily_calorie_goal: int = None
) -> str:
    """Add a new health goal (weight, calories, etc.) with optional daily calorie goal"""
    try:
        # Try Supabase first
        if supabase_manager.is_connected():
            goal_data = {
                "goal_type": goal_type.lower(),
                "target_value": float(target_value),
                "current_value": 0.0,
                "description": description or "",
                "is_active": True
            }
            goal_id = supabase_manager.add_health_goal(goal_data)
            
            result = f"Health goal added successfully!\n\nGoal: {goal_type.title()}\nTarget: {target_value}\nGoal ID: {goal_id}"
            
            # If daily calorie goal is provided, add it as a separate goal
            if daily_calorie_goal:
                calorie_goal_data = {
                    "goal_type": "daily_calories",
                    "target_value": float(daily_calorie_goal),
                    "current_value": 0.0,
                    "description": "Daily calorie intake target",
                    "is_active": True
                }
                calorie_goal_id = supabase_manager.add_health_goal(calorie_goal_data)
                result += f"\n\nDaily Calorie Goal: {daily_calorie_goal} calories\nCalorie Goal ID: {calorie_goal_id}"
            
            return result
        
        # Fallback to in-memory storage
        goal_id = str(uuid.uuid4())
        goal_data = {
            "goal_id": goal_id,
            "goal_type": goal_type.lower(),
            "target_value": target_value,
            "current_value": 0.0,
            "description": description,
            "created_at": datetime.now().isoformat()
        }
        
        health_goals[goal_id] = goal_data
        
        result = f"Health goal added successfully! (Local Storage)\n\nGoal: {goal_type.title()}\nTarget: {target_value}\nGoal ID: {goal_id}"
        
        # If daily calorie goal is provided, add it as a separate goal
        if daily_calorie_goal:
            calorie_goal_id = str(uuid.uuid4())
            calorie_goal_data = {
                "goal_id": calorie_goal_id,
                "goal_type": "daily_calories",
                "target_value": daily_calorie_goal,
                "current_value": 0.0,
                "description": "Daily calorie intake target",
                "created_at": datetime.now().isoformat()
            }
            health_goals[calorie_goal_id] = calorie_goal_data
            result += f"\n\nDaily Calorie Goal: {daily_calorie_goal} calories\nCalorie Goal ID: {calorie_goal_id}"
        
        return result
    
    except Exception as e:
        return f"Error adding health goal: {str(e)}"

@mcp.tool()
def update_health_goal(
    goal_id: str,
    target_value: float = None,
    current_value: float = None,
    description: str = None
) -> str:
    """Update an existing health goal"""
    try:
        # Try Supabase first
        if supabase_manager.is_connected():
            updates = {}
            if target_value is not None:
                updates["target_value"] = float(target_value)
            if current_value is not None:
                updates["current_value"] = float(current_value)
            if description is not None:
                updates["description"] = description
            
            success = supabase_manager.update_health_goal(goal_id, updates)
            if success:
                return f"Health goal updated successfully!\n\nGoal ID: {goal_id}\nUpdates applied successfully"
            else:
                return f"Health goal {goal_id} not found or update failed"
        
        # Fallback to in-memory storage
        if goal_id not in health_goals:
            return f"Health goal {goal_id} not found"
        
        goal = health_goals[goal_id]
        
        if target_value is not None:
            goal["target_value"] = target_value
        if current_value is not None:
            goal["current_value"] = current_value
        if description is not None:
            goal["description"] = description
        
        return f"Health goal updated successfully! (Local Storage)\n\nGoal: {goal['goal_type'].title()}\nTarget: {goal['target_value']}\nCurrent: {goal['current_value']}"
    
    except Exception as e:
        return f"Error updating health goal: {str(e)}"

@mcp.tool()
def get_health_goals() -> str:
    """Get all active health goals"""
    try:
        # Try Supabase first
        if supabase_manager.is_connected():
            goals = supabase_manager.get_health_goals()
            
            if not goals:
                return "No active health goals found. Add a goal to get started!"
            
            result = "Active Health Goals\n\n"
            for goal in goals:
                progress = (goal.get("current_value", 0) / goal["target_value"]) * 100 if goal["target_value"] > 0 else 0
                result += f"{goal['goal_type'].title()}\n"
                result += f"  Target: {goal['target_value']}\n"
                result += f"  Current: {goal.get('current_value', 0)}\n"
                result += f"  Progress: {progress:.1f}%\n"
                result += f"  Description: {goal.get('description', 'No description')}\n"
                result += f"  Goal ID: {goal['goal_id']}\n\n"
            
            return result
        
        # Fallback to in-memory storage
        active_goals = [goal for goal in health_goals.values() if goal.get("is_active", True)]
        
        if not active_goals:
            return "No active health goals found. Add a goal to get started! (Local Storage)"
        
        result = "Active Health Goals (Local Storage)\n\n"
        for goal in active_goals:
            progress = (goal.get("current_value", 0) / goal["target_value"]) * 100 if goal["target_value"] > 0 else 0
            result += f"{goal['goal_type'].title()}\n"
            result += f"  Target: {goal['target_value']}\n"
            result += f"  Current: {goal.get('current_value', 0)}\n"
            result += f"  Progress: {progress:.1f}%\n"
            result += f"  Description: {goal.get('description', 'No description')}\n"
            result += f"  Goal ID: {goal['goal_id']}\n\n"
        
        return result
    
    except Exception as e:
        return f"Error getting health goals: {str(e)}"

@mcp.tool()
def add_food_log(
    meal_type: str,
    food_item: str,
    calories: int = None
) -> str:
    """Add a food item to your daily log"""
    try:
        today = date.today().isoformat()
        
        # Try Supabase first
        if supabase_manager.is_connected():
            food_data = {
                "meal_type": meal_type.lower(),
                "food_item": food_item,
                "calories": calories,
                "date": today
            }
            food_id = supabase_manager.add_food_log(food_data)
            
            # Get today's total calories from Supabase
            today_foods = supabase_manager.get_food_logs(today)
            total_calories = sum(f.get("calories", 0) for f in today_foods)
            
            result = f"Food logged successfully!\n\nMeal: {meal_type.title()}\nFood: {food_item}\n"
            if calories:
                result += f"Calories: {calories}\n"
            result += f"\nToday's Total Calories: {total_calories}"
            
            # Check for daily calorie goal and update current value
            try:
                goals = supabase_manager.get_health_goals()
                daily_calorie_goal = None
                daily_goal_id = None
                for goal in goals:
                    if goal.get("goal_type") == "daily_calories" and goal.get("is_active", True):
                        daily_calorie_goal = goal.get("target_value")
                        daily_goal_id = goal.get("goal_id")
                        break
                
                if daily_calorie_goal and daily_goal_id:
                    # Update the current value to reflect today's consumption
                    supabase_manager.update_health_goal(daily_goal_id, {"current_value": total_calories})
                    
                    remaining = daily_calorie_goal - total_calories
                    progress = (total_calories / daily_calorie_goal) * 100
                    
                    result += f"\n\nDaily Calorie Limit: {daily_calorie_goal} calories"
                    result += f"\nCalories Consumed: {total_calories} calories"
                    result += f"\nProgress: {progress:.1f}%"
                    if remaining > 0:
                        result += f"\nRemaining Limit: {remaining} calories"
                    else:
                        result += f"\nOver Limit by: {abs(remaining)} calories"
            except:
                pass  # If goal check fails, just show the food log
            
            return result
        
        # Fallback to in-memory storage
        food_id = str(uuid.uuid4())
        
        food_data = {
            "food_id": food_id,
            "meal_type": meal_type.lower(),
            "food_item": food_item,
            "calories": calories,
            "date": today,
            "created_at": datetime.now().isoformat()
        }
        
        food_logs.append(food_data)
        
        # Calculate today's total calories
        today_foods = [f for f in food_logs if f["date"] == today]
        total_calories = sum(f.get("calories", 0) for f in today_foods)
        
        result = f"Food logged successfully! (Local Storage)\n\nMeal: {meal_type.title()}\nFood: {food_item}\n"
        if calories:
            result += f"Calories: {calories}\n"
        result += f"\nToday's Total Calories: {total_calories}"
        
        # Check for daily calorie goal in local storage and update current value
        daily_calorie_goal = None
        daily_goal_id = None
        for goal_id, goal in health_goals.items():
            if goal.get("goal_type") == "daily_calories":
                daily_calorie_goal = goal.get("target_value")
                daily_goal_id = goal_id
                # Update the current value to reflect today's consumption
                goal["current_value"] = total_calories
                break
        
        if daily_calorie_goal:
            remaining = daily_calorie_goal - total_calories
            progress = (total_calories / daily_calorie_goal) * 100
            
            result += f"\n\nDaily Calorie Budget: {daily_calorie_goal} calories"
            result += f"\nCalories Consumed: {total_calories} calories"
            result += f"\nProgress: {progress:.1f}%"
            if remaining > 0:
                result += f"\nRemaining Budget: {remaining} calories"
            else:
                result += f"\nOver Budget by: {abs(remaining)} calories"
        
        return result
    
    except Exception as e:
        return f"Error adding food log: {str(e)}"

@mcp.tool()
def get_food_log() -> str:
    """Get today's food log with calorie goal progress"""
    try:
        today = date.today().isoformat()
        
        # Try Supabase first
        if supabase_manager.is_connected():
            today_foods = supabase_manager.get_food_logs(today)
            
            if not today_foods:
                return "No food logged today"
            
            # Group by meal type
            meals = {}
            for food in today_foods:
                meal_type = food["meal_type"]
                if meal_type not in meals:
                    meals[meal_type] = []
                meals[meal_type].append(food)
            
            result = "Today's Log\n\n"
            total_calories = 0
            
            for meal_type, foods in meals.items():
                result += f"{meal_type.title()}\n"
                meal_calories = 0
                
                for food in foods:
                    result += f"  {food['food_item']}"
                    if food.get("calories"):
                        result += f" ({food['calories']} cal)"
                    result += "\n"
                    meal_calories += food.get("calories", 0)
                
                if meal_calories > 0:
                    result += f"  Meal Total: {meal_calories} calories\n"
                result += "\n"
                total_calories += meal_calories
            
            result += f"Daily Total: {total_calories} calories"
            
            # Check for daily calorie goal and update current value
            try:
                goals = supabase_manager.get_health_goals()
                daily_calorie_goal = None
                daily_goal_id = None
                for goal in goals:
                    if goal.get("goal_type") == "daily_calories" and goal.get("is_active", True):
                        daily_calorie_goal = goal.get("target_value")
                        daily_goal_id = goal.get("goal_id")
                        break
                
                if daily_calorie_goal and daily_goal_id:
                    # Update the current value to reflect today's consumption
                    supabase_manager.update_health_goal(daily_goal_id, {"current_value": total_calories})
                    
                    remaining = daily_calorie_goal - total_calories
                    progress = (total_calories / daily_calorie_goal) * 100
                    
                    result += f"\n\nDaily Calorie Budget: {daily_calorie_goal} calories"
                    result += f"\nCalories Consumed: {total_calories} calories"
                    result += f"\nProgress: {progress:.1f}%"
                    if remaining > 0:
                        result += f"\nRemaining Budget: {remaining} calories"
                    else:
                        result += f"\nOver Budget by: {abs(remaining)} calories"
            except:
                pass  # If goal check fails, just show the food log
            
            return result
        
        # Fallback to in-memory storage
        today_foods = [f for f in food_logs if f["date"] == today]
        
        if not today_foods:
            return "No food logged today"
        
        # Group by meal type
        meals = {}
        for food in today_foods:
            meal_type = food["meal_type"]
            if meal_type not in meals:
                meals[meal_type] = []
            meals[meal_type].append(food)
        
        result = "Today's Food Log (Local Storage)\n\n"
        total_calories = 0
        
        for meal_type, foods in meals.items():
            result += f"{meal_type.title()}\n"
            meal_calories = 0
            
            for food in foods:
                result += f"  {food['food_item']}"
                if food.get("calories"):
                    result += f" ({food['calories']} cal)"
                result += "\n"
                meal_calories += food.get("calories", 0)
            
            if meal_calories > 0:
                result += f"  Meal Total: {meal_calories} calories\n"
            result += "\n"
            total_calories += meal_calories
        
        result += f"Daily Total: {total_calories} calories"
        
        # Check for daily calorie goal in local storage and update current value
        daily_calorie_goal = None
        daily_goal_id = None
        for goal_id, goal in health_goals.items():
            if goal.get("goal_type") == "daily_calories":
                daily_calorie_goal = goal.get("target_value")
                daily_goal_id = goal_id
                # Update the current value to reflect today's consumption
                goal["current_value"] = total_calories
                break
        
        if daily_calorie_goal:
            remaining = daily_calorie_goal - total_calories
            progress = (total_calories / daily_calorie_goal) * 100
            
            result += f"\n\nDaily Calorie Budget: {daily_calorie_goal} calories"
            result += f"\nCalories Consumed: {total_calories} calories"
            result += f"\nProgress: {progress:.1f}%"
            if remaining > 0:
                result += f"\nRemaining Budget: {remaining} calories"
            else:
                result += f"\nOver Budget by: {abs(remaining)} calories"
        
        return result
    
    except Exception as e:
        return f"Error getting food log: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio") 