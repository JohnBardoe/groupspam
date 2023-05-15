FROM python:3.9-alpine
WORKDIR /usr/src/app

COPY . .
RUN python -m pip install --upgrade pip && python -m pip install --no-cache-dir -r requirements.txt
EXPOSE 8000

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
