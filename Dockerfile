FROM python:3

COPY requirements.txt /
RUN pip install -r requirements.txt

COPY shyr/ /shyr/
COPY server.py index.html /

CMD [ "python", "-u", "./server.py" ]
