# Object Detection

* Author: Shubham Dilip Jain
* Download: https://github.com/ShubhamJain7/objectDetection-NVDA-Addon/releases

This add-on allows users to perform object detection on image elements present on their screen and get results in the form of a sentence and bounding boxes drawn around the detected objects. Users can move their mouse pointer or finger (in case of touch screens) inside a bounding box to hear the object label. The result sentence can be either announced or it can be presented in a virtual, browseable window that allows users to access the result character-by-character, word-by-word, as a whole and even copy the result. This add-on works well only with "natural images" of people, animals and some common objects.

_Note: Mouse tracking must be enabled for the bounding box label to be announced._

### Usage
----
- After installing, the user must first set their preferred gesture at __Preferences->Input gestures->Vision__. 

- Keying the set gesture once triggers the object detection process and the sentence form of the obtained result is announced to the user (this may take a few seconds). Along with this announcement, bounding boxes are also drawn around the detected objects. Users can move their mouse pointer or finger (in case of touch screens) to announce the object label. The object label is only announced once when the bounding box is entered. The box must be re-entered for subsequent announcements. These bounding boxes only disappear when the focus shifts to another element. (Mouse tracking must be enabled for this work).

- Keying the same gesture more than once also triggers the object detection process but the sentence form of the result is presented in a virtual window and no bounding boxes are drawn. Users can use navigation keys in this window to browse the result letter-by-letter, word-by-word, as a whole or even copy it. Users must escape this window before starting another object detection process. This can be done by pressing the `ESC` key or shifting focus to another element.

- Users can also prevent the object detection process from starting on non-graphic elements by checking the `filter non-graphic elements` option under __Preferences->Settings->Vision->Object detection add-on__. This prevents users from accidentally starting the object detection process on elements that do not contain images and will produce bad results. Unchecking it allows users to perform detections on elements that may contain images but fail to report the same.


### Building it yourself
----
Requirements:
* [Python 3](http://www.python.org) for Windows. See website for installers.
* [Scons](http://www.scons.org/) - Can be installed by running `pip install Scons` or using a windows installer from the website.
* [Markdown](https://pypi.org/project/Markdown/) - Can be installed by running `pip install Markdown`.

Once the requirements are satisfied:
1. Clone this repo
2. Open a command line and navigate to the cloned repo
3. Run the command `scons` in the directory containing the **sconstruct** file

You can then install the add-on in NVDA by double-clicking on the **.nvda-addon** file while NVDA is running or goto NVDA->tools->manage add-ons->Install and the selecting the **.nvda-addon** file.

### Developer notes
----
This add-on makes use of the [YOLOv3-darknet](https://pjreddie.com/darknet/yolo/) model for object detection. You can download the config and weights file of any YOLOv3 model and replace the existing model in `addon/globalPlugins/objectDetection/models` and use that instead (you must ensure that the config and weights file are named `yolov3.cfg` and `yolov3.weights` respectively, for this to work). The larger models are better at detecting objects but at a cost of time taken. In general, a medium-sized model, such as the one packaged in this add-on (YOLOv3-416) is the best choice.
The model relies [OpenCV 4.3.0](https://opencv.org/), the required DLL's of which can be found at `addon/globalPlugins/objectDetection/dlls`. The `YOLOv3-DLL.dll` file interface with the model itself and can be found at or built from [here](https://github.com/ShubhamJain7/YOLOv3-DLL).
