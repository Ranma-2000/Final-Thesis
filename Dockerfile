FROM python:3.10.6

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

ADD main.py .

ADD xgb_ecg.model .

ADD realtime_processing.py .

CMD [ "python3", "-u", "main.py"]

