FROM python:3.11
WORKDIR /dist
COPY . .
USER root
RUN pip install -r requirements.txt

CMD ["python3","tasker.py"]
