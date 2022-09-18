# -*- coding: utf-8 -*-
"""
Created on Sat Aug 27 20:51:25 2022

@author: los317
"""

from collections import ChainMap
import socket
import aranet4.client as a45
import asyncio
import time
import nest_asyncio
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import atexit
import RPi.GPIO as GPIO
import os
import requests
nest_asyncio.apply()


START = True
class TimeKeeper:
    def __init__(self) -> None:
        self.datetime = self.get_datetime()

    def get_datetime(self,timezone:str = "America/New_York") -> datetime:
        url = 'https://timeapi.io/api/Time/current/zone'
        payload = dict(timeZone=timezone)
        self.r = requests.get(url, params=payload)
        if self.r.ok:
            try:
                current_time = datetime.fromisoformat(self.r.json()['dateTime'].split('.')[0].replace('T'," "))
            except KeyError:
                current_time = datetime.now()
        return current_time


class GoogleSheet:

    def __init__(self, spreadsheet_id:str, data_sheet_name:str = '') -> None:
        self.sheet_id = spreadsheet_id
        self.SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        self.creds = service_account.Credentials.from_service_account_file(
                "key.json", scopes=self.SCOPES)
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.get_sheet_names()
        self.respond_time = 0
        self.range_name = ''
        if data_sheet_name:
            self.data_sheet_name = data_sheet_name
        self.data = [[]]
    
    @property
    def ach(self) -> float:
        value = self.get_first_value_last_row(self.sheet_ach)
        self._ach = float(value if value != '' else 0) 
        print(self._ach)
        return self._ach
           
    @property
    def eAch(self) -> float:
        value = self.get_first_value_last_row(self.sheet_eAch)
        self._eAch = float(value if value != '' else 0) 
        print(self._eAch)
        return self._eAch
    
    @property
    def data_sheet_name(self) -> str:
        return self._data_sheet_name

    @data_sheet_name.setter
    def data_sheet_name(self, value:str) -> None:
        self._data_sheet_name = self.find_sheet(value)
        self.sheet_range = f"'{self._data_sheet_name}'!A:I"
        self.sheet_eAch = f"'{self._data_sheet_name}'!K:K"
        self.sheet_ach = f"'{self._data_sheet_name}'!J:J"

    def get_sheet_names(self) -> None:
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.sheet_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        self.sheet_names = [sheet.get("properties", {}).get("title", "Sheet1") for sheet in sheets]

    def find_sheet(self, sensor_name:str) -> str:
        name = sensor_name.split(' ')[-1].strip()
        for sheet_name in self.sheet_names:
            if name in sheet_name:
                print(f'sheet found for sensor: {sensor_name} is {sheet_name}')
                return sheet_name
        return ''

    def get_values(self, range_name:str = None) -> list:
        """
        Creates the batch_update the user has access to.
        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
            """
        # pylint: disable=maybe-no-member
        if range_name:
            self.range_name = range_name
        elif self.range_name == '':
            raise ValueError(f"{self.__name__} is missing 'range_name' agrugment")
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id, range=self.range_name).execute()
            rows = result.get('values', [])
            print(f"{len(rows)} rows retrieved")
            return result.get('values', [])
        except HttpError as error:
            print(f"An error occurred: {error}")
            return error
         
            
    def get_last_row_values(self, range_name:str) -> list:
        data = self.get_values(range_name)
        if data:
            return data[-1]
        return []
        
    def get_first_value_last_row(self, range_name:str) -> str:
        data = self.get_last_row_values(range_name)
        if data:
            return data[0]
        return ''
        
    def append_values(self, range_name:str, value_input_option:str = "USER_ENTERED",
                      values:list = None) -> bool:
        """
        Creates the batch_update the user has access to.
        Parameters:
            spreadsheet_id: A string that contains the spreadsheet's id. For example, the url "https://docs.google.com/spreadsheets/d/1CM29gwKIzeXsAppeNwrc8lbYaVMmUclprLuLYuHog4k/edit" the characters 
                            between /d/{spreadsheet's id}/ gives you this "1CM29gwKIzeXsAppeNwrc8lbYaVMmUclprLuLYuHog4k".
            range_name: A range in the "A1:B1" format.
            value_input_option: Allows you to select how the sheet will treat the data entered. For example, "USER_ENTERED" will have the sheet behave as if you typed it in manually.
            _values: The values to be added to the sheet in a 2-d list i.e. [[col1, col2, col3], [col1, col2, col3]] where each list of the list will be a row and the elements are the column entries. 
        """

        if values is None:
            return
            

        # pylint: disable=maybe-no-member
        sheet_data = self.get_first_value_last_row(range_name)
        if sheet_data and sheet_data == values[0][0].replace(" 0"," "):
            print("Timestamp is already in the sheet.")
            return
        try:
            body = {
                'values': values
            }

            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id, range=range_name,
                valueInputOption=value_input_option, body=body).execute()
            print(f"{(result.get('updates').get('updatedCells'))} cells appended.")
            return True

        except HttpError as error:
            print(f"An error occurred: {error}")
            return False

class Pi_Pin:
    def __init__(self, pin:int = 4, initial_state:int = GPIO.LOW) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT, initial=initial_state)
        self.pin = pin
        self.state = initial_state
            
    def on(self) -> None:
        GPIO.output(self.pin, GPIO.HIGH)
        self.state = GPIO.input(self.pin)
        
    def off(self) -> None:
        GPIO.output(self.pin, GPIO.LOW)
        self.state = GPIO.input(self.pin)

def get_current_data(DATA:dict, COLUMNS:tuple) -> int:
    '''
        refactor
    '''
    
    # Get the IP Address
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        DATA['IP Address'] = s.getsockname()[0]
        print('IP Address:', DATA['IP Address'])
    print("I am getting the readings.")
    date_format = '%m-%d-%Y %I:%M %p'
    current_time = TimeKeeper().datetime
    current = a45.get_current_readings(DATA["mac"])
    DATA['datetime'] = (current_time - timedelta(seconds=current.ago)).strftime(date_format)
    # The chains the dicts together so if the underlining data changes this will update too.
    merged_data = ChainMap(DATA, current.__dict__)
    output_data = [[merged_data[key] for key in COLUMNS]]
    print(COLUMNS)
    print(output_data)
    return (output_data, current.interval - current.ago)


def upload_data(current_sheet:GoogleSheet, data:list) -> bool:
    name = data[0][-1]
    current_sheet.data_sheet_name = name
    result = current_sheet.append_values(range_name=current_sheet.sheet_range, values=data)
    time.sleep(1)
    return result

    
def main() -> None:
    SENSOR_MAC = os.getenv('SENSOR_MAC')
    if not SENSOR_MAC:
        print("SENSOR_MAC is not set.")
        SENSOR_MAC = "60:C0:BF:47:0B:F5"
    # When megred these are all the keys ['mac', 'IP Address', 'name', 'version', 'temperature', 'humidity', 'pressure', 'co2', 'battery', 'status', 'interval', 'ago', 'stored'] 
    #Made a tuple which saves space
    COLUMNS = ('datetime', 'co2', 'humidity', 'temperature', 'pressure', 'battery', 'IP Address', 'mac', 'name')
    #Setup Google Sheet object and Pi GPIO object
    SHEET_ID = '11RJhNU1jugQpyD05fOoiRYSxE6Wky70YfcveI7yvaP0' #New Sheet
    # SHEET_ID = '1Qy50hjGlFpIjRcMscfFQTwYzs7mZqtBS-BJhs0jDRCU'
    current_sheet = GoogleSheet(SHEET_ID)
    DATA = dict(mac = SENSOR_MAC)
    pin_obj = Pi_Pin()
    while START:
        try:
            current_data, wait_time_offset = get_current_data(DATA, COLUMNS)
        except TimeoutError:
            print("I am sleeping 20 seconds and trying again")
            time.sleep(20)
            current_data, wait_time_offset = get_current_data(DATA, COLUMNS)
        
        # wait = get_current_data(current_sheet, DATA, COLUMNS, pin_obj)
        start_time = time.time()
        if upload_data(current_sheet, current_data):
            current_ach = current_sheet.ach
            current_eAch = current_sheet.eAch
            ach_offset = current_eAch - 5 if current_eAch > 5 else 5
            if current_ach >= ach_offset and pin_obj.state == GPIO.HIGH:
                print(f"{current_ach} is less than 5 air changes per hour and turning on fan.")
                pin_obj.on()
            else:
                pin_obj.off()
        wait_time = wait_time_offset - round(start_time - time.time())
        wait_time = 20 if wait_time < 0 else wait_time

        # print(current)
        print(f'the wait is {wait_time}')
        step = 10
        for i in range(wait_time, 0, -1*step):
            time.sleep(step)
            print(f"I have {i-step} more seconds to wait.")

        
if __name__ == '__main__':
    main()
