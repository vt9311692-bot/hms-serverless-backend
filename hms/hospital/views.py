from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import login
from .models import AvailabilitySlot, Booking, User
import requests
import json
import os
import datetime

# --- SERVERLESS EMAIL INTEGRATION ---
SERVERLESS_URL = "http://localhost:3000/dev/email"

def trigger_email(trigger_type, email, name):
    try:
        payload = {
            "trigger": trigger_type,
            "email": email,
            "name": name
        }
        requests.post(SERVERLESS_URL, json=payload, timeout=2)
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not connect to local Serverless Email Service: {e}")

# --- GOOGLE CALENDAR INTEGRATION ---
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def create_google_calendar_event(doctor, patient, slot):
    """
    Creates calendar events for both users.
    Assumes OAuth tokens are available or handles the absence gracefully for local demo.
    """
    try:
        # In a production app, we would fetch the user's OAuth tokens from the database.
        # For this local demo structure, we assume token.json exists locally from an OAuth flow.
        if not os.path.exists('token.json'):
            print(f"Warning: token.json not found. Skipping Google Calendar API call for {patient.username} and {doctor.username}.")
            return

        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar.events'])
        service = build('calendar', 'v3', credentials=creds)

        start_time = slot.start_time.isoformat()
        end_time = slot.end_time.isoformat()

        # Event for Patient
        patient_event = {
            'summary': f'Appointment with Dr. {doctor.username}',
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time},
        }
        service.events().insert(calendarId='primary', body=patient_event).execute()
        print("Google Calendar event created for patient.")

        # Event for Doctor
        doctor_event = {
            'summary': f'Appointment with {patient.username}',
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time},
        }
        service.events().insert(calendarId='primary', body=doctor_event).execute()
        print("Google Calendar event created for doctor.")

    except Exception as e:
        print(f"Google Calendar Integration Error: {e}")


# --- VIEWS ---

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def signup(request):
    """View to register a new Doctor or Patient and trigger SIGNUP_WELCOME email."""
    if request.method == 'POST':
        # Support JSON payload or Form data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST
            
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role')

        if not username or not password or not role or not email:
            return JsonResponse({'error': 'Missing required fields (username, password, email, role).'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists.'}, status=400)

        user = User.objects.create_user(username=username, email=email, password=password, role=role)
        
        # Trigger Serverless Email Function
        trigger_email('SIGNUP_WELCOME', email, username)
        
        login(request, user)
        return JsonResponse({'message': f'{role.capitalize()} signed up successfully!'})
    
    return HttpResponseBadRequest("Invalid request method.")

@csrf_exempt
@login_required
def create_slot(request):
    """View for Doctors to create availability slots."""
    if not request.user.is_doctor():
        return HttpResponseForbidden("Error: Only doctors can create availability slots.")
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST
            
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        slot = AvailabilitySlot.objects.create(
            doctor=request.user,
            start_time=start_time,
            end_time=end_time
        )
        return JsonResponse({'message': 'Slot created successfully', 'slot_id': slot.id})
    
    return HttpResponseBadRequest("Invalid request method.")

@login_required
def list_available_slots(request):
    """View for Patients to see only future, unbooked slots."""
    if not request.user.is_patient():
        return HttpResponseForbidden("Error: Only patients can view available slots.")
    
    now = timezone.now()
    slots = AvailabilitySlot.objects.filter(
        is_booked=False, 
        start_time__gt=now
    ).values('id', 'doctor__username', 'start_time', 'end_time')
    
    return JsonResponse({'available_slots': list(slots)})

@csrf_exempt
@login_required
def book_slot(request, slot_id):
    """View for Patients to book a slot. Contains Race Condition Protection."""
    if not request.user.is_patient():
        return HttpResponseForbidden("Error: Only patients can book slots.")
    
    if request.method == 'POST':
        with transaction.atomic():
            try:
                # DESIGN DECISION: PESSIMISTIC LOCKING
                # We use select_for_update() to lock the specific row until this transaction completes.
                slot = AvailabilitySlot.objects.select_for_update().get(id=slot_id)
                
                if slot.is_booked:
                    return JsonResponse(
                        {'error': 'Sorry, this slot was just booked by someone else.'}, 
                        status=400
                    )
                
                Booking.objects.create(patient=request.user, slot=slot)
                slot.is_booked = True
                slot.save()
                
                # TRIGGER BOOKING CONFIRMATION EMAIL
                trigger_email('BOOKING_CONFIRMATION', request.user.email, request.user.username)
                
                # TRIGGER GOOGLE CALENDAR CREATION
                create_google_calendar_event(slot.doctor, request.user, slot)
                
                return JsonResponse({'message': 'Slot booked successfully!', 'booking_id': slot.booking.id})
                
            except AvailabilitySlot.DoesNotExist:
                return JsonResponse({'error': 'Slot not found.'}, status=404)
                
    return HttpResponseBadRequest("Invalid request method.")
