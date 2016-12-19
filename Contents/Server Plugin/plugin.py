#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

"""
Enphase Indigo Plugin
Authors: See (repo)

Works in combination with FrontViewAPI+ Emby Plugin to display info for
single Emby client.

"""

import datetime
import simplejson
import time as t
import requests
import urllib2
import os
import shutil
import flatdict
from ghpu import GitHubPluginUpdater
from requests.auth import HTTPDigestAuth

try:
    import indigo
except:
    pass

# Establish default plugin prefs; create them if they don't already exist.
kDefaultPluginPrefs = {
    u'configMenuPollInterval': "300",  # Frequency of refreshes.
    u'configMenuServerTimeout': "15",  # Server timeout limit.
    # u'refreshFreq': 300,  # Device-specific update frequency
    u'showDebugInfo': False,  # Verbose debug logging?
    u'configUpdaterForceUpdate': False,
    u'configUpdaterInterval': 24,
    u'showDebugLevel': "1",  # Low, Medium or High debug output.
    u'updaterEmail': "",  # Email to notify of plugin updates.
    u'updaterEmailsEnabled': False  # Notification of plugin updates wanted.
}


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debugLog(u"Initializing Emby plugin.")

        self.debug = self.pluginPrefs.get('showDebugInfo', False)
        self.debugLevel = self.pluginPrefs.get('showDebugLevel', "1")
        self.deviceNeedsUpdated = ''
        self.prefServerTimeout = int(self.pluginPrefs.get('configMenuServerTimeout', "15"))
        self.updater = GitHubPluginUpdater(self)
        self.configUpdaterInterval = self.pluginPrefs.get('configUpdaterInterval', 24)
        self.configUpdaterForceUpdate = self.pluginPrefs.get('configUpdaterForceUpdate', False)

        # Convert old debugLevel scale to new scale if needed.
        # =============================================================
        if not isinstance(self.pluginPrefs['showDebugLevel'], int):
            if self.pluginPrefs['showDebugLevel'] == "High":
                self.pluginPrefs['showDebugLevel'] = 3
            elif self.pluginPrefs['showDebugLevel'] == "Medium":
                self.pluginPrefs['showDebugLevel'] = 2
            else:
                self.pluginPrefs['showDebugLevel'] = 1

    def __del__(self):
        if self.debugLevel >= 2:
            self.debugLog(u"__del__ method called.")
        indigo.PluginBase.__del__(self)

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if self.debugLevel >= 2:
            self.debugLog(u"closedPrefsConfigUi() method called.")

        if userCancelled:
            self.debugLog(u"User prefs dialog cancelled.")

        if not userCancelled:
            self.debug = valuesDict.get('showDebugInfo', False)
            self.debugLevel = self.pluginPrefs.get('showDebugLevel', "1")
            self.debugLog(u"User prefs saved.")

            if self.debug:
                indigo.server.log(u"Debugging on (Level: {0})".format(self.debugLevel))
            else:
                indigo.server.log(u"Debugging off.")

            if int(self.pluginPrefs['showDebugLevel']) >= 3:
                self.debugLog(u"valuesDict: {0} ".format(valuesDict))

        return True

    # Start 'em up.
    def deviceStartComm(self, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"deviceStartComm() method called.")
        indigo.server.log(u"Starting Enphase/Envoy device: " + dev.name)
        dev.stateListOrDisplayStateIdChanged()
        dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Online")
        dev.stateListOrDisplayStateIdChanged()


# Default Indigo Plugin StateList
# This overrides and pulls the current state list (from devices.xml and then adds whatever to it via these calls
# http://forums.indigodomo.com/viewtopic.php?f=108&t=12898
# for summary
# Issue being that with trigger and control page changes will add the same to all devices unless check what device within below call - should be an issue for this plugin

    def getDeviceStateList(self,dev):
        if self.debugLevel>=2:
            self.debugLog(u'getDeviceStateList called')

        stateList = indigo.PluginBase.getDeviceStateList(self, dev)
        if stateList is not None:
            # Add any dynamic states onto the device based on the node's characteristics.
                someNumState = self.getDeviceStateDictForNumberType(u"someNumState", u"Some Level Label",
                                                                    u"Some Level Label")
                someStringState = self.getDeviceStateDictForStringType(u"someStringState", u"Some Level Label",
                                                                       u"Some Level Label")
                someOnOffBoolState = self.getDeviceStateDictForBoolOnOffType(u"someOnOffBoolState", u"Some Level Label",
                                                                             u"Some Level Label")
                someYesNoBoolState = self.getDeviceStateDictForBoolYesNoType(u"someYesNoBoolState", u"Some Level Label",
                                                                             u"Some Level Label")
                someOneZeroBoolState = self.getDeviceStateDictForBoolOneZeroType(u"someOneZeroBoolState",
                                                                                 u"Some Level Label",
                                                                                 u"Some Level Label")
                someTrueFalseBoolState = self.getDeviceStateDictForBoolTrueFalseType(u"someTrueFalseBoolState",
                                                                                     u"Some Level Label",
                                                                                     u"Some Level Label")
                stateList.append(someNumState)
                stateList.append(someStringState)
                stateList.append(someOnOffBoolState)
                stateList.append(someYesNoBoolState)
                stateList.append(someOneZeroBoolState)
                stateList.append(someTrueFalseBoolState)
                try:

                    if self.PanelDict is not None:
                        x=0
                        for array in self.PanelDict:
                            numberArray = "Panel"+str(x)
                            Statearray = self.getDeviceStateDictForNumberType(numberArray,numberArray,numberArray)
                            stateList.append(Statearray)
                            x=x+1
                except Exception as error:
                    self.errorLog(unicode('error in statelist Panel:'+error.message))
        return stateList

    # Shut 'em down.
    def deviceStopComm(self, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"deviceStopComm() method called.")
        indigo.server.log(u"Stopping Emby device: " + dev.name)
        dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Disabled")

    def forceUpdate(self):
        self.updater.update(currentVersion='0.0.0')

    def checkForUpdates(self):
        if self.updater.checkForUpdate() == False:
            indigo.server.log(u"No Updates are Available")

    def updatePlugin(self):
        self.updater.update()

    def runConcurrentThread(self):

        try:
            while True:

                if self.debugLevel >= 2:
                    self.debugLog(u" ")

                for dev in indigo.devices.itervalues(filter="self"):
                    if self.debugLevel >= 2:
                        self.debugLog(u"MainLoop:  {0}:".format(dev.name))
                    # self.debugLog(len(dev.states))
                    self.refreshDataForDev(dev)

                self.sleep(120)

        except self.StopThread:
            self.debugLog(u'Restarting/or error. Stopping Enphase/Envoy thread.')
            pass

    def shutdown(self):
        if self.debugLevel >= 2:
            self.debugLog(u"shutdown() method called.")

    def startup(self):
        if self.debugLevel >= 2:
            self.debugLog(u"Starting EmbyPlugin. startup() method called.")
        if os.path.exists('/Library/Application Support/Perceptive Automation/images/EmbyPlugin') == 0:
            os.makedirs('/Library/Application Support/Perceptive Automation/images/EmbyPlugin')

        # See if there is a plugin update and whether the user wants to be notified.
        try:
            if self.configUpdaterForceUpdate:
                self.updatePlugin()

            else:
                self.checkForUpdates()
            self.sleep(1)
        except Exception as error:
            self.errorLog(u"Update checker error: {0}".format(error))

    def validatePrefsConfigUi(self, valuesDict):
        if self.debugLevel >= 2:
            self.debugLog(u"validatePrefsConfigUi() method called.")

        error_msg_dict = indigo.Dict()

        # self.errorLog(u"Plugin configuration error: ")

        return True, valuesDict

    def fixErrorState(self, dev):
        self.deviceNeedsUpdated = False
        dev.stateListOrDisplayStateIdChanged()
        update_time = t.strftime("%m/%d/%Y at %H:%M")
        dev.updateStateOnServer('deviceLastUpdated', value=update_time)
        if self.debugLevel >= 2:
            self.debugLog(u"Update Time method called.")
            # dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Offline")

    def getTheData(self, dev):
        """
        The getTheData() method is used to retrieve FrontView API Client Data
        """
        if self.debugLevel >= 2:
            self.debugLog(u"getTheData FrontViewAPI method called.")

        # dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Download")
        try:
            url = 'http://' + dev.pluginProps['sourceXML'] + '/production.json'
            r = requests.get(url)
            result = r.json()
            if self.debugLevel >= 2:
                self.debugLog(u"Result:" + unicode(result))

            dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Online")
            dev.setErrorStateOnServer(None)
            # dev.updateStateOnServer('deviceTimestamp', value=t.time())
            return result

        except Exception as error:

            indigo.server.log(u"Error connecting to Device:" + dev.name)
            self.WaitInterval = 60
            if self.debugLevel >= 2:
                self.debugLog(u"Device is offline. No data to return. ")
            dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Offline")
            # dev.updateStateOnServer('deviceTimestamp', value=t.time())
            dev.setErrorStateOnServer(u'Offline')
            result = ""
            return result

    def getthePanels(self, dev):
        """
        The getTheData() method is used to retrieve FrontView API Client Data
        """
        if self.debugLevel >= 2:
            self.debugLog(u"getthePanels Enphase Envoy method called.")

        if dev.pluginProps['envoySerial'] is not None:


        # dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Download")
            try:
                url = 'http://' + dev.pluginProps['sourceXML'] + '/api/v1/production/inverters'
                password = dev.pluginProps['envoySerial']
                password = password[-6:]

                if self.debugLevel >=2:
                    self.debugLog(u"getthePanels: Password:"+unicode(password))

                r = requests.get(url, auth=HTTPDigestAuth('envoy',password))
                result = r.json()
                if self.debugLevel >= 2:
                    self.debugLog(u"Inverter Result:" + unicode(result))

                return result

            except Exception as error:

                indigo.server.log(u"Error connecting to Device:" + dev.name)

                if self.debugLevel >= 2:
                    self.debugLog(u"Device is offline. No data to return. ")

                # dev.updateStateOnServer('deviceTimestamp', value=t.time())

                result = ""
                return result

    def parseStateValues(self, dev):
        """
        The parseStateValues() method walks through the dict and assigns the
        corresponding value to each device state.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"Saving Values method called.")


        dev.updateStateOnServer('numberInverters', value=int(self.finalDict['production'][0]['activeCount']))


        dev.stateListOrDisplayStateIdChanged()
        update_time = t.strftime("%m/%d/%Y at %H:%M")
        dev.updateStateOnServer('deviceLastUpdated', value=update_time)
        # dev.updateStateOnServer('deviceTimestamp', value=t.time())

    def setStatestonil(self, dev):
        if self.debugLevel >= 2:
            self.debugLog(u'setStates to nil run')



    def refreshDataAction(self, valuesDict):
        """
        The refreshDataAction() method refreshes data for all devices based on
        a plugin menu call.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataAction() method called.")
        self.refreshData()
        return True

    def refreshData(self):
        """
        The refreshData() method controls the updating of all plugin
        devices.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshData() method called.")

        try:
            # Check to see if there have been any devices created.
            if indigo.devices.itervalues(filter="self"):
                if self.debugLevel >= 2:
                    self.debugLog(u"Updating data...")

                for dev in indigo.devices.itervalues(filter="self"):
                    self.refreshDataForDev(dev)

            else:
                indigo.server.log(u"No Emby Client devices have been created.")

            return True

        except Exception as error:
            self.errorLog(u"Error refreshing devices. Please check settings.")
            self.errorLog(unicode(error))
            return False

    def refreshDataForDev(self, dev):

        if dev.configured:
            if self.debugLevel >= 2:
                self.debugLog(u"Found configured device: {0}".format(dev.name))

            if dev.enabled:
                if self.debugLevel >= 2:
                    self.debugLog(u"   {0} is enabled.".format(dev.name))

                # timeDifference = int(t.time()) - int(dev.states['deviceTimestamp'])
                # Change to using Last Updated setting - removing need for deviceTimestamp altogether

                timeDifference = int(t.time() - t.mktime(dev.lastChanged.timetuple()))
                if self.debugLevel >= 1:
                    self.debugLog(dev.name + u": Time Since Device Update = " + unicode(timeDifference))
                    # self.errorLog(unicode(dev.lastChanged))
                # Get the data.

                # If device is offline wait for 60 seconds until rechecking
                if dev.states['deviceIsOnline'] == False and timeDifference >= 60:
                    if self.debugLevel >= 2:
                        self.debugLog(u"Offline: Refreshing device: {0}".format(dev.name))
                    self.finalDict = self.getTheData(dev)

                # if device online normal time
                if dev.states['deviceIsOnline']:
                    if self.debugLevel >= 2:
                        self.debugLog(u"Online: Refreshing device: {0}".format(dev.name))
                    self.finalDict = self.getTheData(dev)
                    self.PanelDict = self.getthePanels(dev)


                    # Put the final values into the device states - only if online
                if dev.states['deviceIsOnline']:
                    self.parseStateValues(dev)
            else:
                if self.debugLevel >= 2:
                    self.debugLog(u"    Disabled: {0}".format(dev.name))

    def refreshDataForDevAction(self, valuesDict):
        """
        The refreshDataForDevAction() method refreshes data for a selected device based on
        a plugin menu call.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataForDevAction() method called.")

        dev = indigo.devices[valuesDict.deviceId]

        self.refreshDataForDev(dev)
        return True

    def stopSleep(self, start_sleep):
        """
        The stopSleep() method accounts for changes to the user upload interval
        preference. The plugin checks every 2 seconds to see if the sleep
        interval should be updated.
        """
        try:
            total_sleep = float(self.pluginPrefs.get('configMenuUploadInterval', 300))
        except:
            total_sleep = iTimer  # TODO: Note variable iTimer is an unresolved reference.
        if t.time() - start_sleep > total_sleep:
            return True
        return False

    def toggleDebugEnabled(self):
        """
        Toggle debug on/off.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"toggleDebugEnabled() method called.")
        if not self.debug:
            self.debug = True
            self.pluginPrefs['showDebugInfo'] = True
            indigo.server.log(u"Debugging on.")
            self.debugLog(u"Debug level: {0}".format(self.debugLevel))

        else:
            self.debug = False
            self.pluginPrefs['showDebugInfo'] = False
            indigo.server.log(u"Debugging off.")
