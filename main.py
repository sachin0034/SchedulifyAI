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
import streamlit.components.v1 as components
from twilio.rest import Client

logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Your Vapi API Authorization token and OpenAI API key
auth_token = os.getenv('AUTH_TOKEN')
phone_number_id = os.getenv('PHONE_NUMBER_ID')
openApi = os.getenv('OPENAI_API_KEY')

# Your Twilio account SID and Auth Token
twilio_account_sid = os.getenv('twilio_account_sid')
twilio_auth_token = os.getenv('twilio_auth_token')

# Google Calendar API setup
SCOPES = [os.getenv('GOOGLE_SCOPES')]

client = OpenAI(api_key=openApi)
twilio_client = Client(twilio_account_sid, twilio_auth_token)

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

def create_event(name, date, time, email):
    service = get_calendar_service()
    start_datetime = f'{date[:4]}-{date[4:6]}-{date[6:8]}T{time}:00'
    end_datetime = f'{date[:4]}-{date[4:6]}-{date[6:8]}T{int(time[:2]) + 1}:{time[3:]}:00'
    
    event = {
        'summary': f'Interview with {name}',
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'Asia/Kolkata',
        },
        'attendees': [
            {'email': email},
        ],
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return event.get('htmlLink')
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None

# Function to make a call
def make_call(phone_number, user_prompt):
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    data = {
        'assistant': {
            "firstMessage": "hello",
            "model": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": user_prompt
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
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Extract the name, date (in YYYY/MM/DD format), time (in 24-hour format), and email from the following transcript of an interview scheduling call. Provide the information in this exact format: Name: [Name], Date: [YYYYMMDD], Time: [HH:MM], Email: [email@example.com]"},
            {"role": "user", "content": transcript}
        ]
    )
    return response.choices[0].message.content

def fetch_twilio_call_logs():
    try:
        calls = twilio_client.calls.list(limit=20)  # Fetch the last 20 calls
        call_logs = []
        for call in calls:
            call_log = {
                "SID": call.sid,
                "From": call.from_,
                "To": call.to,
                "Status": call.status,
                "Start Time": call.start_time,
                "End Time": call.end_time,
                "Duration": call.duration
            }
            call_logs.append(call_log)
        return call_logs
    except Exception as e:
        logging.error(f"Failed to fetch Twilio call logs: {e}")
        return []

# Streamlit App
st.title('Call Dashboard')

# Sidebar
st.sidebar.title('Navigation')
options = ['Single Call', 'Show Meeting', 'Transcript', 'Google Calendar', 'Twilio Call Logs']
choice = st.sidebar.selectbox('Select a section', options)

# Single Call Section
if choice == 'Single Call':
    st.header('Single Call')
    phone_number = st.text_input('Enter phone number (with country code)')
    user_prompt = st.text_area('Enter the prompt for the call')
    if st.button('Make Call'):
        message, response = make_call(phone_number, user_prompt)
        st.write(message)
        st.json(response)
        if 'id' in response:
            st.session_state['last_call_id'] = response['id']

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
                email = info_parts[3].split(': ')[1]
                
                st.write(f"Parsed Name: {name}")
                st.write(f"Parsed Date (YYYYMMDD): {date}")
                st.write(f"Parsed Time (24-hour): {time}")
                st.write(f"Email : {email}")
                
                # Schedule the meeting in Google Calendar
                event_link = create_event(name, date, time, email)
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

# Google Calendar Section
elif choice == 'Google Calendar':
    st.header('Google Calendar')
    calendar_url = 'https://calendar.google.com/calendar/embed?src=sachinparmar0246%40gmail.com&ctz=Asia%2FKolkata'
    components.iframe(calendar_url, width=800, height=600)

# Twilio Call Logs Section
elif choice == 'Twilio Call Logs':
    st.header('Twilio Call Logs')
    call_logs = fetch_twilio_call_logs()

    if call_logs:
        for log in call_logs:
            st.write(f"Call SID: {log['SID']}")
            st.write(f"From: {log['From']}")
            st.write(f"To: {log['To']}")
            st.write(f"Status: {log['Status']}")
            st.write(f"Start Time: {log['Start Time']}")
            st.write(f"End Time: {log['End Time']}")
            st.write(f"Duration: {log['Duration']}")
            st.write("---")
    else:
        st.write("No call logs found or failed to fetch call logs.")
