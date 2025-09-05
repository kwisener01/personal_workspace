from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
import os
from typing import Dict, Any
import uvicorn
from calendar_airtable_server import CalendarAirtableServer

app = FastAPI(title="Calendar & Airtable MCP Server")

# Initialize the service
calendar_service = CalendarAirtableServer()

@app.get("/")
async def root():
    return {"message": "Calendar & Airtable MCP Server is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/calendar/events")
async def create_calendar_event(event_data: Dict[str, Any]):
    """Create a new calendar event"""
    try:
        result = await calendar_service.create_google_event(event_data)
        if result:
            return {"success": True, "event": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to create event")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/events")
async def get_calendar_events(start_time: str = None, end_time: str = None):
    """Get calendar events"""
    try:
        events = await calendar_service.get_google_events(start_time, end_time)
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/check-availability")
async def check_availability(data: Dict[str, Any]):
    """Check calendar availability"""
    try:
        from datetime import datetime, timedelta
        
        date = data.get("date")
        start_time = data.get("start_time") 
        duration = data.get("duration_minutes", 60)
        
        # Convert to datetime objects
        start_datetime = datetime.fromisoformat(f"{date}T{start_time}:00")
        end_datetime = start_datetime + timedelta(minutes=duration)
        
        # Check calendar for conflicts
        events = await calendar_service.get_google_events(
            start_datetime.isoformat() + 'Z',
            end_datetime.isoformat() + 'Z'
        )
        
        is_available = len(events) == 0
        conflicts = [event.get('summary', 'Untitled') for event in events] if events else []
        
        return {
            "available": is_available,
            "conflicts": conflicts,
            "requested_slot": {
                "date": date,
                "start_time": start_time,
                "duration_minutes": duration
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/airtable/{table_name}")
async def get_airtable_records(table_name: str, filter_formula: str = None):
    """Get records from Airtable"""
    try:
        records = await calendar_service.get_airtable_records(table_name, filter_formula)
        return {"records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/airtable/{table_name}")
async def create_airtable_record(table_name: str, fields: Dict[str, Any]):
    """Create a new Airtable record"""
    try:
        result = await calendar_service.create_airtable_record(table_name, fields)
        if result:
            return {"success": True, "record": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to create record")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks")
async def create_task(task_data: Dict[str, Any]):
    """Create a new task in Airtable"""
    try:
        fields = {
            "Name": task_data.get("name"),
            "Status": task_data.get("status", "To Do"),
            "Priority": task_data.get("priority", "Medium"),
            "Due Date": task_data.get("due_date"),
            "Notes": task_data.get("notes", "")
        }
        
        # Remove None values
        fields = {k: v for k, v in fields.items() if v is not None}
        
        result = await calendar_service.create_airtable_record("Tasks", fields)
        if result:
            return {"success": True, "task": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to create task")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/contacts/search")
async def search_contacts(search_data: Dict[str, Any]):
    """Search for contacts in Airtable"""
    try:
        search_term = search_data.get("search_term", "").lower()
        records = await calendar_service.get_airtable_records("Contacts")
        
        matching_contacts = []
        for record in records:
            fields = record.get("fields", {})
            name = fields.get("Name", "").lower()
            email = fields.get("Email", "").lower()
            
            if search_term in name or search_term in email:
                matching_contacts.append({
                    "id": record.get("id"),
                    "name": fields.get("Name"),
                    "email": fields.get("Email"),
                    "phone": fields.get("Phone")
                })
        
        return {"contacts": matching_contacts, "count": len(matching_contacts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reminders")
async def create_reminder(reminder_data: Dict[str, Any]):
    """Create a reminder (calendar event + Airtable task)"""
    try:
        from datetime import datetime, timedelta
        
        title = reminder_data.get("title")
        reminder_datetime = reminder_data.get("datetime")
        notes = reminder_data.get("notes", "")
        
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
        
        return {
            "success": True,
            "calendar_created": calendar_result is not None,
            "airtable_created": airtable_result is not None,
            "calendar_event": calendar_result,
            "airtable_task": airtable_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)