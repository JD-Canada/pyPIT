# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 14:54:06 2017

@author: Jason
"""
import os
import os.path
import pandas as pd
import numpy as np

def importTIRIS():
    """
    Import untreated TIRIS data in the form of tabular data with three columns 
    labeled "Antenna", "Tag", "MSTime" in this order. MSTime needs to be in decimal time.
    """
    inputWS = "./TIRIS"
    RawTIRIS=pd.DataFrame()
    files = os.listdir(inputWS)
    for f in files:
        dat = pd.read_csv(os.path.join(inputWS,f), sep=',',header=1,skipfooter=1, engine='python') 
        dat['Download']=f
        RawTIRIS=RawTIRIS.append(dat)
        del dat
        print "Imported %s"%(f)
        
    RawTIRIS.columns=['Antenna','Tag', 'MSTime','Download']
    RawTIRIS=RawTIRIS[['Antenna','Tag', 'MSTime']]
    
    RawTIRIS = RawTIRIS[(RawTIRIS.Tag != 226000518440) & (RawTIRIS.Tag != 3582447370239)]
    
    return RawTIRIS
    
def importMetadata(export):
    
    """
    Import metadata of study. Metadata is entered in .xlsx files following the 
    example formats in the ./Metadata folder. 
    """
    
    #file imports
    if export == "Dmax":
        Trial = pd.read_excel('./Metadata/Trial_2hr.xlsx')
    if export == "AttemptRate":
        Trial = pd.read_excel('./Metadata/Trial.xlsx') 
    if export == "Video":
        Trial = pd.read_excel('./Metadata/Trial.xlsx')

    Tags = pd.read_excel('./Metadata/Tags.xlsx')
    BetweenTrials = pd.read_excel('./Metadata/Between_Trials.xlsx')
    CameraStartTimes = pd.read_excel('./Metadata/Camera_start_times.xlsx')
    StartEndOfDayTimes = pd.read_excel('./Metadata/StartEndOfDayTimes.xlsx')
    TagsInTank = pd.read_excel('./Metadata/TagsInTank.xlsx')
    NumberTags=pd.read_excel('./Metadata/NumberTagsTrial.xlsx')
    AntennaSpec=pd.read_excel('./Metadata/Burstflume_antennasspec.xlsx')
    
    return Tags,Trial,BetweenTrials,CameraStartTimes,StartEndOfDayTimes,TagsInTank,NumberTags,AntennaSpec

def includeLags(df):
    
    """
    Calculate lag times between antenna detections. Data is first sorted by 
    Tag and MSTime and then grouped by Tag
    """
    
    df=df.sort_values(['Tag','MSTime'])
    df['Lag'] = 86400*df.groupby(['Tag'])['MSTime'].diff()
    df['FalseAttempts']=False
    
    return df

def includeMetadata(df,Trial):
    
    """
    Matches MSTime of detection with corresponding metadata (e.g. trial index, 
    flow rate, configuration) 
    """
    
    MSTime_idx = df['MSTime']
    start_time_idx = Trial['TrialStart']
    stop_time_idx = Trial['TrialStop']
    start_idx = start_time_idx.searchsorted(MSTime_idx, side='right')-1     #finds which index MSTime_idx is closest to in start_time_idx
    end_idx = stop_time_idx.searchsorted(MSTime_idx, side='right')          #finds which index MSTime_idx is closest to in stop_time_idx
    df['idx'] = np.where(start_idx == end_idx, end_idx, np.nan)
    
    df = df.merge(Trial, left_on=['idx'], right_index=True, how='left')     #merges dataframes on idx
    df = df.drop(['idx'], axis=1) 
    
    return df
  
def handleFalsePositives(df,lagThreshold):
    
    """
    Exception routine to remove false attempts caused by fish holding station in 
    the lee of weir baffles. Fish holding station for long periods in undetectable 
    zones cause "false attempts" (e.g. lags > threshold lag time).
    This code could be modified to treat other exceptions that need to be taken 
    care of before numbering attempts. If you don't have station holding in your 
    study, you can just skip over this function.
    """
    
    df=df.sort_values(['Tag','MSTime'])
    df['AntennaDifference'] = df.groupby(['Tag'])['Antenna'].diff()
    df['FalseAttempts'] = (df['Lag']>lagThreshold)&(df['AntennaDifference'].isin([-2,-1,0,1,2]))&(df['Antenna']!=1)&(df['Configuration']==500)&(df['Tag']==df['Tag'].shift())
    df = df.drop(['AntennaDifference'], axis=1)

    return df

def includePresences(df,lagThreshold):

    Lags = df[(df.Lag > lagThreshold) | (df.Lag.isnull()) ]
    Lags = Lags[Lags['FalseAttempts'] == False]
    Lags['Presence'] = Lags.groupby(['Tag']).cumcount()+1
    df = pd.merge(df,Lags[['Tag','MSTime','Presence']], how='left', on=['Tag','MSTime'])
    df=df.fillna(method='ffill') 
    
    df['Category']=0
         
    return Lags,df

def handleExceptions(df,export):
    
    """
    Case specific exception handling:
        
    For my study I had fish that prematurely entered the flume, either partly stayed
    within the flume or fully stayed within the flume during the mid-day buffer,
    or remained in the flume after the trials were over while still being detected.
    To handle these scenarios I attributed each possibility a category flag as follows:
        
        (0) - good attempt within the time boundaries of a trial
        (1) - attempt starting and ending prematurely to the first trial of the day
        (2) - attempt starting prematurely, but ending within the first trial 
        (3) - attempt starting within trial but ending within the mid-day buffer
        (4) - attempt beginning and ending within mid-day buffer
        (5) - beginning within the mid-day buffer but ending during the second trial
        (6) - an attempt beginning in the first trial and ending in the second ... weir baffles
        (7) - an attempt beginning in second trial and ending in the end of day buffer
        (8) - attempt occuring completely within the end of day buffer
        
    """
    
    df=df.drop(['Category'], axis =1)
    Grouped = df.groupby(['Tag','Presence'])
    Categories=Grouped.agg({'Configuration':[('Configuration','first')],'Flow':[('First','first'),('Last','last')]})
    Categories=Categories.reset_index()
    Categories.columns = ['Tag','Presence','Configuration','FlowFirst','FlowLast']

    Categories['Category']=np.where(Categories.FlowFirst == Categories.FlowLast, 0, np.nan) 
    Categories['Category']=np.where(((Categories.FlowFirst == "SDB") & (Categories.FlowLast == "SDB")), 1, Categories.Category) 
    Categories['Category']=np.where(((Categories.FlowFirst == "SDB") & (Categories.FlowLast != "SDB")), 2, Categories.Category) 
    Categories['Category']=np.where((((Categories.FlowFirst == 100)|(Categories.FlowFirst == 150)) & (Categories.FlowLast =="MDB")), 3, Categories.Category)
    Categories['Category']=np.where(((Categories.FlowFirst == "MDB") & (Categories.FlowLast =="MDB")), 4, Categories.Category)
    Categories['Category']=np.where(((Categories.FlowFirst == "MDB") & ((Categories.FlowLast == 100)|(Categories.FlowLast == 150))), 5, Categories.Category)
    Categories['Category']=np.where(((Categories.FlowFirst == 100) & (Categories.FlowLast == 150)), 6, Categories.Category) 
    Categories['Category']=np.where(((Categories.FlowFirst == 150) & (Categories.FlowLast == 100)), 6, Categories.Category) 
    Categories['Category']=np.where((((Categories.FlowFirst == 100)|(Categories.FlowFirst == 150)) & (Categories.FlowLast =="EDB")), 7, Categories.Category)
    Categories['Category']=np.where(((Categories.FlowFirst =="EDB") & (Categories.FlowLast =="EDB")), 8, Categories.Category)
    Categories['Cull']=np.where((Categories.FlowFirst!=Categories.FlowLast), Categories.FlowLast, np.nan) #used to figure out what the end trial is to remove for condition 


    df = pd.merge(df,Categories, how='left', on=['Tag','Presence','Configuration'])
    
    """
    Treats data based on rules for select categories (e.g. keep only the valid 
    part of an attempt that spanned into the break)
    """
    df=df[(df['Tag'].isin([226000745697,226000769051]) & df['Configuration'].isin([500])) == False] 
    if export == "Dmax":
        df=df[df['Category'].isin([0,2,3,5,6,7])] 
        df=df[(df['Category'].isin([6]) & (df['Cull']==df['Flow'])) == False]
        df=df[(df['Flow'].isin(['MDB']) |df['Flow rate'].isin(['EDB'])) == False] 
        print "Outputing Dmax style data"
    elif export == "AttemptRate":
        df=df[df['Category'].isin([0,2,3,4,5,6,7])] 
        print "Outputing attempt rate style data"
    elif export == "Video":
        df=df[df['Category'].isin([0])] 
        print "Outputing only case 0 events for video analysis"
    return df
    
def includeAttemptData(df):

    """
    Calculate duration of each attempt along with relevant attempt data:
        -MaxAntenna
        -FirstAntenna
        -LastAntenna 
    """
    aggformula= {'MSTime':[('Start','first'),('Stop','last')],
              'Antenna':[('MaxAntenna','max'),('FirstAntenna','first'),('LastAntenna','last'),'idxmin','idxmax'],
              'Configuration':[('Configuration','first')],'Category':[('Category','first')],'Trial':[('Trial','first')]}       
    
    duration=df.groupby(['Tag','Presence']).agg(aggformula)
    duration=duration.reset_index()
    duration.columns = ['Tag','Presence','Category','AttemptStart','AttemptStop',
                   'Configuration','MaxAntenna','FirstAntenna',
                             'LastAntenna','idxmin','idxmax','Trial']
    duration['Duration']=86400*(duration.AttemptStop-duration.AttemptStart)
    
    """
    Calculate time to Dmax:
    """
    TDmax=pd.concat([df.loc[duration['idxmin']],df.loc[duration['idxmax']]])
    TDmax=TDmax[['Tag','Presence','MSTime','Category','Flow','Trial','Date','TrialStart','TrialStop','TStartAttemptRate']]
    TDmax=TDmax.reset_index(drop=True)
    TDmax['TDmax']=TDmax.groupby(['Tag','Presence'])['MSTime'].diff()*86400
    TDmax=TDmax[pd.notnull(TDmax['TDmax'])]
    TDmax=TDmax[['Tag','Presence','MSTime','TDmax','Flow','Date','TrialStart','TrialStop','TStartAttemptRate']]
    
    df = pd.merge(duration, TDmax, on=['Tag','Presence']).drop(['idxmin','idxmax'],1)
    
    df['TrialAttempt'] = df.groupby(['Tag','Trial']).cumcount()+1 
    df['DayAttempt'] = df.groupby(['Tag','Date']).cumcount()+1
    df['Event']=1
    
    """
    Add event free intervals at end of trials
    """
    idxEventFree = df.groupby(['Tag','Trial'])['TrialAttempt'].transform(max) == df['TrialAttempt']
    EventFree=df[idxEventFree]                                                      
    EventFree=EventFree[EventFree['Category'].isin([0])]
    EventFree['Event']=0
    EventFree['TrialAttempt'] = EventFree.TrialAttempt+1
    EventFree[EventFree.columns.difference(['Tag','Trial','Category','Date',
                                            'TrialStart','TrialStop','TStartAttemptRate','Configuration',
                                            'Event',
                                            'Configuration','Flow'])]=np.nan #remove untrue data
    df = pd.concat([df,EventFree])    
    
    """
    Add event free intervals at end of trials
    """
    df=df.sort_values(['Tag','Trial','TrialAttempt'])
    df['stop_shifted'] = df.groupby(['Tag','Date'])['AttemptStop'].transform(lambda x:x.shift())
    
    #hacky way to change trial starts for case handling ... not sure if there is a way around it though
    df['TrialStart']=np.where((((df.Category == 3)|(df.Category == 7)|(df.Category == 6))), df['TStartAttemptRate'],df['TrialStart'])
    df['startCond1']=(np.where(df.TrialAttempt != 1, df['stop_shifted'], 
      np.where(((df.TrialAttempt==1)&(df.Category.shift()==6)), df['stop_shifted'], 
               df['TrialStart']))-df['TrialStart'])*86400/60 
    
    df['stopCond1']=(df['AttemptStart']-df['TrialStart'])*86400/60
    df['stopCond1']=(np.where(df.stopCond1.isnull(), (df['TrialStop']-df['TrialStart'])*86400/60, df['stopCond1']))
    
    return df

def populateFishMetaData(df,TagsInTank,Tags,Trial,AntennaSpec):
    

    
    #df=pd.merge(df,AntennaSpec, how='left', on=['MaxAntenna'])
    return df