import globalPluginHandler
from contentRecog import recogUi

from ._doObjectDetection import *

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
		"kb:Alt+NVDA+1": "detectObjectsTinyYOLOv3",
		"kb:Alt+NVDA+2": "detectObjectsYOLOv3",
		"kb:Alt+NVDA+3": "detectObjectsDETR"
	}
