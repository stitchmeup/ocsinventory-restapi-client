""" Class for OCS Inventory REST API Client. """

import json
from requests import Session, Response, ConnectionError
import time
from typing import Any, Union, Text


class Client(Session):
    """
    OCS Inventory REST API Client.
    Inherit from requests.Session.
    """

    def __init__(self, base_url: str, auth: tuple = None) -> None:
        """
        :param base_url: type`str` Base URL to OCS Inventory API.
        :param auth: type`tuple` username and password for BASIC Authentication.
        """
        super().__init__()
        self.base_url = base_url
        self.auth = auth
        self.verify = False

    # Requests
    # GET
    def get(self, url: Union[Text, bytes], **kwargs: Any) -> Response:
        """
        Override get method to add retry 3 times on ConnecectionError.
        :param url: :type:`Union[Text, bytes]` URL to get.
        :param kwargs: :type:`Any` arguments to pass to Session.get.
        :rtype: Response
        """
        for i in range(3):
            try:
                return super().get(url, **kwargs)
            except ConnectionError as e:
                time.sleep(0.5)
                if i == 2:
                    raise e

    def get_computers_id(self) -> Response:
        """
        Get list of computers ID.
        :rtype: requests.Response
        """
        url: str = self.base_url + '/computers/listID'
        return self.get(url)

    def get_computer_details(self, computer_id: int) -> Response:
        """
        Get one computer details.
        :param id: :type:`int` computer id.
        :rtype: requests.Response
        """
        url: str = self.base_url + '/computer/' + str(computer_id)
        return self.get(url)

    def get_computers_details(self, start: int, limit: int) -> Response:
        """
        Get computers details.
        :param start: :type:`int` start index.
        :param limit: :type:`int` limit in index to look for.
        :rtype: requests.Response
        """
        url: str = self.base_url + '/computers'
        params: {str, str | int} = {
            'start': start,
            'limit': limit
        }
        return self.get(url, params=params)

    def get_computers_search(self, start: int, limit: int, search_criteria: str, search_value: str) -> Response:
        """
        Get computers for which the search value match the search criteria.
        :param start: :type:`int` start index.
        :param limit: :type:`int` limit in index to look for.
        :param search_criteria: :type:`str` search criteria to look for. Search criteria must be in the hardware table.
        :param search_value: :type:`str` search value with exact match.
        :rtype: requests.Response
        Search criteria:
            "ARCH"
            "ARCHIVE"
            "CATEGORY_ID"
            "CHECKSUM"
            "DEFAULTGATEWAY"
            "DESCRIPTION"
            "DEVICEID"
            "DNS"
            "ETIME"
            "FIDELITY"
            "ID"
            "IPADDR"
            "IPSRC"
            "LASTCOME"
            "LASTDATE"
            "MEMORY"
            "NAME"
            "OSCOMMENTS"
            "OSNAME"
            "OSVERSION"
            "PROCESSORN"
            "PROCESSORS"
            "PROCESSORT"
            "QUALITY"
            "SSTATE"
            "SWAP"
            "TYPE"
            "USERAGENT"
            "USERDOMAIN"
            "USERID"
            "UUID"
            "WINCOMPANY"
            "WINOWNER"
            "WINPRODID"
            "WINPRODKEY"
            "WORKGROUP"
        """
        url: str = self.base_url + '/computers/search'
        params: {str, str | int} = {
            'start': start,
            'limit': limit,
            search_criteria: search_value,
        }
        return self.get(url, params=params)

    # Helpers
    # Instance Methods
    def total_nb_computers(self) -> int:
        """
        Return the total number of computers.
        :rtype: `int`
        """
        res: Response = self.get_computers_id()
        ids: [{str, str | int}] = res.text
        return len(json.loads(ids))

    def search_in_all_computers(self, search_criteria: str, search_value: str) -> Response:
        """
        Get computers for which the search value match the search criteria in all computers.
        :param search_criteria: :type:`str` search criteria to look for. Search criteria must be in the hardware table.
        :rtype: requests.Response
        Wrapper of `get_computers_search()` (see its doc for search criteria's list).
        """
        return self.get_computers_search(0, self.total_nb_computers(), search_criteria, search_value)

    def list_computers_id(self) -> [int]:
        response: requests.Response = self.get_computers_id()
        if self.is_response_valid(response):
            return [computer_id['ID'] for computer_id in self.response_to_collection(response)]
        else:
            self._raise_api_error()

    def computers_by_tag(self, tag: str) -> [dict]:
        """
        Return list of computers with a given tag.
        :param tag: :type:`str` tag to look for.
        :rtype: `list`
        """
        computers: [dict] = []
        for computer_id in self.list_computers_id():
            response: Response = self.get_computer_details(computer_id)
            if self.is_response_valid(response):
                computer_details: {str, object} = self.response_to_collection(response)
                if self.computer_has_tag(computer_details, tag):
                    computers.append(computer_details)
            else:
                self._raise_api_error()
        return computers

    def computers_by_software(self, software_criteria: str, software_value: str) -> [dict]:
        """
        Return list of computers with a given software name.
        :param software_criteria: :type:`str`
        :param software_value: :type:`str`
        :rtype: `list`
        Search Criteria:
            "BITSWIDTH"
            "COMMENTS"
            "FILENAME"
            "FILESIZE"
            "FOLDER"
            "GUID"
            "HARDWARE_ID"
            "ID"
            "INSTALLDATE"
            "LANGUAGE"
            "NAME"
            "PUBLISHER"
            "SOURCE"
            "VERSION"
        """
        computers: [dict] = []
        for computer_id in self.list_computers_id():
            response: Response = self.get_computer_details(computer_id)
            if self.is_response_valid(response):
                computer_details: {str, object} = self.response_to_collection(response)
                if self.computer_has_software(computer_details, software_criteria, software_value):
                    computers.append(computer_details)
            else:
                self._raise_api_error()
        return computers

    # Static Methods
    @staticmethod
    def extract_computer_id(computer_details: dict) -> str:
        """
        Return the computer id found in computer details (hardware > NAME)
        :param computer_details: :type:`dict` Computers details can be obtained by instance method `get_computer_details()`.
        :rtype: `str`
        """
        return [key for key in computer_details.keys()][0]

    @staticmethod
    def extract_computer_name(computer_details: dict) -> str:
        """
        Return the computer name found in computer details (hardware > NAME)
        :param computer_details: :type:`dict` Computers details can be obtained by instance method `get_computer_details()`.
        :rtype: `str`
        """
        computer_id: str = Client.extract_computer_id(computer_details)
        return computer_details[computer_id]['hardware']['NAME']

    @staticmethod
    def computer_has_tag(computer_details: dict, search_tag: str) -> bool:
        """
        Return True if tag in computer_details.
        :param computer_details: :type:`dict` Computers details can be obtained by instance method `get_computer_details()`.
        :param search_tag: :type:`str` search tag to look for.
        :rtype: `bool`
        """
        computer_id = [key for key in computer_details.keys()][0]
        accountinfo: [dict] = computer_details[computer_id]['accountinfo']
        if len(accountinfo) == 0:
            return False
        tags: str = accountinfo[0]['TAG']
        return search_tag in tags

    @staticmethod
    def computer_has_software(computer_details: dict, software_criteria: str, software_value: str) -> bool:
        """
        Return True if software in computer_details.
        :param computer_details: :type:`dict` Computers details can be obtained by instance method `get_computer_details()`.
        :param software_criteria: :type:`str`
        :param software_value: :type:`str`
        :rtype: `bool`
        """
        computer_id = [key for key in computer_details.keys()][0]
        softwares: [dict] = computer_details[computer_id][""]
        if len(softwares) != 0:
            for soft in softwares:
                try:
                    if software_value in soft[software_criteria]:
                        return True
                except TypeError:
                    pass
        return False

    @ staticmethod
    def is_response_valid(response: Response) -> bool:
        """
        Return true if response's HTTP status code is 200.
        :param response: type`requests.Response`
        :rtype: `bool`
        """
        return getattr(response, 'status_code') == 200

    @staticmethod
    def response_to_collection(response: Response) -> Any:
        """
        Return the transformation of the response's body in a collection using json module.
        :param response: type`requests.Response`
        :rtype: Any
        """
        return json.loads(response.text)

    @staticmethod
    def _raise_api_error(response: Response) -> None:
        raise RuntimeError(
            response,
            getattr(response, "status_code"),
            "Error with OCS Inventory REST API."
        )
