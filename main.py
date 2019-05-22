import binascii
import struct
import socket

#### Struct Encoding Types
StructCodeInt16 = "!h" ## Unsigned Int16
StructCodeInt32 = "!L" ## Unsigned Int32

#### NRPE Specific definitions
NRPE_Version = ("","One", "Two", "Three")
NRPE_Packet_Type = ("", "Query", "Response")
NRPE_Response = ("Ok", "Warning", "Critical", "Unknown")
NRPE_Version_1 = 1
NRPE_Version_2 = 2
NRPE_Version_3 = 3
NRPE_Packet_Type_Query = 1
NRPE_Packet_Type_Response = 2
NRPE_Response_Ok = 0
NRPE_Response_Warning = 1
NRPE_Response_Critical = 2
NRPE_Response_Unknown = 3
NRPE_Response_Type_Query = 3
#NRPE_Response_Type_Query = 2321

#### RandomDefintions
NullByte = b"\x00"
TwoCharSuffix = "SG"

class NRPEpacket:
	port = 5666
	server = "127.0.0.1"
	nrpeVersion = NRPE_Version_2
	nrpePacketType = NRPE_Packet_Type_Query
	nrpeResponseCode = NRPE_Response_Type_Query
	ownSocket = None
	def CalculateCRC(self):
		tempBuffer = struct.pack(StructCodeInt16,self.nrpeVersion)
		tempBuffer += struct.pack(StructCodeInt16,self.nrpePacketType)
		tempBuffer += NullByte * 4
		tempBuffer += struct.pack(StructCodeInt16,self.nrpeResponseCode)
		tempBuffer += self.content
		return (struct.pack(StructCodeInt32, binascii.crc32(tempBuffer) & 0xffffffff))
	def PadTo1024Bytes(self,command):
		if len(command) <= 1024:
			tempBuffer = command
		else:
			Error("Command string is too long!")
		while len(tempBuffer) < 1024:
			tempBuffer += "\x00"
		tempBuffer += TwoCharSuffix
		return tempBuffer.encode()
	def Connect(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((self.server,self.port))
	def Send(self):
		tempBuffer = struct.pack(StructCodeInt16,self.nrpeVersion)
		tempBuffer += struct.pack(StructCodeInt16,self.nrpePacketType)
		tempBuffer += self.crc
		tempBuffer += struct.pack(StructCodeInt16,self.nrpeResponseCode)
		tempBuffer += self.content
		self.socket.send(tempBuffer)
	def Recv(self):
		tempBuffer = self.socket.recv(2048)
		self.nrpeVersion = struct.unpack(StructCodeInt16,tempBuffer[0:2])[0]
		self.nrpePacketType = struct.unpack(StructCodeInt16,tempBuffer[2:4])[0]
		self.crc = tempBuffer[4:8]
		self.nrpeResponseCode = struct.unpack(StructCodeInt16,tempBuffer[8:10])[0]
		self.content = tempBuffer[10:]
		if self.crc != self.CalculateCRC():
			print ("CRC does not match!")
	def PrintOut(self):
		print(" -=-=-=-= Begin NRPE Content =-=-=-=-")
		print("| NRPE Version       =  %i  -  %s" % (self.nrpeVersion,NRPE_Version[self.nrpeVersion]))
		print("| NRPE Packet Type   =  %i  -  %s" % (self.nrpePacketType,NRPE_Packet_Type[self.nrpePacketType]))
		print("| NRPE Packet CRC    =  %i" % struct.unpack(StructCodeInt32,self.crc)[0])
		print("| NRPE Response Code =  %i  -  %s" % (self.nrpeResponseCode,NRPE_Response[self.nrpeResponseCode]))
		print("| Packet Content:")
		print("| %s" % self.content.decode().strip(TwoCharSuffix).strip("\x00"))
		print(" -=-=-=-= End NRPE Content =-=-=-=-")
	def Close(self):
		if not self.ownSocket:
			self.socket.close()
	def AutoSend(self):
		print("Sending...")
		self.PrintOut()
		self.Send()
		print("Receiving...")
		self.Recv()
		self.PrintOut()
		self.Close()
	def __init__(self, command, socket=None):
		self.content = self.PadTo1024Bytes(command)
		self.crc = self.CalculateCRC()
		if not socket:
			self.Connect()
		else:
			self.socket = socket
			self.ownSocket = True

#y = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#y.connect(("127.0.0.1",5666))
x = NRPEpacket("alias_disk")
#x.server = "127.0.0.2"
#x.port = 5666
x.AutoSend()
