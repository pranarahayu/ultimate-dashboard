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

posdict = {'gk':{'position':'Goalkeeper',
                 'metrics':['Name','Long Goal Kick Ratio','Pass Accuracy','Cross Claim',
                            'Keeper - Sweeper','Saves','Save Ratio','Penalty Save']},
           'cb':{'position':'Center Back',
                 'metrics':['Name','Shots','Goals','Assist','Pass Accuracy',
                            'Tackle','Intercept','Recovery','Blocks','Aerial Won Ratio']},
           'fb':{'position':'Fullback',
                 'metrics':['Name','Shots','Goals','Create Chance','Assist','Pass Accuracy','Dribble',
                            'Cross','Tackle','Intercept','Recovery','Blocks','Aerial Won Ratio']},
           'cm':{'position':'Midfielder',
                 'metrics':['Name','Shots','Goals','Create Chance','Shot on Target Ratio','Assist',
                            'Pass Accuracy','Dribble','Tackle','Intercept','Recovery','Blocks']},
           'cam/w':{'position':'Attacking 10/Winger',
                    'metrics':['Name','Shots','Goals','Create Chance','Shot on Target Ratio',
                               'Conversion Ratio','Assist','Pass Accuracy','Dribble','Cross',
                               'Tackle','Intercept','Recovery']},
           'fw':{'position':'Forward',
                 'metrics':['Name','Shots','Goals','Create Chance','Shot on Target Ratio',
                            'Conversion Ratio','Assist','Pass Accuracy','Dribble','Tackle',
                            'Intercept','Recovery','Aerial Won Ratio']}}

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

def add_og(data):
  df = data.copy()
  dfog = df[['Match', 'Team', 'Opponent', 'Own Goal']]
  dfog = dfog.groupby(['Match', 'Team', 'Opponent'], as_index=False).sum()
  dfog['Team'] = dfog['Opponent']
  dfog['Goal - Own Goal'] = dfog['Own Goal']
  df_clean = dfog[['Team', 'Goal - Own Goal']]
  df_clean = df_clean.groupby('Team', as_index=False).sum()
  return df_clean

def add_conc(data):
  df = data.copy()
  conc = df[['Opponent','Goal','Penalty Goal','Shot on','Shot off','Shot Blocked']]
  conc['Goals Conceded'] = conc['Goal']+conc['Penalty Goal']
  conc['Shots Allowed'] = conc['Shot on']+conc['Shot off']+conc['Shot Blocked']
  conc = conc[['Opponent','Goals Conceded','Shots Allowed']].rename(columns={'Opponent':'Team'})
  df_clean1 = conc.groupby('Team', as_index=False).sum()

  dfog = df[['Team','Own Goal']]
  df_clean2 = dfog.groupby('Team', as_index=False).sum()

  df_clean = pd.merge(df_clean1, df_clean2, on='Team', how='left')
  df_clean['Goals Conceded'] = df_clean['Goals Conceded']+df_clean['Own Goal']
  df_clean = df_clean[['Team','Goals Conceded','Shots Allowed']]

  return df_clean

def data_team(data, komp, month, gw, venue, cat):
  df = data.copy()
  df_og = data.copy()
  gw_list = gw
  vn_list = venue
  mn_list = month

  from datetime import date
  df['Date'] = pd.to_datetime(df.Date)
  df['Month'] = df['Date'].dt.strftime('%B')

  df = df[df['Kompetisi']==komp]
  df = df[df['Home/Away'].isin(vn_list)]
  df = df[df['Gameweek'].isin(gw_list)]
  df = df[df['Month'].isin(mn_list)]

  dfog = add_og(df)
  dfconc = add_conc(df)

  df['Shots'] = df['Shot on']+df['Shot off']+df['Shot Blocked']
  df['Goals'] = df['Penalty Goal']+df['Goal']
  df['Penalties Awarded'] = df['Penalty Goal']+df['Penalty Missed']
  df['Shots - Inside Box'] = df['Shot on - Inside Box']+df['Shot off - Inside Box']+df['Shot Blocked - Inside Box']
  df['Shots - Outside Box'] = df['Shot on - Outside Box']+df['Shot off - Outside Box']+df['Shot Blocked - Outside Box']
  df['Goals - Inside Box'] = df['Penalty Goal']+df['Goal - Inside Box']
  df['Goals - Open Play'] = df['Goal - Open Play']+df['Goal - Counter Attack']
  df['Goals - Set Pieces'] = df['Goal - Set-Piece Free Kick']+df['Goal - Throw in']+df['Goal - Corner Kick']
  df['Total Pass'] = df['Pass']+df['Pass Fail']
  df['Chances Created'] = df['Key Pass']+df['Assist']
  df['Crosses'] = df['Cross']+df['Cross Fail']
  df['Dribbles'] = df['Dribble']+df['Dribble Fail']
  df['Tackles'] = df['Tackle']+df['Tackle Fail']
  df['Defensive Actions'] = df['Tackles']+df['Intercept']+df['Clearance']+df['Recovery']
  df['Saves'] = df['Save']+df['Penalty Save']
  df['Blocks'] = df['Block']+df['Block Cross']
  df['Aerial Duels'] = df['Aerial Won']+df['Aerial Lost']
  df['Errors'] = df['Error Goal - Error Led to Chance'] + df['Error Goal - Error Led to Goal']

  df = df[['Team', 'Shots', 'Shot on', 'Shot off', 'Shot Blocked',
           'Shots - Inside Box', 'Shots - Outside Box',
           'Goals', 'Penalties Awarded', 'Penalty Goal',
           'Goals - Inside Box', 'Goal - Outside Box', 'Goals - Open Play',
           'Goals - Set Pieces', 'Goal - Corner Kick', 'Total Pass', 'Pass',
           'Chances Created', 'Crosses', 'Cross', 'Dribbles', 'Dribble',
           'Tackles', 'Intercept', 'Clearance', 'Recovery', 'Defensive Actions',
           'Blocks', 'Aerial Duels', 'Aerial Won', 'Saves',
           'Errors', 'Error Goal - Error Led to Chance', 'Error Goal - Error Led to Goal',
           'Own Goal', 'Foul', 'Yellow Card', 'Red Card', 'Offside', 'Goal Kick - Goal Kick Launch',
           'Goal Kick - No Sub-action', 'Goal Kick', 'Pass - Long Ball', 'Assist']]
  df = df.groupby('Team', as_index=False).sum()
  df['Conversion Ratio'] = round(df['Goals']/df['Shots'],2)
  df['Shot on Target Ratio'] = round(df['Shot on']/df['Shots'],2)
  df['Successful Cross Ratio'] = round(df['Cross']/df['Crosses'],2)
  df['Pass per Shot'] = round(df['Total Pass']/df['Shots'],2)
  df['Pass Accuracy'] = round(df['Pass']/df['Total Pass'],2)
  df['Aerial Won Ratio'] = round(df['Aerial Won']/df['Aerial Duels'],2)
  df['Goal Kick Grounded Ratio'] = round(df['Goal Kick - No Sub-action']/df['Goal Kick'],2)
  df['Long Ball Ratio'] = round(df['Pass - Long Ball']/df['Pass'],2)

  df1 = pd.merge(df, dfog, on='Team', how='left')
  df2 = pd.merge(df1, dfconc, on='Team', how='left')
  df2['Goals'] = df2['Goals'] + df2['Goal - Own Goal']

  df2 = df2[['Team', 'Shots', 'Shot on', 'Shot off', 'Shot Blocked', 'Shot on Target Ratio',
             'Shots - Inside Box', 'Shots - Outside Box', 'Goals', 'Penalties Awarded', 'Penalty Goal',
             'Goals - Inside Box', 'Goal - Outside Box', 'Goals - Open Play', 'Goals - Set Pieces',
             'Goal - Corner Kick', 'Goal - Own Goal', 'Total Pass', 'Pass', 'Pass Accuracy',
             'Chances Created', 'Pass per Shot', 'Crosses', 'Cross', 'Successful Cross Ratio',
             'Dribbles', 'Dribble', 'Tackles', 'Intercept', 'Clearance', 'Recovery', 'Defensive Actions',
             'Blocks', 'Aerial Duels', 'Aerial Won', 'Aerial Won Ratio', 'Saves', 'Goals Conceded', 'Shots Allowed',
             'Errors', 'Error Goal - Error Led to Chance', 'Error Goal - Error Led to Goal',
             'Own Goal', 'Foul', 'Yellow Card', 'Red Card', 'Offside', 'Goal Kick Grounded Ratio', 'Long Ball Ratio',
             'Goal Kick - Goal Kick Launch', 'Goal Kick - No Sub-action', 'Assist']]

  gt = ['Team', 'Shots', 'Shot on', 'Shot off', 'Shot Blocked', 'Shot on Target Ratio', 'Shots - Inside Box',
        'Shots - Outside Box', 'Goals', 'Penalties Awarded', 'Penalty Goal', 'Goals - Inside Box', 'Goal - Outside Box',
        'Goals - Open Play', 'Goals - Set Pieces', 'Goal - Corner Kick', 'Goal - Own Goal', 'Assist']
  
  ip = ['Team', 'Total Pass', 'Pass', 'Pass Accuracy', 'Chances Created',
        'Pass per Shot', 'Crosses', 'Cross', 'Successful Cross Ratio', 'Dribbles', 'Dribble']
  
  op = ['Team', 'Tackles', 'Intercept', 'Clearance', 'Recovery', 'Defensive Actions',
        'Blocks', 'Aerial Duels', 'Aerial Won', 'Aerial Won Ratio', 'Saves',
        'Goals Conceded', 'Shots Allowed']
  
  misc = ['Team', 'Errors', 'Error Goal - Error Led to Chance', 'Error Goal - Error Led to Goal',
          'Own Goal', 'Foul', 'Yellow Card', 'Red Card', 'Offside', 'Goal Kick Grounded Ratio',
          'Goal Kick - Goal Kick Launch', 'Goal Kick - No Sub-action']
  
  if (cat == 'Goal Threat'):
    df2 = df2[gt]
  elif (cat == 'in Possession'):
    df2 = df2[ip]
  elif (cat == 'out of Possession'):
    df2 = df2[op]
  else:
    df2 = df2[misc]

  return df2

def get_list(data):
  df = data.copy()
  df['Shots'] = df['Shot on']+df['Shot off']+df['Shot Blocked']
  df['Goals'] = df['Penalty Goal']+df['Goal']
  df['Goals Cont.'] = df['Goals']+df['Assist']
  df['Penalties Given'] = df['Penalty Goal']+df['Penalty Missed']
  df['Shots - Inside Box'] = df['Shot on - Inside Box']+df['Shot off - Inside Box']+df['Shot Blocked - Inside Box']
  df['Shots - Outside Box'] = df['Shot on - Outside Box']+df['Shot off - Outside Box']+df['Shot Blocked - Outside Box']
  df['Goals - Inside Box'] = df['Penalty Goal']+df['Goal - Inside Box']
  df['Goals - Open Play'] = df['Goal - Open Play']+df['Goal - Counter Attack']
  df['Goals - Set Pieces'] = df['Goal - Set-Piece Free Kick']+df['Goal - Throw in']+df['Goal - Corner Kick']
  df['Total Pass'] = df['Pass']+df['Pass Fail']
  df['Chances Created'] = df['Key Pass']+df['Assist']
  df['Crosses'] = df['Cross']+df['Cross Fail']
  df['Dribbles'] = df['Dribble']+df['Dribble Fail']
  df['Tackles'] = df['Tackle']+df['Tackle Fail']
  df['Defensive Actions'] = df['Tackles']+df['Intercept']+df['Clearance']+df['Recovery']
  df['Saves'] = df['Save']+df['Penalty Save']
  df['Blocks'] = df['Block']+df['Block Cross']
  df['Aerial Duels'] = df['Aerial Won']+df['Aerial Lost']
  df['Errors'] = df['Error Goal - Error Led to Chance'] + df['Error Goal - Error Led to Goal']

  jatuh = ['No','Player ID','Team ID','Position (in match)','Gameweek','Opponent','Match','Home/Away','Venue',
           'Date','Result','Starter/Subs','Subs','Player Rating','Ball Possession','Pass Team','Kick In','Unnamed: 296','DoB',
           'Unnamed: 297','Unnamed: 298','Unnamed: 299','Unnamed: 300','Unnamed: 301','Unnamed: 302','Unnamed: 303',
           'Fantasy Assist','Fantasy Assist - Penalty','Fantasy Assist - Free kick','Fantasy Assist - Goal by rebound',
           'Fantasy Assist - Own goal by pass/cross','Fantasy Assist - Own goal by rebound','Unnamed: 310','Kompetisi','Nickname',
           'DoB','Nat. Status','Age Group']

  df = df.drop(jatuh, axis=1)
  df['Conversion Ratio'] = round(df['Goals']/df['Shots'],2)
  df['Shot on Target Ratio'] = round(df['Shot on']/df['Shots'],2)
  df['Successful Cross Ratio'] = round(df['Cross']/df['Crosses'],2)
  df['Pass per Shot'] = round(df['Total Pass']/df['Shots'],2)
  df['Pass Accuracy'] = round(df['Pass']/df['Total Pass'],2)
  df['Aerial Won Ratio'] = round(df['Aerial Won']/df['Aerial Duels'],2)
  df['Goal Kick Grounded Ratio'] = round(df['Goal Kick - No Sub-action']/df['Goal Kick'],2)
  df['Long Ball Ratio'] = round(df['Pass - Long Ball']/df['Pass'],2)

  metrik = list(df)
  return metrik

def get_detail(data):
  db = data.copy()
  import datetime as dt
  from datetime import date

  today = date.today()
  db['Age'] = db['DoB'].apply(lambda x: today.year - x.year - ((today.month, today.day) < (x.month, x.day)))

  #adding age group based on the player's age
  def age_group(row):
    if row['DoB'] < dt.datetime(2000,1,1):
      return 'Senior'
    else:
      return 'U23'
  db['Age Group'] = db.apply(lambda row: age_group(row), axis=1)

  #adding nationality status
  def status(row):
    if row['Nationality'] == 'Indonesia':
      return 'Local'
    elif row['Nationality'] != 'Indonesia':
      return 'Foreign'

  db['Nat. Status'] = db.apply(lambda row: status(row), axis=1)

  return db

def data_player(data, komp, team, pos, month, venue, gw, age, nat, metrik, mins, cat, data2):
  df = data.copy()
  db = data2.copy()
  gw_list = gw
  vn_list = venue
  mn_list = month
  ag_list = age
  nt_list = nat
  ps_list = pos
  mt_list = metrik
  tm_list = team

  df = df[df['Kompetisi']==komp]
  df = df[df['Team'].isin(tm_list)]
  df = df[df['Home/Away'].isin(vn_list)]
  df = df[df['Gameweek'].isin(gw_list)]
  df = df[df['Month'].isin(mn_list)]
  df = df[df['Age Group'].isin(ag_list)]
  df = df[df['Position'].isin(ps_list)]
  df = df[df['Nat. Status'].isin(nt_list)]

  df['Shots'] = df['Shot on']+df['Shot off']+df['Shot Blocked']
  df['Goals'] = df['Penalty Goal']+df['Goal']
  df['Goals Cont.'] = df['Goals']+df['Assist']
  df['Penalties Given'] = df['Penalty Goal']+df['Penalty Missed']
  df['Shots - Inside Box'] = df['Shot on - Inside Box']+df['Shot off - Inside Box']+df['Shot Blocked - Inside Box']
  df['Shots - Outside Box'] = df['Shot on - Outside Box']+df['Shot off - Outside Box']+df['Shot Blocked - Outside Box']
  df['Goals - Inside Box'] = df['Penalty Goal']+df['Goal - Inside Box']
  df['Goals - Open Play'] = df['Goal - Open Play']+df['Goal - Counter Attack']
  df['Goals - Set Pieces'] = df['Goal - Set-Piece Free Kick']+df['Goal - Throw in']+df['Goal - Corner Kick']
  df['Total Pass'] = df['Pass']+df['Pass Fail']
  df['Chances Created'] = df['Key Pass']+df['Assist']
  df['Crosses'] = df['Cross']+df['Cross Fail']
  df['Dribbles'] = df['Dribble']+df['Dribble Fail']
  df['Tackles'] = df['Tackle']+df['Tackle Fail']
  df['Defensive Actions'] = df['Tackles']+df['Intercept']+df['Clearance']+df['Recovery']
  df['Saves'] = df['Save']+df['Penalty Save']
  df['Blocks'] = df['Block']+df['Block Cross']
  df['Aerial Duels'] = df['Aerial Won']+df['Aerial Lost']
  df['Errors'] = df['Error Goal - Error Led to Chance'] + df['Error Goal - Error Led to Goal']

  jatuh = ['No','Team ID','Player ID','Position (in match)','Gameweek','Opponent','Match','Home/Away','Venue',
           'Date','Result','Starter/Subs','Subs','Player Rating','Ball Possession','Pass Team','Kick In','Unnamed: 296',
           'Unnamed: 297','Unnamed: 298','Unnamed: 299','Unnamed: 300','Unnamed: 301','Unnamed: 302','Unnamed: 303',
           'Fantasy Assist','Fantasy Assist - Penalty','Fantasy Assist - Free kick','Fantasy Assist - Goal by rebound',
           'Fantasy Assist - Own goal by pass/cross','Fantasy Assist - Own goal by rebound','Unnamed: 310','Kompetisi',
           'Month','Nickname','DoB','Position','Nationality','Nat. Status','Age Group','Age']

  df = df.drop(jatuh, axis=1)
  df = df.groupby(['Name','Team'], as_index=False).sum()
  df['Conversion Ratio'] = round(df['Goals']/df['Shots'],2)
  df['Shot on Target Ratio'] = round(df['Shot on']/df['Shots'],2)
  df['Successful Cross Ratio'] = round(df['Cross']/df['Crosses'],2)
  df['Pass per Shot'] = round(df['Total Pass']/df['Shots'],2)
  df['Pass Accuracy'] = round(df['Pass']/df['Total Pass'],2)
  df['Aerial Won Ratio'] = round(df['Aerial Won']/df['Aerial Duels'],2)
  df['Goal Kick Grounded Ratio'] = round(df['Goal Kick - No Sub-action']/df['Goal Kick'],2)
  df['Long Ball Ratio'] = round(df['Pass - Long Ball']/df['Pass'],2)

  temp = db[['Name', 'Age', 'Position', 'Nationality']]
  dfx = pd.merge(df, temp, on='Name', how='left')
  datafull = dfx[dfx['MoP'] >= mins].reset_index(drop=True)
  datafull = datafull[mt_list]

  def p90_Calculator(variable_value):
    p90_value = round((((variable_value/df['MoP']))*90),2)
    return p90_value
    
  temp2 = df.drop(['Name', 'Team'], axis=1)
  p90 = temp2.apply(p90_Calculator)
  p90['Name'] = df['Name']
  p90['Team'] = df['Team']
  p90['MoP'] = df['MoP']
  p90['Conversion Ratio'] = df['Conversion Ratio']
  p90['Shot on Target Ratio'] = df['Shot on Target Ratio']
  p90['Successful Cross Ratio'] = df['Successful Cross Ratio']
  p90['Pass per Shot'] = df['Pass per Shot']
  p90['Pass Accuracy'] = df['Pass Accuracy']
  p90['Aerial Won Ratio'] = df['Aerial Won Ratio']
  p90['Goal Kick Grounded Ratio'] = df['Goal Kick Grounded Ratio']
  p90['Long Ball Ratio'] = df['Long Ball Ratio']

  p902 = pd.merge(p90, temp, on='Name', how='left')
  data90 = p902[p902['MoP'] >= mins].reset_index(drop=True)
  data90 = data90[mt_list]

  if (cat=='per 90'):
    return data90
  elif (cat=='Total'):
    return datafull
