# Object Detection global plugin main module
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import globalPluginHandler
from scriptHandler import script
from globalCommands import SCRCAT_VISION
import vision
from typing import Optional
from collections import deque
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

_cachedResults = deque(maxlen=10)

class PresentResults():
	def __init__(self, result:ObjectDetectionResults):
		self.result = result
		self.cacheResult()

		sentence = result.sentence
		boxes = result.boxes
		imgInfo = result.imgInfo

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

	def cacheResult(self):
		global  _cachedResults
		alreadyCached = False
		for cachedResult in _cachedResults:
			if self.result.imageHash == cachedResult.imageHash:
				alreadyCached = True
				break
		if not alreadyCached:
			_cachedResults.appendleft(self.result)


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		# Translators: Input trigger to perform object detection on focused image
		description=_("Perform object detection on focused image"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+D",
	)
	def script_detectObjectsTinyYOLOv3(self, gesture):
		global _cachedResults
		if not isScreenCurtainEnabled():
			recognizer = doDetectionTinyYOLOv3(PresentResults)
			filterNonGraphic = ObjectDetectionHighlighter.getSettings().filterNonGraphicElements
			recognizeNavigatorObject(recognizer, filterNonGraphic=filterNonGraphic, cachedResults=_cachedResults)

	@script(
		description=_("Present object detection result in a virtual window"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+V",
	)
	def script_virtualResultWindow(self, gesture):
		global _cachedResults
		lastResult = _cachedResults[-1]
		sentenceResult = contentRecog.SimpleTextResult(lastResult.sentence)
		resObj = VirtualResultWindow(result=sentenceResult)
		# This method queues an event to the main thread.
		resObj.setFocus()
