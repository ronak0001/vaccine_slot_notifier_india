__author__ = "Ronak Prajapati"
__copyright__ = "Copyright 2021, RKP, Vaccine Slot Notifier India"
__version__ = "1.0.3"
__maintainer__ = "Ronak Prajapati"
__email__ = "prajapatironak12@gmail.com"
__status__ = "Development"
__module_name__ = "main"
__project_name__ = "Vaccine Slot Notifier India"


from utils.common import *
import os
from time import perf_counter


if __name__ == "__main__":
    start = perf_counter()
    mode = os.getenv('mode', '')
    config_file = os.getenv('config_file', '')

    cfg = get_config(config_file, mode)

    subscribers_grouped_df = fetch_subscribers(cfg['subscribers_input_file_path'],
                                               eval(cfg['subscribers_group_by_cols'])+eval(cfg['geo_cols']))

    for i, row in subscribers_grouped_df[eval(cfg['geo_cols'])].\
            drop_duplicates().iterrows():

        initialise_params(cfg, state_name=row['state_name'], district_name=row['district_name'])
        dates = eval(cfg['dates'])
        slots_resp_df = find_slots_by_district(cfg['slot_check_by_district_url_multiple_days'].
                                               format(dates[0], dates[1], dates[2], dates[3],
                                                      dates[4], dates[5], dates[6]),
                                               eval(cfg['request_header']))

        if len(slots_resp_df) == 0:
            continue
        print(row['district_name'] + ", " + row['state_name'])

        send_email_alerts(cfg, slots_resp_df, subscribers_grouped_df)
    stop = perf_counter()
    print("Total Execution Time: {} Seconds.".format(stop-start))
