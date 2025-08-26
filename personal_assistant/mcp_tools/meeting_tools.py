"""
MCP Tools for Meeting Management
Simplified version with hardcoded data
"""

from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import sys
import os

# Initialize MCP server
mcp = FastMCP()

# Hardcoded sample meetings data
SAMPLE_MEETINGS = [
    {
        "meeting_id": "m001",
        "title": "Team Daily Standup",
        "date": "2024-12-16",
        "time": "09:00",
        "duration_minutes": 30,
        "attendees": ["john@company.com", "sarah@company.com"],
        "location": "Conference Room A",
        "description": "Daily team sync",
        "status": "scheduled"
    },
    {
        "meeting_id": "m002",
        "title": "Client Demo Presentation",
        "date": "2024-12-16",
        "time": "14:00",
        "duration_minutes": 60,
        "attendees": ["client@external.com"],
        "location": "Virtual - Zoom",
        "description": "Q4 results presentation",
        "status": "scheduled"
    },
    {
        "meeting_id": "m003",
        "title": "Project Planning",
        "date": "2024-12-17",
        "time": "10:00",
        "duration_minutes": 90,
        "attendees": ["team@company.com", "manager@company.com"],
        "location": "Meeting Room B",
        "description": "Q1 2025 planning session",
        "status": "scheduled"
    }
]

@mcp.tool()
def add_meeting(
    title: str,
    date: str,
    time: str,
    duration_minutes: int = 60,
    attendees: str = "",
    location: str = "",
    description: str = ""
) -> str:
    """Add a new meeting to the calendar (Demo - returns success message)
    
    Args:
        title: Meeting title/subject
        date: Meeting date in YYYY-MM-DD format
        time: Meeting time in HH:MM format
        duration_minutes: Duration of meeting in minutes (default: 60)
        attendees: Comma-separated list of attendee emails
        location: Meeting location (physical or virtual)
        description: Meeting description or agenda
    
    Returns:
        str: Success message with meeting ID
    """
    meeting_id = f"m{len(SAMPLE_MEETINGS) + 1:03d}"
    return f"Meeting '{title}' would be scheduled with ID: {meeting_id} (Demo Mode)"

@mcp.tool()
def list_meetings(
    start_date: str = "",
    end_date: str = "",
    status: str = "all"
) -> str:
    """List meetings within a date range (Demo - returns hardcoded data)
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        status: Filter by status: scheduled|completed|cancelled|all (default: all)
    
    Returns:
        str: Formatted list of meetings
    """
    # Format meetings list
    result = f"Demo Mode - Showing {len(SAMPLE_MEETINGS)} sample meetings:\n\n"
    
    for meeting in SAMPLE_MEETINGS:
        attendees_str = ", ".join(meeting["attendees"])
        result += f" {meeting['title']} \n"
        result += f"{meeting['date']} at {meeting['time']} ({meeting['duration_minutes']} min)\n"
        result += f"📍 {meeting['location']}\n"
        result += f"👥 Attendees: {attendees_str}\n"
        result += f"📝 {meeting['description']}\n"
        result += f"Status: {meeting['status']}\n"
        result += f"ID: {meeting['meeting_id']}\n\n"
    
    return result

@mcp.tool()
def search_meetings(query: str, search_type: str = "title") -> str:
    """Search meetings by title, attendee, or description (Demo - searches hardcoded data)
    
    Args:
        query: Search term
        search_type: Search field: title|attendee|description|all (default: title)
    
    Returns:
        str: Formatted list of matching meetings
    """
    query = query.lower()
    matching_meetings = []
    
    for meeting in SAMPLE_MEETINGS:
        match = False
        
        if search_type in ["title", "all"]:
            if query in meeting["title"].lower():
                match = True
        
        if search_type in ["attendee", "all"]:
            for attendee in meeting["attendees"]:
                if query in attendee.lower():
                    match = True
                    break
        
        if search_type in ["description", "all"]:
            if query in meeting["description"].lower():
                match = True
        
        if match:
            matching_meetings.append(meeting)
    
    if not matching_meetings:
        return f"No meetings found matching '{query}' in {search_type}."
    
    # Format results
    result = f"Found {len(matching_meetings)} meeting(s) matching '{query}':\n\n"
    for meeting in matching_meetings:
        result += f" {meeting['title']}  on {meeting['date']} at {meeting['time']}\n"
        result += f"📍 {meeting['location']} | 🆔 {meeting['meeting_id']}\n\n"
    
    return result

@mcp.tool()
def update_meeting(meeting_id: str, updates: str) -> str:
    """Update a meeting's details (Demo - returns success message)
    
    Args:
        meeting_id: The meeting ID to update
        updates: JSON string with updates (e.g., '{"title": "New Title", "time": "10:00"}')
    
    Returns:
        str: Success or error message
    """
    return f"Meeting {meeting_id} would be updated (Demo Mode)"

@mcp.tool()
def delete_meeting(meeting_id: str) -> str:
    """Delete/cancel a meeting (Demo - returns success message)
    
    Args:
        meeting_id: The meeting ID to delete
    
    Returns:
        str: Success or error message
    """
    return f"Meeting {meeting_id} would be deleted (Demo Mode)"

@mcp.tool()
def get_meeting_conflicts(date: str, time: str, duration_minutes: int = 60) -> str:
    """Check for meeting conflicts at a specific time (Demo - checks against hardcoded data)
    
    Args:
        date: Meeting date in YYYY-MM-DD format
        time: Meeting time in HH:MM format
        duration_minutes: Duration to check for conflicts (default: 60)
    
    Returns:
        str: List of conflicting meetings or confirmation of no conflicts
    """
    # Parse proposed meeting time
    proposed_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    proposed_end = proposed_start + timedelta(minutes=duration_minutes)
    
    conflicts = []
    
    for meeting in SAMPLE_MEETINGS:
        if meeting["date"] == date and meeting["status"] == "scheduled":
            existing_start = datetime.strptime(f"{meeting['date']} {meeting['time']}", "%Y-%m-%d %H:%M")
            existing_end = existing_start + timedelta(minutes=meeting["duration_minutes"])
            
            # Check for overlap
            if (proposed_start < existing_end and proposed_end > existing_start):
                conflicts.append(meeting)
    
    if not conflicts:
        return f"No conflicts found for {date} at {time}."
    
    result = f"Found {len(conflicts)} conflict(s) for {date} at {time}:\n\n"
    for conflict in conflicts:
        result += f" {conflict['title']} \n"
        result += f"{conflict['date']} {conflict['time']} - {conflict['duration_minutes']} min\n"
        result += f"📍 {conflict['location']}\n\n"
    
    return result

if __name__ == "__main__":
    mcp.run(transport="stdio") 