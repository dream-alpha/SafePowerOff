from Screens.Screen import Screen
import Screens.Standby
from Components.ActionMap import ActionMap
from Components.config import config
from Components.AVSwitch import AVSwitch
from Components.SystemInfo import SystemInfo
from Components.Task import job_manager
from GlobalActions import globalActionMap
from enigma import eDVBVolumecontrol, eDVBLocalTimeHandler, eServiceReference, eTimer, quitMainloop
from RecordingUtils import isRecordingOrRecordingSoon


class Standby(Screen):
	def Power(self):
		print("leave standby")
		#set input to encoder
		self.avswitch.setInput("ENCODER")
		#restart last played service
		#unmute adc
		self.leaveMute()
		#kill me
		self.close(True)

	def setMute(self):
		if (eDVBVolumecontrol.getInstance().isMuted()):
			self.wasMuted = 1
			print("mute already active")
		else:
			self.wasMuted = 0
			eDVBVolumecontrol.getInstance().volumeToggleMute()

	def leaveMute(self):
		if self.wasMuted == 0:
			eDVBVolumecontrol.getInstance().volumeToggleMute()

	def __init__(self, session, request_shutdown=False):
		self.request_shutdown = request_shutdown
		self.shutdown_timer = eTimer()
		self.shutdown_timer_conn = self.shutdown_timer.timeout.connect(self.doShutdown)

		Screen.__init__(self, session)
		self.avswitch = AVSwitch()

		print("enter standby")

		self["actions"] = ActionMap(
			["StandbyActions"],
			{
				"power": self.Power
			},
			-1
		)

		globalActionMap.setEnabled(False)

		#mute adc
		self.setMute()

		self.paused_service = None
		self.prev_running_service = None
		self.time_handler_conn = False

		if self.session.current_dialog:
			if self.session.current_dialog.ALLOW_SUSPEND == Screen.SUSPEND_STOPS:
				#get currently playing service reference
				self.prev_running_service = self.session.nav.getCurrentlyPlayingServiceReference()
				#stop actual played dvb-service
				self.session.nav.stopService()
			elif self.session.current_dialog.ALLOW_SUSPEND == Screen.SUSPEND_PAUSES:
				self.paused_service = self.session.current_dialog
				self.paused_service.pauseService()

		#set input to vcr scart
		if SystemInfo["ScartSwitch"]:
			self.avswitch.setInput("SCART")
		else:
			self.avswitch.setInput("AUX")
		self.onFirstExecBegin.append(self.__onFirstExecBegin)
		self.onClose.append(self.__onClose)

		if config.misc.standbyCounter.value == 0 and config.misc.useTransponderTime.value:
			th = eDVBLocalTimeHandler.getInstance()
			if not th.ready():
				refstr = config.tv.lastservice.value if config.servicelist.lastmode.value == 'tv' else config.radio.lastservice.value
				ref = eServiceReference(refstr)
				if ref.valid():
					self.time_handler_conn = th.m_timeUpdated.connect(self.timeReady)
					self.session.nav.playService(ref, False, False)

	def timeReady(self):
		if self.time_handler_conn:
			self.time_handler_conn = None
			self.session.nav.stopService()

	def __onClose(self):
		Screens.Standby.inStandby = None

		self.timeReady()

		if not self.session.shutdown:
			if self.prev_running_service:
				self.session.nav.playService(self.prev_running_service)
			elif self.paused_service:
				self.paused_service.unPauseService()
		self.session.screen["Standby"].boolean = False
		globalActionMap.setEnabled(True)

	def __onFirstExecBegin(self):
		Screens.Standby.inStandby = self
		self.session.screen["Standby"].boolean = True
		config.misc.standbyCounter.value += 1
		if self.request_shutdown and (isRecordingOrRecordingSoon(self.session) or job_manager.getPendingJobs()):
			self.shutdown_timer.start(60000)

	def doShutdown(self):
		if not(isRecordingOrRecordingSoon(self.session) or job_manager.getPendingJobs()):
			self.shutdown_timer.stop()
			quitMainloop(1)

	def createSummary(self):
		return StandbySummary


class StandbySummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget source="global.CurrentTime" render="Label" position="0,0" size="132,64" font="Regular;40" halign="center">
			<convert type="ClockToText" />
		</widget>
		<widget source="session.RecordState" render="FixedLabel" text=" " position="0,0" size="132,64" zPosition="1" >
			<convert type="ConfigEntryTest">config.usage.blinking_display_clock_during_recording,True,CheckSourceBoolean</convert>
			<convert type="ConditionalShowHide">Blink</convert>
		</widget>
	</screen>"""
