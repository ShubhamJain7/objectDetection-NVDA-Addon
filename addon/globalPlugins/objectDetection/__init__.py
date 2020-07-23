# Object Detection global plugin main module
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License
from typing import Optional

import globalPluginHandler
from scriptHandler import script
from globalCommands import SCRCAT_VISION
import ui
import scriptHandler
import vision
from visionEnhancementProviders.screenCurtain import ScreenCurtainSettings
from contentRecog.recogUi import RecogResultNVDAObject

from ._doObjectDetection import *
from ._resultUI import getNavigatorObjectImage

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

_activeRecognizer = None

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	@script(
		# Translators: Input trigger to perform object detection on focused image
		description=_("Perform object detection on focused image"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+D",
	)
	def script_detectObjectsTinyYOLOv3(self, gesture):
		global _activeRecognizer
		if _activeRecognizer:
			_activeRecognizer.cancel()
		if not isScreenCurtainEnabled():
			recognizer = doDetectionTinyYOLOv3(PresentResults)
			imageDetails = getNavigatorObjectImage(recognizer, False)
			if imageDetails:
				pixels, imgInfo = imageDetails
				ui.message("Recognizing")
				_activeRecognizer = recognizer
				handler: PresentResults = recognizer.recognize(pixels, imgInfo, None)
				if handler:
					handler.createVirtualWindow()
				_activeRecognizer = None
		else:
			ui.message("Screen curtain is enabled. Disable screen curtain to use the object detection add-on.")