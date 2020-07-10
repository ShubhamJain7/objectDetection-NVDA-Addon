# Object Detection

* Author: Shubham Dilip Jain
* Download: https://github.com/ShubhamJain7/objectDetection-NVDA-Addon

This add-on allows users to perform object detection on an image element present on their screen. The result is presented as a sentence of the form "The image contains a `x`, `y's` and a `z`".

### Usage
----
Detection is triggered by pressing Alt+NVDA+D. When the detection is complete, "Result Document" is announced. Users can then access the result as a navigator object by pressing CTRL+arrow keys. Press ESC to escape the result.

### Building it yourself
----
Requirements:
* a Python distribution (2.7 or greater is recommended). Check the [Python Website](http://www.python.org) for Windows Installers.
* Scons - [Website](http://www.scons.org/) - version 2.1.0 or greater. Install it using **easy_install** or grab an windows installer from the website.
* GNU Gettext tools, if you want to have localization support for your add-on - Recommended. Any Linux distro or cygwin have those installed. You can find windows builds [here](http://gnuwin32.sourceforge.net/downlinks/gettext.php).
* Markdown-2.0.1 or greater, if you want to convert documentation files to HTML documents. You can [Download Markdown](https://pypi.org/project/Markdown/) or get it using `easy_install markdown`.

Once the requirements are satisfied:
1. Clone this repo
2. Open a command line and navigate to the cloned repo
3. Run the command `scons` in the directory containing the **sconstruct** file

You can then install the add-on in NVDA by double clicking on the **.nvda-addon** file while NVDA is running or goto NVDA->tools->manage add-ons->Install and the selecting the **.nvda-addon** file.


### Developer notes
----
This add-on makes use of the [Tiny-YOLOv3-darknet](https://pjreddie.com/darknet/yolo/) model for object detection. It also contains code for using other versions of the YOLOv3 model and the [DE⫶TR](https://github.com/facebookresearch/detr) model, these have been turned off at the moment, until final decisions about which model to use are made. You can download the config and weights file of any YOLOv3 model and replace the Tiny model in `addon/globalPlugins/objectDetection/models` and use that instead (you may need to rename the files or change the code in `addon/globalPlugins/objectDetection/_YOLOv3.py` a bit for it to work). The DE⫶TR model must be converted to ONNX before use. There is no direct download for it but it is fairly easy to convert using PyTorch's `torch.onnx.export`.
All models rely [OpenCV 4.3.0](https://opencv.org/), the required DLL's of which can be found at `addon/globalPlugins/objectDetection/dlls`. Appart from OpenCV, the DE⫶TR model also uses [ONNX Runtime 1.3.0](https://github.com/microsoft/onnxruntime) to run, whose DLL can be found at the same location. 
The DLL files that interface with the models themselves, `YOLOv3-DLL.dll` and `DETR-DLL.dll`, can be built from [here](https://github.com/ShubhamJain7/YOLOv3-DLL) and [here](https://github.com/ShubhamJain7/DETR-DLL) respectively. 