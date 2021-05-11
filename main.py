__author__ = "Ronak Prajapati"
__copyright__ = "Copyright 2021, RKP, Vaccine Slot Notifier India"
__version__ = "1.0.1"
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
    # print(subscribers_grouped_df)

    for i, row in subscribers_grouped_df[eval(cfg['geo_cols'])].\
            drop_duplicates().iterrows():
        # print(row['district_name'] + ", " + row['state_name'])

        [ds_curr, ds_end] = initialise_params(cfg, state_name=row['state_name'], district_name=row['district_name'])

        while ds_curr <= ds_end:
            cfg['date'] = ds_curr.strftime('%d-%m-%Y')
            # print("Date: {}".format(cfg['date']))

            slots_resp_df = find_slots_by_district(cfg['slot_check_by_district_url'],
                                                   eval(cfg['request_header']))

            if len(slots_resp_df) == 0:
                ds_curr += timedelta(int(1))
                continue

            send_email_alerts(cfg, slots_resp_df, subscribers_grouped_df)

            ds_curr += timedelta(int(1))

    stop = perf_counter()
    print("Total Execution Time: {} Seconds.".format(stop-start))
