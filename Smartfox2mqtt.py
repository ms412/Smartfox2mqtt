#!/usr/bin/python3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


__app__ = "Smartfox"
__VERSION__ = "0.1"
__DATE__ = "02.05.2023"
__author__ = "Markus Schiesser"
__contact__ = "M.Schiesser@gmail.com"
__copyright__ = "Copyright (C) 2023 Markus Schiesser"
__license__ = 'GPL v3'

import sys
import os
import time
import json
import logging
from configobj import ConfigObj
#from smartfox import Smartfox

from library.mqttclientV2 import mqttclient
from library.logger import loghandler
from library.smartfox import Smartfox


class SmartfoxController(object):

    def __init__(self,configfile='Smartfox2mqtt.config'):
    #    threading.Thread.__init__(self)

        self._configfile = os.path.join(os.path.dirname(__file__),configfile)
        print(self._configfile)

        self._configBroker =  None
        self._configLog = None
        self._configSmartfox = None
        self._configInverter = None

        self._mqtt = None
        self._smartfox = None
        self._inverter = None

        self._rootLoggerName = ''

    def readConfig(self) -> bool:

        _config = ConfigObj(self._configfile)

        if bool(_config) is False:
            print('ERROR config file not found',self._configfile)
            sys.exit()
            #exit

        self._configBroker = _config.get('BROKER',None)
        self._configLog = _config.get('LOGGING',None)
        self._configSmartfox = _config.get('SMARTFOX',None)
       # self._configInverter = _config.get('INVERTER', None)
        #print(self._configSmartfox)

        return True

    def startLogger(self) -> bool:
       # self._log = loghandler('marantec')

        self._configLog['DIRECTORY'] = os.path.dirname(__file__)
        self._root_logger = loghandler(self._configLog.get('NAME','SMARTFOX3'))
        self._root_logger.handle(self._configLog.get('LOGMODE','PRINT'),self._configLog)
        self._root_logger.level(self._configLog.get('LOGLEVEL','DEBUG'))
        self._rootLoggerName = self._configLog.get('NAME',self.__class__.__name__)
        self._log = logging.getLogger(self._rootLoggerName + '.' + self.__class__.__name__)

        self._log.info('Start %s, %s'%(__app__,__VERSION__))

        return True

    def startMqttBroker(self) -> bool:
        self._log.debug('Methode: startMqtt()')
        self._mqtt = mqttclient(self._rootLoggerName)

        _host = self._configBroker.get('HOST','localhost')
        _port = self._configBroker.get('PORT',1883)

        _state = False
        while not _state:
            _state = self._mqtt.connect(_host,_port)
            if not _state:
                self._log.error('Failed to connect to broker: %s',_host)
                time.sleep(5)

        self._log.debug('Sucessful connect to broker: %s',_host)

        _subscribe = (self._configBroker['SUBSCRIBE']) + '/#'
        self._mqtt.subscribe(_subscribe,self.brokerCallback)

        return True

    def brokerCallback(self, msg):
        self._log.info('callback')
        #print('Callback ',client,userdata,msg)
        self._log.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        _type = msg.topic.split('/')[-1]
        _obj = self._inputObjectRegister.get(_type,False)
        self._log.info('callback %s'%(_obj))
        if _obj:
            _obj.eventSys(str(msg.payload.decode("utf-8")))
        pass

    def startSmartfox(self):
        # Initialize a new Smartfox2mqtt connection
        #self._smartfox = Smartfox(self._configSmartfox.get('HOST','192.168.2.80'))
        self._smartfox = Smartfox(self._configSmartfox.get('HOST','192.168.2.80'),
                                  self._configSmartfox.get('PORT','502'),
                                  logger=self._rootLoggerName)

        self._smartfox.readConfigFile(self._configSmartfox.get('REGISTERFILE','/opt/Smartfox2mqtt/data/SmartfoxRegister.json'))
        if self._smartfox.connect():
           return True

        return False

    def getDataFromSmartfox(self):
        _data = self._configSmartfox.get('REGISTER')

        return self._smartfox.queryData(_data)


    def publishData(self):
        self._log.debug('Send Update State')
        _topic = self._configBroker.get('PUBLISH','/SMARTHOME/DEFAULT')

        self._mqtt.publish(_topic,self.getDataFromSmartfox())

        return True

    def start(self):
        self.readConfig()
        self.startLogger()
        self.startMqttBroker()
        self.startSmartfox()

        while(True):
            self.publishData()
            time.sleep(15)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        configfile = sys.argv[1]
    else:
     #   configfile = '/opt/alarm/AlarmController.config'
        configfile = './Smartfox2mqtt.config'

    a = SmartfoxController(configfile)
    a.start()