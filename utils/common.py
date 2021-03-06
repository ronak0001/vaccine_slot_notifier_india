__author__ = "Ronak Prajapati"
__copyright__ = "Copyright 2021, RKP, Vaccine Slot Notifier India"
__version__ = "1.0.5"
__maintainer__ = "Ronak Prajapati"
__email__ = "prajapatironak12@gmail.com"
__status__ = "Development"
__module_name__ = "common"
__project_name__ = "Vaccine Slot Notifier India"

from configparser import ConfigParser, ExtendedInterpolation
import requests
import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import os
pd.options.mode.chained_assignment = None  # default='warn'


def get_config(config_file, mode):
    """
    This function uses the configparser to the read the app.config file from
    given location for given mode.

    :param config_file: The location of the app.config file
    :type config_file: str
    :param mode: The mode/section of the init_cfg file which is of interest
    :param mode: str
    :return: Returns the section of interest from the app.config file
    :rtype: dict
    """
    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read(config_file)

    return config[mode]


def fetch_subscribers(path, group_by_cols):
    """
    This function fetches subscribers data from given path and performs group
    by on given group by columns to create list of recipients with similar
    requirements.

    :param path: The location of the data file containing subscribers info
    or the url of google sheet containing subscribers info
    :type path: str
    :param group_by_cols: list of columns for group by
    :type group_by_cols: list
    :return: Returns dataframe consisting subscribers information
    :rtype: pandas.DataFrame()
    """
    subscribers_raw_resp = pd.read_csv(path)
    subscribers = pd.DataFrame()
    subscribers['recipients'] = subscribers_raw_resp['Email']
    subscribers['min_age_limit'] = subscribers_raw_resp['Age Group'].apply(lambda x: x[:2])
    subscribers['dose'] = subscribers_raw_resp['Dose'].apply(lambda x: x[-1])
    subscribers['state_name'] = subscribers_raw_resp['State']
    subscribers['district_name'] = subscribers_raw_resp[subscribers_raw_resp.columns[4:-1]].apply(
        lambda x: ','.join(x.dropna().astype(str)), axis=1)

    subscribers = subscribers.groupby(group_by_cols).agg(lambda x: ','.join(set(x))).reset_index()

    return subscribers


def force_reset_state_district_data(cfg):
    """
    Calls functions to fetch latest states and districts data, stores and also
    returns updated data as a dataframe.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :return: Updated state and district data
    :rtype: pandas.DataFrame()
    """
    response = get_states(cfg['states_get_url'], eval(cfg['request_header']))

    df = pd.DataFrame()
    for i, row in pd.DataFrame(response.json()['states']).iterrows():
        cfg['state_id'] = str(row['state_id'])
        temp_df = pd.DataFrame()
        temp_df = get_districs(cfg['districts_get_url'], eval(cfg['request_header']))
        temp_df['state_name'] = row['state_name']
        temp_df['state_id'] = row['state_id']

        df = df.append(temp_df)
    df.to_csv(cfg['states_districts_info_file_path'], index=False)
    return df.reset_index(drop=True)


def set_state_district(cfg, state_name, district_name, force_reset=False):
    """
    Setting up state_name, state_id, district_name and district_id in config.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :param state_name: state name
    :type state_name: str
    :param district_name: state name
    :type district_name: str
    :param force_reset: force reset for resetting state district data
    :type force_reset: bool
    :return: no value
    :rtype: none
    """
    cfg['state_name'] = state_name
    cfg['district_name'] = district_name

    if force_reset:
        states_district_info = force_reset_state_district_data(cfg)
    else:
        states_districts_info = pd.read_csv(cfg['states_districts_info_file_path'])

    states_districts_info = states_districts_info.loc[
                            (states_districts_info['state_name'] == cfg['state_name']) &
                            (states_districts_info['district_name'] == cfg['district_name']),
                            list(states_districts_info.columns)]

    cfg['state_id'] = str(states_districts_info['state_id'].values[0])
    cfg['district_id'] = str(states_districts_info['district_id'].values[0])
    pass


def set_sender(cfg):
    """
    Setting up sender in config.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :return: no value
    :rtype: none
    """
    if os.getenv('sender', '') != cfg['dummy_check']:
        cfg['sender'] = os.getenv('sender', '')
    pass


def set_dates(cfg):
    """
    Setting up dates in config based on triggered date and date_window from
    environment.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :return: no value
    :rtype: none
    """
    ds_trig = datetime.now().date().strftime("%d-%m-%Y")

    if os.getenv('date_window', '') != cfg['dummy_check']:
        cfg['date_window'] = os.getenv('date_window', '')

    cfg['dates'] = str(get_dates(ds_trig, cfg['date_window']))
    pass


def set_gsheet(cfg):
    """
    Setting up credentials of google sheet in config.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :return: no value
    :rtype: none
    """
    if os.getenv('gsheet_id', '') != cfg['dummy_check']:
        cfg['subscribers_input_gsheet_id'] = os.getenv('gsheet_id', '')
    pass


def initialise_params(cfg):
    """
    Initialising necessary parameters.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :return: no value
    :rtype: none
    """
    set_sender(cfg)
    set_gsheet(cfg)
    set_dates(cfg)
    pass


def get_states(url, headers):
    """
    Function to call API to get all states information.
    Sample Request: https://cdn-api.co-vin.in/api/v2/admin/location/states

    :param url: url to be used to make requests and get data from server
    :type url: str
    :param headers: header containing user-agent and other necessary parameters
    :type headers: dict
    :return: Returns dataframe containing response from server
    :rtype: pandas.DataFrame()
    """
    response = requests.get(url, headers=headers)
    return pd.DataFrame(response.json()['states'])


def get_districs(url, headers):
    """
    Function to call API to get all districts information.
    Sample Request: https://cdn-api.co-vin.in/api/v2/admin/location/districts/16

    :param url: url to be used to make requests and get data from server
    :type url: str
    :param headers: header containing user-agent and other necessary parameters
    :type headers: dict
    :return: Returns dataframe containing response from server
    :rtype: pandas.DataFrame()
    """
    response = requests.get(url, headers=headers)
    return pd.DataFrame(response.json()['districts'])


def get_dates(date, date_window):
    """
    Given date and date_window, this function generate end date and returns
    current date and end date.

    :param date: current date
    :type date: str
    :param date_window: interval in days
    :type date_window: str
    :return: Returns array containing dates based on given date window
    :rtype: array<str>
    """
    ds_curr = datetime.strptime(date, "%d-%m-%Y")
    dates = []

    for i in range(0, int(date_window)):
        dates.append((ds_curr + timedelta(i)).strftime("%d-%m-%Y"))

    return dates


def find_slots_by_pin(url, headers):
    """
    Function to call API to find slots by pin-code.
    Sample Request: https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin?pincode=110001&date=31-03-2021

    :param url: url to be used to make requests and get data from server
    :type url: str
    :param headers: header containing user-agent and other necessary parameters
    :type headers: dict
    :return: Returns dataframe containing response from server
    :rtype: pandas.DataFrame()
    """
    response = requests.get(url, headers=headers)
    return pd.DataFrame(response.json()['sessions'])


def find_slots_by_district(url, headers):
    """
    Function to call API to find slots by district.
    Sample Request: https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict?district_id=512&date=31-03-2021

    :param url: url to be used to make requests and get data from server
    :type url: str
    :param headers: header containing user-agent and other necessary parameters
    :type headers: dict
    :return: Returns dataframe containing response from server
    :rtype: pandas.DataFrame()
    """
    response = requests.get(url, headers=headers)
    return pd.DataFrame(response.json()['sessions'])


def send_email_alerts(cfg, slots_resp_df, subscribers_df):
    """
    Filters slots according to subscribers info and prepares data to be
    send via email.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :param slots_resp_df: dataframe consisting slots response from server
    :type slots_resp_df: pandas.DataFrame()
    :param subscribers_df: dataframe consisting subscribers info
    :type subscribers_df: pandas.DataFrame()
    :return: no value
    :rtype: none
    """
    slots_resp_df = slots_resp_df.melt(id_vars=slots_resp_df.columns.difference(eval(cfg['dose_cols_slots'])).to_list(),
                                       value_vars=eval(cfg['dose_cols_slots']), var_name=cfg['dose_col_main'],
                                       value_name=cfg['capacity_col_main'])

    slots_resp_df[cfg['dose_col_main']] = slots_resp_df[cfg['dose_col_main']].apply(lambda x: x[-1])
    slots_resp_df = slots_resp_df[slots_resp_df[cfg['capacity_col_main']] > 0]

    slots_resp_df_partial = slots_resp_df[eval(cfg['slots_resp_df_partial_cols']) +
                                          eval(cfg['subscribers_group_by_cols']) +
                                          eval(cfg['geo_cols'])]

    slots_resp_df_partial.loc[:, 'info'] = "Pincode: " + slots_resp_df_partial['pincode'].map(str) \
                                           + " | Center: " + slots_resp_df_partial['name'].map(str) \
                                           + " | Vaccine: " + slots_resp_df_partial['vaccine'].map(str)\
                                           + " | Dose: " + slots_resp_df_partial['dose'].map(str)\
                                           + " | Capacity: " + slots_resp_df_partial['capacity'].map(str)\
                                           + " | Date: " + slots_resp_df_partial['date'].map(str)\
                                           + "\n\n"

    slots_resp_df_aggr = slots_resp_df_partial[eval(cfg['subscribers_group_by_cols'])
                                               + eval(cfg['geo_cols'])
                                               + eval(cfg['email_message_info_col'])]\
        .groupby(eval(cfg['subscribers_group_by_cols'])+eval(cfg['geo_cols'])).agg(lambda x: ' \n'.join(set(x)))

    slots_resp_df_aggr = slots_resp_df_aggr.reset_index().astype(str)
    subscribers_df = subscribers_df.astype(str)
    slots_resp_final = slots_resp_df_aggr.merge(subscribers_df, on=eval(cfg['subscribers_group_by_cols'])+eval(cfg['geo_cols']))

    send_notification(cfg, slots_resp_final)

    pass


def send_notification(cfg, slots_resp_final):
    """
    Iterates over rows of final dataframe and calls function to send
    email to different classifications of similar subscribers.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :param slots_resp_final: dataframe consisting aggregated entries
    :type slots_resp_final: pandas.DataFrame()
    :return: no value
    :rtype: none
    """
    for i, row in slots_resp_final.iterrows():
        cfg['min_age_limit'] = str(row['min_age_limit'])
        cfg['recipients'] = str(row['recipients'].split(','))

        send_email(cfg['sender'], eval(cfg['recipients']),
                   cfg['email_subject'], cfg['email_message'].format(row['info']),
                   os.getenv('sender_password', ''))
    pass


def send_email(sender, recipients, subject, message, password):
    """
    Given sender, recipients, subject and message, this function create a
    connection to smtp server and sends email.

    :param sender: sender's email address
    :type sender: str
    :param recipients: list of recipients
    :type recipients: list
    :param subject: subject of the email
    :type subject: str
    :param message: body of the email
    :type message: str
    :param password: password
    :type password: str
    :return: no value
    :rtype: none
    """
    try:
        msg = EmailMessage()
        msg.set_content(message)

        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = "you"

        smtpObj = smtplib.SMTP("smtp.gmail.com", 587)
        smtpObj.ehlo()
        smtpObj.starttls()
        smtpObj.login(sender, password)
        smtpObj.sendmail(sender, recipients, msg.as_bytes().decode('unicode_escape').encode('utf-8'))
    except Exception as e:
        print(e)
