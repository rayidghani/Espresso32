from google.auth import ServiceAccount
from google.sheet import Spreadsheet
from config import Config
import gc
import time
import util
import sys
import uerrno
import esp32
import time
from machine import Pin, I2C, SPI, ADC
import ssd1306
from time import sleep
from hx711 import HX711


def test():

    # enable garbage collection
    gc.enable()
    print('garbage collection threshold: ' + str(gc.threshold()))

    # load configuration for a file
    config = Config('main.conf', 'key.json')

    # create an instance of ServiceAccount class
    # which then is going to be used to obtain an OAuth2 token
    # for writing data to a sheet
    sa = ServiceAccount()
    sa.email(config.get('google_service_account_email'))
    sa.scope('https://www.googleapis.com/auth/spreadsheets')
    sa.private_rsa_key(config.private_rsa_key())

    # create an instance of Spreadsheet which is used to write data to a sheet
    spreadsheet = Spreadsheet()
    spreadsheet.set_service_account(sa)
    spreadsheet.set_id(config.get('google_sheet_id'))
    spreadsheet.set_range('A:A')

    while 1:
        a=esp32.hall_sensor()   # read the internal hall sensor
        time.sleep(1)
        spreadsheet.append_values([a])

def initialize_google_sheets():
       # load configuration for a file
    config = Config('main.conf', 'key.json')

    # create an instance of ServiceAccount class
    # which then is going to be used to obtain an OAuth2 token
    # for writing data to a sheet
    sa = ServiceAccount()
    sa.email(config.get('google_service_account_email'))
    sa.scope('https://www.googleapis.com/auth/spreadsheets')
    sa.private_rsa_key(config.private_rsa_key())

    # create an instance of Spreadsheet which is used to write data to a sheet
    spreadsheet = Spreadsheet()
    spreadsheet.set_service_account(sa)
    spreadsheet.set_id(config.get('google_sheet_id'))
    spreadsheet.set_range('A:A')
    return spreadsheet


def hall_sensor():
    while 1:
        print(esp32.hall_sensor())
        time.sleep(1)

def get_temperature():
    print(esp32.raw_temperature())


def start_timer(start_threshold):
    #print(esp32.hall_sensor())
    if (esp32.hall_sensor() > start_threshold):
        return 1
    else:
        return 0


def stop_timer(stop_threshold):
    #print(esp32.hall_sensor())
    if (esp32.hall_sensor() < stop_threshold):
        return 1
    else:
        return 0


def manage_timer(start_threshold, stop_threshold, show_oled = 1):
    # change to 1) get initial value at start 2) if it goes 20 above start 3) if it gets ot within 5% of initial stop
    # initial_temperature = esp32.hall_sensor()
    # start_threshold = initial_temperature + 15
    # stop_threshold = initial_temperature + 3

    if show_oled:
        oled_i2c = init_spi()
    while 1:
        time.sleep(1)
        if start_timer(start_threshold):
            print("Starting timer")
            num_seconds=0
            while not stop_timer(stop_threshold):
                time.sleep(1)
                num_seconds+=1
                print(num_seconds) # print to display
                if show_oled:
                    write_to_oled(oled_i2c, num_seconds)
            print("timer stopped")
            sheet = initialize_google_sheets()
            sheet.append_values([num_seconds])

def init_oled():
    # ESP32 Pin assignment 
    i2c = I2C(-1, scl=Pin(22), sda=Pin(21))

    # ESP8266 Pin assignment
    #i2c = I2C(-1, scl=Pin(5), sda=Pin(4))

    oled_width = 128
    oled_height = 64
    oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
    return oled


def write_to_oled(oled,message):

    oled.fill(0)
    oled.show()
    oled.text(str(message), 0, 0)
    oled.show()


def test_oled():
    # ESP32 Pin assignment 
    #i2c = I2C(-1, scl=Pin(22), sda=Pin(21))

    # ESP8266 Pin assignment
    #i2c = I2C(-1, scl=Pin(5), sda=Pin(4))

    #oled_width = 128
    #oled_height = 64
    #oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
    oled = init_spi()
    oled.text('rtew', 0, 0)
    oled.show()


def scan_oled():
    # ESP32 Pin assignment 
    i2c = I2C(-1, scl=Pin(22), sda=Pin(21))

    # ESP8266 Pin assignment
    #i2c = I2C(-1, scl=Pin(5), sda=Pin(4))
    print(i2c.scan())



def init_spi():
    spi = SPI(-1, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
    # ESP8266 Pin assignment
    #i2c = I2C(-1, scl=Pin(5), sda=Pin(4))

    oled_width = 128
    oled_height = 64
    oled = ssd1306.SSD1306_SPI(oled_width, oled_height, spi, dc=Pin(17), cs=Pin(5), res=Pin(16))
    return oled

def test_raw_weight():
    pot = ADC(Pin(39))
    pot.atten(ADC.ATTN_11DB)      
    pot2 = ADC(Pin(36))
    pot2.atten(ADC.ATTN_11DB)   

    while True:
      pot_value = pot2.read()-pot.read()
      print(pot_value)
      sleep(0.1)

def init_weight():
    hx711 = HX711(14, 27)
    hx711.set_scale(9100/5.9)
    hx711.tare()
    return hx711


def get_weight(hx711):
    return hx711.get_units()




