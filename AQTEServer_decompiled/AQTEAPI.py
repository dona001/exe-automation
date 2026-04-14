# uncompyle6 version 3.9.3
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.10.0 (default, Mar  2 2025, 19:23:58) [Clang 16.0.0 (clang-1600.0.26.3)]
# Embedded file name: AQTEAPI.py
from HllApi import HllApi
from time import sleep
import threading

class AQTEAPI(HllApi):
    pSpace = bytes()

    def __init__(self, dllLoc, func):
        HllApi.__init__(self, dllLoc, func)
        self.connected = False
        return

    def isConnected(self):
        return self.connected

    _ps_lock = threading.Lock()

    def psConnect(self, psid):
        with self._ps_lock:
            print ('connecting to {}').format(psid)
            self.pSpace = bytes(psid)
            self.connectPresentationSpace(psid)
            self.connected = True
        return

    def psDisconnect(self, psid):
        with self._ps_lock:
            self.disconnectPresentationSpace()
            self.disconnectWindowServices(psid)
            self.connected = False
        return

    def send_pause(self, time):
        self.pause(time)
        return

    def notifyHost(self, timeOut=300):
        beforeScreen = str()
        beforeScreen = self.copyPresentationSpaceToString(beforeScreen)['screen']
        self.startHostNotification(self.pSpace + '   B')
        self.sendKey('@E')
        while self.wait() > 0 and timeOut > 0:
            sleep(0.01)

        while self.queryHostUpdate(self.pSpace) != 0 and timeOut > 0:
            self.pause(1)
            sleep(0.01)
            timeOut -= 1

        self.stopHostNotification(self.pSpace)
        afterScreen = str()
        afterScreen = self.copyPresentationSpaceToString(afterScreen)['screen']
        while beforeScreen == afterScreen and timeOut > 0:
            afterScreen = self.copyPresentationSpaceToString(afterScreen)['screen']
            sleep(0.01)
            timeOut -= 1

        if timeOut == 0:
            return -1
        return

    def notifySearch(self, searchString, timeOut=300):
        self.notifyHost(timeOut)
        while timeOut > 0 and self.searchPresentationSpace(searchString)['returnCode'] != 0:
            sleep(0.01)
            timeOut -= 1

        if timeOut == 0:
            return -1
        return

    def findEntryField(self, fieldName, field='NU'):
        location = self.searchPresentationSpace(fieldName)['position']
        if location > 0:
            return self.findFieldPosition(field, location)['length']
        else:
            return -1

        return

    def findEntryFieldLength(self, fieldName, field='NU'):
        location = self.searchPresentationSpace(fieldName)['position']
        if location > 0:
            return self.findFieldLength(location, field)['length']
        else:
            return 0

        return

    def findEntryFieldLengthByPos(self, position):
        return self.findFieldLength(position, '')['length']

    def fillEntryField(self, fieldName, fieldValue, field='NU'):
        location = self.findEntryField(fieldName, field)
        if location > 0:
            return self.copyStringToField(fieldValue, location)
        else:
            return -1

        return

    def clearScreen(self, timeOut=300):
        self.sendKey('@C')
        while self.wait() > 0 and timeOut > 0:
            sleep(0.01)

        return

    def processScreen(self, screen):
        count = 0
        buildString = ''
        while count < 8000:
            buildString = buildString + screen[count]
            if count % 80 == 0:
                buildString = buildString + '\n'
            count = count + 1

        return buildString

    def printScreen(self):
        i = 0
        fullScreenPrint = ' '
        sepLine = '\n--------------------------------------------------------------------------------\n'
        while i < 8000:
            fullScreenPrint = fullScreenPrint + ' '
            i = i + 1

        fullScreenPrint = self.copyPresentationSpace(fullScreenPrint)
        finalString = self.processScreen(fullScreenPrint)
        finalString = sepLine + finalString.strip() + sepLine
        print 'Screen Shot Taken'
        return finalString


return

# okay decompiling AQTEServer.exe_extracted/PYZ-00.pyz_extracted/AQTEAPI.pyc
