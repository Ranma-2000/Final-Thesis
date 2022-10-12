FROM python:3.10.6

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

ADD read_com.py .

ADD xgb_ecg.model .

CMD [ "python3", "-u", "read_com.py"]

