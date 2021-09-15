Millimanipulation_Mark3
====
This project is for the Millimanipulation Mark 3 device driver with automatic control and Graphical User Interface (GUI) using Python 3.7.
‘Millimanipulation’ is a mm-scale scraping device for studying the removal behaviour of soft solid layers from solid substrates, firstly presented by the P4G group (Professor Ian Wilson) at the Department of Chemical Engineering and Biotechnology, University of Cambridge. The Mark 3 millimanipulation device was created by Magens et al. (2017) J. Food Eng. 197, 48–59. 

![Magens et al. (2017) J. Food Eng. 197, 48–59](https://ars.els-cdn.com/content/image/1-s2.0-S0260877416304046-gr3.jpg)

The sample is fixed on a two-axis (x and z) moving platform, controlled by two positioners (Standa 8MVT40-13-1- MEn1 and Standa 8MT50-100BS1-MEn1, respectively). Both positioners are driven by the controller (Standa 8SMC4-USB-B9-2). A force transducer (ME-Meßsysteme GmbH KD40s ±2 N) is connected to a vertical blade, which hangs from an arm on a frictionless pivot, to measure the horizontal force when the blade contacts the sample layer. The transducer signal is then amplified and collected as an analogue input by a DAQ (National Instruments USB-6009).

This repository includes: <br>
* Code of millimanipulation GUI

Getting started
----
1. Clone the repository.
2. Install dependencies.
```python
pip3 install -r requirements.txt
```
3. Download the software of package for 8SMC4 controller from [Standa's page](http://files.xisupport.com/Software.en.html#drivers).
