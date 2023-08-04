
import json
import logging
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
#from pymodbus.client.sync import ModbusTcpClient


class Smartfox(object):
    def __init__(self,host, port,logger):

        _libName = str(__name__.rsplit('.', 1)[-1])
        self._log = logging.getLogger(logger + '.' + _libName + '.' + self.__class__.__name__)

        self._log.debug('Create Smartfox Modbus Object')

        self._host = host
        self._port = port
        self._client = None

        self._registerFile = "./data/SmartfoxRegister.json"
        self._register = None

        self._dataType = {
          'uint16':1,
          'int16':1,
          'int32':2,
          'uint32':2,
          'STR16':8,
          'uint64':4,
          'int64':4
          }

    def readConfigFile(self,file=False):
        if file is False:
            file = self._registerFile
            self._log.info('read local file')

        with open(file) as _data:
            self._register = json.load(_data)

    def connect(self):
        self._client = ModbusTcpClient(self._host, self._port)
        return self._client.connect()

    def readRegister(self,slaveId,name):
      #  print(type(self._register),self._register)
        _item = self._register.get(name,False)
        if _item is False:
          #  print('%s Name not found',name)
            self._log.critical('Value not found %s',name)
            return False
        _address = _item['Start'] -1
        _size = _item['Size']
        _type = _item['Type']
        _scale = _item['Scale Factor']
        if not _scale:
            _scale = 1
        _units =  _item['Units']

        try:
            _value = self.getData(slaveId,_address,_size)
            _value = self.evaluateData(_value,_type)
        except:
            self._log.error('Problem during evaluation')
     #   print(type(_value),_value)
      #  print(_value*_scale,_units)
        return (_value*_scale,_units)


    def getData(self,slaveId,address,size):
      #  print(slaveId,address,size)
        received = self._client.read_holding_registers(address=address,
                                           count= size,
                                           unit=slaveId)
     #   print(received)
        message = BinaryPayloadDecoder.fromRegisters(received.registers, byteorder=Endian.Big, wordorder=Endian.Big)
        return message

    def evaluateData(self,message,dataType):
        if dataType == 'int32':
            _data = message.decode_32bit_int()
        elif dataType == 'uint32':
            _data = message.decode_32bit_uint()
        elif dataType == 'uint64':
            _data = message.decode_64bit_uint()
        elif dataType == 'STR16':
            _data = message.decode_string(16).rstrip('\x00')
        elif dataType == 'STR32':
            _data = message.decode_string(32).rstrip('\x00')
        elif dataType == 'int16':
            _data = message.decode_16bit_int()
        elif dataType == 'uint16':
            _data = message.decode_16bit_uint()
        else:  # if no data type is defined do raw interpretation of the delivered data
          #  _data = message.decode_16bit_uint()
          #  print('unknown Data Type')
            self._log.error('unkown datattype')
            _data = False

        return _data

    def queryData(self,data=False):
        _store = {}

        if not data:
            self._log.info('read local data')
            data= [
                'Energy from grid',
                'Energy into grid',
                'Energy Smartfox',
                'Day Energy from grid',
                'Day Energy into grid',
                'Day Energy Smartfox',
                'Power total',
                'Power L1',
                'Power L2',
                'Power L3',
                'Voltage L1',
                'Voltage L2',
                'Voltage L3',
                'Current L1',
                'Current L2',
                'Current L3',
                'Frequency',
                'Power Smartfox'
                ]

        for _item in data:
            _localStore = {}
            (data,unit) =self.readRegister(1,_item)
          #  print(data,unit)
            _localStore['data_value'] = data
            _localStore['data_unit'] = unit
            _store[_item] = _localStore

    #    print(json.dumps(_store))
        return json.dumps(_store)




   
if __name__ == "__main__":
    smart = Smartfox('192.168.2.80')
    smart.readConfigFile()

    if smart.connect():
        print('Connected')
        #smart.readRegister(1, 'Energy from grid')
        smart.queryData()
       # smart.readAllRegisters()
    else:
        print('Failed to Connect')