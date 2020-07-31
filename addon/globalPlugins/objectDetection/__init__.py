# Object Detection global plugin main module
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import globalPluginHandler
from scriptHandler import script
from globalCommands import SCRCAT_VISION
import scriptHandler
import vision
from typing import Optional
from visionEnhancementProviders.screenCurtain import ScreenCurtainSettings
from contentRecog.recogUi import RecogResultNVDAObject

from ._doObjectDetection import *
from ._resultUI import recognizeNavigatorObject
from ._detectionResult import ObjectDetectionResults

from visionEnhancementProviders.objectDetectionHighlighter import ObjectDetectionHighlighter
from locationHelper import RectLTRB


def isScreenCurtainEnabled():
	return any([x.providerId == ScreenCurtainSettings.getId() for x in vision.handler.getActiveProviderInfos()])

_previousResult:Optional[ObjectDetectionResults] = None


class SpeakResult():
	def __init__(self, result:ObjectDetectionResults):
		global _previousResult
		_previousResult = result
		ui.message(result.sentence)

class CreateVirtualResultWindow():
	def __init__(self, result:ObjectDetectionResults):
		global _previousResult
		_previousResult = result
		sentenceResult = contentRecog.SimpleTextResult(result.sentence)
		resObj = RecogResultNVDAObject(result=sentenceResult)
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
			x = doDetectionTinyYOLOv3(SpeakResult)
			# `Alt+NVDA+D` -> filter non-graphic elements
			if scriptCount==0:
				recognizeNavigatorObject(x, True)
			# `Alt+NVDA+D+D+..` -> don't filter non-graphic elements
			else:
				recognizeNavigatorObject(x, False)
		else:
			ui.message("Screen curtain is enabled. Disable screen curtain to use the object detection add-on.")

	@script(
		description=_("Speak previous object detection result"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+Q",
	)
	def script_speakPreviousResult(self, gesture):
		global _previousResult
		SpeakResult(_previousResult)

	@script(
		description=_("Create virtual window with previous object detection result"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+W",
	)
	def script_createVirtualPreviousResultWindow(self, gesture):
		global _previousResult
		CreateVirtualResultWindow(_previousResult)

	@script(
		description=_("Draw Bounding boxes around detected objects"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+E",
	)
	def script_drawBoundingBoxes(self, gesture):
		global _previousResult
		if _previousResult:
			boxes = _previousResult.boxes
			imgInfo = _previousResult.imgInfo

			providerId = ObjectDetectionHighlighter.getSettings().getId()
			providerInfo = vision.handler.getProviderInfo(providerId)
			odh = vision.handler.getProviderInstance(providerInfo)
			if not odh:
				vision.handler.initializeProvider(providerInfo)
				odh = vision.handler.getProviderInstance(providerInfo)

			for box in boxes:
				left = box.x + imgInfo.screenLeft
				top = box.y + imgInfo.screenTop
				right = left + box.width
				bottom = top + box.height
				odh.addObjectRect(box.label, RectLTRB(left, top, right, bottom))
			ui.message("Bounding boxes presented")
