# Object Detection: YOLOv3 model DLL interface
# Copyright 2020 Shubham Dilip Jain, released under the AGPL-3.0 License

import os
from ctypes import *
from collections import Counter
from ._detectionResult import Detection


class YOLOv3Detection():
	"""Class that interfaces with the YOLOv3 DLL that performs object detection. Responsible to converting
	results to appropriate formats and ensuring DLL dependencies are satisfied."""
	def __init__(self, imagePath):
		""" Defines paths to all the required files (image, DLLs and model files)
		@param imagePath: path to image to be recognized
		"""
		self.baseDir = os.path.abspath(os.path.dirname(__file__))

		self.imagePath = imagePath
		self.configFile = self.baseDir + "/models/yolov3.cfg"
		self.weightsFile = self.baseDir + "/models/yolov3.weights"

		# Must be in dependency order (ie. A<-B<-C where C depends on B and B depends on A).
		self.dllPaths = ["\\dlls\\opencv_core430.dll", "\\dlls\\opencv_imgproc430.dll",
						"\\dlls\\opencv_imgcodecs430.dll", "\\dlls\\opencv_dnn430.dll", "\\dlls\\YOLOv3-DLL.dll"]
		self.dllPaths = [self.baseDir + dllPath for dllPath in self.dllPaths]

		self._checkFiles()

	# define singular and plural forms of class labels
	CLASSES_SINGULAR = ['a person', 'a bicycle', 'a car', 'a motorbike', 'an aeroplane', 'a bus', 'a train',
						'a truck', 'a boat', 'a traffic light', 'a fire hydrant', 'a stop sign', 'a parking meter',
						'a bench', 'a bird', 'a cat', 'a dog', 'a horse', 'a sheep', 'a cow', 'an elephant', 'a bear',
						'a zebra', 'a giraffe', 'a backpack', 'an umbrella', 'a handbag', 'a tie', 'a suitcase',
						'a frisbee', 'a pair of skis', 'a snowboard', 'a sports ball', 'a kite', 'a baseball bat',
						'a baseball glove', 'a skateboard', 'a surfboard', 'a tennis racket', 'a bottle',
						'a wine glass', 'a cup', 'a fork', 'a knife', 'a spoon', 'a bowl', 'a banana', 'an apple',
						'a sandwich', 'an orange', 'broccoli', 'a carrot', 'a hot dog', 'a pizza', 'a donut', 'a cake',
						'a chair', 'a sofa', 'a potted plant', 'a bed', 'a dining table', 'a toilet', 'a tv monitor',
						'a laptop', 'a mouse', 'a remote', 'a keyboard', 'a cell phone', 'a microwave', 'an oven',
						'a toaster', 'a sink', 'a refrigerator', 'a book', 'a clock', 'a vase', 'a scissor',
						'a teddy bear', 'a hairdryer', 'a toothbrush']

	CLASSES_PLURAL = ['people', 'bicycles', 'cars', 'motorbikes', 'aeroplanes', 'buses', 'trains', 'trucks', 'boats',
					'traffic lights', 'fire hydrants', 'stop signs', 'parking meters', 'benches', 'birds', 'cats',
					'dogs', 'horses', 'multiple sheep', 'cows', 'elephants', 'bears', 'zebras', 'giraffes',
					'backpacks', 'umbrellas', 'handbags', 'ties', 'suitcases', 'frisbees', 'skis', 'snowboards',
					'sports balls', 'kites', 'baseball bats', 'baseball gloves', 'skateboards', 'surfboards',
					'tennis rackets', 'bottles', 'wine glasses', 'cups', 'forks', 'knives', 'spoons', 'bowls',
					'bananas', 'apples', 'sandwiches', 'oranges', 'broccoli', 'carrots', 'hot dogs', 'pizzas',
					'donuts', 'cakes', 'chairs', 'sofas', 'potted plants', 'beds', 'dining tables', 'toilets',
					'tv monitors', 'laptops', 'mice', 'remotes', 'keyboards', 'cell phones', 'microwaves', 'ovens',
					'toasters', 'sinks', 'refrigerators', 'books', 'clocks', 'vases', 'scissors', 'teddy bears',
					'hairdryers', 'toothbrushes']

	# python definition of 'Detection' struct
	class Detection(Structure):
		_fields_ = [("classId", c_int),
					("probability", c_float),
					("x", c_int),
					("y", c_int),
					("width", c_int),
					("height", c_int), ]

	def _checkFiles(self):
		"""Checks if all the required files are present. Raises a L{FileNotFoundError} if any
		file is missing"""
		notFound = ""
		if not os.path.exists(self.imagePath):
			notFound = notFound + f'\nobjectDetection(YOLOv3): image not found at {self.imagePath}'

		if not os.path.exists(self.configFile):
			notFound = notFound + f'\nobjectDetection(YOLOv3): Config file not found at {self.configFile}'

		if not os.path.exists(self.weightsFile):
			notFound = notFound + f'\nobjectDetection(YOLOv3): Weights file not found at {self.weightsFile}'

		for dllPath in self.dllPaths:
			if not os.path.exists(dllPath):
				notFound = notFound + f'\nobjectDetection(YOLOv3): DLL file not found at {dllPath}'

		if notFound != "":
			raise FileNotFoundError(notFound)

	def _loadDLLs(self):
		"""Loads all the DLL files. """
		# loads all the DLLs required by the YOLOv3 DLL
		for dllPath in self.dllPaths[:-1]:
			# all the d
			_ = CDLL(dllPath)

		# load the YOLOv3 DLL
		lib = CDLL(self.dllPaths[-1])
		return lib

	def _getDetections(self, lib) -> iter:
		"""Calls the DLL public methods and gets the object detection results.
		@return: List of L{Detection} objects
		"""
		lib.doDetection.restype = c_int
		lib.doDetection.argtypes = [c_char_p, c_char_p, c_char_p]

		# call 'doDetection' function and get number of objects detected
		res = lib.doDetection(self.configFile.encode('utf-8'), self.weightsFile.encode('utf-8'),
							self.imagePath.encode('utf-8'))
		DetectedObjectsArray = self.Detection * res

		# continue if objects were detected
		if res != 0:
			# define return type and arguments of 'getDetections' function
			lib.getDetections.restype = c_int
			lib.getDetections.argtypes = [POINTER(DetectedObjectsArray), c_int]

			# define array to store 'Detection's and call the 'getDetections' function
			objects = DetectedObjectsArray()
			_ = lib.getDetections(objects, res)
			return objects
		else:
			return []

	def _createSentence(self) -> str:
		"""Creates a English sentence from the lables of all detected objects
		@return: sentence form of object detection result
		"""
		self._checkFiles()
		lib = self._loadDLLs()
		results = self._getDetections(lib)
		if results:
			# get class labels and their frequency counts
			# assuming singular
			classLabels = [self.CLASSES_SINGULAR[d.classId] for d in results]
			counts = Counter(classLabels)
			number_of_items = len(counts)

			output_string = "The image contains "
			for i, key in enumerate(counts.keys()):
				if counts[key] == 1:
					output_string = output_string + key
				# if there are multiple instances of the same object in the image, use plural form
				else:
					output_string = output_string + self.CLASSES_PLURAL[self.CLASSES_SINGULAR.index(key)]

				# rules for listing out identified objects
				if i < (number_of_items - 2):
					# add commas only if there are more than two objects
					if number_of_items > 2:
						output_string = output_string + ", "
					else:
						output_string = output_string + " "
				# use and if its the second last object
				elif i == (number_of_items - 2):
					output_string = output_string + " and "
				# end sentence with a full-stop
				else:
					output_string = output_string + "."

			return output_string
		else:
			return "Cannot identify any objects in the image."

	def getResults(self) -> tuple:
		"""Performs object detection on input image and returns the result in sentence form and the object
		detection results.
		@return: Tuple of the form (sentence, boxes) where sentence is the result in sentence form and
		boxes is a list of the locations of the detected objects along with the associated object label.
		"""
		lib = self._loadDLLs()
		detections = self._getDetections(lib)
		boxes = []
		sentence = self._createSentence()
		for detection in detections:
			words = self.CLASSES_SINGULAR[detection.classId].split(" ")
			# get only relevant part of the class label in singular form
			classLabel = " ".join(words[1:]) if len(words) > 1 else words[0]
			boxes.append(Detection(classLabel, detection.x, detection.y, detection.width, detection.height))

		return (sentence, boxes)
