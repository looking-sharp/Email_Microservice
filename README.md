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
---
