import streamlit as st
import requests
from openai import OpenAI
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os
import logging
import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Your Vapi API Authorization token and OpenAI API key
auth_token = os.getenv('AUTH_TOKEN')
phone_number_id = os.getenv('PHONE_NUMBER_ID')
openApi = os.getenv('OPENAI_API_KEY')

# Google Calendar API setup
SCOPES = [os.getenv('GOOGLE_SCOPES')]


client = OpenAI(api_key=openApi)

def get_calendar_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logging.info("Starting new OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)  # Use port=0 to automatically select an available port
            logging.info("Server completed, saving credentials")
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


def create_event(name, date, time):
    service = get_calendar_service()
    start_datetime = f'{date[:4]}-{date[4:6]}-{date[6:8]}T{time}:00'
    end_datetime = f'{date[:4]}-{date[4:6]}-{date[6:8]}T{int(time[:2]) + 1}:{time[3:]}:00'
    
    event = {
        'summary': f'Interview with {name}',
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'America/New_York',
        },
        'attendees': [
            {'email': 'sachinparmar0246@gmail.com'},
        ],
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return event.get('htmlLink')
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None

# Function to make a call
def make_call(phone_number, prompt):
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    data = {
        'assistant': {
            "firstMessage": prompt,
            "model": {
                "provider": "openai",
                "model": "gpt-4-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an AI interviewer assistant. Your task is to schedule an interview for TechAvtar. Ask a few questions to the user like their name, and when they will be available for the interview, including date and time."
                    }
                ]
            },
            "voice": "jennifer-playht"
        },
        'phoneNumberId': phone_number_id,
        'customer': {
            'number': phone_number,
        },
    }

    response = requests.post('https://api.vapi.ai/call/phone', headers=headers, json=data)

    if response.status_code == 201:
        return 'Call created successfully', response.json()
    else:
        return 'Failed to create call', response.text

def fetch_call_logs():
    url = "https://api.vapi.ai/calls"
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def fetch_transcript(call_id):
    url = f"https://api.vapi.ai/call/{call_id}"
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        call_data = response.json()
        transcript = call_data.get('transcript', 'No transcript available')
        return transcript
    else:
        return "Failed to retrieve transcript."

def extract_info_from_transcript(transcript):
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "Extract the name, date (in YYYY/MM/DD format), and time (in 24-hour format) from the following transcript of an interview scheduling call. Provide the information in this exact format: Name: [Name], Date: [YYYYMMDD], Time: [HH:MM]"},
            {"role": "user", "content": transcript}
        ]
    )
    return response.choices[0].message.content

# Streamlit App
st.title('Call Dashboard')

# Sidebar
st.sidebar.title('Navigation')
options = ['Single Call', 'Call Logs', 'Show Meeting', 'Transcript']
choice = st.sidebar.selectbox('Select a section', options)

# Single Call Section
if choice == 'Single Call':
    st.header('Single Call')
    phone_number = st.text_input('Enter phone number (with country code)')
    prompt = st.text_area('Enter the prompt for the call')
    if st.button('Make Call'):
        message, response = make_call(phone_number, prompt)
        st.write(message)
        st.json(response)
        if 'id' in response:
            st.session_state['last_call_id'] = response['id']

# Call Logs Section
elif choice == 'Call Logs':
    st.header('Call Logs')
    call_logs = fetch_call_logs()

    if call_logs:
        for log in call_logs:
            st.write(f"Call ID: {log['id']}")
            st.write(f"Phone Number: {log['phoneNumber']}")
            st.write(f"Status: {log['status']}")
            st.write(f"Start Time: {log['startedAt']}")
            st.write(f"End Time: {log['endedAt']}")
            st.write("---")
    else:
        st.write("No call logs found or failed to fetch call logs.")

elif choice == 'Show Meeting':
    st.header('Show Meeting')
    if 'last_call_id' in st.session_state:
        call_id = st.session_state['last_call_id']
        transcript = fetch_transcript(call_id)
        if transcript != "Failed to retrieve transcript.":
            extracted_info = extract_info_from_transcript(transcript)
            st.write(extracted_info)
            
            # Parsing the extracted info
            try:
                info_parts = extracted_info.split(', ')
                name = info_parts[0].split(': ')[1]
                date = info_parts[1].split(': ')[1]
                time = info_parts[2].split(': ')[1]
                
                st.write(f"Parsed Name: {name}")
                st.write(f"Parsed Date (YYYYMMDD): {date}")
                st.write(f"Parsed Time (24-hour): {time}")
                
                # Schedule the meeting in Google Calendar
                event_link = create_event(name, date, time)
                if event_link:
                    st.write(f"Meeting scheduled! View it here: {event_link}")
                else:
                    st.write("Failed to schedule the meeting.")
            except IndexError:
                st.write("Error: Unable to parse the extracted information. The format may be incorrect.")

# Transcript Section
elif choice == 'Transcript':
    st.header('Transcript')
    call_id = st.text_input('Enter the Call ID to fetch the transcript')
    if st.button('Fetch Transcript'):
        transcript = fetch_transcript(call_id)
        st.write(transcript)
