#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from pymodbus.client import ModbusSerialClient
from struct import unpack as Montafloat
import os.path
import datetime

#Conectando ao GPS por modbus RTU
client = ModbusSerialClient(method="rtu", port="/dev/ttyUSB0", baudrate=19200, timeout=2, parity="N", stopbits=1, bytesize=8)
client.connect()

#De acordo com a leitura faz o print da mensagem
if client.connect():
	print("Connect Sucessful")
else:
	print("Erro MODBUS")

#Faz leitura de holding register a partir do 101 para pegar em float os valores
read = client.read_holding_registers(100,10,1)

#Arrumar as leituras feitas em forma de word para float
Latitude = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[0]) + '{0:02x}'.format(read.registers[1]))))
Longitude = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[2]) + '{0:02x}'.format(read.registers[3]))))
Altitude = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[4]) + '{0:02x}'.format(read.registers[5]))))
UTC = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[6]) + '{0:02x}'.format(read.registers[7]))))
Date = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[8]) + '{0:02x}'.format(read.registers[9]))))

#Coleta Numero de satelite e qualidade de sinal
read = client.read_holding_registers(2004,4,1)
Sinal_quality = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[0]) + '{0:02x}'.format(read.registers[1]))))
Qtd_Satelites = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[2]) + '{0:02x}'.format(read.registers[3]))))

#Coleta PDOP, HDOP e VDOP
read = client.read_holding_registers(2128,6,1)
PDOP = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[0]) + '{0:02x}'.format(read.registers[1]))))
HDOP = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[2]) + '{0:02x}'.format(read.registers[3]))))
VDOP = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[4]) + '{0:02x}'.format(read.registers[5]))))

#Coleta Direcao e Velocidade
read = client.read_holding_registers(2206, 4, 1)
Speed = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[0]) + '{0:02x}'.format(read.registers[1]))))
Direction = str(Montafloat('!f', bytes.fromhex('{0:02x}'.format(read.registers[2]) + '{0:02x}'.format(read.registers[3]))))



#Por algum motivo a string vem com outros caracteres, tiro as ()e,
str_to_remove = "(),"
for i in str_to_remove:
	Latitude = Latitude.replace(i, '')
for i in str_to_remove:
	Longitude = Longitude.replace(i, '')
for i in str_to_remove:
	Altitude = Altitude.replace(i, '')
for i in str_to_remove:
	UTC = UTC.replace(i, '')
for i in str_to_remove:
	Date = Date.replace(i, '')
for i in str_to_remove:
	Sinal_quality = Sinal_quality.replace(i, '')
for i in str_to_remove:
	Qtd_Satelites = Qtd_Satelites.replace(i, '')
for i in str_to_remove:
	PDOP = PDOP.replace(i, '')
for i in str_to_remove:
	HDOP = HDOP.replace(i, '')
for i in str_to_remove:
	VDOP = VDOP.replace(i, '')
for i in str_to_remove:
	Speed = Speed.replace(i, '')
for i in str_to_remove:
	Direction = Direction.replace(i, '')




#print dos valores tratados para teste	
print("Latitude= " + Latitude)
print("Longitude= " + Longitude)
print("Altitude= " + Altitude)
print("UTC= " + UTC)
print("Date= " + Date)
print("Sinal Quality= " + Sinal_quality)
print("Qtd Satelites= " + Qtd_Satelites)
print("PDOP= " + PDOP)
print("HDOP= " + HDOP)
print("VDOP= " + VDOP)
print("Speed= " + Speed)
print("Direction= " + Direction)

#Cria nome arquivo com base no relogio do controlador
data = datetime.date.today()
nome_arquivo = ("../../../media/pi/SENSORVILLE/Tracking_GPS/" + str(data) + ".csv")


#Verifica se ja tem arquivo com o nome
criado = os.path.exists(nome_arquivo)

if criado:
	arquivo = open(nome_arquivo, "a")
	arquivo.write(Date + ";" + UTC + ";" + Latitude + ";" + Longitude + ";" + Altitude + ";" + Sinal_quality + ";" + Qtd_Satelites + ";" + Speed + ";" + Direction + ";" + PDOP + ";" + HDOP + ";" + VDOP + "\r")
	arquivo.close()
else:
	arquivo = open(nome_arquivo, "a")
	arquivo.write("Date;UTC;Latitude;Longitude;Altitude;Sinal_quality;Qtd_Satelites;Speed;Direction;PDOP;HDOP;VDOP\r")
	arquivo.write(Date + ";" + UTC + ";" + Latitude + ";" + Longitude + ";" + Altitude + ";" + Sinal_quality + ";" + Qtd_Satelites + ";" + Speed + ";" + Direction + ";" + PDOP + ";" + HDOP + ";" + VDOP + "\r")
	arquivo.close()

client.close()
