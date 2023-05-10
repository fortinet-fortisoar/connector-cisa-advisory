import json
import requests
from bs4 import BeautifulSoup
import datetime
from dateutil.relativedelta import relativedelta
from connectors.core.connector import get_logger, ConnectorError
from .constant import *
from integrations.crudhub import make_request

logger = get_logger('cisa-advisory')

class Advisory():

    def __init__(self, url):
         self.url = url

    def get_ics_data(self):
        try:
            ics_advisory_url_by_year_links_list = []
            output = []
            response = requests.get(self.url, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a'):
                if 'ics-advisory' in link.get('href'):
                    ics_advisory_url_by_year_links_list.append(link.get('href'))
            for advisory_link in ics_advisory_url_by_year_links_list:
                json_file_data = requests.get(self.url + advisory_link, verify=False)
                for item in json.loads(json_file_data.text):
                    output.append(item)
            return output
        except Exception as err:
            logger.exception(str(err))
            raise ConnectorError(err)

    def date_filter_advisory(self, params, ics_data):
        try:
            today_date = datetime.date.today()
            if params['date_filter'] == 'Today':
                filter_ics_advisory_data = [ics for ics in ics_data if ics.get('release_date') == str(today_date)]
                return filter_ics_advisory_data
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
                last_month_end_date = today_date.replace(day=1) - datetime.timedelta(days=1)
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
                        filter_ics_advisory = [ics for ics in ics_data if ics.get('release_date') == last_publish_date]
                        return filter_ics_advisory
                    else:
                        today_date += delta
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

def get_ics_advisory(config, params):
    try:
        ics_advisory_url = REPO_URL + 'ics-advisory/'
        advisory_obj = Advisory(ics_advisory_url)
        ics_data = advisory_obj.get_ics_data()
        if params['date_filter']:
            return advisory_obj.date_filter_advisory(params, ics_data)
        else:
            return ics_data
    except Exception as err:
        logger.exception(str(err))
        raise Exception(err)

def get_ics_advisory_by_vendor(config, params):
    try:
        output = []
        ics_advisory_url = REPO_URL + 'ics-advisory/'
        advisory_obj = Advisory(ics_advisory_url)
        ics_advisory_data = advisory_obj.get_ics_data()
        for advisory in ics_advisory_data:
            if params['vendor'].strip().lower() == advisory['vendor'].lower() or params['vendor'].strip().lower() in \
                    advisory['vendor'].lower():
                output.append(advisory)
        return output
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)

def get_ics_advisory_by_product(config, params):
    try:
        output = []
        ics_advisory_url = REPO_URL + 'ics-advisory/'
        advisory_obj = Advisory(ics_advisory_url)
        ics_advisory_data = advisory_obj.get_ics_data(ics_advisory_url, params)
        for advisory in ics_advisory_data:
            if params['product'].strip().lower() == advisory['product'].lower() or params['product'].strip().lower() in \
                    advisory['product'].lower():
                if params['version'].strip() != "":
                    if params['version'].strip() in advisory['affected_product']:
                        output.append(advisory)
                    else:
                        continue
                else:
                    output.append(advisory)
        return output
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)

def get_ics_advisory_by_year(config, params):
    try:
        ics_advisory_url_by_year = REPO_URL + 'ics-advisory/' + str(params['year']) + '-ics-advisory.json'
        json_file_data = requests.get(ics_advisory_url_by_year, verify=False)
        return json.loads(json_file_data.text)
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)

def get_ics_medical_advisory(config, params):
    try:
        ics_medical_advisory_url = REPO_URL + 'ics-medical-advisory/'
        advisory_obj = Advisory(ics_medical_advisory_url)
        ics_data = advisory_obj.get_ics_data()
        if params['date_filter']:
            return advisory_obj.date_filter_advisory(params, ics_data)
        else:
            return ics_data
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)

def get_ics_medical_advisory_by_vendor(config, params):
    try:
        output = []
        ics_advisory_url = REPO_URL + 'ics-medical-advisory/'
        advisory_obj = Advisory(ics_advisory_url)
        ics_advisory_data = advisory_obj.get_ics_data()
        for advisory in ics_advisory_data:
            if params['vendor'].strip().lower() == advisory['vendor'].lower() or params['vendor'].strip().lower() in \
                    advisory['vendor'].lower():
                output.append(advisory)
        return output
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)

def get_ics_medical_advisory_by_product(config, params):
    try:
        output = []
        ics_advisory_url = REPO_URL + 'ics-medical-advisory/'
        advisory_obj = Advisory(ics_advisory_url)
        ics_advisory_data = advisory_obj.get_ics_data(ics_advisory_url, params)
        for advisory in ics_advisory_data:
            if params['product'].strip().lower() == advisory['product'].lower() or params['product'].strip().lower() in \
                    advisory['product'].lower():
                if params['version'].strip() != "":
                    if params['version'].strip() in advisory['affected_product']:
                        output.append(advisory)
                    else:
                        continue
                else:
                    output.append(advisory)
        return output
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)

def get_ics_medical_advisory_by_year(config, params):
    try:
        ics_advisory_url_by_year = REPO_URL + 'ics-medical-advisory/' + str(params['year']) + '-ics-medical-advisory.json'
        json_file_data = requests.get(ics_advisory_url_by_year, verify=False)
        return json.loads(json_file_data.text)
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError(err)

def check_health(config):
    module_name = 'i_c_s_advisories'
    try:
        make_request('/api/3/{}'.format(module_name), 'GET')
        return True
    except Exception as err:
        logger.exception(str(err))
        raise ConnectorError("ICS Advisory modules is not present in environment")

operations = {
    "get_ics_advisory": get_ics_advisory,
    "get_ics_advisory_by_vendor": get_ics_advisory_by_vendor,
    "get_ics_advisory_by_year": get_ics_advisory_by_year,
    "get_ics_advisory_by_product": get_ics_advisory_by_product,
    "get_ics_medical_advisory": get_ics_medical_advisory,
    "get_ics_medical_advisory_by_vendor": get_ics_medical_advisory_by_vendor,
    "get_ics_medical_advisory_by_year": get_ics_medical_advisory_by_year,
    "get_ics_medical_advisory_by_product": get_ics_medical_advisory_by_product
}
