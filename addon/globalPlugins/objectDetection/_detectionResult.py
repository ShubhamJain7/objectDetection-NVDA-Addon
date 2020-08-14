# Object Detection: detection and result classes
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

from contentRecog import RecogImageInfo
from collections import namedtuple


class Detection():
	def __init__(self, label: str, x: int, y: int, width: int, height: int):
		self.label = label
		self.x = x
		self.y = y
		self.width = width
		self.height = height


class ObjectDetectionResults():
	def __init__(self, imageHash: int, imgInfo: RecogImageInfo, sentence: str, boxes: iter):
		self.imageHash = imageHash
		self.imgInfo = imgInfo
		self.sentence = sentence
		self.boxes = boxes

	def getAdjustedLTRBBoxes(self) -> namedtuple:
		adjustedBoxes = []
		detectionLTRB = namedtuple('Detection', ['label', 'left', 'top', 'right', 'bottom'])
		for box in self.boxes:
			left = box.x + self.imgInfo.screenLeft
			top = box.y + self.imgInfo.screenTop
			right = left + box.width
			bottom = top + box.height
			adjustedBoxes.append(detectionLTRB(box.label, left, top, right, bottom))
		return adjustedBoxes
