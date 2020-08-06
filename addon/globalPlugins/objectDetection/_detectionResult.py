from contentRecog import RecogImageInfo

class Detection():
	def __init__(self, label:str, x:int, y:int, width:int, height:int):
		self.label = label
		self.x = x
		self.y = y
		self.width = width
		self.height = height


class ObjectDetectionResults():
	def __init__(self, imageHash:int, imgInfo:RecogImageInfo, sentence:str, boxes:iter):
		self.imageHash = imageHash
		self.imgInfo = imgInfo
		self.sentence = sentence
		self.boxes = boxes
