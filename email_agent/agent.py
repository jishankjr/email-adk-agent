# os → file handling
# base64 → encoding
# EmailMessage → create email
# load_dotenv → load API keys
# Agent → AI agent
# LiteLlm → connect to Groq
# Credentials → saved login
# InstalledAppFlow → Google sign-in
# build → Gmail API connection

import os
import base64
from email.message import EmailMessage

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail permission
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Load variables from .env
load_dotenv()

# File names
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def _get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    return service

def send_email(to: str, subject: str, body: str) -> dict:
    try:
        service = _get_gmail_service()

        message = EmailMessage()
        message.set_content(body)
        message["To"] = to
        message["Subject"] = subject

        encoded = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        sent = (
            service.users()
            .messages()
            .send(
                userId="me",
                body={"raw": encoded}
            )
            .execute()
        )

        return {
            "status": "success",
            "message_id": sent.get("id"),
            "detail": f"Email sent to {to}"
        }

    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }

root_agent = Agent(
    name="email_agent",
    model=LiteLlm(
        model="groq/llama-3.3-70b-versatile"
    ),
    description="An AI agent that sends emails using Gmail.",
    instruction=(
        "You are an AI email assistant. "
        "When a user wants to send an email, collect the recipient, "
        "subject and body. If anything is missing, ask for it. "
        "Before sending, always show the draft and ask for confirmation. "
        "Only after the user confirms, call the send_email tool."
    ),
    tools=[send_email],
)