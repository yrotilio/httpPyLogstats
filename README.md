# httpPyLogstats

## Summary
Consumes an actively written-to w3c-formatted HTTP access log (https://www.w3.org/Daemon/User/Config/Logging.html)

Example log lines:
```
127.0.0.1 - james [09/May/2018:16:00:39 +0000] "GET /report HTTP/1.0" 200 123
127.0.0.1 - jill [09/May/2018:16:00:41 +0000] "GET /api/user HTTP/1.0" 200 234
127.0.0.1 - frank [09/May/2018:16:00:42 +0000] "POST /api/user HTTP/1.0" 200 34
127.0.0.1 - mary [09/May/2018:16:00:42 +0000] "POST /api/user HTTP/1.0" 503 12
```

* Display stats every 10s about the traffic during those 10s: the sections of the web site with the most hits, as well as interesting summary statistics on the traffic as a whole. A section is defined as being what's before the second '/' in the resource section of the log line. For example, the section for "/pages/create" is "/pages"
* User can keep the app running and monitor the log file continuously
* Whenever total traffic for the past 2 minutes exceeds a certain number on average, a message saying “High traffic generated an alert - hits = {value}, triggered at {time}” is triggered. The default threshold is 10 requests per second, and is overridable.
* Whenever the total traffic drops again below that value on average for the past 2 minutes, another message detailing when the alert recovered is triggered.
* All messages showing when alerting thresholds are crossed remain visible on the page for historical reasons.

## Usage

* Docker image
```
docker run -d mryro/httppylogstats:1.0
```

## Ideas to enhance httPyLostats

* Find a faster log parsing method
* Create a alert class to enhance alert creation
* Create an alert pattern that allows user to configure their own alerts
* Isolate log parsing and statistics refreshing (multi-proc)
* Display statistics in a web page

