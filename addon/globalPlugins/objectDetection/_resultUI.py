# Object Detection: navigator object recognition, recognition tracking
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import api
import ui
import time
import screenBitmap
from typing import Optional
from logHandler import log
import queueHandler
from contentRecog import ContentRecognizer, RecogImageInfo
from contentRecog.recogUi import RecogResultNVDAObject


#: Keeps track of the recognition in progress, if any.
_activeRecog: Optional[ContentRecognizer] = None

def recognizeNavigatorObject(recognizer, filterNonGraphic=True, cachedResults=None):
	"""User interface function to recognize content in the navigator object.
	This should be called from a script or in response to a GUI action.
	@param recognizer: The content recognizer to use.
	@type recognizer: L{contentRecog.ContentRecognizer}
	"""
	global _activeRecog
	if isinstance(api.getFocusObject(), RecogResultNVDAObject):
		# Translators: Reported when content recognition (e.g. OCR) is attempted,
		# but the user is already reading a content recognition result.
		ui.message(_("Already in a content recognition result"))
		return
	nav = api.getNavigatorObject()

	if filterNonGraphic and not recognizer.validateObject(nav):
		return
	# Translators: Reported when content recognition (e.g. OCR) is attempted,
	# but the content is not visible.
	notVisibleMsg = _("Content is not visible")
	try:
		left, top, width, height = nav.location
	except TypeError:
		log.debugWarning("Object returned location %r" % nav.location)
		ui.message(notVisibleMsg)
		return
	if not recognizer.validateBounds(nav.location):
		return
	try:
		imgInfo = RecogImageInfo.createFromRecognizer(left, top, width, height, recognizer)
	except ValueError:
		ui.message(notVisibleMsg)
		return

	if _activeRecog:
		if not (0 < (time.time() - _activeRecog.timeCreated) <= 3):
			ui.message("Already running an object detection process. Please try again later.")
			return
		else:
			_activeRecog.cancel()

	sb = screenBitmap.ScreenBitmap(imgInfo.recogWidth, imgInfo.recogHeight)
	pixels = sb.captureImage(left, top, width, height)

	rowHashes = []
	for i in range(imgInfo.recogWidth):
		row = []
		for j in range(imgInfo.recogHeight):
			row.append(pixels[j][i].rgbRed)  # column major order
		rowHashes.append(hash(str(row)))

	imageHash = hash(str(rowHashes))
	for result in cachedResults:
		if result.imageHash == imageHash:
			handler = recognizer.getResultHandler(result)
			return

	# Translators: Reporting when content recognition (e.g. OCR) begins.
	ui.message(_("Recognizing"))

	_activeRecog = recognizer

	recognizer.recognize(imageHash, pixels, imgInfo, _recogOnResult)


def _recogOnResult(result):
	global _activeRecog
	recognizer: ContentRecognizer = _activeRecog
	_activeRecog = None
	# This might get called from a background thread, so any UI calls must be queued to the main thread.
	if isinstance(result, Exception):
		# Translators: Reported when recognition (e.g. OCR) fails.
		log.error("Recognition failed: %s" % result)
		queueHandler.queueFunction(queueHandler.eventQueue, ui.message, _("Recognition failed"))
		return
	if recognizer:
		handler = recognizer.getResultHandler(result)
