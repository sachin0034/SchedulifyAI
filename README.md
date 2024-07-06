# SchedulifyAI

This project is a Streamlit-based application that allows users to manage and schedule calls using various APIs. The application includes features for making single calls, viewing call logs, showing meeting details, and fetching call transcripts. Additionally, it integrates with the Google Calendar API to schedule events.

## Features

- **Single Call**: Make a call to a specified phone number with a custom prompt.
- **Call Logs**: View logs of previous calls.
- **Show Meeting**: Extract and display meeting details from call transcripts.
- **Transcript**: Fetch and display call transcripts.

## Technologies Used

- **Streamlit**: For building the web interface.
- **OpenAI API**: For generating responses from the GPT-4 model.
- **Google Calendar API**: For scheduling events.
- **Vapi API**: For making and managing calls.
- **dotenv**: For managing environment variables.

## Prerequisites

- Python 3.7 or higher
- Pip (Python package installer)

## Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/call-dashboard.git
    cd call-dashboard
    ```

2. **Create a virtual environment**:

    ```bash
    python -m venv venv
    ```

3. **Activate the virtual environment**:

    - On Windows:

      ```bash
      venv\Scripts\activate
      ```

    - On macOS/Linux:

      ```bash
      source venv/bin/activate
      ```

4. **Install the required packages**:

    ```bash
    pip install -r requirements.txt
    ```

5. **Create a `.env` file** in the project directory with the following content:

    ```plaintext
    AUTH_TOKEN=your_vapi_auth_token
    PHONE_NUMBER_ID=your_phone_number_id
    OPENAI_API_KEY=your_openai_api_key
    GOOGLE_SCOPES=https://www.googleapis.com/auth/calendar
    ```

6. **Add your `credentials.json` file** for Google Calendar API in the project directory.

## Usage

1. **Run the Streamlit application**:

    ```bash
    streamlit run app.py
    ```

2. **Access the application**:

    Open your web browser and go to `http://localhost:8501`.

3. **Navigate through the application**:

    - Use the sidebar to select different sections (Single Call, Call Logs, Show Meeting, Transcript).
    - In the Single Call section, enter a phone number and a prompt, then click "Make Call" to initiate a call.
    - View call logs in the Call Logs section.
    - In the Show Meeting section, extract and display meeting details from the latest call transcript.
    - Fetch and view call transcripts in the Transcript section.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Contact

If you have any questions or need further assistance, feel free to contact:

- **Email**: sachinparmar98134@gmail.com
- **GitHub**: [your-username](https://github.com/sachin0034)

