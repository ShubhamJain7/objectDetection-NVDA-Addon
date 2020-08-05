# Object Detection global plugin main module
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import globalPluginHandler
from scriptHandler import script
from globalCommands import SCRCAT_VISION
import vision
from typing import Optional
from visionEnhancementProviders.screenCurtain import ScreenCurtainSettings

from ._doObjectDetection import *
from ._resultUI import recognizeNavigatorObject, VirtualResultWindow
from ._detectionResult import ObjectDetectionResults

from visionEnhancementProviders.objectDetectionHighlighter import ObjectDetectionHighlighter
from locationHelper import RectLTRB


def isScreenCurtainEnabled():
	isEnabled = any([x.providerId == ScreenCurtainSettings.getId() for x in vision.handler.getActiveProviderInfos()])
	if isEnabled:
		ui.message("Screen curtain is enabled. Disable screen curtain to use the object detection add-on.")
	return isEnabled

_previousResult:Optional[ObjectDetectionResults] = None


class PresentResults():
	def __init__(self, result:ObjectDetectionResults):
		global _previousResult
		_previousResult = result
		sentence = _previousResult.sentence
		boxes = _previousResult.boxes
		imgInfo = _previousResult.imgInfo

		ui.message(sentence)

		if not boxes:
			return

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

		sentenceResult = contentRecog.SimpleTextResult(result.sentence)
		resObj = VirtualResultWindow(result=sentenceResult, objectDetectionHandler=odh)
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
		if not isScreenCurtainEnabled():
			x = doDetectionTinyYOLOv3(PresentResults)
			filterNonGraphic = ObjectDetectionHighlighter.getSettings().filterNonGraphicElements
			recognizeNavigatorObject(x, filterNonGraphic=filterNonGraphic)

	@script(
		description=_("Present previous object detection result"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+Q",
	)
	def script_speakPreviousResult(self, gesture):
		global _previousResult
		PresentResults(_previousResult)
