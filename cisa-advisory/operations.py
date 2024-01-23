"""
Copyright start
MIT License
Copyright (c) 2024 Fortinet Inc
Copyright end
"""
import json
import re
import requests
from bs4 import BeautifulSoup
import datetime
from dateutil.relativedelta import relativedelta
from connectors.core.connector import get_logger, ConnectorError
from .constants import *

logger = get_logger('cisa-advisory')


class Advisory():

    def __init__(self):
        pass

    def get_status(self, config):
        if not config['prodYumRepoURL'].startswith('https://') and not config['prodYumRepoURL'].startswith('http://'):
            yum_repo_url = 'https://{0}'.format(config['prodYumRepoURL'])
            response = requests.get(yum_repo_url)
            if response.status_code == 200:
                return True, yum_repo_url
            else:
                yum_repo_url = 'http://{0}'.format(config['prodYumRepoURL'])
                response = requests.get(yum_repo_url)
                if response.status_code == 200:
                    return True, yum_repo_url
                else:
                    return False
        else:
            response = requests.get(config['prodYumRepoURL'])
            if response.status_code == 200:
                return True, config['prodYumRepoURL']
            else:
                return False

    def get_ics_data(self, advisory_type, yum_repo_url):
        try:
            ics_advisory_url_by_year_links_list = []
            output = []
            url = yum_repo_url + CISA_FOLDER_PATH + advisory_type + '/'
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a'):
                if advisory_type in link.get('href'):
                    ics_advisory_url_by_year_links_list.append(
                        link.get('href'))
            for advisory_link in ics_advisory_url_by_year_links_list:
                json_file_data = requests.get(
                    url + advisory_link)
                for item in json.loads(json_file_data.text):
                    output.append(item)
            return output
        except Exception as err:
            logger.exception(str(err))
            raise ConnectorError(err)

    def get_ics_data_by_year(self, params, advisory_type, yum_repo_url):
        ics_advisory_url_by_year = yum_repo_url + CISA_FOLDER_PATH + advisory_type + '/' + \
            str(params['year']) + '-' + advisory_type + '.json'
        json_file_data = requests.get(
            ics_advisory_url_by_year)
        output = json.loads(json_file_data.text)
        return output

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
            if params['date_filter'] == 'After Date':
                filter_data = []
                pattern = r'^\d{4}-\d{2}-\d{2}T'
                if isinstance(params['selectDate'], int):
                    date_time = datetime.datetime.fromtimestamp(
                        params['selectDate']).strftime("%Y-%m-%d")
                    date_list = self.get_dates_between(
                        date_time, today_date.isoformat())
                    for date in date_list:
                        for ics in ics_data:
                            if ics.get('release_date') == date.strftime("%Y-%m-%d"):
                                filter_data.append(ics)
                    return filter_data
                elif re.match(pattern, params['selectDate']):
                    date_time = datetime.datetime.strptime(
                        params['selectDate'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
                    date_list = self.get_dates_between(
                        date_time, today_date.isoformat())
                    for date in date_list:
                        for ics in ics_data:
                            if ics.get('release_date') == date.strftime("%Y-%m-%d"):
                                filter_data.append(ics)
                    return filter_data
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
            else:
                logger.exception(
                    'Date Filter does not support value {0}'.format(params['date_filter']))
                raise Exception('Date Filter does not support value {0}'.format(
                    params['date_filter']))
        except Exception as err:
            logger.exception(str(err))
            raise ConnectorError(err)

    def get_dates_between(self, previous_date, current_date):
        previous_date = datetime.date.fromisoformat(previous_date)
        current_date = datetime.date.fromisoformat(current_date)

        # Initialize a list to store the dates
        dates_between = []

        # Add one more day on provided date
        previous_date += datetime.timedelta(days=1)

        # Iterate through each date between the previous and current date
        current = previous_date
        while current <= current_date:
            dates_between.append(current)
            current += datetime.timedelta(days=1)

        return dates_between

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

    def get_known_exploited_vulnerability_cves(self, kev_cve_url):
        response = requests.get(kev_cve_url)
        if response.status_code == 200:
	        return json.loads(response.text)


def get_advisory(config, params):
    try:
        advisory_obj = Advisory()
        yum_repo_url = advisory_obj.get_status(config)[1]
        advisory_type = ADVISORY_TYPE.get(params['advisory_type'])
        ics_data = advisory_obj.get_ics_data(advisory_type, yum_repo_url)
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
        advisory_obj = Advisory()
        yum_repo_url = advisory_obj.get_status(config)[1]
        advisory_type = ADVISORY_TYPE.get(params['advisory_type'])
        output = advisory_obj.get_ics_data_by_year(
            params, advisory_type, yum_repo_url)
        return sorted(output, key=lambda k: k['release_date'], reverse=True)
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)


def get_advisory_by_vendor(config, params):
    try:
        output = []
        advisory_obj = Advisory()
        yum_repo_url = advisory_obj.get_status(config)[1]
        advisory_type = ADVISORY_TYPE.get(params['advisory_type'])
        advisory_data = advisory_obj.get_ics_data(advisory_type, yum_repo_url)
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
        advisory_obj = Advisory()
        yum_repo_url = advisory_obj.get_status(config)[1]
        advisory_type = ADVISORY_TYPE.get(params['advisory_type'])
        advisory_data = advisory_obj.get_ics_data(advisory_type, yum_repo_url)
        for advisory in advisory_data:
            vendor_ratio = advisory_obj.set_ratio(
                str(params['vendor'].strip()), advisory['vendor'])
            product_ratio = advisory_obj.set_ratio(
                str(params['product'].strip()), advisory['product'])
            if vendor_ratio >= params['vendorSimilarityThreshold'] and product_ratio >= params[
                    'productSimilarityThreshold']:
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


def get_known_exploited_vulnerability_cves(config, params):
    try:
        advisory_obj = Advisory()
        yum_repo_url = advisory_obj.get_status(config)[1]
        kev_cve_url = yum_repo_url + CISA_KNOWN_EXPLOITED_VULNERABILITY_URL
        return advisory_obj.get_known_exploited_vulnerability_cves(kev_cve_url)
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)


def check_health(config):
    advisory = Advisory()
    return advisory.get_status(config)[0]


operations = {
    "get_advisory": get_advisory,
    "get_advisory_by_year": get_advisory_by_year,
    "get_advisory_by_vendor": get_advisory_by_vendor,
    "get_advisory_by_product": get_advisory_by_product,
    "get_known_exploited_vulnerability_cves": get_known_exploited_vulnerability_cves
}
