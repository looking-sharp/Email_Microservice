FROM python:3.9-slim-buster
WORKDIR /service1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]