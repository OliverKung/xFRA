**Read this in other languages: [中文](README.md), [English](README_en.md).**
# xFRA: A Python-based Universal Frequency Response Analyzer Software
xFRA is a universal FRA software with a GUI based on PyQt. The design philosophy of xFRA is built upon universal virtual instrumentation, encompassing the GUI, data conversion, and instrument communication.
## GUI (xFRA)
The GUI (xFRA) is written using PyQt.
## Data Conversion (xConv)
The data conversion layer (xConv) comprises two components: an S2P parser (xSNP_Interaptor) and a formula parser (xFormula). It can read files stored in S2P format and convert them into various formats. The conversion functionality is based on the formula parser, which can directly parse formulas edited in plain text and provides corresponding complex number conversion capabilities.
## Instrument Communication Layer (xDriver)
The instrument communication layer (xDriver) provides a universal conversion layer for transforming various signals measured by devices into S2P files. It provides base classes here. The first type is the VNA class, defined as instruments that can directly output S2P files—they can directly return S2P files describing the network after basic test requirements are provided. The other type is the EM class (Excitation-Measurement class), which is defined more broadly to include excitation and measurement instruments that can be combined arbitrarily. EM classes designed with this concept enable operations such as using a computer sound card as the excitation source while using an oscilloscope to measure frequency response.
## To Do List
### xFRA
- [x] Complete GUI reference design
- [ ] GUI data import and plotting
- [ ] GUI data cursors
### xConv
- [ ] Read and parse S2P files
- [ ] Parse arbitrary formulas
- [ ] Provide basic mathematical functions
### xDriver
- [ ] Define basic input/output formats
- [ ] Driver for NanoVNA
- [ ] Driver for SVA1000X
- [ ] Driver for OSC+AFG