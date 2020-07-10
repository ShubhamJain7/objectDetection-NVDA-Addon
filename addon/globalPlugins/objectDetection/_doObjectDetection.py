import os
import threading
import tempfile
import wx
import contentRecog
from ._YOLOv3 import YOLOv3Detection
from ._DETR import DETRDetection

class doObjectDetection(contentRecog.ContentRecognizer):
	def recognize(self, pixels, imgInfo, onResult):
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


class doDetectionTinyYOLOv3(doObjectDetection):
	def detect(self, imagePath):
		result = YOLOv3Detection(imagePath, tiny=True).getSentence()
		return contentRecog.SimpleTextResult(result)


class doDetectionYOLOv3(doObjectDetection):
	def detect(self, imagePath):
		result = YOLOv3Detection(imagePath, tiny=False).getSentence()
		return contentRecog.SimpleTextResult(result)


class doDetectionDETR(doObjectDetection):
	def detect(self, imagePath):
		result = DETRDetection(imagePath).getSentence()
		return contentRecog.SimpleTextResult(result)
