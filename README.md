# Mini Hospital Management System (HMS)

This is a local Django-based Hospital Management System with a decoupled Serverless Email Service and Google Calendar integration.

## Setup and Run

### Prerequisites
- Python 3.9+
- Node.js and npm (for the Serverless Framework)
- **PostgreSQL Database Engine** (installed locally and running)

### 1. Database Setup (PostgreSQL)
1. Open pgAdmin (installed with PostgreSQL).
2. Create a new database named `hms_db`.
3. The Django app expects default local credentials: `User: postgres`, `Password: password`, `Port: 5432`. (Modify `settings.py` if yours are different).

### 2. Setup the Serverless Email Service
Open a terminal and navigate to the `email-service` directory:
```bash
cd email-service
npm install -g serverless
npm install serverless-offline
```
Before starting the server, to enable **REAL** SMTP sending, open `handler.py` and replace `your_email@gmail.com` and `your_app_password` with real Gmail credentials (or pass them via environment variables). 
Then start the service:
```bash
serverless offline start
```
*The email service will now be listening locally on port 3000.*

### 3. Setup the Django App
Open a **new** terminal and navigate to the project root:
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
cd hms
python manage.py migrate
python manage.py runserver
```

### 4. Google Calendar OAuth (Required for Demo)
To fully test the Google Calendar integration:
1. Go to Google Cloud Console.
2. Enable Google Calendar API and Create OAuth 2.0 Client IDs (Desktop App).
3. Download the JSON file, rename it to `credentials.json`, and place it in the `hms/` folder.
4. Run `python generate_google_token.py` to pop open your browser and authenticate.
*This generates `token.json`, giving the booking view permission to create calendar events!*

---

## System Architecture

The architecture decouples the core booking engine from the notification system to ensure high performance during the critical path of a transaction.
- **Backend**: Django handles the core business logic, utilizing its built-in session-based authentication to enforce strict role-based access (Doctors vs. Patients).
- **Database**: PostgreSQL (locally simulated via SQLite for this specific demo setup) serves as the persistent store.
- **Serverless Integration**: When a user signs up or confirms a booking, the Django view fires a fast, asynchronous HTTP POST request to the local `serverless-offline` endpoint running our AWS Lambda handler simulation. This ensures the web request isn't blocked by slow SMTP servers.
- **Google Calendar**: Interacts via the `google-api-python-client`. We decoupled this logically so it runs only after the database lock has successfully been committed.

---

## The Design Decision

### Problem: The Booking Race Condition
The hardest architectural problem in a scheduling system is preventing double-booking when two patients attempt to book the exact same slot at the exact same millisecond. 

### Approaches Considered:
1. **Optimistic Locking (Versioning):** We could add a `version` integer to the `AvailabilitySlot` model. When a patient books, we check if the version matches what they saw. If another patient booked it first, the version increments, and the second patient's transaction fails upon save.
2. **Pessimistic Locking (Database Row-Level Lock):** We could use the database's native locking mechanism to literally lock the specific row the moment the transaction begins, forcing any simultaneous requests to queue and wait until the first transaction finishes.

### My Choice: Pessimistic Locking
I chose **Pessimistic Locking** using Django's `select_for_update()`. 
**Defense:** In a financial or healthcare booking system, absolute data integrity is the highest priority. Optimistic locking relies on application-level checks which can be prone to race conditions if the ORM bypasses the version check during complex queries. By executing `AvailabilitySlot.objects.select_for_update().get(id=slot_id)` inside a `transaction.atomic()` block, the lock is enforced at the absolute lowest level—the database engine itself. 
If Patient A starts booking, the database literally locks that row. When Patient B tries to read the row a millisecond later, their query is paused by the database until Patient A's transaction commits. Once it commits, Patient B reads the updated `is_booked = True` state and gets safely rejected. This guarantees zero double-bookings regardless of horizontal scaling or application logic flaws.

*(Note: While SQLite locks the entire database during a transaction, migrating to PostgreSQL immediately upgrades this to a true, highly concurrent row-level lock without changing any Django code).*

---

## Limitations

1. **Synchronous Calendar API Call:** Currently, the Google Calendar API call is made synchronously inside the view. In production, if the Google API is slow or down, the user's web request will hang. 
   - *Fix:* I would immediately move this API call into a Celery background task so the web request can return instantly.
2. **SQLite for Production:** The current demo uses SQLite. SQLite doesn't support true row-level locks, so our pessimistic lock essentially locks the whole database, which would cripple performance with multiple concurrent users.
   - *Fix:* Swap the database backend to PostgreSQL to unlock true row-level concurrency.
3. **No Centralized Token Management:** We are using a local `token.json` for a single user for the demo.
   - *Fix:* Build a full OAuth2 redirect flow and store access/refresh tokens in the database linked to individual `User` models so multiple real doctors and patients can connect their respective calendars.
