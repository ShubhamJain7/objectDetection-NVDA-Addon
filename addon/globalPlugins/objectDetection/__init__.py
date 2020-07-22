# Object Detection global plugin main module
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import globalPluginHandler
from scriptHandler import script
from globalCommands import SCRCAT_VISION
import ui
import scriptHandler
import vision
from visionEnhancementProviders.screenCurtain import ScreenCurtainSettings
from contentRecog.recogUi import RecogResultNVDAObject

from ._doObjectDetection import *
from ._resultUI import recognizeNavigatorObject

def isScreenCurtainEnabled():
	return any([x.providerId == ScreenCurtainSettings.getId() for x in vision.handler.getActiveProviderInfos()])


class PresentResults():
	def __init__(self, result):
		self.result = result

	def speakResult(self):
		ui.message(self.result)

	def createVirtualWindow(self):
		result = contentRecog.SimpleTextResult(self.result)
		resObj = RecogResultNVDAObject(result=result)
		# This method queues an event to the main thread.
		resObj.setFocus()

	def speakResultAndCreateVirtualWindow(self):
		ui.message(self.result)
		result = contentRecog.SimpleTextResult(self.result)
		resObj = RecogResultNVDAObject(result=result)
		# This method queues an event to the main thread.
		resObj.setFocus()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		# Translators: Input trigger to perform object detection on focused image
		description=_("Perform object detection on focused image"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+D",
	)
	def script_detectObjectsTinyYOLOv3(self, gesture):
		scriptCount = scriptHandler.getLastScriptRepeatCount()
		if not isScreenCurtainEnabled():
			x = doDetectionTinyYOLOv3(PresentResults)
			# `Alt+NVDA+D` -> filter non-graphic elements
			if scriptCount==0:
				recognizeNavigatorObject(x, True)
			# `Alt+NVDA+D+D+..` -> don't filter non-graphic elements
			else:
				recognizeNavigatorObject(x, False)
		else:
			ui.message("Screen curtain is enabled. Disable screen curtain to use the object detection add-on.")

	# def script_detectObjectsYOLOv3(self, gesture):
	# 	x = doDetectionYOLOv3()
	# 	recogUi.recognizeNavigatorObject(x)

	# def script_detectObjectsDETR(self, gesture):
	# 	x = doDetectionDETR()
	# 	recogUi.recognizeNavigatorObject(x)