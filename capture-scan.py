#!/usr/bin/python3
from evdev import InputDevice, categorize, ecodes
import colorsys
import unicornhat as unicorn
from time import sleep
import mysql.connector


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


dev = InputDevice('/dev/input/event5') # This is the manually proved HID device. -Build auto-detection
badgePart = ''
ascii_codes = {
    0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
    10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'q', 17: u'w', 18: u'e', 19: u'r',
    20: u't', 21: u'y', 22: u'u', 23: u'i', 24: u'o', 25: u'p', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL', 
    30: u'a', 31: u's', 32: u'd', 33: u'f', 34: u'g', 35: u'h', 36: u'j', 37: u'k', 38: u'l', 39: u';',
    40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'z', 45: u'x', 46: u'c', 47: u'v', 48: u'b', 49: u'n',
    50: u'm', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 57: u' ', 100: u'RALT'
}

unicorn.set_layout(unicorn.AUTO)
unicorn.rotation(0)
unicorn.brightness(1)
u_width,u_height=unicorn.get_shape()

def blinkarray(r,g,b,t):
    for y in range(u_height):
        for x in range(u_width):
            unicorn.set_pixel(x,y,r,g,b)
    unicorn.show()
    sleep(t)
    for y in range(u_height):
        for x in range(u_width):
            unicorn.set_pixel(x,y,0,0,0)
    unicorn.show()

def sqlreq(sqlcommand,r,c):
    db = mysql.connector.connect(host="localhost", user="pi", password="pi", database="badge")
    dbc = db.cursor()
    dbc.execute(sqlcommand)
    if r == 1:
        row = dbc.fetchone()
        return row
    if c == 1:
         db.commit()
    db.close()

#print(dev)
#dev.ungrab()

dev.grab()

for event in dev.read_loop():
    if event.type == ecodes.EV_KEY:
        data = categorize(event)
        if data.keystate == 1:
            if data.scancode != 28:
                ascii_lup = ascii_codes.get(data.scancode) or u'UNKNOWN:{}'.format(data.scancode)
                badgePart += str(ascii_lup)
            else:
                badgeScan = int(badgePart)
                row = sqlreq("SELECT * FROM AccessListPRI WHERE badge_id='{}';".format(badgeScan),1,0)
                if row != None:
                    if row[7]  == 1:
                        blinkarray(0,255,0,.5)
                        print(f"{bcolors.OKGREEN}AUTHORIZED{bcolors.ENDC}\t{badgeScan}\t{row[4]}\t{row[5]}")
                        sqlreq("UPDATE AccessListPRI SET last_scan_time=(CURRENT_TIMESTAMP), last_scan_authallow=1 WHERE id={};".format(row[0]),0,1)
                        sqlreq("INSERT INTO ScanRecord (badge_id, scan_time, auth) VALUES({}, (CURRENT_TIMESTAMP), 1);".format(badgeScan),0,1)
                    else:
                        blinkarray(255,0,0,.5)
                        print(f"{bcolors.FAIL}UNAUTHORIZED{bcolors.ENDC}\t{badgeScan}\t{row[4]}\t{row[5]}")
                        sqlreq("UPDATE AccessListPRI SET last_scan_time=(CURRENT_TIMESTAMP), last_scan_authallow=0 WHERE id={};".format(row[0]),0,1)
                        sqlreq("INSERT INTO ScanRecord (badge_id, scan_time, auth) VALUES({}, (CURRENT_TIMESTAMP), 0);".format(badgeScan),0,1)
                else:
                    blinkarray(255,0,0,.250)
                    blinkarray(0,0,255,.250)
                    row = sqlreq("SELECT CURRENT_TIMESTAMP",1,0)
                    print(f"{bcolors.FAIL}UNAUTHORIZED{bcolors.ENDC}\t{badgeScan}\tINVALID\t{row[0]}")
                    sqlreq("INSERT INTO ScanRecord (badge_id, scan_time, auth) VALUES({}, (CURRENT_TIMESTAMP), 0);".format(badgeScan),0,1)
                badgePart = ''
