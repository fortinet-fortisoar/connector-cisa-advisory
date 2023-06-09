"""
This file will be auto-generated on each "new operation action", so avoid editing in this file.
"""
import json
import re
import requests
from bs4 import BeautifulSoup
import datetime
from dateutil.relativedelta import relativedelta
from connectors.core.connector import get_logger, ConnectorError
from .constant import *
from integrations.crudhub import make_request

logger = get_logger('cisa-advisory')


class Advisory():

    def __init__(self, advisory_type):
        self.advisory_type = advisory_type

    def get_ics_data(self):
        try:
            ics_advisory_url_by_year_links_list = []
            output = []
            url = REPO_URL + self.advisory_type + '/'
            response = requests.get(url, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a'):
                if self.advisory_type in link.get('href'):
                    ics_advisory_url_by_year_links_list.append(
                        link.get('href'))
            for advisory_link in ics_advisory_url_by_year_links_list:
                json_file_data = requests.get(
                    url + advisory_link, verify=False)
                for item in json.loads(json_file_data.text):
                    output.append(item)
            return output
        except Exception as err:
            logger.exception(str(err))
            raise ConnectorError(err)

    def date_filter_advisory(self, params, ics_data):
        try:
            today_date = datetime.date.today()
            if params['date_filter'] == 'Last 7 Days':
                filter_date = today_date + relativedelta(days=-7)
                return self.get_advisory_by_date(today_date, filter_date, ics_data)
            if params['date_filter'] == 'Last 30 Days':
                filter_date = today_date + relativedelta(days=-30)
                return self.get_advisory_by_date(today_date, filter_date, ics_data)
            if params['date_filter'] == 'This Month':
                filter_date = today_date.replace(day=1)
                return self.get_advisory_by_date(today_date, filter_date, ics_data)
            if params['date_filter'] == 'This Year':
                filter_date = today_date.replace(day=1, month=1)
                return self.get_advisory_by_date(today_date, filter_date, ics_data)
            if params['date_filter'] == 'Last Month':
                last_month_end_date = today_date.replace(
                    day=1) - datetime.timedelta(days=1)
                last_month_start_date = last_month_end_date.replace(day=1)
                return self.get_advisory_by_date(last_month_end_date, last_month_start_date, ics_data)
            if params['date_filter'] == 'Last 3 Months':
                filter_date = today_date + relativedelta(months=-3)
                return self.get_advisory_by_date(today_date, filter_date, ics_data)
            if params['date_filter'] == 'Last 6 Months':
                filter_date = today_date + relativedelta(months=-6)
                return self.get_advisory_by_date(today_date, filter_date, ics_data)
            if params['date_filter'] == 'Last Date Published Advisory':
                delta = datetime.timedelta(days=-1)
                last_publish_date = ""
                while True:
                    for ics in ics_data:
                        if ics.get('release_date') == str(today_date):
                            last_publish_date = str(today_date)
                            break
                    if last_publish_date != "":
                        filter_ics_advisory = [ics for ics in ics_data if ics.get(
                            'release_date') == last_publish_date]
                        return filter_ics_advisory
                    else:
                        today_date += delta
            if params['date_filter'] == 'Custom Date':
                pattern = r'^\d{4}-\d{2}-\d{2}T'
                if isinstance(params['selectDate'], int):
                    date_time = datetime.datetime.fromtimestamp(
                        params['selectDate']).strftime("%Y-%m-%d")
                    filter_data = [ics for ics in ics_data if ics.get(
                        'release_date') == date_time]
                    return filter_data
                elif re.match(pattern, params['selectDate']):
                    date_time = datetime.datetime.strptime(
                        params['selectDate'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
                    filter_data = [ics for ics in ics_data if ics.get(
                        'release_date') == date_time]
                    return filter_data
        except Exception as err:
            logger.exception(str(err))
            raise ConnectorError(err)

    def get_advisory_by_date(self, end_date, start_date, ics_data):
        try:
            filter_ics_advisory = []
            delta = datetime.timedelta(days=1)
            while start_date <= end_date:
                for ics in ics_data:
                    if ics.get('release_date') == str(start_date):
                        filter_ics_advisory.append(ics)
                start_date += delta
            return filter_ics_advisory
        except Exception as err:
            logger.exception(str(err))
            raise ConnectorError(err)

    def set_ratio(self, str1, str2):
        try:
            if str1.lower() in str2.lower() or str2.lower() in str1.lower():
                return 100

            count = 0

            # Unique within string
            modified_str1 = self.remove_special_characters(str1.lower())
            modified_str2 = list(
                set(self.remove_special_characters(str2.lower()).split(' ')))
            for data in ' '.join(modified_str2).split():
                if re.search(r'\b{0}\b'.format(data), modified_str1):
                    count += 1
            if len(modified_str2) <= len(modified_str1.split(' ')):
                return round(count / len(modified_str2) * 100)
            return round(count / len(modified_str1.split(' ')) * 100)
        except Exception as err:
            logger.exception(str(err))
            raise Exception(err)

    def remove_special_characters(self, text):
        try:
            return re.sub(r'[^\w\s]', ' ', text)
        except Exception as err:
            logger.exception(str(err))
            raise Exception(err)


def get_advisory(config, params):
    try:
        if params['advisory_type'] == 'ICS Advisory':
            advisory_obj = Advisory('ics-advisory')
        elif params['advisory_type'] == 'ICS Medical Advisory':
            advisory_obj = Advisory('ics-medical-advisory')
        ics_data = advisory_obj.get_ics_data()
        if params['date_filter']:
            output = advisory_obj.date_filter_advisory(params, ics_data)
            return sorted(output, key=lambda k: k['release_date'], reverse=True)
        else:
            return sorted(ics_data, key=lambda k: k['release_date'], reverse=True)
    except Exception as err:
        logger.exception(str(err))
        raise Exception(err)


def get_advisory_by_year(config, params):
    try:
        if params['advisory_type'] == 'ICS Advisory':
            advisory_type = 'ics-advisory'
        elif params['advisory_type'] == 'ICS Medical Advisory':
            advisory_type = 'ics-medical-advisory'
        ics_advisory_url_by_year = REPO_URL + advisory_type + '/' + \
            str(params['year']) + '-' + advisory_type + '.json'
        json_file_data = requests.get(ics_advisory_url_by_year, verify=False)
        output = json.loads(json_file_data.text)
        return sorted(output, key=lambda k: k['release_date'], reverse=True)
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)


def get_advisory_by_vendor(config, params):
    try:
        output = []
        if params['advisory_type'] == 'ICS Advisory':
            advisory_obj = Advisory('ics-advisory')
        elif params['advisory_type'] == 'ICS Medical Advisory':
            advisory_obj = Advisory('ics-medical-advisory')
        advisory_data = advisory_obj.get_ics_data()
        for advisory in advisory_data:
            ratio = advisory_obj.set_ratio(
                str(params['vendor'].strip()), advisory['vendor'])
            if ratio >= params['similarityThreshold']:
                output.append(advisory)
        return sorted(output, key=lambda k: k['release_date'], reverse=True)
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)


def get_advisory_by_product(config, params):
    try:
        output = []
        if params['advisory_type'] == 'ICS Advisory':
            advisory_obj = Advisory('ics-advisory')
        elif params['advisory_type'] == 'ICS Medical Advisory':
            advisory_obj = Advisory('ics-medical-advisory')
        ics_advisory_data = advisory_obj.get_ics_data()
        for advisory in ics_advisory_data:
            ratio = advisory_obj.set_ratio(
                str(params['product'].strip()), advisory['product'])
            if ratio >= params['similarityThreshold']:
                if str(params['version']).strip() != "":
                    if str(params['version']).strip() in advisory['affected_product']:
                        output.append(advisory)
                    else:
                        continue
                else:
                    output.append(advisory)
        return sorted(output, key=lambda k: k['release_date'], reverse=True)
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)

operations = {
    "get_advisory": get_advisory,
    "get_advisory_by_year": get_advisory_by_year,
    "get_advisory_by_vendor": get_advisory_by_vendor,
    "get_advisory_by_product": get_advisory_by_product
}
