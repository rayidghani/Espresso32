from google.auth import ServiceAccount
from google.sheet import Spreadsheet
from config import Config
import gc
import util
import sys
import uerrno
from machine import Pin, I2C, SPI, ADC
import ssd1306
from hx711 import HX711
from writer import writer, freesans20, newyork30, arial28
import ntp
import ntptime
import machine
import esp32
import time


def initialize_google_sheets():
    # things to remember: 
    # create google service account
    # create key in web interface
    # convert key to rsa
    # enable apis
    # get email address for service account

    # enable garbage collection
    gc.enable()
    print('garbage collection threshold: ' + str(gc.threshold()))

    # load configuration for a file
    config = Config('main.conf', 'key.json')

    # create an instance of ServiceAccount class
    # which then is going to be used to obtain an OAuth2 token
    # for writing data to a sheet
    sa = ServiceAccount()
    # this is not your gmail address - it is a service account address
    sa.email(config.get('google_service_account_email'))
    sa.scope('https://www.googleapis.com/auth/spreadsheets')

    # sh extract_key.sh ../stone-host-164605-297e1653f579.json ../key.json
    # need to convert json key to rsa key with this script
    sa.private_rsa_key(config.private_rsa_key())

    # create an instance of Spreadsheet which is used to write data to a sheet
    spreadsheet = Spreadsheet()
    spreadsheet.set_service_account(sa)
    spreadsheet.set_id(config.get('google_sheet_id'))
    spreadsheet.set_range('A:A')
    return spreadsheet


def write_google(a):
    sheet = initialize_google_sheets()
    #time_weight_pairs.insert(start_time,5,6.5)
    sheet.append_values(a)


######################################
#####  hall sensor functions #########
######################################


def hall_sensor_internal_loop_print():
    while 1:
        print(esp32.hall_sensor())
        time.sleep(1)

def start_timer_internal_hall(start_threshold):
    #print(esp32.hall_sensor())
    if (esp32.hall_sensor() > start_threshold):
        return 1
    else:
        return 0

def stop_timer_internal_hall(stop_threshold):
    #print(esp32.hall_sensor())
    if (esp32.hall_sensor() < stop_threshold):
        return 1
    else:
        return 0

def start_timer_external_hall(pinid=34):
    #print(esp32.hall_sensor())
    # set up at  gpio34
    value = ADC(Pin(pinid,Pin.IN, Pin.PULL_UP)).read()
    if (value == 0):
        return 1
    else:
        return 0

def stop_timer_external_hall(pinid=34):
    #print(esp32.hall_sensor())
    # set up at  gpio34
    value = ADC(Pin(pinid, Pin.IN, Pin.PULL_UP)).read()
    if (value == 4095):
        return 1
    else:
        return 0


######################################
########### oled  functions ##########
######################################


# oled - ssd1306 with vspi

def init_spi_oled():
    spi = SPI(-1, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
    # ESP8266 Pin assignment
    #i2c = I2C(-1, scl=Pin(5), sda=Pin(4))

    oled_width = 128
    oled_height = 64
    oled = ssd1306.SSD1306_SPI(oled_width, oled_height, spi, dc=Pin(17), cs=Pin(5), res=Pin(16))
    return oled


def init_i2c_oled():
    # not used 
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
    oled = init_spi_oled()
    oled.text('rtew', 0, 0)
    oled.show()


def scan_oled():
    # ESP32 Pin assignment 
    i2c = I2C(-1, scl=Pin(22), sda=Pin(21))

    # ESP8266 Pin assignment
    #i2c = I2C(-1, scl=Pin(5), sda=Pin(4))
    print(i2c.scan())

def write_to_oled_with_font(ssd, message, fontname):
    ssd.fill(0)
    #rhs = 128 -1
    #ssd.line(rhs - 20, 0, rhs, 20, 1)
    #square_side = 10
    #ssd.fill_rect(rhs - square_side, 0, square_side, square_side, 1)
    wri = writer.Writer(ssd, fontname)
    writer.Writer.set_textpos(ssd, 0, 0)  # verbose = False to suppress console output
    wri.printstring(message)
    ssd.show()


######################################
#########  weight  functions #########
######################################


# weights hx711 and load cell

def init_weight():
    hx711 = HX711(14, 27)
    hx711.set_scale(9100/5.9)
    hx711.tare()
    return hx711


def test_raw_weight():
    pot = ADC(Pin(39))
    pot.atten(ADC.ATTN_11DB)      
    pot2 = ADC(Pin(36))
    pot2.atten(ADC.ATTN_11DB)   

    while True:
      pot_value = pot2.read()-pot.read()
      print(pot_value)
      time.sleep(0.1)


def get_weight(hx711):
    # takes tared and calibrated and returns weight in grams
    return hx711.get_units()

def print_weight(hx711,ssd, fontname):
    weight = get_weight(hx711)
    write_to_oled_with_font(ssd, str(weight) + 'g', fontname)


 
######################################
########  misc functions #########
######################################


def print_temperature():
    print(esp32.raw_temperature())


def get_localtime_as_string():
    ntptime.settime()
    year, month, day, hour, minute, second, ms, dayinyear = time.localtime()
    time_as_string = str(year)+'/'+str(month)+'/'+str(day)+' '+str(hour)+':'+str(minute)+':'+str(second)
    return time_as_string



def read_a2d(pinid):
    pot = ADC(Pin(pinid,Pin.IN, Pin.PULL_UP))
    #pot.atten(ADC.ATTN_11DB)
    print(pot.read())


def loop_read_a2d(pinid):
    while 1:
        read_a2d(pinid)
        time.sleep(1)

def test_sleep():
    print("awake but going to sleep")
    machine.deepsleep()


def init_sleep():
 t = machine.TouchPad(machine.Pin(14))       # assign touch pin 14 to t
 t.config(300)               # configure the threshold at which the pin is considered touched
 esp32.wake_on_touch(True)   # enable wake_on_touch
 return t




######################################
########  printing functions #########
######################################



def print_time_weight(write_to_google_sheet=0):
    # change to 1) get initial value at start 2) if it goes 20 above start 3) if it gets ot within 5% of initial stop
    # initial_temperature = esp32.hall_sensor()
    # start_threshold = initial_temperature + 15
    # stop_threshold = initial_temperature + 3

    oled_i2c = init_spi_oled()
    hx711 = init_weight()
    #start_threshold = 100
    #stop_threshold = 80
    sheet = initialize_google_sheets()
    ntptime.settime()
    polling_interval=0.1
    idle_time=0
    write_to_oled_with_font(oled_i2c, 'Espresso32', freesans20)

    while 1:
        time.sleep(polling_interval)
        idle_time+=polling_interval
        if idle_time > 120:
            write_to_oled_with_font(oled_i2c, 'sleeping', freesans20)
            time.sleep(5)
            t=init_sleep()
            # machine.lightsleep()
            machine.deepsleep()

        # if start_timer(start_threshold):
        if start_timer_external_hall():
            print("Starting timer")
            start_time = get_localtime_as_string()
            num_seconds=0
            weight=0
            time_weight_pairs=[]
            time_weight_pairs.append([start_time,num_seconds,weight])
            # while not stop_timer(stop_threshold):
            while not stop_timer_external_hall():
                time.sleep(1)
                num_seconds+=1
                weight = round(get_weight(hx711),2)
                time_weight_pairs.append([start_time,num_seconds,weight])
                print(num_seconds) # print to display
                # write_to_oled(oled_i2c, str(num_seconds)+ 'sec')
                write_to_oled_with_font(oled_i2c, str(num_seconds)+'sec\n' + str(weight) + 'g', arial28)
            print("timer stopped")
            if write_to_google_sheet and (num_seconds > 5):
                sheet.append_values(time_weight_pairs)
            idle_time=0
    

gc.enable()
print('garbage collection threshold: ' + str(gc.threshold()))
t=init_sleep()
time.sleep(2)
print_time_weight() # pass 1 if you want to write to google sheet