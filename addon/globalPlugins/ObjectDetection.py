import globalPluginHandler
from contentRecog import recogUi
from .ObjectDetection import *

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def script_detectObjectsTinyYOLOv3(self, gesture):
		x = doDetectionTinyYOLOv3()
		recogUi.recognizeNavigatorObject(x)

	def script_detectObjectsYOLOv3(self, gesture):
		x = doDetectionYOLOv3()
		recogUi.recognizeNavigatorObject(x)

	def script_detectObjectsDETR(self, gesture):
		x = doDetectionDETR()
		recogUi.recognizeNavigatorObject(x)

	__gestures={
		"kb:NVDA+A": "detectObjectsTinyYOLOv3",
		"kb:NVDA+B": "detectObjectsYOLOv3",
		"kb:NVDA+C": "detectObjectsDETR"
	}
