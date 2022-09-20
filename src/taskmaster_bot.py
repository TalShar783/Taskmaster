import os
import pygsheets

keyfile_path = f"{os.getcwd()}\\keyfile.json"

gc = pygsheets.authorize(service_file=keyfile_path)

sh = gc.open('Recreational Funds')
wks = sh.sheet1
print(wks.get_value('A2'))

print(wks.get_values(start='B3', end='B20'))
