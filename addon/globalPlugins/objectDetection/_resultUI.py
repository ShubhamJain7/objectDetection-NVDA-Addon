from typing import Optional

import api
import ui
import screenBitmap
from logHandler import log
import queueHandler
from contentRecog import ContentRecognizer, RecogImageInfo
from contentRecog.recogUi import RecogResultNVDAObject

#: Keeps track of the recognition in progress, if any.
_activeRecog: Optional[ContentRecognizer] = None

def recognizeNavigatorObject(recognizer, filterNonGraphic=True):
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
	if not recognizer.validateBounds(left, top, width, height):
		return
	try:
		imgInfo = RecogImageInfo.createFromRecognizer(left, top, width, height, recognizer)
	except ValueError:
		ui.message(notVisibleMsg)
		return
	if _activeRecog:
		_activeRecog.cancel()
	# Translators: Reporting when content recognition (e.g. OCR) begins.
	ui.message(_("Recognizing"))
	sb = screenBitmap.ScreenBitmap(imgInfo.recogWidth, imgInfo.recogHeight)
	pixels = sb.captureImage(left, top, width, height)
	_activeRecog = recognizer

	recognizer.recognize(pixels, imgInfo, _recogOnResult)

def _recogOnResult(result):
	global _activeRecog
	recognizer: ContentRecognizer = _activeRecog
	_activeRecog = None
	# This might get called from a background thread, so any UI calls must be queued to the main thread.
	if isinstance(result, Exception):
		# Translators: Reported when recognition (e.g. OCR) fails.
		log.error("Recognition failed: %s" % result)
		queueHandler.queueFunction(queueHandler.eventQueue,
			ui.message, _("Recognition failed"))
		return
	if recognizer:
		handler = recognizer.createResultHandler(result)
