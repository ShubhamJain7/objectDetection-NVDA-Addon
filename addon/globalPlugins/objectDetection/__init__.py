# Object Detection global plugin main module
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import globalPluginHandler
from contentRecog import recogUi
from scriptHandler import script
from globalCommands import SCRCAT_VISION

from ._doObjectDetection import *

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	@script(
		# Translators: Input trigger to perform object detection on focused image
		description=_("Perform object detection on focused image"),
		category=SCRCAT_VISION,
		gesture="kb:Alt+NVDA+D",
	)
	def script_detectObjectsTinyYOLOv3(self, gesture):
		x = doDetectionTinyYOLOv3()
		recogUi.recognizeNavigatorObject(x)

	# def script_detectObjectsYOLOv3(self, gesture):
	# 	x = doDetectionYOLOv3()
	# 	recogUi.recognizeNavigatorObject(x)

	# def script_detectObjectsDETR(self, gesture):
	# 	x = doDetectionDETR()
	# 	recogUi.recognizeNavigatorObject(x)