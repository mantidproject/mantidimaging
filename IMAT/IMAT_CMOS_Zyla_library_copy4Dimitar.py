from __future__ import division
from __future__ import print_function
# IMAT CMOS Zyla subroutines and functions
from builtins import str
from past.utils import old_div
from genie_python.genie import cset, begin, end, change, waitfor_move, resume, get_pv
import time
import numpy
# from __future__ import print_function
import sys
import os
import math
from CaChannel import CaChannel, CaChannelException
import ca
from SDK_Andor.Zyla.ADAndorZyla import ADAndorZyla


def header():
    print("")
    print(" ========================================================")
    print("  Python Script to perform a multiple image acquisition  ")
    print(" ========================================================")
    print("")
    print(("  Connected camera : ", IMATCamera.pvManufacturer.getw(), " "))
    print(IMATCamera.pvModel.getw())
    print(" =========================================================")
    print("")

def ensure_dir(f):
    if not os.path.exists(f):
        os.makedirs(f)

def write_csv(f, *args):
    f.writelines([",".join(args), "\n"])

def waitNewImageReady(camera):
    camera.startAcquire(1)
    while(camera.acquireDone != True) :
        time.sleep(1)

IMATCamera              = ADAndorZyla("IN:IMAT:", "13ANDOR3:", "cam1:")
Ex_time                 = CaChannel("IN:IMAT:13ANDOR3:cam1:AcquireTime")
TiffFilePathPV          = CaChannel("IN:IMAT:13ANDOR3:TIFF1:FilePath")
TiffFilePathExistsPV    = CaChannel("IN:IMAT:13ANDOR3:TIFF1:FilePathExists_RBV")
TiffFileNamePV          = CaChannel("IN:IMAT:13ANDOR3:TIFF1:FileName")
TiffFileTemplatePV      = CaChannel("IN:IMAT:13ANDOR3:TIFF1:FileTemplate")
TiffFileNumberPV        = CaChannel("IN:IMAT:13ANDOR3:TIFF1:FileNumber")
TiffFileAutoIncrementPV = CaChannel("IN:IMAT:13ANDOR3:TIFF1:AutoIncrement")
TiffFileCallBacksPV     = CaChannel("IN:IMAT:13ANDOR3:TIFF1:EnableCallbacks")
TiffFileWriteFilePV     = CaChannel("IN:IMAT:13ANDOR3:TIFF1:WriteFile")
TiffFileAutoSavePV      = CaChannel("IN:IMAT:13ANDOR3:TIFF1:AutoSave")
BeamMonitorPV           = CaChannel("IN:IMAT:DAE:MON:5:C")

# pylint: disable=W0613
def CMOS_Zyla_radio(image_type, n_radio, expo_time, mon_th, x, y, z, rot, RBnumber, runno, ctitle, data_type):

    TiffFilePathPV.searchw()
    TiffFilePathExistsPV.searchw()
    TiffFileNamePV.searchw()
    TiffFileTemplatePV.searchw()
    TiffFileNumberPV.searchw()
    TiffFileAutoIncrementPV.searchw()
    TiffFileCallBacksPV.searchw()
    TiffFileWriteFilePV.searchw()
    TiffFileAutoSavePV.searchw()
    Ex_time.searchw()
    # BeamMonitorPV.setTimeout(20)
    # BeamMonitorPV.searchw()
    time.sleep(1)


    time.sleep(3)

    header()
    sampleName = ctitle

    runNumber          = RBnumber
    filePath           = "M:\\Data"
    filePath           = "M:\\Users" #WK

    StartingFileNumber  = 0        # Starting number of files
    NumberOfImages      = n_radio
    #
    if( image_type == 0 ):
        MinBeamCountsPerSec = 0  #dark field
    else:
        MinBeamCountsPerSec = mon_th  #radiography, beam monitor 3a  counts per sec  4000

    Ex_time.putw(expo_time)
    MinBeamCounts = (MinBeamCountsPerSec * IMATCamera.pvAcquireTime.getw()) * 0.85

    #Create the structure Tree for Flat
    ensure_dir(filePath)
    ensure_dir(filePath + '\\' + runNumber)
    ensure_dir(filePath + '\\'+ runNumber + '\\'+sampleName + '\\' + data_type )

    #Replace filepath for the camera saving
    # filePath           = "C:\\Data"
    filePath           = "C:\\Users"  #WK

    # Variables NOT to be changed usually
    fileName           = "IMAT" + runno    + "_" + sampleName + "_" + data_type
    filePrefix = fileName + "\x00"                             # Why do we have to force a NULL  ?
    filePathPrefix = filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + "\x00"
    TiffFilePathPV.array_put(filePathPrefix)                   # Path for file saving (MUST EXISTS !)
    TiffFileNamePV.array_put(filePrefix)                       # File name header
    TiffFileNamePV.pend_io()
    TiffFileTemplatePV.array_put("%s%s_%3.3d.tif\x00")             # Default File name format
    TiffFileNumberPV.putw(StartingFileNumber)                    # Starting number of files
    TiffFileAutoIncrementPV.putw(1)                                # File number will be auto incremented
    TiffFileCallBacksPV.putw(1)                                    # Ensure Callbacks are  Enabled
    TiffFileAutoSavePV.putw(0)                                    # Ensure Auto Save is DISABLED
    change(title=sampleName + "  -  " + data_type)
    print(filePathPrefix)

    if(TiffFilePathExistsPV.getw() != 1) :
        print("Non-existing destination Path. Exiting...")
        TiffFileAutoSavePV.putw(1)    # Ensure Auto Save is RENABLED
        sys.exit(0)

    # cset(rot=rot)
    # waitfor_move()
    # motor_sequence(sequence)

    # cset(y=y)
    # waitfor_move()
    # cset(x=x)
    # waitfor_move()
    # cset(z=z);
    # waitfor_move()

    # resume()   # added by WK 12/03/2018

    image_counter = 0
    while(image_counter < NumberOfImages) :
        time.sleep(1)
        # StartBeamCount = BeamMonitorPV.getw()
        StartBeamCount = get_pv("IN:IMAT:DAE:MON:5:C")

        waitNewImageReady(IMATCamera)
        # EndBeamCount = BeamMonitorPV.getw()
        EndBeamCount = get_pv("IN:IMAT:DAE:MON:5:C")
        if( (EndBeamCount-StartBeamCount) >= MinBeamCounts) :
            print(("Total Beam  Counts =", EndBeamCount-StartBeamCount, "  image acquired: ", image_counter))
            TiffFileWriteFilePV.putw(1)
            image_counter += 1
        else :
            print(("Image Not Saved: Beam Counts= ", EndBeamCount-StartBeamCount, "  image acquiring: ", image_counter))

    TiffFileAutoSavePV.putw(1)        # Ensure Auto Save is RENABLED


def CMOS_Zyla_radio_log(image_type, n_radio, expo_time, mon_th, x, y, z, rot, RBnumber, runno, ctitle, data_type):
    TiffFilePathPV.searchw()
    TiffFilePathExistsPV.searchw()
    TiffFileNamePV.searchw()
    TiffFileTemplatePV.searchw()
    TiffFileNumberPV.searchw()
    TiffFileAutoIncrementPV.searchw()
    TiffFileCallBacksPV.searchw()
    TiffFileWriteFilePV.searchw()
    TiffFileAutoSavePV.searchw()
    Ex_time.searchw()
    # BeamMonitorPV.setTimeout(15)
    # BeamMonitorPV.searchw()
    # af 19/02/2020
    get_pv("IN:IMAT:DAE:MON:5:C")
    time.sleep(1)

    header()
    sampleName = ctitle

    runNumber          = RBnumber
    filePath           = "M:\\Data"
    StartingFileNumber  = 0        # Starting number of files
    NumberOfImages      = n_radio
    #
    if( image_type == 0 ):
        MinBeamCountsPerSec = 0  #dark field
    else:
        MinBeamCountsPerSec = mon_th  #radiography, beam monitor 3a  counts per sec  4000

    Ex_time.putw(expo_time)
    MinBeamCounts = (MinBeamCountsPerSec * IMATCamera.pvAcquireTime.getw()) * 0.85

    #Create the structure Tree for Flat
    ensure_dir(filePath)
    ensure_dir(filePath + '\\' + runNumber)
    ensure_dir(filePath + '\\'+ runNumber + '\\'+sampleName + '\\' + data_type )

    #Open Log File
    fileName_log = "IMAT" + runno + "_" + sampleName
    f = open( filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + fileName_log +'_log.txt', 'w')

    #Replace filepath for the camera saving
    filePath           = "C:\\Data"

    # Variables NOT to be changed usually
    fileName           = "IMAT" + runno    + "_" + sampleName + "_" + data_type
    filePrefix = fileName + "\x00"                             # Why do we have to force a NULL  ?
    filePathPrefix = filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + "\x00"
    TiffFilePathPV.array_put(filePathPrefix)                   # Path for file saving (MUST EXISTS !)
    TiffFileNamePV.array_put(filePrefix)                       # File name header
    TiffFileNamePV.pend_io()
    TiffFileTemplatePV.array_put("%s%s_%3.3d.tif\x00")             # Default File name format
    TiffFileNumberPV.putw(StartingFileNumber)                    # Starting number of files
    TiffFileAutoIncrementPV.putw(1)                                # File number will be auto incremented
    TiffFileCallBacksPV.putw(1)                                    # Ensure Callbacks are  Enabled
    TiffFileAutoSavePV.putw(0)                                    # Ensure Auto Save is DISABLED
    change(title=sampleName + "  -  " + data_type)
    print(filePathPrefix)

    if(TiffFilePathExistsPV.getw()!= 1):
        print("Non-existing destination Path. Exiting...")
        TiffFileAutoSavePV.putw(1) # Ensure Auto Save is RENABLED
        return

    write_csv(f, 'TIME STAMP', 'IMAGE TYPE' , 'IMAGE COUNTER', 'COUNTS BM3 before image', 'COUNTS BM3 after image')

    # cset(rot=rot)
    # waitfor_move()
    # motor_sequence(sequence)

    cset(y=y)
    waitfor_move()
    cset(x=x)
    waitfor_move()
    cset(z=z)
    waitfor_move()
    resume()   # added by WK 24/03/2018

    image_counter = 0
    while(image_counter < NumberOfImages) :
        time.sleep(1)
        # StartBeamCount = BeamMonitorPV.getw()
        StartBeamCount = get_pv("IN:IMAT:DAE:MON:5:C")
        waitNewImageReady(IMATCamera)
        # EndBeamCount = BeamMonitorPV.getw()
        EndBeamCount = get_pv("IN:IMAT:DAE:MON:5:C")
        if( (EndBeamCount-StartBeamCount) >= MinBeamCounts):
            print(("Total Beam  Counts =", EndBeamCount-StartBeamCount, "  image acquired: ", image_counter))
            TiffFileWriteFilePV.putw(1)
            if( image_type == 0 ):
                write_csv(f, str(time.ctime()), 'Dark Field', str(image_counter), 'Monitor 3 before: '+ str(StartBeamCount), 'Monitor 3 after: '+ str(EndBeamCount))
            else:
                write_csv(f, str(time.ctime()), 'Radiography', str(image_counter), 'Monitor 3 before: '+ str(StartBeamCount), 'Monitor 3 after: '+ str(EndBeamCount))
                # write_csv(f, str(time.ctime()), 'Radiography', str(image_counter), 'Monitor 3 before: '+ str(StartBeamCount), 'Monitor 3 after: '+ str(EndBeamCount), 'RHController: '+ str(rh), 'M4a_Counts: '+ str(m4a), 'M4b_Counts: '+ str(m4b), 'M5a_Counts: '+ str(m5a), '   M5b_Counts: ', str(m5b))
            image_counter += 1
        else :
            print(("Image NOT SAVED, intensity variation over 20% --> Beam Counts= ", EndBeamCount-StartBeamCount, "  image number: ", image_counter))

    TiffFileAutoSavePV.putw(1)        # Ensure Auto Save is RENABLED


def CMOS_Zyla_tomo_log(image_type, n_radio, expo_time, mon_th, x, y, z, start_a, end_a, step_a, RBnumber, runno, ctitle, data_type):

    TiffFilePathPV.searchw()
    TiffFilePathExistsPV.searchw()
    TiffFileNamePV.searchw()
    TiffFileTemplatePV.searchw()
    TiffFileNumberPV.searchw()
    TiffFileAutoIncrementPV.searchw()
    TiffFileCallBacksPV.searchw()
    TiffFileWriteFilePV.searchw()
    TiffFileAutoSavePV.searchw()
    Ex_time.searchw()
    # af 19/02/2020
    # BeamMonitorPV.setTimeout(15)
    # BeamMonitorPV.searchw()
    get_pv("IN:IMAT:DAE:MON:5:C")
    time.sleep(1)

    header()
    sampleName = ctitle

    runNumber          = RBnumber
    filePath           = "M:\\Data"
    StartingFileNumber  = 0    # Starting number of files
    NumberOfImages      = n_radio
    #
    if( image_type == 0 ):
        MinBeamCountsPerSec = 0  #dark field
    else:
        MinBeamCountsPerSec = mon_th  #radiography, beam monitor 3a  counts per sec  4000

    Ex_time.putw(expo_time)
    MinBeamCounts = (MinBeamCountsPerSec * IMATCamera.pvAcquireTime.getw()) * 0.85

    #Create the structure Tree for Flat
    ensure_dir(filePath)
    ensure_dir(filePath + '\\' + runNumber)
    ensure_dir(filePath + '\\'+ runNumber + '\\'+sampleName + '\\' + data_type )

    #Open Log File
    fileName_log = "IMAT" + runno + "_" + sampleName
    f = open( filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + fileName_log +'_log.txt', 'w')

    #Replace filepath for the camera saving
    filePath           = "C:\\Data"

    # Variables NOT to be changed usually
    fileName           = "IMAT" + runno    + "_" + sampleName + "_" + data_type
    filePrefix = fileName + "\x00"                             # Why do we have to force a NULL  ?
    filePathPrefix = filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + "\x00"
    TiffFilePathPV.array_put(filePathPrefix)                   # Path for file saving (MUST EXISTS !)
    TiffFileNamePV.array_put(filePrefix)                       # File name header
    TiffFileNamePV.pend_io()
    TiffFileTemplatePV.array_put("%s%s_%3.3d.tif\x00")             # Default File name format
    TiffFileNumberPV.putw(StartingFileNumber)                    # Starting number of files
    TiffFileAutoIncrementPV.putw(1)                                # File number will be auto incremented
    TiffFileCallBacksPV.putw(1)                                    # Ensure Callbacks are  Enabled
    TiffFileAutoSavePV.putw(0)                                    # Ensure Auto Save is DISABLED
    change(title=sampleName + "  -  " + data_type)
    print(filePathPrefix)

    if(TiffFilePathExistsPV.getw() != 1) :
        print("Non-existing destination Path. Exiting...")
        TiffFileAutoSavePV.putw(1)    # Ensure Auto Save is RENABLED
        sys.exit(0)


    write_csv(f, 'TIME STAMP', 'IMAGE TYPE' , 'IMAGE COUNTER', 'IMAGE ANGLE', 'COUNTS BM3 before image', 'COUNTS BM3 after image')
    print("test2")
    cset(y=y)
    waitfor_move()
    cset(x=x)
    waitfor_move()
    cset(z=z)
    waitfor_move()
    resume()

    image_counter = 0
    current_a = start_a

    while(current_a <= end_a) :
        cset(rot=current_a)
        waitfor_move()
        time.sleep(1)
        # StartBeamCount = BeamMonitorPV.getw()
        # waitNewImageReady(IMATCamera)
        # EndBeamCount = BeamMonitorPV.getw()
        StartBeamCount = get_pv("IN:IMAT:DAE:MON:5:C")
        waitNewImageReady(IMATCamera)
        EndBeamCount = get_pv("IN:IMAT:DAE:MON:5:C")
        if( (EndBeamCount-StartBeamCount) >= MinBeamCounts) :
            print(("Time stamp: ", time.ctime(), "  Image n: ", image_counter, "  Projection angle=", current_a))
           # print ("Time stamp: ", time.ctime(), "  Image n: ", image_counter, "  Projection angle=", current_a,"   Time left=", (30/3600) * (360-current_a)/step_a)
            TiffFileWriteFilePV.putw(1)
            if current_a < 10:
                print((" Current angular position: ", current_a, "     Wait for the image: ", image_counter, " Time = ", time.ctime()))
            if current_a >=10 and current_a < 100:
                print((" Current angular position: ", current_a, "    Wait for the image: ", image_counter, " Time = ", time.ctime()))
            if current_a >=100:
                print((" Current angular position: ", current_a, "   Wait for the image: ", image_counter, " Time = ", time.ctime()))
            write_csv(f, str(time.ctime()), 'Projection', str(image_counter), "Angle:" + str(current_a), 'Monitor 3 before: '+ str(StartBeamCount), 'Monitor 3 after: '+ str(EndBeamCount))
            current_a += step_a
            image_counter += 1
        else :
            print(("Projection NOT SAVED, intensity variation over 20% --> Beam Counts= ", EndBeamCount-StartBeamCount, "  image number: ", image_counter))
    TiffFileAutoSavePV.putw(1)        # Ensure Auto Save is RENABLED


def CMOS_Zyla_multi_tomo_log(image_type, n_radio, expo_time, mon_th, x, y, z, start_a, end_a, step_a, RBnumber, runno, ctitle, data_type):

    TiffFilePathPV.searchw()
    TiffFilePathExistsPV.searchw()
    TiffFileNamePV.searchw()
    TiffFileTemplatePV.searchw()
    TiffFileNumberPV.searchw()
    TiffFileAutoIncrementPV.searchw()
    TiffFileCallBacksPV.searchw()
    TiffFileWriteFilePV.searchw()
    TiffFileAutoSavePV.searchw()
    Ex_time.searchw()
    #af 19/02/2020
    # BeamMonitorPV.setTimeout(15)
    # BeamMonitorPV.searchw()
    get_pv("IN:IMAT:DAE:MON:5:C")

    time.sleep(1)

    header()
    sampleName = ctitle

    runNumber          = RBnumber
    filePath           = "M:\\Data"
    StartingFileNumber  = 0    # Starting number of files
    NumberOfImages      = n_radio
    #
    if( image_type == 0 ):
        MinBeamCountsPerSec = 0  #dark field
    else:
        MinBeamCountsPerSec = mon_th  #radiography, beam monitor 3a  counts per sec  4000

    Ex_time.putw(expo_time)
    MinBeamCounts = (MinBeamCountsPerSec * IMATCamera.pvAcquireTime.getw()) * 0.85

    #Create the structure Tree for Flat
    ensure_dir(filePath)
    ensure_dir(filePath + '\\' + runNumber)
    ensure_dir(filePath + '\\'+ runNumber + '\\'+sampleName + '\\' + data_type )

    #Open Log File
    fileName_log = "IMAT" + runno + "_" + sampleName
    f = open( filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + fileName_log +'_log.txt', 'w')

    #Replace filepath for the camera saving
    filePath           = "C:\\Data"

    # Variables NOT to be changed usually
    fileName           = "IMAT" + runno    + "_" + sampleName + "_" + data_type
    filePrefix = fileName + "\x00"                             # Why do we have to force a NULL  ?
    filePathPrefix = filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + "\x00"
    TiffFilePathPV.array_put(filePathPrefix)                   # Path for file saving (MUST EXISTS !)
    TiffFileNamePV.array_put(filePrefix)                       # File name header
    TiffFileNamePV.pend_io()
    TiffFileTemplatePV.array_put("%s%s_%4.4d.tif\x00")             # Default File name format
    TiffFileNumberPV.putw(StartingFileNumber)                    # Starting number of files
    TiffFileAutoIncrementPV.putw(1)                                # File number will be auto incremented
    TiffFileCallBacksPV.putw(1)                                    # Ensure Callbacks are  Enabled
    TiffFileAutoSavePV.putw(0)                                    # Ensure Auto Save is DISABLED
    change(title=sampleName + "  -  " + data_type)
    print(filePathPrefix)

    if(TiffFilePathExistsPV.getw() != 1) :
        print("Non-existing destination Path. Exiting...")
        TiffFileAutoSavePV.putw(1)    # Ensure Auto Save is RENABLED
        sys.exit(0)


    write_csv(f, 'TIME STAMP', 'IMAGE TYPE' , 'IMAGE COUNTER', 'IMAGE ANGLE', 'COUNTS BM3 before image', 'COUNTS BM3 after image')
    cset(y=y)
    waitfor_move()
    cset(x=x)
    waitfor_move()
    cset(z=z)
    waitfor_move()
    resume()

    image_counter = 0
    current_a = start_a

    while(current_a <= end_a) :
        cset(axa=current_a,axb=current_a,axc=current_a)
        waitfor_move()
        time.sleep(1)
        # StartBeamCount = BeamMonitorPV.getw()
        # waitNewImageReady(IMATCamera)
        # EndBeamCount = BeamMonitorPV.getw()
        StartBeamCount = get_pv("IN:IMAT:DAE:MON:5:C")
        waitNewImageReady(IMATCamera)
        EndBeamCount = get_pv("IN:IMAT:DAE:MON:5:C")
        if( (EndBeamCount-StartBeamCount) >= MinBeamCounts) :
            print(("Time stamp: ", time.ctime(), "  Image n: ", image_counter, "  Projection angle=", current_a))
            TiffFileWriteFilePV.putw(1)
            if current_a < 10:
                print((" Current angular position: ", current_a, "     Wait for the image: ", image_counter, " Time = ", time.ctime()))
            if current_a >=10 and current_a < 100:
                print((" Current angular position: ", current_a, "    Wait for the image: ", image_counter, " Time = ", time.ctime()))
            if current_a >=100:
                print((" Current angular position: ", current_a, "   Wait for the image: ", image_counter, " Time = ", time.ctime()))
            write_csv(f, str(time.ctime()), 'Projection', str(image_counter), "Angle:" + str(current_a), 'Monitor 3 before: '+ str(StartBeamCount), 'Monitor 3 after: '+ str(EndBeamCount))
            current_a += step_a
            image_counter += 1
        else :
            print(("Projection NOT SAVED, intensity variation over 20% --> Beam Counts= ", EndBeamCount-StartBeamCount, "  image number: ", image_counter))
    TiffFileAutoSavePV.putw(1)        # Ensure Auto Save is RENABLED #added by GB on 11/10/2018


def CMOS_Zyla_multi_golden_tomo_log(image_type, n_radio, expo_time, mon_th, x, y, z, RBnumber, runno, ctitle, data_type):

    TiffFilePathPV.searchw()
    TiffFilePathExistsPV.searchw()
    TiffFileNamePV.searchw()
    TiffFileTemplatePV.searchw()
    TiffFileNumberPV.searchw()
    TiffFileAutoIncrementPV.searchw()
    TiffFileCallBacksPV.searchw()
    TiffFileWriteFilePV.searchw()
    TiffFileAutoSavePV.searchw()
    Ex_time.searchw()
    BeamMonitorPV.searchw()
    time.sleep(1)

    header()
    sampleName = ctitle
    runNumber          = RBnumber
    filePath           = "M:\\Data"
    StartingFileNumber  = 0    # Starting number of files
    NumberOfImages      = n_radio
        #
    if( image_type == 0 ):
        MinBeamCountsPerSec = 0  #dark field
    else:
        MinBeamCountsPerSec = mon_th  #radiography, beam monitor 3a  counts per sec  4000

    Ex_time.putw(expo_time)
    MinBeamCounts = (MinBeamCountsPerSec * IMATCamera.pvAcquireTime.getw()) * 0.85

        #Create the structure Tree for Flat
    ensure_dir(filePath)
    ensure_dir(filePath + '\\' + runNumber)
    ensure_dir(filePath + '\\'+ runNumber + '\\'+sampleName + '\\' + data_type )

        #Open Log File
    fileName_log = "IMAT" + runno + "_" + sampleName
    f = open( filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + fileName_log +'_log.txt', 'w')

        #Replace filepath for the camera saving
    filePath           = "C:\\Data"

        # Variables NOT to be changed usually
    fileName           = "IMAT" + runno    + "_" + sampleName + "_" + data_type
    filePrefix = fileName + "\x00"                             # Why do we have to force a NULL  ?
    filePathPrefix = filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + "\x00"
    TiffFilePathPV.array_put(filePathPrefix)                   # Path for file saving (MUST EXISTS !)
    TiffFileNamePV.array_put(filePrefix)                       # File name header
    TiffFileNamePV.pend_io()
    TiffFileTemplatePV.array_put("%s%s_%4.4d.tif\x00")             # Default File name format
    TiffFileNumberPV.putw(StartingFileNumber)                    # Starting number of files
    TiffFileAutoIncrementPV.putw(1)                                # File number will be auto incremented
    TiffFileCallBacksPV.putw(1)                                    # Ensure Callbacks are  Enabled
    TiffFileAutoSavePV.putw(0)                                    # Ensure Auto Save is DISABLED
    change(title=sampleName + "  -  " + data_type)
    print(filePathPrefix)

    if(TiffFilePathExistsPV.getw() != 1) :
        print("Non-existing destination Path. Exiting...")
        TiffFileAutoSavePV.putw(1)    # Ensure Auto Save is RENABLED
        sys.exit(0)

    write_csv(f, 'TIME STAMP', 'IMAGE TYPE' , 'IMAGE COUNTER', 'IMAGE ANGLE', 'COUNTS BM3 before image', 'COUNTS BM3 after image')
    cset(y=y)
    waitfor_move()
    cset(x=x)
    waitfor_move()
    cset(z=z)
    waitfor_move()
    resume()
    image_counter = 0
    current_a = 0
    G = 360*(old_div((1+math.sqrt(5)),2))

    while(image_counter <= n_radio) :
        cset(axa=current_a,axb=current_a,axc=current_a)
        waitfor_move()

        time.sleep(1)
        StartBeamCount = BeamMonitorPV.getw()
        waitNewImageReady(IMATCamera)
        EndBeamCount = BeamMonitorPV.getw()
        if( (EndBeamCount-StartBeamCount) >= MinBeamCounts) :
            print(("Time stamp: ", time.ctime(), "  Image n: ", image_counter, "  Projection angle=", current_a))
            TiffFileWriteFilePV.putw(1)
            if current_a < 10:
                print((" Current angular position: ", current_a, "     Wait for the image: ", image_counter, " Time = ", time.ctime()))
            if current_a >=10 and current_a < 100:
                print((" Current angular position: ", current_a, "    Wait for the image: ", image_counter, " Time = ", time.ctime()))
            if current_a >=100:
                print((" Current angular position: ", current_a, "   Wait for the image: ", image_counter, " Time = ", time.ctime()))
            write_csv(f, str(time.ctime()), 'Projection', str(image_counter), "Angle:" + str(current_a), 'Monitor 3 before: '+ str(StartBeamCount), 'Monitor 3 after: '+ str(EndBeamCount))
            image_counter += 1
            current_a = (image_counter*G)%360.0
        else :
            print(("Projection NOT SAVED, intensity variation over 20% --> Beam Counts= ", EndBeamCount-StartBeamCount, "  image number: ", image_counter))
    TiffFileAutoSavePV.putw(1)        # Ensure Auto Save is RENABLED # added by TC on 01/07/2018


def CMOS_Zyla_multi_radio_log(image_type, n_radio, expo_time, mon_th, x, y, z, rot, RBnumber, runno, ctitle, data_type):

    TiffFilePathPV.searchw()
    TiffFilePathExistsPV.searchw()
    TiffFileNamePV.searchw()
    TiffFileTemplatePV.searchw()
    TiffFileNumberPV.searchw()
    TiffFileAutoIncrementPV.searchw()
    TiffFileCallBacksPV.searchw()
    TiffFileWriteFilePV.searchw()
    TiffFileAutoSavePV.searchw()
    Ex_time.searchw()
    BeamMonitorPV.searchw()

    time.sleep(1)

    header()
    sampleName = ctitle

    runNumber          = RBnumber
    filePath           = "M:\\Data"
    StartingFileNumber  = 0        # Starting number of files
    NumberOfImages      = n_radio
        #
    if( image_type == 0 ):
        MinBeamCountsPerSec = 0  #dark field
    else:
        MinBeamCountsPerSec = mon_th  #radiography, beam monitor 3a  counts per sec  4000

    Ex_time.putw(expo_time)
    MinBeamCounts = (MinBeamCountsPerSec * IMATCamera.pvAcquireTime.getw()) * 0.85

        #Create the structure Tree for Flat
    ensure_dir(filePath)
    ensure_dir(filePath + '\\' + runNumber)
    ensure_dir(filePath + '\\'+ runNumber + '\\'+sampleName + '\\' + data_type )

        #Open Log File
    fileName_log = "IMAT" + runno + "_" + sampleName
    f = open( filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + fileName_log +'_log.txt', 'w')

        #Replace filepath for the camera saving
    filePath           = "C:\\Data"

        # Variables NOT to be changed usually
    fileName           = "IMAT" + runno    + "_" + sampleName + "_" + data_type
    filePrefix = fileName + "\x00"                             # Why do we have to force a NULL  ?
    filePathPrefix = filePath + '\\'+ runNumber + '\\' + sampleName + '\\' + data_type + "\x00"
    TiffFilePathPV.array_put(filePathPrefix)                   # Path for file saving (MUST EXISTS !)
    TiffFileNamePV.array_put(filePrefix)                       # File name header
    TiffFileNamePV.pend_io()
    TiffFileTemplatePV.array_put("%s%s_%4.4d.tif\x00")             # Default File name format
    TiffFileNumberPV.putw(StartingFileNumber)                    # Starting number of files
    TiffFileAutoIncrementPV.putw(1)                                # File number will be auto incremented
    TiffFileCallBacksPV.putw(1)                                    # Ensure Callbacks are  Enabled
    TiffFileAutoSavePV.putw(0)                                    # Ensure Auto Save is DISABLED
    change(title=sampleName + "  -  " + data_type)
    print(filePathPrefix)

    if(TiffFilePathExistsPV.getw()!=1):
        print("Non-existing destination Path. Exiting...")
        TiffFileAutoSavePV.putw(1) # Ensure Auto Save is RENABLED
        sys.exit(0)
    write_csv(f, 'TIME STAMP', 'IMAGE TYPE' , 'IMAGE COUNTER', 'COUNTS BM3 before image', 'COUNTS BM3 after image')

    cset(axa=rot,axb=rot, axc=rot)
    waitfor_move()
    cset(axa=rot,axb=rot, axc=rot)
    waitfor_move()
    cset(y=y)
    waitfor_move()
    cset(x=x)
    waitfor_move()
    cset(z=z)
    waitfor_move()

    resume()

    image_counter = 0
    while(image_counter < NumberOfImages) :
        time.sleep(1)
        StartBeamCount = BeamMonitorPV.getw()
        waitNewImageReady(IMATCamera)
        EndBeamCount = BeamMonitorPV.getw()
        if( (EndBeamCount-StartBeamCount) >= MinBeamCounts) :
            print(("Total Beam  Counts =", EndBeamCount-StartBeamCount, "  image acquired: ", image_counter))
            TiffFileWriteFilePV.putw(1)
            if( image_type == 0 ):
                write_csv(f, str(time.ctime()), 'Dark Field', str(image_counter), 'Monitor 3 before: ' + str(StartBeamCount), '   Monitor 3 after:  ', str(EndBeamCount))
            else:
                write_csv(f, str(time.ctime()), 'Radiography', str(image_counter), 'Monitor 3 before: ' + str(StartBeamCount), '   Monitor 3 after:  ', str(EndBeamCount))
            image_counter += 1
        else :
            print(("Image NOT SAVED, intensity variation over 20% --> Beam Counts= ", EndBeamCount-StartBeamCount, "  image number: ", image_counter))

    TiffFileAutoSavePV.putw(1)        # Ensure Auto Save is RENABLED # added by TC on 01/07/18