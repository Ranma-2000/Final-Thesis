FROM python:3.10.6

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

ADD gateway.py .

ADD xgb_ecg.model .

ADD connect_local_port.py .

ADD data_processing.py .

ADD main_client.py .

#CMD [ "python3", "-u", "gateway.py"]

