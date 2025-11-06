from signalwire.rest import Client as signalwire_client
import asyncio
from dotenv import load_dotenv

import os
load_dotenv()
SIGNALWIRE_PROJECT_ID = "bbed47d0-57a7-47b3-9940-d7177ffe7491"
SIGNALWIRE_AUTH_TOKEN = "PT68fd27e6a4fece48d75eba37cb24ed77c7a76dc5feb4059c"
SIGNALWIRE_SPACE_URL = "the-equity-agency-holdings.signalwire.com"
SIGNALWIRE_PHONE_NUMBER = "+15025217221"  # Replace with your SignalWire number



sw_client = signalwire_client(SIGNALWIRE_PROJECT_ID, SIGNALWIRE_AUTH_TOKEN, signalwire_space_url=SIGNALWIRE_SPACE_URL)

def sendsms(to, body):
    message = sw_client.messages.create(
        body=body,
        to=to,
        from_=SIGNALWIRE_PHONE_NUMBER
    )
    return message.sid



def firstagent(name, address, phonenumber):
    firstname = name
    propertyaddress = address
    body = f"Hi {firstname}, would you be open to discussing a cash offer for your property at {propertyaddress}?"
    to = phonenumber

    try:
        sendsms(to,body)
    except:
        print("failed")

    return firstname

