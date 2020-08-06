# Object Detection model specific detection modules
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import os
import threading
import tempfile
from typing import Any

import wx
import ui
import contentRecog
from logHandler import log
from controlTypes import ROLE_GRAPHIC
from ._detectionResult import ObjectDetectionResults
from ._YOLOv3 import YOLOv3Detection
from ._DETR import DETRDetection

#: Elements with width or height small than this value will not be processed
_sizeThreshold = 128


class doObjectDetection(contentRecog.ContentRecognizer):
	def __init__(self, resultHandlerClass):
		self.resultHandlerClass = resultHandlerClass

	def recognize(self, imageHash, pixels, imgInfo, onResult):
		self.imageHash = imageHash
		self.imgInfo = imgInfo
		bmp = wx.EmptyBitmap(imgInfo.recogWidth, imgInfo.recogHeight, 32)
		bmp.CopyFromBuffer(pixels, wx.BitmapBufferFormat_RGB32)
		self._imagePath = tempfile.mktemp(prefix="nvda_ObjectDetect_", suffix=".jpg")
		bmp.SaveFile(self._imagePath, wx.BITMAP_TYPE_JPEG)
		self._onResult = onResult
		t = threading.Thread(target=self._bgRecog)
		t.daemon = True
		t.start()

	def _bgRecog(self):
		try:
			result = self.detect(self._imagePath)
		except Exception as e:
			result = e
		finally:
			os.remove(self._imagePath)
		if self._onResult:
			self._onResult(result)

	def cancel(self):
		self._onResult = None

	def detect(self, imagePath):
		raise NotImplementedError

	def validateObject(self, nav):
		return True

	def validateBounds(self, left, top, width, height):
		return True

	def getResultHandler(self, result: Any):
		return self.resultHandlerClass(result)


class doDetectionTinyYOLOv3(doObjectDetection):

	def __init__(self, resultHandlerClass):
		super(doDetectionTinyYOLOv3, self).__init__(resultHandlerClass)

	def detect(self, imagePath):
		sentence, boxes = YOLOv3Detection(imagePath, tiny=True).getResults()
		result = ObjectDetectionResults(self.imageHash, self.imgInfo, sentence, boxes)
		return result

	def validateObject(self, nav):
		if nav.role != ROLE_GRAPHIC:
			ui.message("Currently focused element is not an image. Please try again with an image element.")
			log.debug(f"(objectDetection) Navigation object role:{nav.role}")
			return False
		return True

	def validateBounds(self, left, top, width, height):
		if width < _sizeThreshold or height < _sizeThreshold:
			ui.message("Image too small to produce good results. Please try again with a larger image.")
			log.debug(f"(objectDetection) Capture bounds: width={width}, height={height}.")
			return False
		return True
