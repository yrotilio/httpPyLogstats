import pandas as pd
import time

from httpPyLogstats import alert_high_traffic

config = {
    'alerts': {
        'high_traffic': {
            'enabled': True,
            'limit_period': 2,
            'limit_value': 1
        }
    }
}

empty_alerts_df = pd.DataFrame(columns=["date_start", "date_end", "type", "value"])


def make_log_df(nb_logs):
    returned_df = pd.DataFrame()
    for i in range(0, nb_logs):
        now = time.time()
        df = pd.DataFrame({"date_time": [now]}, index=[now])
        returned_df = pd.concat([returned_df, df])
    return returned_df


def test_no_alert_high_traffic():
    global config
    global empty_alerts_df

    logs_stats_df = make_log_df(1)

    tested_alert_df = alert_high_traffic(alert_high_traffic_config=config['alerts']['high_traffic'],
                       log_stats_df=logs_stats_df,
                       alerts_df=empty_alerts_df)

    assert tested_alert_df.empty


def test_spawn_alert_high_traffic():
    global config
    global empty_alerts_df

    logs_stats_df = make_log_df(10)

    tested_alert_df = alert_high_traffic(alert_high_traffic_config=config['alerts']['high_traffic'],
                       log_stats_df=logs_stats_df,
                       alerts_df=empty_alerts_df)

    active_alerts = tested_alert_df.loc[tested_alert_df["date_end"].isnull()]
    archived_alerts = tested_alert_df.loc[tested_alert_df["date_end"].notnull()]

    assert archived_alerts.empty
    assert not active_alerts.empty
    assert len(active_alerts) == 1

    time.sleep(2)

    tested_alert_df = alert_high_traffic(alert_high_traffic_config=config['alerts']['high_traffic'],
                       log_stats_df=logs_stats_df,
                       alerts_df=tested_alert_df)

    active_alerts = tested_alert_df.loc[tested_alert_df["date_end"].isnull()]
    archived_alerts = tested_alert_df.loc[tested_alert_df["date_end"].notnull()]

    assert not archived_alerts.empty
    assert active_alerts.empty
    assert len(archived_alerts) == 1
