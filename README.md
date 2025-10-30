# email_microservice
An email microservice software to be used to contact users for various uses.

## Database Structure
![Email Microservice RS](images/Email%20Microservice%20RS.png)

## GET requests
All the GET requests our microservice allows

## POST requests
All the POST requests our microservice allows

## Send Email
This request is used to send an email using the email microservice
### Endpoint
```http
POST /send-email
```
### Description
This endpoint accepts a JSON payload containing the email details and sends te message to the spesified recipiants

### Request
**Content-type:** application/json \
**Schema:**
```json
{
  "subject": "string",
  "body": "string",
  "recipients": ["string"],
  "is_html": "boolean"
}
```
|Field|Required|Notes|
|-----|--------|-----|
|subject|yes|subject of the email|
|body|yes|body of email (plain text or html)|
|recipients|yes|array of emails of recipiants|
|is_html|no|defaults to false if not provided|
