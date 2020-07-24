class Detection():
	def __init__(self, label:str, x:int, y:int, width:int, height:int):
		self.label = label
		self.x = x
		self.y = y
		self.width = width
		self.height = height


class ObjectDetectionResults():
	def __init__(self, sentence:str, boxes:iter):
		self.sentence = sentence
		self.boxes = boxes
