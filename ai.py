from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
import os
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openaiclient = OpenAI(api_key=OPENAI_API_KEY)


def getsentiemnt(chat):

    output =  openaiclient.chat.completions.create(
        model="gpt-4o",

        messages=[
            {"role": "system", "content": "You are a helpful assistant. give me the intend of the following text. There will be like affirmative, netative and stop, return in only stop, affirmative,negative. always remember nutral messages are also positive intend"},
            {
                "role": "user",
                "content": chat
            }
        ]
    )

    reply = output.choices[0].message.content

    return reply




def conversation(conversation_history, name, phone, address):
    output = openaiclient.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Alex, a virtual assistant for Red Pin Equity, a property wholesale company. Your goal is to engage potential sellers via SMS and gather key information regarding their property. The tone and flow of the conversation should adapt naturally to each seller’s responses to ensure a personalized experience and avoid appearing like spam. Focus on discovering:\n"
                    "1. Motivation to Sell - Why are they selling? Adjust your phrasing based on the seller’s tone and previous responses.\n"
                    "2. Property Condition - What is the state of the property? Naturally ask about specific details such as the number of bedrooms, bathrooms, and whether the property has a basement or garage.\n"
                    "3. Price Expectations - What price are they looking for? If the seller seems hesitant, gently probe without being pushy.\n"
                    "4. Timeline to Sell - When would they like to sell? Phrase the question conversationally to match the seller's level of interest.\n\n"
                    "Additionally:\n"
                    "- Identify Multiple Properties: If the seller mentions or hints at owning other properties, explore this naturally within the conversation.\n"
                    "- Schedule a Call: When the conversation progresses positively, offer to schedule a time for the seller to speak with a house-buying specialist. Adapt your call scheduling offer to the seller's preferred timing or level of interest.\n\n"
                    "Always maintain a friendly, conversational, and professional tone. Tailor your responses based on the seller’s previous messages and cues to build trust and rapport. If the seller is not interested, politely end the conversation without being intrusive."
                    f"here are some info about the client, name: {name}, property address: {address}"
                    "after scheduling a call always reply: Thank you, see you in the meeting, you will recieve a calendly event link in a while"
                ),
            },
            *conversation_history
        ]
    )

    return output.choices[0].message.content


def calendly(chathistory):
    output = openaiclient.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "if there is time and date mentioned for scheduling a meeting through calendly in the previous chats by user then return that time in proper way that I can use it python... just like this: 2023-12-30 17:00:00. Otherwise return nomeeting",

            },
            *chathistory
        ]
    )
    reply = output.choices[0].message.content

    return reply


