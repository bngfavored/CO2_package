# -*- coding: utf-8 -*-
"""
Created on Sat Aug 27 20:51:25 2022

@author: los317
"""
import aranet4.client as a45
import ezsheets
import asyncio
import time
import nest_asyncio
nest_asyncio.apply()

device_mac = "60:C0:BF:48:38:5F"


        
for _ in range(20):
    current = None
    try:
        current = a45.get_current_readings(device_mac)
        print(current)
        time.sleep(20)
        ss = ezsheets.Spreadsheet('1Qy50hjGlFpIjRcMscfFQTwYzs7mZqtBS-BJhs0jDRCU')
        sheet = ss[0] 
        sheet ['l12'] = current.co2
    except TimeoutError:
        print("I am sleeping 20 seconds")
        time.sleep(20)
        current = a45.get_current_readings(device_mac)
        
   # print(current)
   # wait = current.interval - current.ago
 #   print(f'the wait is {wait}')
   # for i in range(wait, 0, -1):
     #   time.sleep(1)
     #   print(f"I have {i} more seconds to wait.")
    #time.sleep(5)

 

# s




