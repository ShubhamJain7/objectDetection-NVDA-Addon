# Object Detection: YOLOv3 object detection class
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import os
import threading
import tempfile
import wx
import ui
from typing import Any
import contentRecog
from logHandler import log
from locationHelper import RectLTWH
from controlTypes import ROLE_GRAPHIC

from ._detectionResult import ObjectDetectionResults
from ._YOLOv3 import YOLOv3Detection

#: Elements with width or height small than this value will not be processed
_sizeThreshold = 128


class DoDetectionYOLOv3(contentRecog.ContentRecognizer):
	"""Recognizer class that is responsible for calling the YOLOv3 DLL that performs object detection."""
	def __init__(self, resultHandlerClass, timeCreated):
		"""
		@param resultHandlerClass: class that contains code for handling object detection result
		@param timeCreated: stores timestamp of when an instance of this class was created
		"""
		self.resultHandlerClass = resultHandlerClass
		self.timeCreated = timeCreated
		# Set to True only if Focus mode is enabled
		self.checkChildren = False

	def recognize(self, imageHash, pixels, imgInfo, onResult):
		""" Starts the object detection process on a new thread and sets the I{onResult} method
		@param imageHash: hash used to uniquely identify the recognized image
		@param pixels: 2D array of RGBAQUAD values that store image pixels
		@param imgInfo: stores details of the image to be recognized
		@param onResult: Function that defines logic for what to do when result is obtained
		"""
		self.imageHash = imageHash
		self.imgInfo = imgInfo
		# Copy pixels to empty bitmap and save it as a temporary jpeg image
		bmp = wx.EmptyBitmap(imgInfo.recogWidth, imgInfo.recogHeight, 32)
		bmp.CopyFromBuffer(pixels, wx.BitmapBufferFormat_RGB32)
		self._imagePath = tempfile.mktemp(prefix="nvda_ObjectDetect_", suffix=".jpg")
		bmp.SaveFile(self._imagePath, wx.BITMAP_TYPE_JPEG)
		# Set L{onResult} method
		self._onResult = onResult
		# Start object detection on separate thread
		t = threading.Thread(target=self._bgRecog)
		t.daemon = True
		t.start()

	def _bgRecog(self):
		"""Handles the object detection process thread and calls L{onResult} when the result is ready."""
		try:
			result = self.detect(self._imagePath)
		except Exception as e:
			result = e
		finally:
			# Delete temporary image file since we don't need it anymore
			os.remove(self._imagePath)
		if self._onResult:
			self._onResult(result)

	def cancel(self):
		"""Disables result presentation but does not stop the detection process."""
		self._onResult = None

	def detect(self, imagePath: str) -> ObjectDetectionResults:
		""" Gets the object detection results and returns it
		@param imagePath: file system path to input image
		@return: L{ObjectDetectionResults}
		"""
		sentence, boxes = YOLOv3Detection(imagePath).getResults()
		result = ObjectDetectionResults(self.imageHash, self.imgInfo, sentence, boxes)
		return result

	def validateObject(self, obj) -> bool:
		"""Checks if the focus or navigator object or any of its children (only in case of focus objects)
		are graphic. If invalid, a message is presented to the user.
		@param obj: focus/navigator object to be validated
		@return: True is object is valid else False
		"""
		if obj.role != ROLE_GRAPHIC:
			# If in focus mode, check if at least one child of the object is graphic because the focus
			# object itself will not be graphic.
			if self.checkChildren:
				for child in obj.children:
					if child.role == ROLE_GRAPHIC:
						return True
			# Translators: Reported when the focused element is not an image and the filterNonGraphic 
			# option in the Setting is enabled.
			ui.message(
				_("Currently focused element is not an image. Please try again with an image element or "
				"change your add-on settings.")
					)
			log.debug(f"(objectDetection) Navigation object role:{obj.role}")
			return False
		return True

	def validateBounds(self, location: RectLTWH) -> bool:
		"""Checks the bounds of the object to be recognized are greater than the minimum value. If not, a
		message is presented to the user.
		@param location: stores the screen co-ordinates and dimensions of the image object to be recognized
		@return: True is object size is greater than the minimum value, false otherwise
		"""
		# object must be greater than the size threshold in atleast one dimension
		if location.width < _sizeThreshold or location.height < _sizeThreshold:
			# Translators: Reported when the size focused element is too small to produce good results. 
			ui.message(_("Image too small to produce good results. Please try again with a larger image."))
			log.debug(f"(objectDetection) Capture bounds: width={location.width}, height={location.height}.")
			return False
		return True

	def getResultHandler(self, result: Any):
		"""Returns an instance of the L{resultHandlerClass} instantiated with the object detection result
		@param result:
		@return: instance of I{self.resultHandlerClass}
		"""
		return self.resultHandlerClass(result)
