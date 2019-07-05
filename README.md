# httpPyLogstats

## Abstract
    
Consume an actively written-to w3c-formatted HTTP access log (https://www.w3.org/Daemon/User/Config/Logging.html). It should default to reading /tmp/access.log and be overrideable

Example log lines:

```
127.0.0.1 - james [09/May/2018:16:00:39 +0000] "GET /report HTTP/1.0" 200 123
127.0.0.1 - jill [09/May/2018:16:00:41 +0000] "GET /api/user HTTP/1.0" 200 234
127.0.0.1 - frank [09/May/2018:16:00:42 +0000] "POST /api/user HTTP/1.0" 200 34
127.0.0.1 - mary [09/May/2018:16:00:42 +0000] "POST /api/user HTTP/1.0" 503 12
```

* [X] Display stats every 10s about the traffic during those 10s: the sections of the web site with the most hits, as well as interesting summary statistics on the traffic as a whole. A section is defined as being what's before the second '/' in the resource section of the log line. For example, the section for "/pages/create" is "/pages"
* [X] Make sure a user can keep the app running and monitor the log file continuously
* [X] Whenever total traffic for the past 2 minutes exceeds a certain number on average, add a message saying that “High traffic generated an alert - hits = {value}, triggered at {time}”. The default threshold should be 10 requests per second, and should be overridable.
* [X] Whenever the total traffic drops again below that value on average for the past 2 minutes, add another message detailing when the alert recovered.
* [X] Make sure all messages showing when alerting thresholds are crossed remain visible on the page for historical reasons.
* [X] Write a test for the alerting logic.
* [X] Explain how you’d improve on this application design.
  * Faster log parsing
  * Create a alert class
  * Isolate log parsing and statistics (multi-proc)
* [ ] If you have access to a linux docker environment, we'd love to be able to docker build and run your project! If you don't though, don't sweat it. As an example for a solution based on python 3:

```
FROM python:3
RUN touch /var/log/access.log  # since the program will read this by default
WORKDIR /usr/src
ADD . /usr/src
ENTRYPOINT ["python", "main.py"]# this is an example for a python program, pick the language of your choice and we'll have something else write to that log file.
```