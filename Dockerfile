FROM python

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

RUN ["chmod", "755", "/app/Scripts/backend.sh"]

EXPOSE 8000