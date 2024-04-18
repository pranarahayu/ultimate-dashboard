import sys

sys.path.append("xgmodel.py")
import xgmodel
from xgmodel import calculate_xG
from xgmodel import xgfix

import os
import pandas as pd
import glob
from datetime import date
import numpy as np
from sklearn import preprocessing

def assign_xg(data):
  df_match = data.copy()

  #Filtering Data
  df_match = df_match[['Team','Act Name','Action', 'Min', 'Sub 1', 'Sub 2', 'Sub 3', 'Sub 4', 'GW', 'X', 'Y', 'X2', 'Y2']]
  df_match = df_match[(df_match['Action']=='shoot on target') | (df_match['Action']=='shoot off target') | (df_match['Action']=='shoot blocked') | (df_match['Action']=='goal') | (df_match['Action']=='penalty goal') | (df_match['Action']=='penalty missed')]
  df_match = df_match.reset_index()
  df_match = df_match.sort_values(by=['index'], ascending=False)

  #Cleaning Data
  shots = df_match.copy()
  #shots['Min'] = shots['Min'].str.split(' :').str[0]
  shots['Mins'] = shots['Min']
  shots['Mins'] = shots['Mins'].astype(float)
  shots = shots[shots['X'].notna()]

  data = shots[['Act Name', 'Team', 'Action', 'Mins', 'Sub 1', 'Sub 2', 'Sub 3', 'Sub 4', 'X', 'Y', 'X2', 'Y2']]
  data.loc[(data['Action'].str.contains('penalty goal')), 'Sub 3'] = 'Penalty'
  data.loc[(data['Action'].str.contains('penalty goal')), 'Sub 1'] = 'Right Foot'
  data.loc[(data['Action'].str.contains('penalty missed')), 'Sub 3'] = 'Penalty'
  data.loc[(data['Action'].str.contains('penalty missed')), 'Sub 2'] = 'Right Foot'
  data.loc[(data['Action'].str.contains('penalty')), 'X'] = 90
  data.loc[(data['Action'].str.contains('penalty')), 'Y'] = 50
  data.loc[(data['Action'].str.contains('penalty missed')) & ((data['Sub 1'].str.contains('Saved')) | (data['Sub 1'].str.contains('Cleared'))), 'Action'] = 'shoot on target'

  data['Action'] = data['Action'].replace(['shoot on target','shoot off target','shoot blocked','goal','penalty goal','penalty missed'],
                                        ['Shot On','Shot Off','Shot Blocked','Goal','Goal','Shot Off'])
  dft = data.groupby('Action', as_index=False)
  temp = pd.DataFrame(columns = ['Player', 'Team','Event','Mins',
                                 'Shot Type','Situation','X','Y', 'X2', 'Y2'])
  if (('Goal' in data['Action'].unique()) == True):
    df1 = dft.get_group('Goal')
    df1f = df1[['Act Name', 'Team', 'Action', 'Mins', 'Sub 1', 'Sub 3', 'X', 'Y', 'X2', 'Y2']]
    df1f.rename(columns = {'Action':'Event', 'Sub 1':'Shot Type', 'Sub 3':'Situation', 'Act Name':'Player'}, inplace = True)
  else:
    df1f = temp.copy()

  if (('Shot On' in data['Action'].unique()) == True):
    df2 = dft.get_group('Shot On')
    df2f = df2[['Act Name','Team', 'Action', 'Mins', 'Sub 2', 'Sub 3', 'X', 'Y', 'X2', 'Y2']]
    df2f.rename(columns = {'Action':'Event', 'Sub 2':'Shot Type', 'Sub 3':'Situation', 'Act Name':'Player'}, inplace = True)
  else:
    df2f = temp.copy()

  if (('Shot Off' in data['Action'].unique()) == True):
    df3 = dft.get_group('Shot Off')
    if (('Penalty' in df3['Sub 3'].unique()) == True):
      df3f = df3[['Act Name','Team', 'Action', 'Mins', 'Sub 2', 'Sub 3', 'X', 'Y', 'X2', 'Y2']]
      df3f.rename(columns = {'Action':'Event', 'Sub 2':'Shot Type', 'Sub 3':'Situation', 'Act Name':'Player'}, inplace = True)
    else:
      df3f = df3[['Act Name','Team', 'Action', 'Mins', 'Sub 3', 'Sub 4', 'X', 'Y', 'X2', 'Y2']]
      df3f.rename(columns = {'Action':'Event', 'Sub 3':'Shot Type', 'Sub 4':'Situation', 'Act Name':'Player'}, inplace = True)
  else:
    df3f = temp.copy()

  if (('Shot Blocked' in data['Action'].unique()) == True):
    df4 = dft.get_group('Shot Blocked')
    df4f = df4[['Act Name','Team', 'Action', 'Mins', 'Sub 2', 'Sub 3', 'X', 'Y', 'X2', 'Y2']]
    df4f.rename(columns = {'Action':'Event', 'Sub 2':'Shot Type', 'Sub 3':'Situation', 'Act Name':'Player'}, inplace = True)
  else:
    df4f = temp.copy()

  sa = pd.concat([df1f, df2f, df3f, df4f])
  #sa = sa.dropna()
  sa.loc[(sa['Situation'].str.contains('Open play')), 'Situation'] = 'Open Play'
  sa.loc[(sa['Situation'].str.contains('Freekick')), 'Situation'] = 'Set-Piece Free Kick'
  sa.loc[(sa['Shot Type'].str.contains('Header')), 'Shot Type'] = 'Head'

  df_co = sa.sort_values(by=['Mins'], ascending=False)
  df_co['x'] = 100-df_co['X']
  df_co['y'] = df_co['Y']
  df_co['c'] = abs(df_co['Y']-50)

  x=df_co['x']*1.05
  y=df_co['c']*0.68

  df_co['X3']=(100-df_co['X'])*1.05
  df_co['Y3']=df_co['Y']*0.68

  df_co['Distance'] = np.sqrt(x**2 + y**2)
  c=7.32
  a=np.sqrt((y-7.32/2)**2 + x**2)
  b=np.sqrt((y+7.32/2)**2 + x**2)
  k = (c**2-a**2-b**2)/(-2*a*b)
  gamma = np.arccos(k)
  if gamma.size<0:
    gamma = np.pi + gamma
  df_co['Angle Rad'] = gamma
  df_co['Angle Degrees'] = gamma*180/np.pi

  def wasitgoal(row):
    if row['Event'] == 'Goal':
      return 1
    else:
      return 0
  df_co['goal'] = df_co.apply(lambda row: wasitgoal(row), axis=1)

  df_co = df_co.sort_values(by=['Mins'])
  df_co = df_co.reset_index()
  shotdata = df_co[['Player','Team','Event','Mins','Shot Type','Situation','X3','Y3','Distance','Angle Rad','Angle Degrees','goal']]

  shots = shotdata.dropna()
  shots.rename(columns = {'Player':'player', 'Event':'event', 'Mins':'mins', 'Shot Type':'shottype',
                          'Situation':'situation','X3':'X','Y3':'Y', 'Distance':'distance',
                          'Angle Rad':'anglerad','Angle Degrees':'angledeg'}, inplace = True)

  body_part_list=[]
  for index, rows in shots.iterrows():
      if (rows['shottype']=='Right Foot') or (rows['shottype']=='Left Foot'):
          body_part_list.append('Foot')
      elif (rows['shottype']=='Head'):
          body_part_list.append('Head')
      else:
          body_part_list.append('Head')

  shots['body_part']=body_part_list

  shots=shots[shots.body_part != 'Other']
  shots=shots.sort_values(by=['mins'])
  shots.loc[(shots['situation'].str.contains('Set')), 'situation'] = 'Indirect'
  shots.loc[(shots['situation'].str.contains('Corner')), 'situation'] = 'Indirect'
  shots.loc[(shots['situation'].str.contains('Throw')), 'situation'] = 'Open Play'
  shots.loc[(shots['situation'].str.contains('Counter')), 'situation'] = 'Open Play'
  dfxg = shots[['distance', 'angledeg', 'body_part', 'situation', 'goal']]

  #Assign numerical value to body part and situation
  label_encoder = preprocessing.LabelEncoder()
  label_encoder.fit(dfxg["body_part"])
  dfxg['body_part_num'] = label_encoder.transform(dfxg["body_part"])

  label_encoder = preprocessing.LabelEncoder()
  label_encoder.fit(dfxg["situation"])
  dfxg['situation_num'] = label_encoder.transform(dfxg["situation"])

  #assigning xG
  xG=dfxg.apply(calculate_xG, axis=1)
  dfxg = dfxg.assign(xG=xG)
  dfxg['xG'] = dfxg.apply(lambda row: xgfix(row), axis=1)

  fixdata = df_co[['Player', 'Team', 'Event', 'Mins', 'X', 'Y', 'X2', 'Y2']]
  fixdata['xG'] = dfxg['xG']

  return fixdata
