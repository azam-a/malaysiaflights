
import unittest
import datetime
import httpretty as HP
import json
from urllib.parse import parse_qsl

from malaysiaflights.aa import AirAsia as AA


class AARequestTests(unittest.TestCase):

    def url_helper(self, from_, to, date):

        host = 'https://argon.airasia.com'
        path = '/api/7.0/search'

        body = {'origin': from_,
                'destination': to,
                'depart': date,
                'passenger-count': '1',
                'infant-count': '0',
                'currency': 'MYR'}

        return host, path, body

    @HP.activate
    def test_search_calls_api_using_correct_path_and_body(self):
        host, path, body = self.url_helper('KUL', 'TGG', '18-06-2015')
        HP.register_uri(HP.POST, host+path, status=200)

        d = datetime.datetime(2015, 6, 18)
        AA.search('KUL', 'TGG', d)
        mocked_request = HP.last_request()
        actual_body = dict(parse_qsl(mocked_request.body.decode()))

        self.assertEqual(path, mocked_request.path)
        self.assertEqual(body, actual_body)


class ResponseExtractionTests(unittest.TestCase):

    def fixture_loader(self, path):
        prefix = 'malaysiaflights/fixtures/'
        with open(prefix + path, 'r') as file_:
            return json.loads(file_.read())

    def setUp(self):
        self.single = self.fixture_loader('aa-single.json')
        self.zero = self.fixture_loader('aa-no-flights.json')

    def test_get_number_of_results_for_valid_response(self):
        json = self.single
        actual = AA.get_number_of_results(json)
        self.assertEqual(4, actual)

    def test_get_number_of_results_for_no_flights_on_date(self):
        json = self.zero
        actual = AA.get_number_of_results(json)
        self.assertEqual(0, actual)

    def test_get_flight_details_using_index_0_should_return_results(self):
        json = self.single
        expected = {
            'flight_number': 'AK6225',
            'departure_airport': 'TGG',
            'arrival_airport': 'KUL',
            'departure_time': 'Sat, 20 Jun 2015 08:20:00 +0800',
            'arrival_time': 'Sat, 20 Jun 2015 09:15:00 +0800',
            'total_fare': 133.99,
            'fare_currency': 'MYR'}
        actual = AA.get_direct_flight_details(json, 0)
        self.assertEqual(expected, actual)

    def test_get_flight_details_using_index_1_should_return_results(self):
        json = self.single
        expected = {
            'flight_number': 'AK6229',
            'departure_airport': 'TGG',
            'arrival_airport': 'KUL',
            'departure_time': 'Sat, 20 Jun 2015 13:10:00 +0800',
            'arrival_time': 'Sat, 20 Jun 2015 14:05:00 +0800',
            'total_fare': 133.99,
            'fare_currency': 'MYR'}
        actual = AA.get_direct_flight_details(json, 1)
        self.assertEqual(expected, actual)

    @unittest.skip('no-data-yet')
    def test_is_connecting_flights_should_return_true_for_connecting(self):
        json = ''
        actual = AA.is_connecting_flights(json, 0)
        self.assertTrue(actual)

    def test_is_connecting_flights_should_return_false_for_direct(self):
        json = self.single
        actual = AA.is_connecting_flights(json, 2)
        self.assertFalse(actual)


class TimeConversionTest(unittest.TestCase):

    def test_convert_to_api_format_returns_correct_output(self):
        date_object = datetime.datetime(2015, 9, 25)
        expected = '25-09-2015'
        actual = AA.to_api(date_object)
        self.assertEqual(expected, actual)

    def test_convert_extracted_time_to_datetime_returns_correct_object(self):
        offset = datetime.timedelta(hours=8)
        expected = datetime.datetime(2015, 6, 20, 13, 10,
                                     tzinfo=datetime.timezone(offset))
        actual = AA.to_datetime('Sat, 20 Jun 2015 13:10:00 +0800')
        self.assertEqual(expected, actual)
