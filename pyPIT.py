# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 14:22:05 2017

@author: Jason
"""

# -*- coding: utf-8 -*-
import numpy as np
import PITfunctions as fn
import pandas as pd

lagThreshold = 40 #seconds
export="Video"
IncludeFinalAttempt="Yes"
df=fn.importTIRIS()

Tags,Trial,BetweenTrials,CameraStartTimes,StartEndOfDayTimes,TagsInTank,NumberTags,AntennaSpec=fn.importMetadata(export)
df=fn.includeLags(df)
df=fn.includeMetadata(df,Trial)
df=fn.handleFalsePositives(df,lagThreshold)

Lags,df = fn.includePresences(df,lagThreshold)
df=fn.handleExceptions(df,export)

df=fn.includeAttemptData(df)

df=df[['Tag','Presence','Category','Trial','TrialAttempt','DayAttempt','Event','startCond1','stopCond1','AttemptStart','AttemptStop']]

#include fish present in trial but not staging an attempt, right join includes  from TagsInTag that do not
df=df.merge(TagsInTank, how='outer', on=['Tag','Trial'], indicator=True)
df=df.merge(Trial,on=['Trial'])
df=df.sort(['Tag','Trial'])


noAttempt=df[df['_merge'] == 'right_only']
df=df[df['_merge']!='right_only']
   
noAttempt['startCond1']=(noAttempt['TrialStart']-noAttempt['TrialStart'])*86400/60
noAttempt['stopCond1']=(noAttempt['TrialStop']-noAttempt['TrialStart'])*86400/60
noAttempt['Event']=0

df=pd.concat([df,noAttempt])
df=df.sort(['Tag','Trial'])
df=df.merge(Tags,on='Tag')
df['HoldingTime']=df.TrialStart-df.CaptureDate
df=df[['Tag','Presence','Category','Trial','Configuration','Flow','Temp','HoldingTime','Species','FL','TrialAttempt','DayAttempt','AttemptStart','AttemptStop','Event','startCond1','stopCond1']]

df['startCond2']=0
df['stopCond2']=df['stopCond1']-df['startCond1']



### manual finishing touches before export
if export == "Dmax":
    dfDmax=df.loc[df.groupby(['Tag','Trial Index'])["MaxAntenna"].idxmax()] #isolates largest Dmax for each individual within each trial
    dfDmax=fn.populateFishMetaData(dfDmax,TagsInTank,Tags,Trial,AntennaSpec)
    dfDmax=dfDmax[pd.notnull(dfDmax.Category)]
    dfDmax = dfDmax[(dfDmax.Species == 'R') | (dfDmax.Species == 'K') ]
    dfDmax.to_excel('../Dmax/Dmax.xlsx') #export treated data

if export == "AttemptRate":
    dfAR=df
    #dfAR=fn.populateFishMetaData(dfAR,TagsInTank,Tags,Trial,AntennaSpec)
    #dfAR['dt']=np.where(dfAR['dt'].isnull(),10800,dfAR['dt'])#fills in nan for dt with 3 hours and a bit, censoring of 
    #dfAR['TrialAttemptNumber']=np.where(dfAR['TrialAttemptNumber'].isnull(),0,dfAR['TrialAttemptNumber'])
    dfAR = dfAR[(dfAR.Species == 'R') | (dfAR.Species == 'K') ]
    dfAR.to_excel('../Attempt_rate/AttemptRate.xlsx')

if export == "Video":
    dfVP = df[(df.Category == 0)]
    dfVP = dfVP[(dfVP.Presence.notnull())]
    dfVP = dfVP[['Tag','AttemptStart','AttemptStop','Trial','TrialAttempt','MaxAntenna','Configuration','Duration']]
    dfVP = dfVP.merge(CameraStartTimes, on="Trial")
    
    dfVP['startFrame'] = (dfVP.AttemptStart - dfVP['VideoStartTime'])*86400
    dfVP['endFrame'] = (dfVP.AttemptStop - dfVP['VideoStartTime'])*86400    
    dfVP=  dfVP.round({'startFrame': 0, 'endFrame': 0})
    dfVP = dfVP[(dfVP.startFrame > 0) & (dfVP.Duration > 0) & ((dfVP.Configuration == 0)|(dfVP.Configuration == 212)|(dfVP.Configuration == 333))]
    dfVP.to_excel('../CutVideo/video_extraction_Times.xlsx')
    
        




