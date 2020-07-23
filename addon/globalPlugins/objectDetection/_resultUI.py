import api
import ui
import screenBitmap
from logHandler import log
from contentRecog import RecogImageInfo
from contentRecog.recogUi import RecogResultNVDAObject

def getNavigatorObjectImage(recognizer, filterNonGraphic=True):
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
		return None
	if not recognizer.validateBounds(left, top, width, height):
		return None
	try:
		imgInfo = RecogImageInfo.createFromRecognizer(left, top, width, height, recognizer)
	except ValueError:
		ui.message(notVisibleMsg)
		return
	sb = screenBitmap.ScreenBitmap(imgInfo.recogWidth, imgInfo.recogHeight)
	pixels = sb.captureImage(left, top, width, height)
	return (pixels, imgInfo)
