import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8000'

# Create sessions so that login cookies are remembered automatically!
doc_session = requests.Session()
pat_session = requests.Session()

def print_step(step_num, title):
    print(f"\n=====================================")
    print(f"STEP {step_num}: {title}")
    print(f"=====================================")
    time.sleep(1)

def run_demo():
    print("🚀 Starting Hospital Management System Automated Demo!")
    
    # Use a unique timestamp so you can run the demo multiple times without "Username already exists" errors!
    unique_id = int(time.time())
    doc_username = f'DrSmith_{unique_id}'
    pat_username = f'JohnDoe_{unique_id}'
    
    # STEP 1: Sign up a Doctor
    print_step(1, "Doctor Signup (Triggers Serverless Welcome Email)")
    doc_payload = {
        'username': doc_username,
        'password': 'password123',
        'email': f'drsmith{unique_id}@hospital.com',
        'role': 'doctor'
    }
    r = doc_session.post(f"{BASE_URL}/signup/", json=doc_payload)
    print(f"Response ({r.status_code}): {r.text}")
    print("-> Check your Serverless terminal to see the email!")
    time.sleep(3)

    # STEP 2: Sign up a Patient
    print_step(2, "Patient Signup (Triggers Serverless Welcome Email)")
    pat_payload = {
        'username': pat_username,
        'password': 'password123',
        'email': f'johndoe{unique_id}@gmail.com',
        'role': 'patient'
    }
    r = pat_session.post(f"{BASE_URL}/signup/", json=pat_payload)
    print(f"Response ({r.status_code}): {r.text}")
    print("-> Check your Serverless terminal to see the email!")
    time.sleep(3)

    # STEP 3: Doctor Creates an Availability Slot
    print_step(3, "Doctor Creates a Slot")
    slot_payload = {
        'start_time': '2026-06-01T10:00:00Z',
        'end_time': '2026-06-01T11:00:00Z'
    }
    r = doc_session.post(f"{BASE_URL}/slots/create/", json=slot_payload)
    print(f"Response ({r.status_code}): {r.text}")
    try:
        slot_id = r.json().get('slot_id')
        print(f"-> Slot #{slot_id} created successfully!")
    except:
        print("Failed to get slot ID. Make sure the server is running.")
        return
    time.sleep(3)

    # STEP 4: Patient views available slots
    print_step(4, "Patient Views Available Slots")
    r = pat_session.get(f"{BASE_URL}/slots/available/")
    print(f"Response ({r.status_code}): {json.dumps(r.json(), indent=2)}")
    time.sleep(3)

    # STEP 5: Patient Books the Slot
    print_step(5, "Patient Books the Slot (Triggers Booking Email & Google Calendar)")
    print(f"Attempting to book Slot #{slot_id}...")
    r = pat_session.post(f"{BASE_URL}/slots/{slot_id}/book/")
    print(f"Response ({r.status_code}): {r.text}")
    print("-> Check your Serverless terminal to see the booking confirmation email!")
    print("-> Check your Google Calendar to see the event!")
    
    print("\n✅ DEMO COMPLETE!")

if __name__ == '__main__':
    run_demo()
