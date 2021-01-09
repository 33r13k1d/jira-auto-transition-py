from python:3.9

RUN mkdir /jira-auto-transition

WORKDIR /jira-auto-transition

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY ./app app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]