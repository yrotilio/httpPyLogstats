FROM python:3
RUN touch /var/log/access.log
WORKDIR /usr/src
ADD . /usr/src
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt
ENTRYPOINT ["python", "-u", "httpPyLogstats.py"]