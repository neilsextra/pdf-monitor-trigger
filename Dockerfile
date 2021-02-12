FROM mcr.microsoft.com/azure-functions/python:2.0
ENV host:logger:consoleLoggingMode=always
COPY . /home/site/wwwroot

RUN cd /home/site/wwwroot && pip install --upgrade pip && pip install -r requirements.txt