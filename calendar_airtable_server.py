import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import aiohttp
from mcp import Server, types
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Initialize the MCP server
server = Server("calendar-airtable-server")

class CalendarAirtableServer:
    def __init__(self):
        self.google_calendar_token = os.getenv('GOOGLE_CALENDAR_TOKEN')
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY')
        self.airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
        
    async def get_google_events(self, start_time: str = None, end_time: str = None):
        """Fetch events from Google Calendar"""
        headers = {
            'Authorization': f'Bearer {self.google_calendar_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'timeMin': start_time or datetime.utcnow().isoformat() + 'Z',
            'timeMax': end_time or (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z',
            'singleEvents': 'true',
            'orderBy': 'startTime'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', [])
                return []
    
    async def create_google_event(self, event_data: Dict[str, Any]):
        """Create a new Google Calendar event"""
        headers = {
            'Authorization': f'Bearer {self.google_calendar_token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://www.googleapis.com/calendar/v3/calendars/primary/events',
                headers=headers,
                json=event_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
    
    async def get_airtable_records(self, table_name: str, filter_formula: str = None):
        """Fetch records from Airtable"""
        headers = {
            'Authorization': f'Bearer {self.airtable_api_key}',
            'Content-Type': 'application/json'
        }
        
        params = {}
        if filter_formula:
            params['filterByFormula'] = filter_formula
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'https://api.airtable.com/v0/{self.airtable_base_id}/{table_name}',
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('records', [])
                return []
    
    async def create_airtable_record(self, table_name: str, fields: Dict[str, Any]):
        """Create a new Airtable record"""
        headers = {
            'Authorization': f'Bearer {self.airtable_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'fields': fields
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'https://api.airtable.com/v0/{self.airtable_base_id}/{table_name}',
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None

# Initialize the service
calendar_service = CalendarAirtableServer()

@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri="calendar://today",
            name="Today's Schedule",
            description="View today's calendar events"
        ),
        types.Resource(
            uri="calendar://week",
            name="Weekly Schedule", 
            description="View this week's calendar events"
        ),
        types.Resource(
            uri="airtable://tasks",
            name="Tasks Database",
            description="Access tasks from Airtable"
        ),
        types.Resource(
            uri="airtable://contacts",
            name="Contacts Database",
            description="Access contacts from Airtable"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read resource content"""
    if uri == "calendar://today":
        today_start = datetime.now().replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        today_end = datetime.now().replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        events = await calendar_service.get_google_events(today_start, today_end)
        
        if not events:
            return "No events scheduled for today."
        
        result = "Today's Schedule:\n"
        for event in events:
            start = event.get('start', {}).get('dateTime', 'All day')
            title = event.get('summary', 'No title')
            result += f"- {start}: {title}\n"
        return result
        
    elif uri == "calendar://week":
        week_start = datetime.now().isoformat() + 'Z'
        week_end = (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
        events = await calendar_service.get_google_events(week_start, week_end)
        
        if not events:
            return "No events scheduled for this week."
            
        result = "This Week's Schedule:\n"
        for event in events:
            start = event.get('start', {}).get('dateTime', 'All day')
            title = event.get('summary', 'No title')
            result += f"- {start}: {title}\n"
        return result
        
    elif uri == "airtable://tasks":
        records = await calendar_service.get_airtable_records("Tasks")
        if not records:
            return "No tasks found in Airtable."
            
        result = "Tasks from Airtable:\n"
        for record in records:
            fields = record.get('fields', {})
            task_name = fields.get('Name', 'Untitled')
            status = fields.get('Status', 'Unknown')
            due_date = fields.get('Due Date', 'No due date')
            result += f"- {task_name} (Status: {status}, Due: {due_date})\n"
        return result
        
    elif uri == "airtable://contacts":
        records = await calendar_service.get_airtable_records("Contacts")
        if not records:
            return "No contacts found in Airtable."
            
        result = "Contacts from Airtable:\n"
        for record in records:
            fields = record.get('fields', {})
            name = fields.get('Name', 'No name')
            email = fields.get('Email', 'No email')
            phone = fields.get('Phone', 'No phone')
            result += f"- {name}: {email}, {phone}\n"
        return result
        
    return f"Unknown resource: {uri}"

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="create_calendar_event",
            description="Create a new calendar event",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "start_datetime": {"type": "string", "description": "Start time (ISO format)"},
                    "end_datetime": {"type": "string", "description": "End time (ISO format)"},
                    "description": {"type": "string", "description": "Event description"},
                    "attendees": {"type": "array", "items": {"type": "string"}, "description": "Attendee emails"}
                },
                "required": ["title", "start_datetime", "end_datetime"]
            }
        ),
        types.Tool(
            name="check_availability",
            description="Check calendar availability for a specific time slot",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date to check (YYYY-MM-DD)"},
                    "start_time": {"type": "string", "description": "Start time (HH:MM)"},
                    "duration_minutes": {"type": "number", "description": "Duration in minutes"}
                },
                "required": ["date", "start_time", "duration_minutes"]
            }
        ),
        types.Tool(
            name="create_airtable_task",
            description="Create a new task in Airtable",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Task name"},
                    "status": {"type": "string", "description": "Task status"},
                    "due_date": {"type": "string", "description": "Due date (YYYY-MM-DD)"},
                    "priority": {"type": "string", "description": "Priority level"},
                    "notes": {"type": "string", "description": "Additional notes"}
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="search_contacts",
            description="Search for contacts in Airtable",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {"type": "string", "description": "Name or email to search for"}
                },
                "required": ["search_term"]
            }
        ),
        types.Tool(
            name="create_reminder",
            description="Create a reminder by adding to both calendar and Airtable",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Reminder title"},
                    "datetime": {"type": "string", "description": "When to be reminded (ISO format)"},
                    "notes": {"type": "string", "description": "Additional notes"}
                },
                "required": ["title", "datetime"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle tool calls"""
    
    if name == "create_calendar_event":
        # Create Google Calendar event
        event_data = {
            "summary": arguments["title"],
            "start": {
                "dateTime": arguments["start_datetime"],
                "timeZone": "America/New_York"  # Adjust to your timezone
            },
            "end": {
                "dateTime": arguments["end_datetime"], 
                "timeZone": "America/New_York"
            }
        }
        
        if "description" in arguments:
            event_data["description"] = arguments["description"]
            
        if "attendees" in arguments:
            event_data["attendees"] = [{"email": email} for email in arguments["attendees"]]
        
        result = await calendar_service.create_google_event(event_data)
        
        if result:
            return [types.TextContent(
                type="text",
                text=f"Calendar event '{arguments['title']}' created successfully!"
            )]
        else:
            return [types.TextContent(
                type="text", 
                text="Failed to create calendar event. Check your credentials."
            )]
            
    elif name == "check_availability":
        # Check if time slot is available
        date = arguments["date"]
        start_time = arguments["start_time"]
        duration = arguments["duration_minutes"]
        
        # Convert to datetime objects
        start_datetime = datetime.fromisoformat(f"{date}T{start_time}:00")
        end_datetime = start_datetime + timedelta(minutes=duration)
        
        # Check calendar for conflicts
        events = await calendar_service.get_google_events(
            start_datetime.isoformat() + 'Z',
            end_datetime.isoformat() + 'Z'
        )
        
        if events:
            conflict_details = []
            for event in events:
                conflict_details.append(f"- {event.get('summary', 'Untitled event')}")
            
            return [types.TextContent(
                type="text",
                text=f"Time slot NOT available. Conflicts:\n" + "\n".join(conflict_details)
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Time slot from {start_time} for {duration} minutes on {date} is AVAILABLE!"
            )]
            
    elif name == "create_airtable_task":
        # Create task in Airtable
        fields = {
            "Name": arguments["name"]
        }
        
        if "status" in arguments:
            fields["Status"] = arguments["status"]
        if "due_date" in arguments:
            fields["Due Date"] = arguments["due_date"]
        if "priority" in arguments:
            fields["Priority"] = arguments["priority"]
        if "notes" in arguments:
            fields["Notes"] = arguments["notes"]
            
        result = await calendar_service.create_airtable_record("Tasks", fields)
        
        if result:
            return [types.TextContent(
                type="text",
                text=f"Task '{arguments['name']}' created in Airtable successfully!"
            )]
        else:
            return [types.TextContent(
                type="text",
                text="Failed to create task in Airtable. Check your credentials."
            )]
            
    elif name == "search_contacts":
        # Search contacts in Airtable
        search_term = arguments["search_term"].lower()
        records = await calendar_service.get_airtable_records("Contacts")
        
        matching_contacts = []
        for record in records:
            fields = record.get("fields", {})
            name = fields.get("Name", "").lower()
            email = fields.get("Email", "").lower()
            
            if search_term in name or search_term in email:
                matching_contacts.append({
                    "name": fields.get("Name", "No name"),
                    "email": fields.get("Email", "No email"),
                    "phone": fields.get("Phone", "No phone")
                })
        
        if matching_contacts:
            result_text = f"Found {len(matching_contacts)} matching contacts:\n"
            for contact in matching_contacts:
                result_text += f"- {contact['name']}: {contact['email']}, {contact['phone']}\n"
        else:
            result_text = f"No contacts found matching '{arguments['search_term']}'"
            
        return [types.TextContent(type="text", text=result_text)]
        
    elif name == "create_reminder":
        # Create reminder (calendar event + Airtable task)
        title = arguments["title"]
        reminder_datetime = arguments["datetime"]
        notes = arguments.get("notes", "")
        
        # Create calendar event
        event_data = {
            "summary": f"Reminder: {title}",
            "start": {
                "dateTime": reminder_datetime,
                "timeZone": "America/New_York"
            },
            "end": {
                "dateTime": (datetime.fromisoformat(reminder_datetime.replace('Z', '')) + timedelta(minutes=15)).isoformat() + 'Z',
                "timeZone": "America/New_York"
            },
            "description": notes
        }
        
        # Create Airtable task
        task_fields = {
            "Name": f"Reminder: {title}",
            "Status": "Pending",
            "Due Date": reminder_datetime.split('T')[0],
            "Notes": notes
        }
        
        calendar_result = await calendar_service.create_google_event(event_data)
        airtable_result = await calendar_service.create_airtable_record("Tasks", task_fields)
        
        if calendar_result and airtable_result:
            return [types.TextContent(
                type="text",
                text=f"Reminder '{title}' created successfully in both calendar and Airtable!"
            )]
        elif calendar_result:
            return [types.TextContent(
                type="text",
                text=f"Reminder '{title}' created in calendar only. Airtable creation failed."
            )]
        elif airtable_result:
            return [types.TextContent(
                type="text", 
                text=f"Reminder '{title}' created in Airtable only. Calendar creation failed."
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"Failed to create reminder '{title}'. Check your credentials."
            )]
    
    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="calendar-airtable-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
