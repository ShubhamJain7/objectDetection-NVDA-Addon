from typing import Optional

import api
import ui
import screenBitmap
from logHandler import log
import queueHandler
from contentRecog import ContentRecognizer, RecogImageInfo
import NVDAObjects.window
import controlTypes
import browseMode
import cursorManager
import eventHandler
import textInfos


class VirtualResultWindow(cursorManager.CursorManager, NVDAObjects.window.Window):
	"""Fake NVDAObject used to present a recognition result in a cursor manager.
	This allows the user to read the result with cursor keys, etc.
	Pressing enter will activate (e.g. click) the text at the cursor.
	Pressing escape dismisses the recognition result.
	"""

	role = controlTypes.ROLE_DOCUMENT
	# Translators: The title of the document used to present the result of content recognition.
	name = _("Result")
	treeInterceptor = None

	def __init__(self, result=None, objectDetectionHandler=None):
		self.parent = parent = api.getFocusObject()
		self.result = result
		self.objectDetectionHandler = objectDetectionHandler
		self._selection = self.makeTextInfo(textInfos.POSITION_FIRST)
		super(VirtualResultWindow, self).__init__(windowHandle=parent.windowHandle)

	def makeTextInfo(self, position):
		# Maintain our own fake selection/caret.
		if position == textInfos.POSITION_SELECTION:
			ti = self._selection.copy()
		elif position == textInfos.POSITION_CARET:
			ti = self._selection.copy()
			ti.collapse()
		else:
			ti = self.result.makeTextInfo(self, position)
		return self._patchTextInfo(ti)

	def _patchTextInfo(self, info):
		# Patch TextInfos so that updateSelection/Caret updates our fake selection.
		info.updateCaret = lambda: self._setSelection(info, True)
		info.updateSelection = lambda: self._setSelection(info, False)
		# Ensure any copies get patched too.
		oldCopy = info.copy
		info.copy = lambda: self._patchTextInfo(oldCopy())
		return info

	def _setSelection(self, textInfo, collapse):
		self._selection = textInfo.copy()
		if collapse:
			self._selection.collapse()

	def setFocus(self):
		ti = self.parent.treeInterceptor
		if isinstance(ti, browseMode.BrowseModeDocumentTreeInterceptor):
			# Normally, when entering browse mode from a descendant (e.g. dialog),
			# we want the cursor to move to the focus (#3145).
			# However, we don't want this for recognition results, as these aren't focusable.
			ti._enteringFromOutside = True
		# This might get called from a background thread and all NVDA events must run in the main thread.
		eventHandler.queueEvent("gainFocus", self)

	def script_exit(self, gesture):
		self.objectDetectionHandler.clearObjectRects()
		eventHandler.executeEvent("gainFocus", self.parent)
	# Translators: Describes a command.
	script_exit.__doc__ = _("Dismiss the recognition result")

	# The find commands are tricky to support because they pop up dialogs.
	# This moves the focus, so we lose our fake focus.
	# See https://github.com/nvaccess/nvda/pull/7361#issuecomment-314698991
	def script_find(self, gesture):
		# Translators: Reported when a user tries to use a find command when it isn't supported.
		ui.message(_("Not supported in this document"))

	def script_findNext(self, gesture):
		# Translators: Reported when a user tries to use a find command when it isn't supported.
		ui.message(_("Not supported in this document"))

	def script_findPrevious(self, gesture):
		# Translators: Reported when a user tries to use a find command when it isn't supported.
		ui.message(_("Not supported in this document"))

	def event_loseFocus(self):
		self.objectDetectionHandler.clearObjectRects()

	__gestures = {
		"kb:escape": "exit",
	}

#: Keeps track of the recognition in progress, if any.
_activeRecog: Optional[ContentRecognizer] = None

def recognizeNavigatorObject(recognizer, filterNonGraphic=True):
	"""User interface function to recognize content in the navigator object.
	This should be called from a script or in response to a GUI action.
	@param recognizer: The content recognizer to use.
	@type recognizer: L{contentRecog.ContentRecognizer}
	"""
	global _activeRecog
	if isinstance(api.getFocusObject(), VirtualResultWindow):
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
		handler = recognizer.getResultHandler(result)
