# Object Detection: detection and result classes
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

from contentRecog import RecogImageInfo
from collections import namedtuple


class Detection():
	"""Stores the detials of a single detection."""
	def __init__(self, label: str, x: int, y: int, width: int, height: int):
		"""
		@param label: Label of detected object
		@param x: x co-ordinate of top left corner of object bounding box
		@param y: y co-ordinate of top left corner of object bounding box
		@param width: width of object bounding box
		@param height: height of object bounding box
		"""
		self.label = label
		self.x = x
		self.y = y
		self.width = width
		self.height = height


class ObjectDetectionResults():
	"""Stores image info and the details of detected objects."""
	def __init__(self, imageHash: int, imgInfo: RecogImageInfo, sentence: str, boxes: iter):
		"""
		@param imageHash: hash used to uniquely identify the recognized image
		@param imgInfo: stores details of the recognized image
		@param sentence: Object detection result in sentence form
		@param boxes: List of all objects detected stored as L{Detection} objects
		"""
		self.imageHash = imageHash
		self.imgInfo = imgInfo
		self.sentence = sentence
		self.boxes = boxes

	def getAdjustedLTRBBoxes(self) -> namedtuple:
		"""Adjusts the in-image co-ordinates of the detections to screen co-ordinates
		@return: List of named tuples with the co-ordinate attributes label, left, top, right and bottom
		"""
		adjustedBoxes = []
		detectionLTRB = namedtuple('Detection', ['label', 'left', 'top', 'right', 'bottom'])
		for box in self.boxes:
			# Account for image displacement from left edge of screen
			left = box.x + self.imgInfo.screenLeft
			# Account for image displacement from top edge of screen
			top = box.y + self.imgInfo.screenTop
			right = left + box.width
			bottom = top + box.height
			adjustedBoxes.append(detectionLTRB(box.label, left, top, right, bottom))
		return adjustedBoxes
