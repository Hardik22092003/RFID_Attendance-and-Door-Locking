from machine import Pin, I2C, RTC
import sdcard, uos
from mfrc522 import MFRC522
import time

# Pins for SPI interface
sck = Pin(18)
mosi = Pin(23)
miso = Pin(19)
cs = Pin(5)

# Setup for RFID
spi = SPI(1, baudrate=1000000, sck=sck, mosi=mosi, miso=miso)
rfid = MFRC522(spi, cs)

# Setup for SD card
sd = sdcard.SDCard(spi, cs)
uos.mount(sd, "/sd")

# Setup for Relay and Solenoid Lock
relay = Pin(13, Pin.OUT)
solenoid_lock = Pin(12, Pin.OUT)

# Setup for RTC
rtc = RTC()
rtc.datetime((2024, 5, 1, 0, 0, 0, 0, 0))

def log_to_sd(card_id):
    with open("/sd/attendance_log.txt", "a") as f:
        f.write(f"{rtc.datetime()}, {card_id}\n")

def unlock_door():
    relay.value(1)
    solenoid_lock.value(1)
    time.sleep(5)
    relay.value(0)
    solenoid_lock.value(0)

def check_rfid():
    (stat, tag_type) = rfid.request(rfid.REQIDL)
    if stat == rfid.OK:
        (stat, raw_uid) = rfid.anticoll()
        if stat == rfid.OK:
            card_id = "".join("%02X" % b for b in raw_uid)
            print("Card detected:", card_id)
            log_to_sd(card_id)
            unlock_door()

while True:
    check_rfid()
    time.sleep(1)
