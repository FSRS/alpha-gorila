## **A Tribute to 7key Pattern Makers...**

#### **AT7PM version - 7.0.0**

Download Sample BMS 'Adam' by しらいし
https://drive.google.com/uc?id=11NOb1JLxeh_3GpaLGnlxLTnVIYTW8k4m

(Unzip AT7PM.zip and download sample BMS and unzip at AT7PM folder.
Thus, Adam should be a subfolder of AT7PM.
Please unzip Adam.zip in Adam folder for sample bms and oggdec.)
or
Just download AT7PM_full.zip

I highly recommend saving your BMS file using UBMSC before running this.
B2BC101 will help to organize BMS file's objects especially for old BMS files
**Caution**: B2BC101 has some bugs as deleting whole objects of some measures.
I also highly recommend using [AnzuBMSDiff](http://yuinore.net/2015/12/difftool/) to check BMS file is sound.

Use (44.1kHz) wave files as keysounds or it will not operate. Use oggcodec
If WavFileWarning occurs, please remove default metadata.

#### **How to Use**

- If you are not using FULL AUTO MODE:

  BEFORE running the code...  

  You can pre-write your pattern on 1P region before running this.
  The object pre-written on 1P region will not be affected.

  Then, organize the objects which you want to use to 2P region
  2P lane number 1 (#XYZ21) has the highest priority, 
  while 2P lane number 7 (#XYZ27) has the lowest priority.

  Therefore, if you want to use non-keysound objects, 
  it is better to place those at 2P lane number 7.

  To run the code properly, define BMS' path and operation sections.
  It is highly recommned to divide a BMS file as multiple sections.

  HOW TO DIVIDE? 
  The measures which have objects of different tracks on same lane 
  should be distinguished as different sections.

  Then, set the values following footnotes.

  Now you are ready to Run the code. Please Pray for no ERRORs.

- If you are using FULL AUTO MODE:
  It is unavailable now. DON'T TRY THIS

This program will not manipulate the scratch lane.(#XYZ16)
If you want to make a scratchy pattern, please pre-write the scratch objects.
Also, if you want to use gimmicks, please write them after running the code.

**CAUTION: The result pattern will still have some 2P objects.***
Please check and organize the objects before playing the pattern. 

This program uses external modules, numpy and scipy.
Please install those modules if ImportError raised.