import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def send_email(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        trigger = body.get('trigger')
        email = body.get('email')
        name = body.get('name', 'User')

        if not trigger or not email:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing trigger or email"})
            }

        # Mocking email sending for local demo
        print(f"\n{'='*50}")
        print(f"📧 SERVERLESS EMAIL TRIGGERED")
        print(f"Trigger Type: {trigger}")
        print(f"Recipient: {email}")
        
        if trigger == 'SIGNUP_WELCOME':
            print(f"Subject: Welcome to HMS, {name}!")
            print("Body: We are glad to have you on board.")
        elif trigger == 'BOOKING_CONFIRMATION':
            print(f"Subject: Booking Confirmed!")
            print(f"Body: Your appointment has been successfully booked.")
        else:
            print(f"Unknown trigger: {trigger}")

        print(f"{'='*50}\n")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Email successfully dispatched to {email} for trigger {trigger}."
            })
        }
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
