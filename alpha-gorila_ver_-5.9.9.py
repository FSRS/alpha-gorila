# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 22:10:09 2020

alpha-gorila version -5.9.9
BMS object Auto placement programe

@author: Discord LuvTek#0832 
Korean manual file is available.
https://docs.google.com/document/d/1r_q_SJpnbhI42PiVULwfMZMvB-yLf-iJAmsO5Xf8EqU/edit?usp=sharing

***Keysounds should be wave files or it will MALFUNCTION!!!***
Does NOT support LN, #RANDOM and mines etc... Sorry for inconvinience.
"""
###import modules###
import copy
import math
import operator
import random
import sys
import numpy as np
from scipy.fftpack import fft
from scipy.io import wavfile
###Define BMS' path and operation sections##
path="Adam\_Adam[test].bms" #Enter the full path of a BMS file
#encoding='UTF-8' #define here?
#Copy of original BMS file will be saved at BMSbackup subfolder 
#USE \\ (double backslash) instead of \

operation_sections=[(1,9),(9,17),(17,25),(25,29),(29,33)] #list of Tuple [(A, B),(C,D),...]
#The program will write a pattern following the order of the list.
#idea: parse with non-keysound-object at 2P scratch lane

#USE tuple (A, B) to write a pattern for measure #A to #(B-1)
#A and B should be 0 or positive number and A<B
##(1, 16) will write a pattern from the measure #001 to #015 (NOT #016)
##(1, 8.5) will write a pattern from the measure #001 to the first half of #008
##(64, 64) will do NOTHING
##(64, 65) will write a pattern for the entire measure #064 

###settings###
#custom your settings

###Don't set values below as 0 or negative number unless you really want to raise the errors.
###You can also set those values as list which has SAME length with operation_sections

tateren_interval=16 #Positive number
#16 for sixteenth note (default), 8 for eigth note, 32/3 for dotted sixteenth note, etc...
#2 notes which have smaller or same interval than tateren_interval regarded as tateren

muri_tateren_interval=24 #Positive number
#24 for twentyfourth note (default), 32 for thirty-second note, etc...
#2 notes which have smaller or same interval than muri_tateren_interval regarded as muri_tateren
##muri_tateren will not be appeared in the pattern unless you pre-writed (pre-wrote? meh) muri_tatren on 1P region

tolerable_tateren=[1,1,1,1,False] #Positive integer or True (Default: 1)
#1 for no tateren (default), 2 for max 2 renta (1 1 2 will appear but 1 1 1 doesn't)
# 4 for max 4 renta (1 1 1 3 and 1 1 1 1 5 will appear but 1 1 1 1 1 doesn't)
## Can also set as float (1.2, 1.5, 2.4,...)
## Float value 2.4 allows 2 renta for 40% , 3 renta for 60% possibility each time.
###False may return absolutely nonsensical tateren pattern. If you want this, ENJOY!
###False value gives some bugs...muri_tateren appears on the result. Please set the value as (not very large) int

MAX_notes_per_measure=False #Positive number as 32. somewhat obvious.
#If you don't want to enable it, use (boolean) False rather than 99 or large number.

lane_restriction=[(1,), (7,), False, False, False]#tuple containing integers 1-7 or False (Default)

#If you don't want to manipulate 1P lane no. 1 and 7 (#XYZ11 and #XYZ19), set this as (1,7)
#If you don't want to manipulate only lane no.1 (#XYZ11), set this as (1,)
#If you want to manipulate all the lanes, set this as False rather than ()

#***please use only positive integer from here. (Don't use list)***
#***do NOT change maxFFT_point&cutoff_freq NOW (It raises error)***
maxFFT_point=12 #Do (2**maxFFT_point) point FFT
##12 or larger integer is recommended (Default=12)
## 2**12=4096 which gives ~11Hz Resolution

cutoff_freq=172 #define cutoff frequency as Hz (Default=172)
##positive number larger than 20 (Human cannot hear below 20Hz)
##frequency domain lower than cutoff_freq will be discarded.

#***please use only boolean from here. (Don't use list)***
erase_unused_nk_obj=True #True or False (Default: True)
#If it is True, it will erase unused non-keysound objects after writting the pattern.

move_unused_2P_obj=False #True or False (Default: False)
#If it is True, it will move unused 2P objects to BGM reion after writting the pattern.
"""
FULL AUTO MODE (UNavailable NOW)
This mode will make a pattern from a non-key (0 notes) BMS file

ENABLE_FULL_AUTO_MODE=False #True or False

total_notes_target=2020 #Positive integer. (positive) non-integer is OK but WHY
#The pattern will have total notes around this value
##If the value is larger than total objects of BMS files it will use almost all of objects.


minimum_keysound_length=50 #positive number larger than 46.5 as ms (millisecond) unit
#keysound files shorter than the value will not be used.

maximum_keysound_length=5000 #positive number larger than minimum_keysound_length as ms unit
#keysound files longer than the value will not be used.
"""
##Define Variables###
table=[6,1,2,3,4,5,8,9] #sc, 1, 2, 3, 4, 5, 6, 7 in BMS format
table_rev=[0,1,2,3,4,5,0,0,6,7]

###Define Functions###
def lcm(a, b): #Least Common Multiple
    """
    Parameters must be integers except 0.
    Returns The Least Common Multiple of a and b as positive integer.
    """
    return abs(a*b) // math.gcd(a, b)

def num_to_nt(num, res_list):
    (n_dec, n_int)=math.modf(num)
    n_int=int(n_int)
    return  (n_int, n_dec*res_list[n_int])


def compare(pos_a, pos_b):
    """
    pos_a and pos_b both should be tuple as (48, 33)

    Returns 1 if a is early than b
    0 if a is same as b
    -1 if a is late than b

    """
    v=0
    if pos_a[0]>pos_b[0]: v=-1
    elif pos_a[0]==pos_b[0]:
        if pos_a[1]>pos_b[1]: v=-1
        if pos_a[1]<pos_b[1]: v=1        
    elif pos_a[0]<pos_b[0]: v=1
    return v

def v_a(t, x , len_list, res_list): #vertial_add
    """

    Parameters
    ----------
    t :  obj' vertical position (48, 33) represents object on #048 33/64
    x : vertical interval to add or sub, use 192th note (1/192) as unit.
        For example, x=12 for sixteenth note addition
        x=-24 for eighth note substraction
    len_list : put bms.measure_len_list
    res_list : put bms.measure_len_list

    Returns tuple same form as t 
    t=(48, 33), x=12 will return t=(48,37) if len_list[48]=64, res_list[48]=64
    -------

    """
    t2=list(t)
    t2[1]=t2[1]*len_list[t2[0]]*192/res_list[t2[0]]#convert t as 1/192 unit
    t2[1]+=x
    #t2[1]=round(t2[1])
    while t2[1]>=192*len_list[t2[0]] and t2[0]<len(res_list)-1:
        t2[1]+=(-192*len_list[t2[0]])
        t2[0]+=1
        
    while t2[1]<0 and t2[0]>0:
        t2[0]+=-1
        t2[1]+=(192*len_list[t2[0]])   
        
    t2[1]=t2[1]/len_list[t2[0]]/192*res_list[t2[0]] #convert t2 as output format    
    #t2[1]=round(t2[1])
    return tuple(t2)

def pfo_dict(ks_set, ks_dct, FFT_dct): #peak_freq_order_dict, not written
    """
    Input ks_set (keysound_set) as {AA, AB, AD, D9, E2, ...}
    ks_dct (keysoud_dict) as bms.keysound_dict
    FFT_dct (FFT_dict) as bms.FFT_dict
    Returns peak_freq_order_dict

    """
    #make peak_freq_set 
    #non-keysound object will raise KeyError. Just define peak_freq = 0
    ##peak_freq cannot be 0 because of cutoff.
            
        #order the keysounds' peak_freq (the lowest one is 0, same number for same peak_freq)
        #define peak_freq_order_dict [['AB', 0], ['AC', 1], ...] (peak_freq order)
        ##peak_freq==0, define the order as False
    temp_list=[]
    peak_freq_list=[]
    
    #collect keysounds' peak_freq
    for ks in ks_set: #example 'AB' is in ks_set
        if ks in ks_dct : #example key 'AB' has a value 'spam.wav'
            if ks_dct[ks] in FFT_dct and not ks_dct[ks] in temp_list: #key 'spam.wav' is in FFT_dict
                temp_list.append(ks_dct[ks])
                if FFT_dct[ks_dct[ks]][1]!=0: peak_freq_list.append(FFT_dct[ks_dct[ks]][1]) #example append 150 (peak_freq)
    pfl=list(set(peak_freq_list)) #remove redundant peak_freq
    pfl.sort()
    ##peak_freq==0, define the order as False
        #example 'AC' has no value in ks_dct
    peak_freq_order_dict={}
    for ks in ks_set:
        order=False
        for i in range(1):
            if ks in ks_dct:
                if ks_dct[ks] in FFT_dct:
                    if FFT_dct[ks_dct[ks]][1]!=0:
                        order=pfl.index(FFT_dct[ks_dct[ks]][1])+1
                    else: break
                else: break
            else: break
        #***write///
        peak_freq_order_dict[ks]=order
    
    #get the index of pfl
    
    return peak_freq_order_dict

def overlap(note_time, lane, obj_1P):
    """
    Parameters
    note_time : tuple (measure#, obj' vertical position)
                       (48, 33) represents object on #048 33/64
                       if resolution of #048 is 64
    lane : integer 0-7, obj' horizontal position
    obj_1P: use op1 
    Returns the object overlaps with another object or not (True or False)
    If the value is True, moving the object to the lane is forbidden
    """
    v=False
    for i in range(len(obj_1P[lane][note_time[0]])):
        if obj_1P[lane][note_time[0]][i][0]==note_time[1]:
            v=True; break
        if obj_1P[lane][note_time[0]][i][0]>note_time[1]: break
    return v

def tateren(note_time, lane, obj_1P, tt_intv, mt_intv, tol_ttn, len_list, res_list):   
    """
    Read the function overlap for Parameters
    
    tt_intv: tateren_interval (or its element)
    mt_intv: muri_tateren_interval (or its element)
    tol_ttn: tolerable_tateren (or its element)
    
    Returns moving the object leads to unwanted tateren or not (True or False)
    If the value is True, moving the object to the lane is forbidden

    """
    result=False
    if type(tol_ttn)==int: tol_tt=tol_ttn
    else:
        prob, tt_0 =math.modf(tol_ttn)
        tt_0=int(tt_0)
        tol_tt=np.random.choice(np.array([tt_0,tt_0+1]), p=[1-prob, prob])
    
    lim_e=v_a(note_time, -(192/tt_intv)*tol_tt, len_list, res_list)
    lim_l=v_a(note_time, (192/tt_intv)*tol_tt, len_list, res_list)

    #get temporary measure(s) data until each side (forward AND backward) 
    #(use tateren_interval*tolerable_tateren)
    v_pos_list_e=[] #save notes early than note_time
    v_pos_list_l=[note_time] #save notes late than note_time
    for mes_no in range(lim_e[0], lim_l[0]+1):
        mes_dat=obj_1P[lane][mes_no]
        for mes_i in mes_dat:
            mes_t=mes_i[0]
            mes_tup=(mes_no, mes_t)
            if compare(lim_e,mes_tup) >= 0 and compare(lim_l,mes_tup) <=0 : #timing comparison
                if compare(mes_tup, note_time)==1: v_pos_list_e.append(mes_tup)
                else: v_pos_list_l.append(mes_tup)
    v_pos_list_e.append(note_time)
    v_e, v_l = v_pos_list_e, v_pos_list_l
    #calculate the interval
    t_c=0 #define tateren_count
    for i in range(len(v_e)-1):
        if mt_intv!=False:
            if compare(v_a(v_e[-(i+1)],-192/mt_intv, len_list, res_list), v_e[-(i+2)]) >= 0: #if muri_tateren exists return True
                result=True; break
        if tt_intv!=False and tol_tt!=False:
            if compare(v_a(v_e[-(i+1)],-192/tt_intv, len_list, res_list), v_e[-(i+2)]) >= 0: 
                t_c+=1
                if t_c >= tol_tt: result=True; break #if tateren_count reaches tolerable_tateren
    if not result:
        for i in range(len(v_l)-1):
            if mt_intv!=False:
                if compare(v_a(v_l[i],192/mt_intv, len_list, res_list), v_l[i+1]) <= 0 :
                    result=True; break
            if tt_intv!=False and tol_tt!=False:
                if compare(v_a(v_l[i],192/tt_intv, len_list, res_list), v_l[i+1]) <= 0 : 
                    t_c+=1
                    if t_c >= tol_tt: result=True; break #if tateren_count reaches tolerable_tateren

    return result

def data_to_BMS(measure, obj_data, res, person, lane_n):
    """
    Parameters
    ----------
    measure : int 0-999
    obj_data : get op1 or op2's sublist. for example, op1[7][48]
    res : measure's resolution
    person : int 0-2 (bgm, 1P and 2P each)
    lane_n : int 0-7 (sc, 1-7 each)

    Returns #04819: 00AB\n
    -------
    """
    msr='0'*(3-len(str(measure)))+str(measure)
    if person==0: ln_n='01'
    else: ln_n=str(person)+str(table[lane_n])
    note_write='00'*res
    for obj in obj_data:
        note_write=note_write[:2*obj[0]]+obj[1]+note_write[2*(obj[0]+1):]    
    n_line='#'+msr+ln_n+':'+note_write+'\n'
    return n_line
    
###Define Modules###
class BMSData(object):
    
    def __init__(self, filename):
        f = open(filename, 'rt', encoding='shift_jisx0213') 
        lines = f.readlines()
        f.close()
        
        self.lines=lines
        self.keysound_dict={} #sound file dict
        self.measure_len_list=[] #measure length list
        self.measure_res_list=[] #measure resolution list
        
        for line in lines:
            if line[-2:] == "\r\n": line = line[:-2]
            else: line = line[:-1]
            (c, _, parameter) = line.partition(' ')
            command = c.upper()
            if _ == " ":
                if command[:4] == "#WAV": self.keysound_dict[command[4:]]=parameter
            elif c[1:4].isnumeric():
                (ms_no, colon, ms_len)=command.partition(':')
                while len(self.measure_len_list)<=int(ms_no[1:4]): 
                    self.measure_len_list.append(1)
                    self.measure_res_list.append(1)
                if ms_no[4:6]=='02': self.measure_len_list[int(ms_no[1:4])]=float(ms_len)
                #calculate LCM of Vertical Grid Resolution
                elif int(ms_no[4]) in (1,2): self.measure_res_list[int(ms_no[1:4])]=lcm(self.measure_res_list[int(ms_no[1:4])],int(len(ms_len)/2))

                #and rewrite the BMS following those Resolution
                ##write the code that makes obj_list
        #rewriteBMS=''
        self.obj_1P_position_list=[[],[],[],[],[],[],[],[]] #sc, 1, 2, 3, 4, 5, 6, 7 in BMS format (1P)
        self.obj_2P_position_list=[[],[],[],[],[],[],[],[]] #sc, 1, 2, 3, 4, 5, 6, 7 in BMS format (2P)
        self.notes_per_measure_list=[]
        for i in range(len(self.measure_len_list)):
            self.notes_per_measure_list.append(0)
            for j in range(8):
                self.obj_1P_position_list[j].append([])
                self.obj_2P_position_list[j].append([])
        # op_list has sublists (0-7 according to the lane #)
            ## the sublists has sublists according to the measure #
                ### sublists contain the vertical position and object nuumber as tuple (0, 'AB')
        for line in lines:
            #flag=False
            if line[1:6].isnumeric():
                if int(line[4]) in (1,2):
                    (ms_no, colon, ms_len)=line.partition(':')
                    (obj, _r, _n)=ms_len.partition('\r')
                    res=self.measure_res_list[int(ms_no[1:4])]
                    l_obj=int(len(obj)/2)
                    if int(line[4])==1:
                        for i in range(int(l_obj)):
                            if obj[2*i:2*(i+1)]!='00':
                                self.obj_1P_position_list[table_rev[int(line[5])]][int(line[1:4])].append((int(i*res/l_obj),obj[2*i:2*(i+1)]))
                                self.notes_per_measure_list[int(line[1:4])]+=1
                    elif int(line[4])==2:
                        for i in range(int(l_obj)):
                            if obj[2*i:2*(i+1)]!='00':
                                self.obj_2P_position_list[table_rev[int(line[5])]][int(line[1:4])].append((int(i*res/l_obj),obj[2*i:2*(i+1)]))
                         
        #FFT the keysounds
            #check foon.wav exists, use s.rpartition('\\')
            #FileNotFoundError Exception
            # do 4096 point FFT
            #if keysound is too short to do 4096 point FFT, try 2048,1024,512 and 256
        self.FFT_dict={}
        flag=True
        errors=''
        for k in self.keysound_dict:
            ks_name=self.keysound_dict[k]
            if not ks_name in self.FFT_dict:             #already checked keysound?
                ks_path=path.rpartition('\\')[0]+'\\'+ks_name
                #print(ks_path)
                file_len, peak_freq, peak_amplitude = 0, 0, 0
                try:
                    fs, data = wavfile.read(ks_path) # load the data
                    
                    if len(data)>=256:
                        file_len=len(data)
                        exp=int(math.log(len(data),2))
                                
                        point=2**min(exp,12) #you can change number 12
                        #for better resolution change 12 to an int over 12
                        
                        c_f=172 #cutoff_freq you can change this
                        c_i=math.ceil(c_f*point/44100)
                        
                        if len((data.shape))==2:
                            A_left, A_right = data.T[0][:point], data.T[1][:point]
                            B_left, B_right =[ele/2**15 for ele in A_left],  [ele/2**15 for ele in A_right]  #16 bit sample wave file
                            C_left, C_right = fft(B_left), fft(B_right)
                            C_l_abs, C_r_abs = np.absolute(C_left), np.absolute(C_right)
                            peak_l_amp=max(C_l_abs[c_i:int(point/2)])
                            peak_r_amp=max(C_r_abs[c_i:int(point/2)])
                            if peak_l_amp > peak_r_amp:
                                peak_amplitude=peak_l_amp
                                peak_freq=list(C_l_abs).index(peak_l_amp)
                            else:
                                peak_amplitude=peak_r_amp
                                peak_freq=list(C_r_abs).index(peak_r_amp)
    
                        elif len((data.shape))==1:
                            A = data.T[:point]
                            B= [ele/2**15 for ele in A]
                            C = fft(B)
                            C_abs=np.absolute(C)
                            peak_amplitude=max(C_abs[c_i:int(point/2)])
                            peak_freq=list(C_abs).index(peak_amplitude)*(2**maxFFT_point/point)
                except: 
                    if flag:
                        print("Oops!",sys.exc_info()[0],"occured.")
                        print('1. Check the file', ks_name, 'exists in your path.')
                        print('2. Convert your keysound file', ks_name[:-4]+'.ogg', 'as .wav format')
                        print('If you want to check all the keyfiles missing please read _keysounds_not_found.txt at your BMS directory')
                    flag=False
                    errors+=ks_name+'\n' 


        #define FFT_dict {'foon.wav': (length, peak_freq, peak_amplitude),...}
            #save peak_freq as int (0-2047 OK)
            #keysound shorter than 5.81ms has peak_freq, peak_amplitude = 0, 0
            self.FFT_dict[ks_name]=(file_len,int(peak_freq), peak_amplitude) #44100 equals 1 sec
        
        #make density_list=[10.5, 2.3 , 4.7 ,...]
            #divide the # of object on 1P lane as its BPM
  
        if errors!='':
            f_new= open(path.rpartition('\\')[0]+'\\'+"_keysounds_not_found.txt","w+")
            f_new.write(errors)
            f_new.close() 

    def writeBMS(self,op_1,op_2):
        lines_write=copy.deepcopy(self.lines)
        for line in self.lines: #Remove 1P 2P data of original BMS file.
            if line[1:4].isnumeric():
                if int(line[4]) in (1,2):
                    lines_write.remove(line)
        if move_unused_2P_obj: m2=0 #if move_unused_2P_obj is True , PLEASE AUTO ARRANGE THE 2P OBJECTS TO BGM REGION
        else: m2=2
        for mes_no in range(len(self.measure_res_list)):
            for lane_no in range(0,8):
                if op_1[lane_no][mes_no]!=[]:
                    #print(op_1[lane_no][mes_no])
                    new_line=data_to_BMS(mes_no, op_1[lane_no][mes_no], self.measure_res_list[mes_no], 1, lane_no)
                    lines_write.append(new_line) 
                if op_2[lane_no][mes_no]!=[]:
                    new_line_2=data_to_BMS(mes_no, op_2[lane_no][mes_no], self.measure_res_list[mes_no], m2, lane_no)
                    lines_write.append(new_line_2)
        new_path=path[:-4]+'_new'+str(random.randint(1000,9999))+path[-4:]      
        re_write=''
        for n_l in lines_write:
            re_write+=n_l+'\n'
        f_new= open(new_path,'w+', encoding='shift_jisx0213')
        f_new.write(re_write)
        f_new.close() 
        return new_path
    
###Main Code###



#values: default or not?

t_i, m_i, t_t= 16, 24, 1
MX_n, l_r = False, False
    
bms = BMSData(path)
#get keysound_dict {'01':'foon.wav', '02':'sofa.wav', ...} 
#get measure_len_list [1,1,1,0.5,1,1,2,...]
#get measure_res_list [192,64,16,...]
#get FFT_dict {'foon.wav': [length, peak_freq, peak_amplitude],...}
l_l=bms.measure_len_list
r_l=bms.measure_res_list
op1=copy.deepcopy(bms.obj_1P_position_list)
op2=copy.deepcopy(bms.obj_2P_position_list)
npm=copy.deepcopy(bms.notes_per_measure_list)
k_d=bms.keysound_dict
f_d=bms.FFT_dict

#IF FULL MODE IS ENABLED, PLEASE AUTO ARRANGE THE OBJECTS TO 2P REGION HERE (not now)

for sect_no in range(len(operation_sections)): #loops following operation_sections
    #define t_i, m_i, t_t, MX_n, l_r
    #***PLEASE check the variable type. LIST or int(float, tuple)?*** it could be mixed up
    if type(tateren_interval)==list: 
        if len(tateren_interval)==len(operation_sections):
                t_i=tateren_interval[sect_no]
        else: print('If tateren_interval is a list, its length should be same with operation_sections')
    else: t_i=tateren_interval
    
    if type(muri_tateren_interval)==list: 
        if len(muri_tateren_interval)==len(operation_sections):
                m_i=muri_tateren_interval[sect_no]
        else: print('If muri_tateren_interval is a list, its length should be same with operation_sections')
    else: m_i=muri_tateren_interval     

    if type(tolerable_tateren)==list: 
        if len(tolerable_tateren)==len(operation_sections):
                t_t=tolerable_tateren[sect_no]
        else: print('If tolerable_tateren is a list, its length should be same with operation_sections')
    else: t_t=tolerable_tateren
    
    if type(MAX_notes_per_measure)==list: 
        if len(MAX_notes_per_measure)==len(operation_sections):
                MX_n=MAX_notes_per_measure[sect_no]
        else: print('If MAX_notes_per_measure is a list, its length should be same with operation_sections')
    else: MX_n=MAX_notes_per_measure
    
    if type(lane_restriction)==list: 
        if len(lane_restriction)==len(operation_sections):
                l_r=lane_restriction[sect_no]
        else: print('If tateren_interval is a list, its length should be same with operation_sections')
    else: l_r=lane_restriction

    section=operation_sections[sect_no] #loops following sections
        #write a pattern from note_time from A to (earlier than) B
    #get A and B as note_time format (31,0), (48,17), etc...
    nt_A, nt_B = num_to_nt(section[0], r_l), num_to_nt(section[1], r_l) 

    
    for lane_no in range(1,8): #loops following 2P lanes 
        obj_list=[]
        ks_name_list=[]
        for mes_no in range(nt_A[0], nt_B[0]+1): #loop for measure
            for note_dat in op2[lane_no][mes_no]: #read o2p lane, measure
                n_dt=(mes_no, note_dat[0])
                if compare(nt_A, n_dt)>=0 and compare(nt_B,n_dt)==-1 : #check object is in nt_A to (earlier than) nt_B
                    obj_list.append(((mes_no, note_dat[0]), note_dat[1])) #append to obj_list [((48,37), 'AB'), ((48,39), 'AC'), ...]
                    ks_name_list.append(note_dat[1])
                if compare(nt_B,n_dt)>=0: break #if late than B, break
    
        keysound_set=set(ks_name_list)  #make keysound_set {'AA', 'AB', 'AC', 'AD', ...}
        pfod=pfo_dict(keysound_set, k_d, f_d)#use function pfod [['AA', 3], ['AB', 1], ['AC', 2] ...]
        #print(obj_list)
        
        olc=copy.deepcopy(obj_list) #use obj_list_copy
        try_lanes=[1,2,3,4,5,6,7]
        if l_r!=False:
            for l in l_r:
                try_lanes.remove(l)
        temp_freq=0
        for n_dat in obj_list: #loops following objects
            temp_rand=random.randint(0,len(try_lanes)-1)
            try: #set dirction
                very_long_instant=1/temp_freq
                direction=int((f_d[k_d[n_dat[1]]][1]-temp_freq)/(f_d[k_d[n_dat[1]]][1]-temp_freq))
            except: #no temp_freq available
                direction=random.choice([1,-1])
            for loop_once in range(1): #to use break
                if MX_n!=False: #check MAX_notes_per_measure
                    if npm[n_dat[0][0]]>=MX_n: break #do not iterate if npm exceeds MXnpm
                itr=0 #itr=0  # modulation iteration
                max_itr=len(try_lanes)
                do_itr=True
                while itr<max_itr and do_itr: # if itr reaches 7 (or 7-(# of restriction_lanes)), pass
                    if pfod[n_dat[1]]!=False: try_lane=try_lanes[pfod[n_dat[1]]%max_itr] #get pfod value
                    else: try_lane=try_lanes[temp_rand]
                    do_lane=False
                    for loop_once_2 in range(1): #to use break
                        if overlap(n_dat[0], try_lane, op1): itr+=1; break#check object overlap (using mod 7 values of array_temp)
                        if tateren(n_dat[0], try_lane, op1, t_i, m_i, t_t, l_l, r_l): itr+=1; break #overlapping==False and tateren==False, check tateren, muri_tateren, notes per measure
                        do_lane=True# it is OK
                    if do_lane: # if it is OK 
                         #modulate op1 and op2, please modulate them in time order.
                        #print('BEFORE', op2[lane_no][n_dat[0][0]])
                        #print((n_dat[0][1],n_dat[1]))
                        op2[lane_no][n_dat[0][0]].remove((n_dat[0][1],n_dat[1])) #remove the element of op2' sublist
                        #print('AFTER', op2[lane_no][n_dat[0][0]])
                        op1[try_lane][n_dat[0][0]].append((n_dat[0][1],n_dat[1])) #insert and arrange op1
                        op1[try_lane][n_dat[0][0]]=sorted(op1[try_lane][n_dat[0][0]], key=operator.itemgetter(0))
                        try: 
                            temp_freq=f_d[k_d[n_dat[1]]][1]
                        except:
                            temp_freq=0
                        npm[n_dat[0][0]]+=1
                        do_itr=False
                        #print('OK')
                    else:#if it is not ok
                        for ks in pfod: #modulate pfod for each lane
                            if pfod[ks]!=False: pfod[ks]+=direction 
                        temp_rand=(temp_rand+direction)%max_itr ##if the order is false, just modulate only object, not the whole list.

op1_final=copy.deepcopy(op1)  
op2_final=copy.deepcopy(op2)  
if erase_unused_nk_obj:
    for lane_no in range(8): #if erase_remainder_nonkey_object is True, erase them on op2
        for mes_no in range(len(r_l)):
            for n_dt in op2[lane_no][mes_no]:
                if not (n_dt[1] in k_d): op2_final[lane_no][mes_no].remove(n_dt)

#***Rewrite the BMS File*** with op1_final and op2_final
# Use Class?
print('Check the file', bms.writeBMS(op1_final, op2_final))
print('PLEASE remove all the variables to access the BMS file')
