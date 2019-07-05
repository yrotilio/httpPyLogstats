import os
import sys
import re
import time
import datetime
import yaml
import argparse
import pandas as pd

host = r'^(?P<host>.*?)'
space = r'\s'
dash = r'\S+'
user = r'(?P<user>\S+)'
reqtime = r'\[(?P<time>.*?)\]'
method = r'\"(?P<method>\S+)'
section = r'(?P<section>/\w+)'
subsection = r'(?P<subsection>/\w+)?'
protocol = r'(?P<protocol>\S+)?\"'
status = r'(?P<status>\d{3})'
size = r'(?P<size>\S+)'

http_re_match = host + space + dash + space + user + space + reqtime + space + method + space + section + subsection + space + protocol + space + status + space + size

log_stats_df = pd.DataFrame()
alerts_df = pd.DataFrame(columns=["date_start", "date_end", "type", "value"])

# Available configuration used as global variable
config = {
    'logfile': '/var/log/access.log',
    'stats_period': 10,
    'stats_refresh': 10,
    'alerts': {
        'high_traffic': {
            'enabled': True,
            'limit_period': 120,
            'limit_value': 10
        }
    }
}


def load_config(config_file_path):
    """
        Load configuration from file
        Loaded configuration can only match known configuration structure (see global default config variable)
        If file path None or not found, exit program
        :param config_file_path: Path to config file
    """
    global config
    try:
        config_file_path = os.path.abspath(config_file_path)
        assert config_file_path
        with open(file=config_file_path) as yaml_data:
            loaded_config = yaml.safe_load(yaml_data)
            for k in config:
                if k in loaded_config:
                    config[k] = loaded_config[k]
    except AssertionError:
        print(f"Config file {config_file_path} not found or unreadable ! Exiting..")
        quit(1)


def log_parser(logline, http_re_match):
    """
        Parse log line with a regex
        If log line matches, insert logline into a global dataframe
        If log line does not match, print warning
        :param logline: HTTP formated log line (https://www.w3.org/Daemon/User/Config/Logging.html)
        :param http_re_match: Regex that validate and split the log line into groups
    """
    global log_stats_df
    match = re.search(http_re_match, logline)
    if match is not None:
        # Need to format HTTP log time into timestamp for comparisons
        date_time = time.mktime(datetime.datetime.strptime(match.group('time'), '%d/%b/%Y:%H:%M:%S +%f').timetuple())

        # Insert every group in case we want to show some more stats one day
        log_stat_df = pd.DataFrame({"date_time": [date_time],
                                    "host": [match.group('host')],
                                    "user_id": [match.group('user')],
                                    "method": [match.group('method')],
                                    "section": [match.group('section')],
                                    "subsection": [match.group('subsection')],
                                    "protocol": [match.group('protocol')],
                                    "response_code": [match.group('status')],
                                    "content_size": [match.group('size')]
                                    }, index=[date_time]
                                   )
        log_stats_df = pd.concat([log_stats_df,log_stat_df])
    else:
        print(f"WARNING: Unmatched log line '{logline}'")


def alert_high_traffic(alert_high_traffic_config, log_stats_df, alerts_df):
    """
        Manages alerts for high traffic, aka request per sec from a http logs dataframe
        Alert configuration is based on 3 parameters :
            - If alert is enabled/disabled
            - Hit rate limit value
            - Hit rate limit period
        If hit rate in log dataframe > hit rate limit during period, creates an high traffic to alert dataframe
        If high traffic alert active and hit rate in log dataframe <= hit rate limit during period, marks high traffic alert as recovered
        Returns an updated alert dataframe
        :param alert_high_traffic_config: Dict representing high traffic alert configuration
        :param log_stats_df: Dataframe of timestamped HTTP logs
        :param alerts_df: Dataframe of timestamped monitored alerts
    """
    limit_period = alert_high_traffic_config['limit_period']
    limit_value = alert_high_traffic_config['limit_value']
    now = time.time()

    log_stats_df_subset = log_stats_df.loc[log_stats_df["date_time"] > now - limit_period ]

    hit_rate = len(log_stats_df_subset) / limit_period

    active_alerts = alerts_df.loc[alerts_df["date_end"].isnull()]
    active_high_traffic_alert = active_alerts.loc[active_alerts["type"] == "High traffic"]
    
    if active_high_traffic_alert.empty:
        if hit_rate > limit_value:
            active_alert = pd.DataFrame({"date_start": now,
                                         "type": "High traffic",
                                         "value_start": f"Hits = {hit_rate} per sec",
                                         "value_end": None,
                                         "date_end": None
                                         }, index=[now])
            alerts_df = pd.concat([alerts_df, active_alert])
    else:
        if hit_rate <= limit_value:
            recovered_alert = pd.DataFrame({"date_end": now,
                                             "type": "High traffic",
                                             "value_start": active_high_traffic_alert["value_start"].item(),
                                             "value_end": f"Hits = {hit_rate} per sec",
                                             "date_start": active_high_traffic_alert["date_start"].item(),
                                            }, index=[active_high_traffic_alert.index.item()])
            alerts_df.update(recovered_alert)
    return alerts_df


def startup():
    """
    Starts up HTTPPyLogstats by :
     - Loading default configuration
     - Loading specific configuration (if passed as an arg)
     - Printing main configuration
     - Checking main configuration
    """
    global config

    default_config_file = './httpPyLogstats.yaml'
    version = "1.0"
    now = time.time()
    date_time = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')

    print('********************************')
    print('HTTP LOGS STATISTICS STARTING UP')
    print('********************************')
    print(f'Version : {version}')
    print(f'{date_time}')
    print()

    if sys.version_info[0] < 3:
        raise Exception("Python 3 or a more recent version is required.")

    load_config(config_file_path=default_config_file)

    parser = argparse.ArgumentParser(description='HTTP Logs Python Statistics')
    parser.add_argument("-c", "--config-file", help='Need config file path', dest="--config-file")

    args = parser.parse_args().__dict__

    if args['--config-file']:
        load_config(config_file_path=args['--config-file'])

    try:
        assert config['logfile']
        logfile = open(config['logfile'], "r")
        assert logfile.readable()
        logfile.close()
    except AssertionError:
        print(f"Log file not readable or configuration incorrect ! Exiting..")
        quit(1)

    print('Loaded configuration:')
    print(f'  Log file analysed : {config["logfile"]}')

    try:
        assert config["stats_refresh"]
        assert config["stats_refresh"] != 0
        assert int(config["stats_refresh"])
    except AssertionError:
        config["stats_refresh"] = 10

    try:
        assert config["stats_period"]
        assert int(config["stats_period"])
    except AssertionError:
        config["stats_period"] = 10

    print(f'  Display statistics about the last {config["stats_period"]} seconds every {config["stats_refresh"]} seconds')
    print()
    print(f'Enabled alerts')
    try:
        assert config['alerts']['high_traffic']['enabled']
        assert int(config["alerts"]["high_traffic"]["limit_value"])
        assert int(config["alerts"]["high_traffic"]["limit_period"])
        print('  [X] High traffic:')
        print(f'     Traffic > {config["alerts"]["high_traffic"]["limit_value"]} request per sec over {config["alerts"]["high_traffic"]["limit_period"]} seconds')
    except AssertionError:
        config['alerts']['high_traffic'] = {
            'enabled': False
        }
        print('  [ ] High traffic')
        pass

    print()
    print(f'Starting analysing {config["logfile"]}')
    print(f'--------------------------------------')


def print_header(now):
    """
    Prints stats title and timestamp
    """
    global config
    date_time = datetime.datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')

    print('*************************************')
    print(f'HTTP LOGS STATISTICS - {date_time}')


def print_log_stats(now, stats_period_seconds, log_stats_df):
    """
    Prints log stats from HTTP log dataframe during period
        :param now: Timestamp to consider as period upper value
        :param stats_period_seconds: Period for printed statistics
        :param log_stats_df: HTTP logs dataframe
    """
    print(f'###  Statistics for the last {stats_period_seconds} seconds ###')
    log_stats_df_subset = log_stats_df.loc[log_stats_df["date_time"] > now - stats_period_seconds]

    log_stats_df_subset_2XX = log_stats_df_subset[log_stats_df_subset["response_code"].str.match(r'^2\d{2}$')]
    log_stats_df_subset_3XX = log_stats_df_subset[log_stats_df_subset["response_code"].str.match(r'^3\d{2}$')]
    log_stats_df_subset_4XX = log_stats_df_subset[log_stats_df_subset["response_code"].str.match(r'^4\d{2}$')]
    log_stats_df_subset_5XX = log_stats_df_subset[log_stats_df_subset["response_code"].str.match(r'^5\d{2}$')]
    log_stats_df_subset_sections = log_stats_df_subset["section"].value_counts().nlargest(3)

    print(f' - Number of hits : {len(log_stats_df_subset)}')
    print(f' - Number of GET : {len(log_stats_df_subset.loc[log_stats_df_subset["method"] == "GET"])}')
    print(f' - Number of POST : {len(log_stats_df_subset.loc[log_stats_df_subset["method"] == "POST"])}')
    print(f' - Number of 2XX : {len(log_stats_df_subset_2XX)}')
    print(f' - Number of 3XX : {len(log_stats_df_subset_3XX)}')
    print(f' - Number of 4XX : {len(log_stats_df_subset_4XX)}')
    print(f' - Number of 5XX : {len(log_stats_df_subset_5XX)}')

    print(f' - Total traffic : {pd.to_numeric(log_stats_df_subset["content_size"]).sum()}')
    print(' - Top 3 sections : ')

    i = 0
    for section, hits in log_stats_df_subset_sections.iteritems():
        i += 1
        print(f'     {i}. {section}: {hits} hits')
        if i >= 3:
            break

    print(f'###############################################################')


def print_alerts_stats(now, stats_period_seconds, alerts_df):
    """
    Prints alert stats from alerts dataframe during period
    Alerts are divided into 4 categories : new alerts, active alerts, recovered alerts, archived alerts
        :param now: Timestamp to consider as period upper value
        :param stats_period_seconds: Period for printed statistics
        :param alerts_df: alerts dataframe
    """

    if not alerts_df.empty:
        active_alerts = alerts_df.loc[alerts_df["date_end"].isnull()]
        archived_alerts = alerts_df.loc[alerts_df["date_end"].notnull()]
        new_alerts = active_alerts.loc[active_alerts["date_start"] > now - stats_period_seconds]
        recovered_alerts = archived_alerts.loc[archived_alerts["date_end"] > now - stats_period_seconds ]

        if len(new_alerts) > 0:
            print(f'### New alerts during the last {stats_period_seconds} seconds###')
            for index, row in new_alerts.iterrows():
                date_time_start = datetime.datetime.fromtimestamp(row['date_start']).strftime('%Y-%m-%d %H:%M:%S')
                print(f" - {row['type']} generated an alert - {row['value_start']}, triggered at {date_time_start}")

        if len(recovered_alerts) > 0:
            print(f'### Recovered alerts during the last {stats_period_seconds} seconds###')
            for index, row in recovered_alerts.iterrows():
                date_time_start = datetime.datetime.fromtimestamp(row['date_start']).strftime('%Y-%m-%d %H:%M:%S')
                date_time_end = datetime.datetime.fromtimestamp(row['date_end']).strftime('%Y-%m-%d %H:%M:%S')
                print(f" - {row['type']} triggered at {date_time_start} recovered at {date_time_end} - was {row['value_start']}, now {row['value_end']}")

        if len(active_alerts) > 0:
            print(f'### Active alerts ###')
            for index, row in active_alerts.iterrows():
                date_time = datetime.datetime.fromtimestamp(row['date_start']).strftime('%Y-%m-%d %H:%M:%S')
                print(f" - Since {date_time} : {row['type']}")

        if len(archived_alerts) > 0:
            print(f'### Past alerts ###')
            for index, row in archived_alerts.iterrows():
                date_time_start = datetime.datetime.fromtimestamp(row['date_start']).strftime('%Y-%m-%d %H:%M:%S')
                date_time_end = datetime.datetime.fromtimestamp(row['date_start']).strftime('%Y-%m-%d %H:%M:%S')
                print(f" - {date_time_start} to {date_time_end} : {row['type']}")
    else:
        print(f'### No alert ###')


if __name__ == '__main__':

    startup()

    logfile = open(config['logfile'], "r")

    before = time.time()
    while logfile.readable():
        now = time.time()
        line = logfile.readline()
        if line:
            log_parser(line, http_re_match)
        else:
            if now - before > config['stats_refresh']:
                if config['alerts']['high_traffic']['enabled']:
                    alerts_df = alert_high_traffic(config['alerts']['high_traffic'], log_stats_df=log_stats_df, alerts_df=alerts_df)
                print_header(now=now)
                print_log_stats(now=now, stats_period_seconds=config['stats_period'], log_stats_df=log_stats_df)
                print_alerts_stats(now=now, stats_period_seconds=config['stats_period'], alerts_df=alerts_df)
                before = time.time()
    quit(0)

