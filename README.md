# Email Microservice <!-- omit in toc -->
An email microservice software to be used to contact users for various uses

- [Features](#features)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Run](#run)
- [Backend Information](#backend-information)
  - [Database Structure](#database-structure)
- [GET requests](#get-requests)
  - [`GET /ping`](#get-ping)
  - [`GET /check-scheduled-email/<schedule_id>`](#get-check-scheduled-emailschedule_id)
- [POST requests](#post-requests)
  - [`POST /send-email`](#post-send-email)
  - [`POST /send-timed-email`](#post-send-timed-email)


## Features

-  **Immediate Email Sending** - Send emails instantly via SMTP
-  **Scheduled Emails** - Queue emails for future delivery
-  **HTML Support** - Rich HTML email templates
-  **Email Logging** - Track all sent emails in SQLite
-  **Background Scheduler** - Automatic processing of scheduled emails
-  **CORS Enabled** - Ready for frontend integration

---

## Quick Start

### Prerequisites

- Python 3.9+
- Gmail account with App Password
- Docker Desktop Installed

### Installation
```bash
# Clone repository into your main project
git clone https://github.com/yourusername/email-microservice.git

# Make data directory for database storage
mkdir data

# create .env file
cd Email-Microservice
touch .env
```
Outside the created repository in your main project folder:
```bash
# Created a docker compose file
touch docker-compose.yml
```
And add the following into your compose file:
```yml
services:
  email-microservice:
    build: ./Email_Microservice
    image: email-microservice
    ports:
      - "5002:5002"
    environment:
      FLASK_APP: app.py
      FLASK_ENV: development
      DATABASE_URL: sqlite:////app_parent/data/email.db
    volumes:
      - ./Email_Microservice/..:/app_parent
```

If your set up is correct, your file tree will look something like this:
```bash
YOUR_PROJECT
├── data
├── Email_Microservice
│   ├── .env
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├──  ...
│   ├── static
│   │   ├── scripts
│   │   │   ├── admin.js
│   │   │   └──  ...
│   │   └── styles
│   │       ├── index.css
│   │       └──  ...
│   └── template
│       ├── index.html
│       └──  ...
└── docker-compose.yml
```

> [!IMPORTANT]
> You must have a data directory in the directory of YOUR_PROJECT

In the `.env` file:
```properties
EMAIL="your-email@gmail.com"
SMTP_PASS="your-app-password"
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"
PORT=5002
CORS_ORIGINS="http://localhost:5000"
ADMIN_CODE="123"
```

> **Note:** Get Gmail App Password from [Google Account Settings](https://support.google.com/accounts/answer/185833)

### Run
If you haven't built it yet, in your main project directory (the one with `docker-compose.yml` in it) run:
```bash
docker-compose up --build email-microservice
```
Or if you have built it,
``` bash
docker-compose up --no-build email-microservice
```

## Backend Information

### Database Structure
![Email Microservice RS](images/Email%20Microservice%20RS.png)
Data is stored using sqlite and is interacted with through SQLAlchemy \
See models.py for more information

## GET requests
All the GET requests our microservice allows

### `GET /ping`
This pings the microservice to ensure it is running and ready to recieve requests

**Response (200):**
```json
{
  "status": "ok",
  "service": "email-microservice"
}
```

**Example Code (Python)**
``` python
import requests

def checkIsOnline() -> bool:
  response = requests.get("http://127.0.0.1:5002/ping")
  return response.status_code == 200

```
---


### `GET /check-scheduled-email/<schedule_id>`
This checks on the status of a scheduled email based on that email's schedule ID

**Response (200)**
```json
{
  "status": "success",
  "statusCode": 200,
  "email_status": "string",
  "scheduled_time": "string",
  "sent_at": "string"
}
```
The sent_at field will be null if the email hasn't been sent yet

**Example Code (Python)**
```Python
import requests

def checkScheduledEmailStatus(scheduleID: str):
  response = requests.get(f"http://127.0.0.1:5002/check-scheduled-email/{scheduleID}")
  return response

```
---

## POST requests
All the POST requests our microservice allows

---

### `POST /send-email`
This request is used to send an email using the email microservice

**Request**
```json
{
  "subject": "string",
  "body": "string",
  "recipients": ["string"],
  "isHTML": "boolean"
}
```
|Field|Required|Notes|
|-----|--------|-----|
|subject|yes|subject of the email|
|body|yes|body of email (plain text or html)|
|recipients|yes|array of emails of recipiants|
|isHTML|no|defaults to false if not provided|

**Response (200):**
```json
{
  "status": "success",
  "message": "Email sent successfully",
  "details":
  {
    "recipiants": ["string"],
    "subject_line": "string" 
  },
  "statusCode": 200
}
```

**Example Code (Python)**
```python
import requests

def sendEmail():
  package = {
    "recipients": ["your-email@email.com"],
    "subject_line": "This is a test email",
    "body": "<p>This is to test the microservice.<\p>",
    "is_html": True
  }
  response = requests.post("http://127.0.0.1:5002/send-email", json=package)    
  print(response)
```
---


### `POST /send-timed-email`
This request is used to submit an email using the email microservice to be sent at a later time/date

**Request**
```json
{
  "subject": "string",
  "body": "string",
  "recipients": ["string"],
  "isHTML": "boolean",
  "timeToSend": "string",
  "dateToSend": "string"
}
```
|Field|Required|Notes|
|-----|--------|-----|
|subject|yes|subject of the email|
|body|yes|body of email (plain text or html)|
|recipients|yes|array of emails of recipiants|
|isHTML|no|defaults to false if not provided|
|timeToSend|yes|needs to be in a correct time format|
|dateToSend|yes|needs to be in a correct date format|

**Response (201)**
``` JSON
{
  "status": "string",
  "message": "string",
  "statusCode": "int",
  "details":
    {
      "schedule_id": "string",
      "recipients": ["string"],
      "subject_line": "string",
      "time_to_send": "string",
      "date_to_send": "string"
    }
}
```

**Example Code (Python)**
```python
import requests
from datetime import datetime, timedelta

def sendTimedEmail():
  current_datetime = datetime.now(timezone.utc)
  # Send 5 mins in the future
  future_datetime = current_datetime + timedelta(minutes=5)
  package = {
    "recipients": ["your-email@email.com"],
    "subject_line": "This is a timed test email",
    "body": f"<p>This email is sent 5 minutes after {current_datetime.time()}.<\p>",
    "is_html": True,
    "time_to_send": str(current_datetime.date()),
    "date_to_send": str(future_datetime.time())
  }
  response = requests.post("http://127.0.0.1:5002/send-timed-email", json=package)    
  print(response)
```
---
