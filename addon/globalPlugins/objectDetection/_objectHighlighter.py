from autoSettingsUtils.autoSettings import SupportedSettingType
import vision
from vision.visionHandlerExtensionPoints import EventExtensionPoints
from vision import providerBase
from windowUtils import CustomWindow
import wx
from typing import Optional
from ctypes import byref, WinError
from ctypes.wintypes import COLORREF, MSG
import winUser
from logHandler import log
from mouseHandler import getTotalWidthAndHeightAndMinimumPosition
from locationHelper import RectLTWH
from collections import namedtuple
import threading
import winGDI
import weakref
from colors import RGB
import core


class HighlightStyle(
		namedtuple("HighlightStyle", ("color", "width", "style", "margin"))
):
	"""Represents the style of a highlight for a particular context.
	@ivar color: The color to use for the style
	@type color: L{RGB}
	@ivar width: The width of the lines to be drawn, in pixels.
		A higher width reduces the inner dimensions of the rectangle.
		Therefore, if you need to increase the outer dimensions of the rectangle,
		you need to increase the margin as well.
	@type width: int
	@ivar style: The style of the lines to be drawn;
		One of the C{winGDI.DashStyle*} enumeration constants.
	@type style: int
	@ivar margin: The number of pixels between the highlight's rectangle
		and the rectangle of the object to be highlighted.
		A higher margin stretches the highlight's rectangle.
		This value may also be negative.
	@type margin: int
	"""

BLUE = RGB(0x03, 0x36, 0xFF)
PINK = RGB(0xFF, 0x02, 0x66)
YELLOW = RGB(0xFF, 0xDE, 0x03)
DASH_BLUE = HighlightStyle(BLUE, 5, winGDI.DashStyleDash, 5)
SOLID_PINK = HighlightStyle(PINK, 5, winGDI.DashStyleSolid, 5)
SOLID_BLUE = HighlightStyle(BLUE, 5, winGDI.DashStyleSolid, 5)
SOLID_YELLOW = HighlightStyle(YELLOW, 2, winGDI.DashStyleSolid, 2)


class ObjectHighlightWindow(CustomWindow):
	transparency = 0xff
	className = u"ObjectHighLighter"
	windowName = u"Object Highlighter Window"
	windowStyle = winUser.WS_POPUP | winUser.WS_DISABLED
	extendedWindowStyle = (
		# Ensure that the window is on top of all other windows
		winUser.WS_EX_TOPMOST
		# A layered window ensures that L{transparentColor} will be considered transparent, when painted
		| winUser.WS_EX_LAYERED
		# Ensure that the window can't be activated when pressing alt+tab
		| winUser.WS_EX_NOACTIVATE
		# Make this a transparent window,
		# primarily for accessibility APIs to ignore this window when getting a window from a screen point
		| winUser.WS_EX_TRANSPARENT
	)
	transparentColor = 0  # Black

	@classmethod
	def _get__wClass(cls):
		wClass = super()._wClass
		wClass.style = winUser.CS_HREDRAW | winUser.CS_VREDRAW
		wClass.hbrBackground = winGDI.gdi32.CreateSolidBrush(COLORREF(cls.transparentColor))
		return wClass

	def updateLocationForDisplays(self):
		if vision._isDebug():
			log.debug("Updating ObjectHighLighter window location for displays")
		displays = [wx.Display(i).GetGeometry() for i in range(wx.Display.GetCount())]
		screenWidth, screenHeight, minPos = getTotalWidthAndHeightAndMinimumPosition(displays)
		# Hack: Windows has a "feature" that will stop desktop shortcut hotkeys from working
		# when a window is full screen.
		# Removing one line of pixels from the bottom of the screen will fix this.
		left = minPos.x
		top = minPos.y
		width = screenWidth
		height = screenHeight - 1
		self.location = RectLTWH(left, top, width, height)
		winUser.user32.ShowWindow(self.handle, winUser.SW_HIDE)
		if not winUser.user32.SetWindowPos(
			self.handle,
			winUser.HWND_TOPMOST,
			left, top, width, height,
			winUser.SWP_NOACTIVATE
		):
			raise WinError()
		winUser.user32.ShowWindow(self.handle, winUser.SW_SHOWNA)

	def __init__(self, highlighter):
		if vision._isDebug():
			log.debug("initializing ObjectHighLighter window")
		super().__init__(
			windowName=self.windowName,
			windowStyle=self.windowStyle,
			extendedWindowStyle=self.extendedWindowStyle
		)
		self.location = None
		self.highlighterRef = weakref.ref(highlighter)
		winUser.SetLayeredWindowAttributes(
			self.handle,
			self.transparentColor,
			self.transparency,
			winUser.LWA_ALPHA | winUser.LWA_COLORKEY)
		self.updateLocationForDisplays()
		if not winUser.user32.UpdateWindow(self.handle):
			raise WinError()

	def windowProc(self, hwnd, msg, wParam, lParam):
		if msg == winUser.WM_PAINT:
			self._paint()
			# Ensure the window is top most
			winUser.user32.SetWindowPos(
				self.handle,
				winUser.HWND_TOPMOST,
				0, 0, 0, 0,
				winUser.SWP_NOACTIVATE | winUser.SWP_NOMOVE | winUser.SWP_NOSIZE
			)
		elif msg == winUser.WM_DESTROY:
			winUser.user32.PostQuitMessage(0)
		elif msg == winUser.WM_TIMER:
			self.refresh()
		elif msg == winUser.WM_DISPLAYCHANGE:
			# wx might not be aware of the display change at this point
			core.callLater(100, self.updateLocationForDisplays)

	def _paint(self):
		highlighter = self.highlighterRef()
		if not highlighter:
			# The highlighter instance died unexpectedly, kill the window as well
			winUser.user32.PostQuitMessage(0)
			return
		with winUser.paint(self.handle) as hdc:
			with winGDI.GDIPlusGraphicsContext(hdc) as graphicsContext:
				for label, rect in highlighter.objectRects:
					HighlightStyle = SOLID_BLUE
					# Before calculating logical coordinates,
					# make sure the rectangle falls within the highlighter window
					rect = rect.intersection(self.location)
					try:
						rect = rect.toLogical(self.handle)
					except RuntimeError:
						log.debugWarning("", exc_info=True)
					rect = rect.toClient(self.handle)
					try:
						rect = rect.expandOrShrink(HighlightStyle.margin)
					except RuntimeError:
						pass
					with winGDI.GDIPlusPen(
						HighlightStyle.color.toGDIPlusARGB(),
						HighlightStyle.width,
						HighlightStyle.style
					) as pen:
						winGDI.gdiPlusDrawRectangle(graphicsContext, pen, *rect.toLTWH())

	def refresh(self):
		winUser.user32.InvalidateRect(self.handle, None, True)


class ObjectHighlighterSettings(providerBase.VisionEnhancementProviderSettings):
	@classmethod
	def getId(cls) -> str:
		return "NVDAHighlighter"

	@classmethod
	def getDisplayName(cls) -> str:
		return _("Object Highlight")

	def _get_supportedSettings(self) -> SupportedSettingType:
		return list()

class ObjectHighlighter(providerBase.VisionEnhancementProvider):
	_refreshInterval = 100
	customWindowClass = ObjectHighlightWindow
	_settings = ObjectHighlighterSettings()
	_window: Optional[customWindowClass] = None

	@classmethod  # override
	def getSettings(cls) -> ObjectHighlighterSettings:
		return cls._settings

	@classmethod  # override
	def getSettingsPanelClass(cls):
		return None

	@classmethod  # override
	def canStart(cls) -> bool:
		return True

	def registerEventExtensionPoints(  # override
			self,
			extensionPoints: EventExtensionPoints
	) -> None:
		extensionPoints.post_focusChange.register(self.handleFocusChange)
		extensionPoints.post_reviewMove.register(self.handleReviewMove)
		extensionPoints.post_browseModeMove.register(self.handleBrowseModeMove)

	def __init__(self):
		super().__init__()
		log.debug("Starting ObjectHighLighter")
		self.objectRects = []
		winGDI.gdiPlusInitialize()
		self._highlighterThread = threading.Thread(
			name=f"{self.__class__.__module__}.{self.__class__.__qualname__}",
			target=self._run
		)
		self._highlighterRunningEvent = threading.Event()
		self._highlighterThread.daemon = True
		self._highlighterThread.start()
		# Make sure the highlighter thread doesn't exit early.
		waitResult = self._highlighterRunningEvent.wait(0.2)
		if waitResult is False or not self._highlighterThread.is_alive():
			raise RuntimeError("Highlighter thread wasn't able to initialize correctly")

	def terminate(self):
		log.debug("Terminating ObjectHighLighter")
		if self._highlighterThread and self._window and self._window.handle:
			if not winUser.user32.PostThreadMessageW(self._highlighterThread.ident, winUser.WM_QUIT, 0, 0):
				raise WinError()
			else:
				self._highlighterThread.join()
			self._highlighterThread = None
		winGDI.gdiPlusTerminate()
		self.objectRects.clear()
		super().terminate()

	def _run(self):
		try:
			if vision._isDebug():
				log.debug("Starting ObjectHighLighter thread")

			window = self._window = self.customWindowClass(self)
			timer = winUser.WinTimer(window.handle, 0, self._refreshInterval, None)
			self._highlighterRunningEvent.set()  # notify main thread that initialisation was successful
			msg = MSG()
			# Python 3.8 note, Change this to use an Assignment expression to catch a return value of -1.
			# See the remarks section of
			# https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getmessage
			while winUser.getMessage(byref(msg), None, 0, 0) > 0:
				winUser.user32.TranslateMessage(byref(msg))
				winUser.user32.DispatchMessageW(byref(msg))
			if vision._isDebug():
				log.debug("Quit message received on ObjectHighLighter thread")
			timer.terminate()
			window.destroy()
		except Exception:
			log.exception("Exception in NVDA Highlighter thread")

	def handleFocusChange(self, obj):
		pass
		# self.updateContextRect(context=Context.FOCUS, obj=obj)
		# if not api.isObjectInActiveTreeInterceptor(obj):
		# 	self.contextToRectMap.pop(Context.BROWSEMODE, None)
		# else:
		# 	self.handleBrowseModeMove()

	def handleReviewMove(self, context):
		pass
		# self.updateContextRect(context=Context.NAVIGATOR)

	def handleBrowseModeMove(self, obj=None):
		pass
		# self.updateContextRect(context=Context.BROWSEMODE)

	def refresh(self):
		"""Refreshes the screen positions of the enabled highlights.
		"""
		if self._window and self._window.handle:
			self._window.refresh()

	def addObjectRect(self, label:str, rect:RectLTWH):
		self.objectRects.append((label ,rect))

VisionEnhancementProvider = ObjectHighlighter