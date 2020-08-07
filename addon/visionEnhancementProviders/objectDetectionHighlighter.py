from autoSettingsUtils.autoSettings import SupportedSettingType
import vision
from vision.visionHandlerExtensionPoints import EventExtensionPoints
from vision import providerBase
from windowUtils import CustomWindow
import wx
from typing import Optional, List
from ctypes import byref, WinError
from ctypes.wintypes import COLORREF, MSG
import winUser
from logHandler import log
from mouseHandler import getTotalWidthAndHeightAndMinimumPosition
from locationHelper import RectLTRB, RectLTWH
from collections import namedtuple
import threading
import winGDI
import weakref
from colors import RGB
import core
import ui
import driverHandler


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


COLORS = [RGB(0xE7, 0x4C, 0x3C), RGB(0x9B, 0x59, 0xB6), RGB(0x34, 0x98, 0xDB), RGB(0x2C, 0x3E, 0x50),
		  RGB(0xE6, 0x7E, 0x22), RGB(0xC0, 0x39, 0x2B), RGB(0x16, 0xA0, 0x85), RGB(0x27, 0xAE, 0x60),
		  RGB(0x2E, 0xCC, 0x71), RGB(0xF1, 0xC4, 0x0F), RGB(0xF3, 0x9C, 0x12), RGB(0xEC, 0xF0, 0xF1),
		  RGB(0xD3, 0x54, 0x00), RGB(0x29, 0x80, 0xB9), RGB(0x7F, 0x8C, 0x8D), RGB(0x8E, 0x44, 0xAD)]


class ObjectDetectionHighlightWindow(CustomWindow):
	transparency = 0xff
	className = u"ObjectDetectionHighLighter"
	windowName = u"Object Detection Highlighter Window"
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
			log.debug("Updating ObjectDetectionHighLighter window location for displays")
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
			log.debug("initializing ObjectDetectionHighLighter window")
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
				for i, (label, rect) in enumerate(highlighter.objectRects):
					borderStyle = HighlightStyle(COLORS[i % len(COLORS)], 5, winGDI.DashStyleSolid, 5)
					# Before calculating logical coordinates,
					# make sure the rectangle falls within the highlighter window
					rect = rect.intersection(self.location)
					try:
						rect = rect.toLogical(self.handle)
					except RuntimeError:
						log.debugWarning("", exc_info=True)
					rect = rect.toClient(self.handle)
					try:
						rect = rect.expandOrShrink(borderStyle.margin)
					except RuntimeError:
						pass
					with winGDI.GDIPlusPen(
							borderStyle.color.toGDIPlusARGB(),
							borderStyle.width,
							borderStyle.style
					) as pen:
						winGDI.gdiPlusDrawRectangle(graphicsContext, pen, *rect.toLTWH())

	def refresh(self):
		winUser.user32.InvalidateRect(self.handle, None, True)


class ObjectDetectionHighlighterSettings(providerBase.VisionEnhancementProviderSettings):
	filterNonGraphicElements = True

	@classmethod
	def getId(cls) -> str:
		return "ObjectDetectionHighlighter"

	@classmethod
	def getDisplayName(cls) -> str:
		return _("Object Detection Highlighter")

	def _get_supportedSettings(self) -> SupportedSettingType:
		settings = [
			driverHandler.BooleanDriverSetting(
				"filterNonGraphicElements",
				"filter non-graphic elements",
				defaultVal=True
			)
		]
		return settings


class ObjectDetectionHighlighter(providerBase.VisionEnhancementProvider):
	_refreshInterval = 100
	customWindowClass = ObjectDetectionHighlightWindow
	_settings = ObjectDetectionHighlighterSettings()
	_window: Optional[customWindowClass] = None

	@classmethod  # override
	def getSettings(cls) -> ObjectDetectionHighlighterSettings:
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
		extensionPoints.post_mouseMove.register(self.handleMouseMove)
		extensionPoints.post_focusChange.register(self.handleFocusChange)

	def __init__(self):
		super().__init__()
		log.debug("Starting ObjectDetectionHighLighter")
		self.objectRects = []
		self.announce = []
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
		log.debug("Terminating ObjectDetectionHighLighter")
		if self._highlighterThread and self._window and self._window.handle:
			if not winUser.user32.PostThreadMessageW(self._highlighterThread.ident, winUser.WM_QUIT, 0, 0):
				raise WinError()
			else:
				self._highlighterThread.join()
			self._highlighterThread = None
		winGDI.gdiPlusTerminate()
		self.clearObjectRects()
		super().terminate()

	def _run(self):
		try:
			if vision._isDebug():
				log.debug("Starting ObjectDetectionHighLighter thread")

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
				log.debug("Quit message received on ObjectDetectionHighLighter thread")
			timer.terminate()
			window.destroy()
		except Exception:
			log.exception("Exception in Object Detection Highlighter thread")

	def handleMouseMove(self, obj, x, y):
		for i in range(len(self.objectRects)):
			label, rect = self.objectRects[i]
			if rect.left < x < rect.right and rect.top < y < rect.bottom:
				if self.announce[i]:
					ui.message(label)
					self.announce[i] = False
			else:
				if not self.announce[i]:
					self.announce[i] = True

	def handleFocusChange(self, obj):
		self.clearObjectRects()

	def refresh(self):
		"""Refreshes the screen positions of the enabled highlights.
		"""
		if self._window and self._window.handle:
			self._window.refresh()

	def addObjectRect(self, label: str, rect: RectLTRB):
		self.objectRects.append((label, rect))
		self.announce.append(True)

	def clearObjectRects(self):
		if self.objectRects:
			self.objectRects.clear()


VisionEnhancementProvider = ObjectDetectionHighlighter
