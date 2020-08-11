# Object Detection global plugin main module
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import globalPluginHandler
import scriptHandler
from scriptHandler import script
from globalCommands import SCRCAT_VISION
import vision
from collections import deque
from visionEnhancementProviders.screenCurtain import ScreenCurtainSettings
import ui
import time
from contentRecog import SimpleTextResult
from logHandler import log

from ._doObjectDetection import DoDetectionYOLOv3
from ._resultUI import recognizeNavigatorObject, VirtualResultWindow
from ._detectionResult import ObjectDetectionResults

from visionEnhancementProviders.objectDetection import ObjectDetection
from locationHelper import RectLTRB


def isScreenCurtainEnabled():
	isEnabled = any([x.providerId == ScreenCurtainSettings.getId() for x in vision.handler.getActiveProviderInfos()])
	if isEnabled:
		ui.message("Screen curtain is enabled. Disable screen curtain to use the object detection add-on.")
	return isEnabled

def getObjectDetectionVisionProvider():
	providerId = ObjectDetection.getSettings().getId()
	providerInfo = vision.handler.getProviderInfo(providerId)
	od = vision.handler.getProviderInstance(providerInfo)
	return od


_cachedResults = deque(maxlen=10)

class SpeakResults():
	def __init__(self, result: ObjectDetectionResults):
		self.result = result
		self.cacheResult()

		sentence = result.sentence
		boxes = result.getAdjustedLTRBBoxes()

		ui.message(sentence)

		if not boxes:
			return

		od = getObjectDetectionVisionProvider()
		for box in boxes:
			od.addObjectRect(box.label, RectLTRB(box.left, box.top, box.right, box.bottom))

	def cacheResult(self):
		global _cachedResults
		alreadyCached = False
		for cachedResult in _cachedResults:
			if self.result.imageHash == cachedResult.imageHash:
				alreadyCached = True
				break
		if not alreadyCached:
			_cachedResults.appendleft(self.result)

class BrowseableResults():
	def __init__(self, result: ObjectDetectionResults):
		self.result = result
		self.cacheResult()

		sentenceResult = SimpleTextResult(result.sentence)
		resObj = VirtualResultWindow(result=sentenceResult)
		resObj.setFocus()

	def cacheResult(self):
		global _cachedResults
		alreadyCached = False
		for cachedResult in _cachedResults:
			if self.result.imageHash == cachedResult.imageHash:
				alreadyCached = True
				break
		if not alreadyCached:
			_cachedResults.appendleft(self.result)
			

_lastCalled = 0
def getScriptCount():
	global _lastCalled
	if 0<(time.time() - _lastCalled)<=3:
		_lastCalled = time.time()
		return 1
	else:
		_lastCalled = time.time()
		return 0


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		description=_("Perform object detection on focused image"),
		category=SCRCAT_VISION
	)
	def script_detectObjectsYOLOv3(self, gesture):
		global _cachedResults
		scriptCount = getScriptCount()
		od = getObjectDetectionVisionProvider()
		filterNonGraphic = ObjectDetection.getSettings().filterNonGraphicElements
		if not isScreenCurtainEnabled():
			if scriptCount == 0:
				if od.currentlyDisplayingRects():
					od.clearObjectRects()
					SpeakResults(_cachedResults[0])
				else:
					recognizer = DoDetectionYOLOv3(SpeakResults)
					recognizeNavigatorObject(recognizer, filterNonGraphic=filterNonGraphic,
											cachedResults=_cachedResults)
			else:
				if od.currentlyDisplayingRects():
					od.clearObjectRects()
					BrowseableResults(_cachedResults[0])
				else:
					recognizer = DoDetectionYOLOv3(BrowseableResults)
					recognizeNavigatorObject(recognizer, filterNonGraphic=filterNonGraphic,
											cachedResults=_cachedResults)
