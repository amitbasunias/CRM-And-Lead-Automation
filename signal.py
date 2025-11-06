from signalwire.relay.client import client

# SignalWire credentials (manually set)
SIGNALWIRE_PROJECT_ID = "bbed47d0-57a7-47b3-9940-d7177ffe7491"
SIGNALWIRE_AUTH_TOKEN = "PT68fd27e6a4fece48d75eba37cb24ed77c7a76dc5feb4059c"
SIGNALWIRE_SPACE_URL = "the-equity-agency-holdings.signalwire.com"
SIGNALWIRE_PHONE_NUMBER = "+15123871315"  # Replace with your actual number

# Initialize SignalWire client
client = Client(project=SIGNALWIRE_PROJECT_ID, token=SIGNALWIRE_AUTH_TOKEN)



print(client)


'''def sendsms(to, body):
    """Send an SMS using SignalWire"""
    message = sw_client.messages.create(
        body=body,
        to=to,
        from_=SIGNALWIRE_PHONE_NUMBER
    )
    return message.sid  # Return message ID

sms = sendsms(to="+8801318676267", body="I am testing")

print(sms)'''