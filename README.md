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
This endpoint accepts a JSON payload containing the email details and sends the message to the spesified recipiants

### Request
**Content-type:** application/json \
**Schema:**
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

## Submit Timed Email
This request is used to submit an email using the email microservice to be sent at a later time/date
### Endpoint
```http
POST /submit-email
```
### Description
This endpoint accepts a JSON payload containing the email details and submits it to be sent later

### Request
**Content-type:** application/json \
**Schema:**
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
