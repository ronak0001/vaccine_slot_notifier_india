__author__ = "Ronak Prajapati"
__copyright__ = "Copyright 2021, RKP, Vaccine Slot Notifier India"
__version__ = "1.0.0"
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
    :type path: str
    :param group_by_cols: list of columns for group by
    :type group_by_cols: list
    :return: Returns dataframe consisting subscribers information
    :rtype: pandas.DataFrame()
    """
    subscribers = pd.read_csv(path)
    subscribers = subscribers.groupby(group_by_cols).agg(lambda x: ','.join(set(x))).reset_index()

    return subscribers


def set_state_id(cfg):
    """
    Setting up state_id in config.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :return: no value
    :rtype: none
    """
    if os.getenv('state_id', '') != cfg['dummy_check']:
        cfg['state_id'] = os.getenv('state_id', '')
    elif os.getenv('state_name', '') != cfg['dummy_check']:
        cfg['state_name'] = os.getenv('state_name', '').replace('_', ' ')
        states_resp_df = get_states(cfg['states_get_url'], eval(cfg['request_header']))
        cfg['state_id'] = str(states_resp_df[states_resp_df['state_name'] == cfg['state_name']]['state_id'].values[0])
    else:
        if os.getenv('state_name', '') == cfg['dummy_check'] and os.getenv('state_id', '') == cfg['dummy_check']:
            raise Exception("No state_name or state_id found in env.sh")
        else:
            raise Exception("Enter valid state_name or state_id")
    pass


def set_district_id(cfg):
    """
    Setting up district_id in config.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :return: no value
    :rtype: none
    """
    if os.getenv('district_id', '') != cfg['dummy_check']:
        cfg['district_id'] = os.getenv('district_id', '')
    elif os.getenv('district_name', '') != cfg['dummy_check']:
        cfg['district_name'] = os.getenv('district_name', '').replace('_', ' ')
        district_resp_df = get_districs(cfg['districts_get_url'], eval(cfg['request_header']))
        cfg['district_id'] = str(district_resp_df[district_resp_df['district_name'] == cfg['district_name']]['district_id'].values[0])
    else:
        if os.getenv('district_name', '') == cfg['dummy_check'] and os.getenv('district_id', '') == cfg['dummy_check']:
            raise Exception("No district_name or district_id found in env.sh")
        else:
            raise Exception("Enter valid district_name or district_id")
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
    :return: Returns start date and end date values
    :rtype: datetime
    """
    if os.getenv('date', '') != cfg['dummy_check']:
        ds_trig = os.getenv('date', '')
    else:
        ds_trig = datetime.now().date().strftime("%d-%m-%Y")

    if os.getenv('date_window', '') != cfg['dummy_check']:
        cfg['date_window'] = os.getenv('date_window', '')

    return get_dates(ds_trig, cfg['date_window'])


def initialise_params(cfg):
    """
    Initialising necessary parameters.

    :param cfg: config parameter is used to provide necessary information
     required to fetch and push data
    :type cfg: dict
    :return: Returns start date and end date values
    :rtype: datetime
    """
    set_state_id(cfg)
    set_district_id(cfg)
    set_sender(cfg)
    return set_dates(cfg)


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
    Given date and date_window, this function generate end date
    and returns current date and end date.

    :param date: current date
    :type date: str
    :param date_window: interval in days
    :type date_window: str
    :return: Returns start date and end date values
    :rtype: datetime
    """
    ds_curr = datetime.strptime(date, "%d-%m-%Y")
    ds_end = ds_curr + timedelta(int(date_window)-1)

    return ds_curr, ds_end


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
    slots_resp_df_partial = slots_resp_df[eval(cfg['slots_resp_df_partial_cols']) +
                                          eval(cfg['subscribers_group_by_cols'])]

    slots_resp_df_partial.loc[:, 'info'] = "vaccine: " + slots_resp_df_partial['vaccine'].map(str)\
                                           + " | block_name: " + slots_resp_df_partial['block_name'].map(str)\
                                           + " | pincode: " + slots_resp_df_partial['pincode'].map(str)\
                                           + " | available_capacity: " + slots_resp_df_partial['available_capacity'].map(str)

    slots_resp_df_aggr = slots_resp_df_partial[eval(cfg['subscribers_group_by_cols'])
                                               + eval(cfg['email_message_info_col'])]\
        .groupby(eval(cfg['subscribers_group_by_cols'])).agg(lambda x: ' \n'.join(set(x)))
    slots_resp_final = slots_resp_df_aggr.merge(subscribers_df, on=eval(cfg['subscribers_group_by_cols']))
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