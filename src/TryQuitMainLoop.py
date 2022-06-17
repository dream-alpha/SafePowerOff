from __init__ import _
from enigma import quitMainloop
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Task import job_manager
import Screens.Standby
from Standby import Standby
from Tools import Notifications
from RecordingUtils import isRecordingOrRecordingSoon


class TryQuitMainloop(MessageBox):
	def __init__(self, session, retvalue=1, timeout=-1, default_yes=True):
		self.retval = retvalue
		recordings = isRecordingOrRecordingSoon(session)
		jobs = len(job_manager.getPendingJobs())
		self.enter_standby = False
		reason = ""
		if recordings:
			reason = _("Recording(s) are in progress or coming up in few seconds!") + '\n'
		if jobs:
			if jobs == 1:
				job = job_manager.getPendingJobs()[0]
				reason += "%s: %s (%d%%)\n" % (job.getStatustext(), job.name, int(100 * job.progress / float(job.end)))
			else:
				reason += (_("%d jobs are running in the background!") % jobs) + '\n'
		if retvalue == 16:
			reason += _("Really reboot into Recovery Mode?\n")
		if reason:
			if retvalue == 1:
				if jobs or recordings:
					self.enter_standby = True
					MessageBox.__init__(self, session, reason + _("Entering idle mode to complete recording(s)/job(s) before powering off."), type=MessageBox.TYPE_INFO, timeout=10)
				else:
					MessageBox.__init__(self, session, reason + _("Really shutdown now?"), type=MessageBox.TYPE_YESNO, timeout=timeout, default=default_yes)
			elif retvalue == 2:
				MessageBox.__init__(self, session, reason + _("Really reboot now?"), type=MessageBox.TYPE_YESNO, timeout=timeout, default=default_yes)
			elif retvalue == 4:
				pass
			elif retvalue == 16:
				MessageBox.__init__(self, session, reason + _("You won't be able to leave Recovery Mode without physical access to the device!"), type=MessageBox.TYPE_YESNO, timeout=timeout, default=default_yes)
			else:
				MessageBox.__init__(self, session, reason + _("Really restart now?"), type=MessageBox.TYPE_YESNO, timeout=timeout, default=default_yes)
			self.skinName = "MessageBox"
			self.onShow.append(self.__onShow)
			self.onHide.append(self.__onHide)
		else:
			self.skin = """<screen name="TryQuitMainloop" position="0,0" size="0,0" flags="wfNoBorder"/>"""
			Screen.__init__(self, session)
			self.close(True)

	def close(self, value):
		if value:
			if self.enter_standby:
				Notifications.AddNotification(Standby, True)
				Screen.close(self, False)
			else:
				quitMainloop(self.retval)
		else:
			MessageBox.close(self, True)

	def __onShow(self):
		Screens.Standby.inTryQuitMainloop = True

	def __onHide(self):
		Screens.Standby.inTryQuitMainloop = False
