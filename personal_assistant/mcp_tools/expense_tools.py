"""
MCP Tools for Expense Management
Simplified version with Supabase storage and user_id integration
"""

from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import sys
import os
from collections import defaultdict

# Add parent directory to path to import utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.supabase_config import SupabaseManager

# Initialize MCP server
mcp = FastMCP()

@mcp.tool()
def add_expense(
    amount: float,
    category: str,
    description: str,
    date: str = "",
    payment_method: str = "credit",
    subcategory: str = "",
    tags: str = "",
    user_id: str = ""
) -> str:
    """Add a new expense to the tracker
    
    Args:
        amount: Expense amount (e.g.,$25.50)
        category: Expense category (food|transportation|entertainment|utilities|healthcare|shopping|electronics|other)
        description: Description of the expense
        date: Expense date in YYYY-MM-DD format (default: today)
        payment_method: Payment method (cash|credit|debit|online) (default: credit)
        subcategory: Subcategory for better organization (optional)
        tags: Comma-separated tags (optional)
        user_id: User ID for expense ownership (optional, uses default if not provided)
    
    Returns:
        str: Success message with expense ID
    """
    print(f"[MCP Tool] add_expense called with: amount={amount}, category={category}, description={description}, user_id={user_id}")
    try:
        # Use provided user_id or default from environment
        target_user_id = user_id or os.getenv('USER_ID', 'default_user')
        
        # Initialize Supabase manager with specific user_id
        supabase_manager = SupabaseManager(user_id=target_user_id)
        
        # Use today's date if not provided
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        expense_data = {
            "amount": float(amount),
            "currency": "USD",
            "category": category.lower(),
            "subcategory": subcategory,
            "description": description,
            "date": date,
            "payment_method": payment_method.lower(),
            "is_recurring": False,
            "tags": tag_list
        }
        print(f"[MCP Tool] Prepared expense data: {expense_data}")
        
        if not supabase_manager.is_connected():
            raise Exception("Database not available. Please check your Supabase configuration.")
            
        expense_id = supabase_manager.add_expense(expense_data)
        print(f"[MCP Tool] Successfully added to Supabase with ID: {expense_id} for user: {target_user_id}")
        return f"Expense of ${amount:.2f} for '{description}' added with ID: {expense_id} for user: {target_user_id}"
        
    except Exception as e:
        return f"Error adding expense: {str(e)}"

@mcp.tool()
def list_expenses(
    start_date: str = "",
    end_date: str = "",
    category: str = "all",
    min_amount: float = 0,
    max_amount: float = 999999,
    list_all: bool = False,
    user_id: str = ""
) -> str:
    """List expenses within specified filters. If list_all is True, ignores other filters.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        category: Filter by category or 'all' (default: all)
        min_amount: Minimum amount filter (default: 0)
        max_amount: Maximum amount filter (default: 999999)
        list_all: If True, lists all expenses ignoring other filters (default: False)
        user_id: User ID to filter expenses (optional, uses default if not provided)
    
    Returns:
        str: Formatted list of expenses
    """
    try:
        # Use provided user_id or default from environment
        target_user_id = user_id or os.getenv('USER_ID', 'default_user')
        
        # Initialize Supabase manager with specific user_id
        supabase_manager = SupabaseManager(user_id=target_user_id)
        
        if not supabase_manager.is_connected():
            raise Exception("Database not available. Please check your Supabase configuration.")
            
        if list_all:
            filters = {}
        else:
            # Build filters for Supabase
            filters = {}
            if start_date:
                filters["start_date"] = start_date
            if end_date:
                filters["end_date"] = end_date
            if category != "all":
                filters["category"] = category.lower()
            if min_amount > 0:
                filters["min_amount"] = min_amount
            if max_amount < 999999:
                filters["max_amount"] = max_amount
        
        expenses = supabase_manager.get_expenses(filters, user_id=target_user_id)
        
        if not expenses:
            return f"No expenses found for user: {target_user_id}"
        
        # Calculate total
        total_amount = sum(e["amount"] for e in expenses)
        
        # Format expenses list
        result = f"Found {len(expenses)} expense(s) for user: {target_user_id} | Total: ${total_amount:.2f}\n\n"
        
        for expense in expenses:
            tags_str = ", ".join(expense.get("tags", []))
            result += f"${expense['amount']:.2f} - {expense['description']}\n"
            result += f"Date: {expense['date']}\n"
            result += f"Category: {expense['category'].title()}"
            if expense.get("subcategory"):
                result += f" > {expense['subcategory']}"
            result += "\n"
            result += f"Payment: {expense['payment_method'].title()}\n"
            if tags_str:
                result += f"Tags: {tags_str}\n"
            result += f"ID: {expense['expense_id']}\n\n"
        
        return result
        
    except Exception as e:
        return f"Error listing expenses: {str(e)}"

@mcp.tool()
def filter_expenses(
    category: str,
    user_id: str = ""
) -> str:
    """Filter expenses by category
    
    Args:
        category: Category to filter by (food|transportation|entertainment|utilities|healthcare|shopping|electronics|other)
        user_id: User ID to filter expenses (optional, uses default if not provided)
    
    Returns:
        str: Formatted list of filtered expenses
    """
    try:
        # Use provided user_id or default from environment
        target_user_id = user_id or os.getenv('USER_ID', 'default_user')
        
        # Initialize Supabase manager with specific user_id
        supabase_manager = SupabaseManager(user_id=target_user_id)
        
        if not supabase_manager.is_connected():
            raise Exception("Database not available. Please check your Supabase configuration.")
            
        # Build filters for category
        filters = {"category": category.lower()}
        print(f"[MCP Tool] Filtering expenses by category: {category} for user: {target_user_id}")
        
        expenses = supabase_manager.get_expenses(filters, user_id=target_user_id)
        
        if not expenses:
            return f"No expenses found for category: {category} and user: {target_user_id}"
        
        # Calculate total
        total_amount = sum(e["amount"] for e in expenses)
        
        # Format expenses list
        result = f"Found {len(expenses)} expense(s) for category '{category}' and user '{target_user_id}' | Total: ${total_amount:.2f}\n\n"
        
        for expense in expenses:
            tags_str = ", ".join(expense.get("tags", []))
            result += f"${expense['amount']:.2f} - {expense['description']}\n"
            result += f"Date: {expense['date']}\n"
            result += f"Payment: {expense['payment_method'].title()}\n"
            if tags_str:
                result += f"Tags: {tags_str}\n"
            result += f"ID: {expense['expense_id']}\n\n"
        
        return result
        
    except Exception as e:
        return f"Error filtering expenses: {str(e)}"

@mcp.tool()
def get_expense_summary(
    period: str = "month",
    group_by: str = "category",
    user_id: str = ""
) -> str:
    """Get expense summary and analytics
    
    Args:
        period: Time period (week|month|quarter|year) (default: month)
        group_by: Group expenses by (category|date|payment_method) (default: category)
        user_id: User ID to get summary for (optional, uses default if not provided)
    
    Returns:
        str: Formatted expense summary
    """
    try:
        # Use provided user_id or default from environment
        target_user_id = user_id or os.getenv('USER_ID', 'default_user')
        
        # Initialize Supabase manager with specific user_id
        supabase_manager = SupabaseManager(user_id=target_user_id)
        
        if not supabase_manager.is_connected():
            raise Exception("Database not available. Please check your Supabase configuration.")
            
        # Calculate date range based on period
        now = datetime.now()
        if period == "week":
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        elif period == "month":
            start_date = now.replace(day=1).strftime("%Y-%m-%d")
        elif period == "quarter":
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(month=quarter_start_month, day=1).strftime("%Y-%m-%d")
        elif period == "year":
            start_date = now.replace(month=1, day=1).strftime("%Y-%m-%d")
        else:
            start_date = None
        
        filters = {"start_date": start_date} if start_date else None
        summary = supabase_manager.get_expense_summary(filters)
        
        if summary["total_expenses"] == 0:
            return f"No expenses found to summarize for user: {target_user_id}"
        
        # Format the summary response
        result = f"Expense Summary for user: {target_user_id} - Last {period.title()}\n"
        result += f"Total Spent: ${summary['total_amount']:.2f}\n"
        result += f"Number of Transactions: {summary['total_expenses']}\n"
        result += f"Average per Transaction: ${summary['average_expense']:.2f}\n\n"
        
        result += f"Breakdown by Category:\n"
        
        # Check if categories exist and handle empty case
        if summary['categories']:
            # Sort categories by amount (highest first)
            sorted_categories = sorted(summary['categories'].items(), key=lambda x: x[1]['amount'], reverse=True)
            
            for category_name, category_data in sorted_categories:
                try:
                    percentage = (category_data['amount'] / summary['total_amount']) * 100 if summary['total_amount'] > 0 else 0
                    result += f"{category_name.title()}: ${category_data['amount']:.2f} ({percentage:.1f}%) - {category_data['count']} transactions\n"
                except (KeyError, TypeError, ZeroDivisionError) as e:
                    print(f"[MCP Tool] Error formatting category {category_name}: {e}")
                    result += f"{category_name.title()}: ${category_data.get('amount', 0):.2f} - {category_data.get('count', 0)} transactions\n"
        else:
            result += "No categories found in expense data.\n"
        
        return result
        
    except Exception as e:
        return f"Error generating expense summary: {str(e)}"

@mcp.tool()
def update_expense(
    expense_id: str,
    updates: str,
    user_id: str = ""
) -> str:
    """Update an expense's details
    
    Args:
        expense_id: The expense ID to update
        updates: JSON string with updates (e.g., '{"amount": 15.75, "category": "food"}')
        user_id: User ID to verify expense ownership (optional, uses default if not provided)
    
    Returns:
        str: Success or error message
    """
    try:
        # Use provided user_id or default from environment
        target_user_id = user_id or os.getenv('USER_ID', 'default_user')
        
        # Initialize Supabase manager with specific user_id
        supabase_manager = SupabaseManager(user_id=target_user_id)
        
        if not supabase_manager.is_connected():
            raise Exception("Database not available. Please check your Supabase configuration.")
            
        # Parse updates JSON
        update_data = json.loads(updates)
        
        # First verify the expense belongs to the user
        user_expenses = supabase_manager.get_expenses(user_id=target_user_id)
        expense_exists = any(e["expense_id"] == expense_id for e in user_expenses)
        
        if not expense_exists:
            return f"Expense {expense_id} not found for user: {target_user_id}"
        
        success = supabase_manager.update_expense(expense_id, update_data)
        
        if success:
            return f"Expense {expense_id} updated successfully for user: {target_user_id}"
        else:
            return f"Failed to update expense {expense_id} for user: {target_user_id}"
            
    except json.JSONDecodeError:
        return "Invalid JSON format for updates."
    except Exception as e:
        return f"Error updating expense: {str(e)}"

@mcp.tool()
def delete_expense(
    expense_id: str,
    user_id: str = ""
) -> str:
    """Delete an expense
    
    Args:
        expense_id: The expense ID to delete
        user_id: User ID to verify expense ownership (optional, uses default if not provided)
    
    Returns:
        str: Success or error message
    """
    try:
        # Use provided user_id or default from environment
        target_user_id = user_id or os.getenv('USER_ID', 'default_user')
        
        # Initialize Supabase manager with specific user_id
        supabase_manager = SupabaseManager(user_id=target_user_id)
        
        if not supabase_manager.is_connected():
            raise Exception("Database not available. Please check your Supabase configuration.")
            
        # First verify the expense belongs to the user
        user_expenses = supabase_manager.get_expenses(user_id=target_user_id)
        expense_exists = any(e["expense_id"] == expense_id for e in user_expenses)
        
        if not expense_exists:
            return f"Expense {expense_id} not found for user: {target_user_id}"
        
        success = supabase_manager.delete_expense(expense_id)
        
        if success:
            return f"Expense {expense_id} deleted successfully for user: {target_user_id}"
        else:
            return f"Failed to delete expense {expense_id} for user: {target_user_id}"
            
    except Exception as e:
        return f"Error deleting expense: {str(e)}"

@mcp.tool()
def get_user_expenses_summary(user_id: str = "") -> str:
    """Get a comprehensive summary of all expenses for a specific user
    
    Args:
        user_id: User ID to get summary for (optional, uses default if not provided)
    
    Returns:
        str: Comprehensive expense summary for the user
    """
    try:
        # Use provided user_id or default from environment
        target_user_id = user_id or os.getenv('USER_ID', 'default_user')
        
        # Initialize Supabase manager with specific user_id
        supabase_manager = SupabaseManager(user_id=target_user_id)
        
        if not supabase_manager.is_connected():
            raise Exception("Database not available. Please check your Supabase configuration.")
        
        # Get all expenses for the user
        all_expenses = supabase_manager.get_expenses(user_id=target_user_id)
        
        if not all_expenses:
            return f"No expenses found for user: {target_user_id}"
        
        # Calculate overall statistics
        total_amount = sum(e["amount"] for e in all_expenses)
        total_transactions = len(all_expenses)
        average_expense = total_amount / total_transactions if total_transactions > 0 else 0
        
        # Category breakdown
        categories = {}
        payment_methods = {}
        
        for expense in all_expenses:
            # Category stats
            category = expense["category"]
            if category not in categories:
                categories[category] = {"count": 0, "amount": 0.0}
            categories[category]["count"] += 1
            categories[category]["amount"] += expense["amount"]
            
            # Payment method stats
            payment_method = expense["payment_method"]
            if payment_method not in payment_methods:
                payment_methods[payment_method] = {"count": 0, "amount": 0.0}
            payment_methods[payment_method]["count"] += 1
            payment_methods[payment_method]["amount"] += expense["amount"]
        
        # Format comprehensive summary
        result = f"📊 COMPREHENSIVE EXPENSE SUMMARY FOR USER: {target_user_id}\n"
        result += "=" * 60 + "\n\n"
        
        result += f"💰 OVERALL STATISTICS:\n"
        result += f"Total Spent: ${total_amount:.2f}\n"
        result += f"Total Transactions: {total_transactions}\n"
        result += f"Average per Transaction: ${average_expense:.2f}\n\n"
        
        result += f"BREAKDOWN BY CATEGORY:\n"
        sorted_categories = sorted(categories.items(), key=lambda x: x[1]['amount'], reverse=True)
        for category_name, category_data in sorted_categories:
            percentage = (category_data['amount'] / total_amount) * 100
            result += f"• {category_name.title()}: ${category_data['amount']:.2f} ({percentage:.1f}%) - {category_data['count']} transactions\n"
        
        result += f"\nBREAKDOWN BY PAYMENT METHOD:\n"
        sorted_payments = sorted(payment_methods.items(), key=lambda x: x[1]['amount'], reverse=True)
        for payment_name, payment_data in sorted_payments:
            percentage = (payment_data['amount'] / total_amount) * 100
            result += f"• {payment_name.title()}: ${payment_data['amount']:.2f} ({percentage:.1f}%) - {payment_data['count']} transactions\n"
        
        # Date range
        dates = [e["date"] for e in all_expenses]
        if dates:
            result += f"\nDATE RANGE:\n"
            result += f"From: {min(dates)} to {max(dates)}\n"
        
        return result
        
    except Exception as e:
        return f"Error generating user expense summary: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio") 