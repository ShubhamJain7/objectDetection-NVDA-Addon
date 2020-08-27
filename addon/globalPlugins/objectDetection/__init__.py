# Object Detection: global plugin main module, result presentation and result caching
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import globalPluginHandler
from scriptHandler import script
from globalCommands import SCRCAT_VISION
import vision
import ui
import time
from contentRecog import SimpleTextResult
from contentRecog.recogUi import RecogResultNVDAObject
from collections import deque

from ._doObjectDetection import DoDetectionYOLOv3
from ._detectionResult import ObjectDetectionResults
from ._resultUI import recognizeNavigatorObject

from visionEnhancementProviders.screenCurtain import ScreenCurtainSettings
from visionEnhancementProviders.objectDetection import ObjectDetection
from locationHelper import RectLTRB


def isScreenCurtainEnabled() -> bool:
	"""Checks if screen curtain is currently enabled or not. Speaks message if it is enabled.
	@return: True if screen curtain is enabled else False
	"""
	isEnabled = any([x.providerId == ScreenCurtainSettings.getId() for x in vision.handler.getActiveProviderInfos()])
	if isEnabled:
		ui.message("Screen curtain is enabled. Disable screen curtain to use the object detection add-on.")
	return isEnabled


def getObjectDetectionVisionProvider() -> ObjectDetection:
	""" Returns an instance of the ObjectDetection visionEnhancementProvider.
	@return: L{ObjectDetection} instance
	"""
	providerId = ObjectDetection.getSettings().getId()
	providerInfo = vision.handler.getProviderInfo(providerId)
	od = vision.handler.getProviderInstance(providerInfo)
	return od


# Stores the last 10 detection results
_cachedResults = deque(maxlen=10)


class SpeakResults():
	"""ResultHandlerClass that speaks the obtained result and draws boxes around the detected objects."""

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
		"""Caches the result in _cachedResults unless it is already cached. The result may already be
		cached since the same ResultHandlerClass is used to present result in case of cache hits."""
		global _cachedResults
		alreadyCached = False
		for cachedResult in _cachedResults:
			if self.result.imageHash == cachedResult.imageHash:
				alreadyCached = True
				break
		if not alreadyCached:
			_cachedResults.appendleft(self.result)


class BrowseableResults():
	""" ResultHandlerClass that presents the obtained result in a virtual result window defined at
		L{contentRecog/resultUi/RecogResultNVDAObject}.
	"""

	def __init__(self, result: ObjectDetectionResults):
		self.result = result
		self.cacheResult()

		sentenceResult = SimpleTextResult(result.sentence)
		resObj = RecogResultNVDAObject(result=sentenceResult)
		resObj.setFocus()

	def cacheResult(self):
		"""Caches the result in _cachedResults unless it is already cached. The result may already be
			cached since the same ResultHandlerClass is used to present result in case of cache hits.
		"""
		global _cachedResults
		alreadyCached = False
		for cachedResult in _cachedResults:
			if self.result.imageHash == cachedResult.imageHash:
				alreadyCached = True
				break
		if not alreadyCached:
			_cachedResults.appendleft(self.result)


# Stores timestamp of when the script was last called. Initially set to zero.
_lastCalled = 0


def recentlyCalled() -> bool:
	"""Checks if the global plugin script was called in the last three seconds or not.
	@return: True if script was called in the last three seconds, else False
	"""
	global _lastCalled
	if (time.time() - _lastCalled) <= 3:
		_lastCalled = time.time()
		return True
	else:
		_lastCalled = time.time()
		return False


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		description=_("Perform object detection on focused image. Press once to speak result, more than "
					"once to present result in a virtual window."),
		category=SCRCAT_VISION
	)
	def script_detectObjectsYOLOv3(self, gesture):
		global _cachedResults
		wasRecentlyCalled = recentlyCalled()
		od: ObjectDetection = getObjectDetectionVisionProvider()
		# get filterNonGraphic preference
		filterNonGraphic = ObjectDetection.getSettings().filterNonGraphicElements

		# If the screen curtain is enabled, a screenshot of the element will only contain black pixels.
		# Such an image won't produce good results so inform the user and quit.
		if not isScreenCurtainEnabled():
			# Script not called in the last 3 seconds so use SpeakResults as resultHandlerClass
			if not wasRecentlyCalled:
				# if the bounding boxes are still being displayed, the user has not moved on to another
				# image and so we can just present the previous result.
				if od.currentlyDisplayingRects():
					od.clearObjectRects()
					# The most recent/previous result is stored at index 0
					SpeakResults(_cachedResults[0])
				else:
					recognizer = DoDetectionYOLOv3(resultHandlerClass=SpeakResults, timeCreated=time.time())
					recognizeNavigatorObject(recognizer, filterNonGraphic=filterNonGraphic,
											cachedResults=_cachedResults)

			# Script was called in the last 3 seconds so the user probably pressed the gesture multiple times and
			# wants the result to be presented in a virtual result window.
			else:
				if od.currentlyDisplayingRects():
					od.clearObjectRects()
					BrowseableResults(_cachedResults[0])
				else:
					recognizer = DoDetectionYOLOv3(resultHandlerClass=BrowseableResults, timeCreated=time.time())
					recognizeNavigatorObject(recognizer, filterNonGraphic=filterNonGraphic,
											cachedResults=_cachedResults)
