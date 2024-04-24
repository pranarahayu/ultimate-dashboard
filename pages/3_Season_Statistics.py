import sys
import io
import streamlit as st
import pandas as pd
import numpy as np
from tempfile import NamedTemporaryFile
import urllib

from listfungsi import data_team
from listfungsi import data_player
from listfungsi import get_list
from listfungsi import get_detail
from listfungsi import get_cs
from listfungsi import milestone
from menu import menu

st.set_page_config(page_title='Full Season Statistics', layout='wide')
st.markdown('# Statistics')

menu()

@st.cache_data(ttl=600)
def load_data(sheets_url):
    xlsx_url = sheets_url.replace("/edit#gid=", "/export?format=xlsx&gid=")
    return pd.read_excel(xlsx_url)

df1 = load_data(st.secrets["datateam"])
df2 = load_data(st.secrets["datapemain"])
histdata = load_data(st.secrets["hist"])

from datetime import date
df1['Date'] = pd.to_datetime(df1.Date)
df1['Month'] = df1['Date'].dt.strftime('%B')
df22 = get_detail(df2)
df = pd.merge(df1, df2.drop(['Name'], axis=1), on='Player ID', how='left')
fulldata = get_detail(df)
mlist = get_list(fulldata)
no_temp = df1[df1['Kompetisi']=='Liga 1']
histodata = milestone(histdata, no_temp)
csdata = get_cs(no_temp)
curdata = df1[['Team','Assist','Yellow Card','Red Card']]
curdata = curdata.groupby(['Team'], as_index=False).sum()
curdata2 = pd.merge(curdata, csdata, on='Team', how='left')

from datetime import date
date = date.today().strftime("%Y-%m-%d")

comps, teams, players = st.tabs(['Milestones', 'Team Stats', 'Player Stats'])

with comps:
    col1, col2 = st.columns(2)
    with col1:
        season = st.selectbox('Select Season(s)',['All Season', 'This Season'], key='98')
    with col2:
        if (season == 'All Season'):
            team = st.selectbox('Select Team', pd.unique(histdata['Team']), key='99')
        else:
            team = st.selectbox('Select Team', pd.unique(no_temp['Team']), key='97')
        all_teams = st.checkbox('Select All Teams', key='300')
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    if all_teams:
        if (season == 'All Season'):
            with col1:
                st.metric(label="Goals", value=histodata['Goal'].sum())
            with col2:
                st.metric(label="Assists", value=histodata['Assist'].sum())
            with col3:
                st.metric(label="Yellow Cards", value=histodata['Yellow Card'].sum())
            with col4:
                st.metric(label="Red Cards", value=histodata['Red Card'].sum())
            with col5:
                st.metric(label="Concededs", value=histodata['Conceded'].sum())
            with col6:
                st.metric(label="Clean Sheets", value=histodata['Clean Sheet'].sum())
        else:
            with col1:
                st.metric(label="Goals", value=int(curdata2['Goal'].sum()))
            with col2:
                st.metric(label="Assists", value=curdata2['Assist'].sum())
            with col3:
                st.metric(label="Yellow Cards", value=curdata2['Yellow Card'].sum())
            with col4:
                st.metric(label="Red Cards", value=curdata2['Red Card'].sum())
            with col5:
                st.metric(label="Concededs", value=int(curdata2['Conceded'].sum()))
            with col6:
                st.metric(label="Clean Sheets", value=int(curdata2['Clean Sheet'].sum()))
    else:
        if (season == 'All Season'):
            with col1:
                st.metric(label="Goals", value=list((histodata[histodata['Team']==team]['Goal']).reset_index(drop=True))[0])
            with col2:
                st.metric(label="Assists", value=list((histodata[histodata['Team']==team]['Assist']).reset_index(drop=True))[0])
            with col3:
                st.metric(label="Yellow Cards", value=list((histodata[histodata['Team']==team]['Yellow Card']).reset_index(drop=True))[0])
            with col4:
                st.metric(label="Red Cards", value=list((histodata[histodata['Team']==team]['Red Card']).reset_index(drop=True))[0])
            with col5:
                st.metric(label="Concededs", value=list((histodata[histodata['Team']==team]['Conceded']).reset_index(drop=True))[0])
            with col6:
                st.metric(label="Clean Sheets", value=list((histodata[histodata['Team']==team]['Clean Sheet']).reset_index(drop=True))[0])
        else:
            with col1:
                st.metric(label="Goals", value=int(list((curdata2[curdata2['Team']==team]['Goal']).reset_index(drop=True))[0]))
            with col2:
                st.metric(label="Assists", value=list((curdata2[curdata2['Team']==team]['Assist']).reset_index(drop=True))[0])
            with col3:
                st.metric(label="Yellow Cards", value=list((curdata2[curdata2['Team']==team]['Yellow Card']).reset_index(drop=True))[0])
            with col4:
                st.metric(label="Red Cards", value=list((curdata2[curdata2['Team']==team]['Red Card']).reset_index(drop=True))[0])
            with col5:
                st.metric(label="Concededs", value=int(list((curdata2[curdata2['Team']==team]['Conceded']).reset_index(drop=True))[0]))
            with col6:
                st.metric(label="Clean Sheets", value=int(list((curdata2[curdata2['Team']==team]['Clean Sheet']).reset_index(drop=True))[0]))
    st.markdown('''<style>
    [data-testid="stMetricLabel"] > div:nth-child(1) {justify-content: center;}
    [data-testid="stMetricValue"] > div:nth-child(1) {justify-content: center;}
    [data-testid="stMetricLabel"] > div:nth-child(1) {justify-content: center;}
    [data-testid="stMetricValue"] > div:nth-child(1) {justify-content: center;}
    [data-testid="stMetricLabel"] > div:nth-child(1) {justify-content: center;}
    [data-testid="stMetricValue"] > div:nth-child(1) {justify-content: center;}
    </style>''', unsafe_allow_html=True)

with teams:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        komp = st.selectbox('Select Competition', ['Liga 1', 'Liga 2'], key='3')
    with col2:
        temp_full = fulldata[fulldata['Kompetisi']==komp]
        month = st.multiselect('Select Month', pd.unique(temp_full['Month']), key='14')
        all_mos = st.checkbox('Select All Months', key='301')
        if all_mos:
            month = pd.unique(temp_full['Month'])
    with col3:
        temp_full = temp_full[temp_full['Month'].isin(month)]
        venue = st.multiselect('Select Venue', pd.unique(temp_full['Home/Away']), key='5')
    with col4:
        temp_full = temp_full[temp_full['Home/Away'].isin(venue)]
        gw = st.multiselect('Select Gameweek', pd.unique(temp_full['Gameweek']), key='4')
        all_gws = st.checkbox('Select All GWs', key='302')
        if all_gws:
            gw = pd.unique(temp_full['Gameweek'])
    with col5:
        cat = st.selectbox('Select Category', ['Goal Threat', 'in Possession', 'out of Possession', 'Misc'], key='13')
    show_tim_data = data_team(fulldata, komp, month, gw, venue, cat)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        show_tim_data.to_excel(writer, sheet_name='Sheet1', index=False)
    download = st.download_button(
        label="Download data as Excel",
        data=buffer.getvalue(),
        file_name='team-data_downloaded ('+date+').xlsx',
        mime='application/vnd.ms-excel', key = 0)
    st.write(show_tim_data)

with players:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        komp = st.selectbox('Select Competition', ['Liga 1', 'Liga 2'], key='6')
        temp_pull = fulldata[fulldata['Kompetisi']==komp]
        team = st.multiselect('Select Teams', pd.unique(temp_pull['Team']), key='10')
        all_teams = st.checkbox('Select All Teams', key='303')
        if all_teams:
            team = pd.unique(temp_pull['Team'])
    with col2:
        temp_pull = temp_pull[temp_pull['Team'].isin(team)]
        pos = st.multiselect('Select Positions', pd.unique(temp_pull['Position']), key='7')
        all_poss = st.checkbox('Select All Positions', key='304')
        if all_poss:
             pos = pd.unique(temp_pull['Position'])
        temp_pull = temp_pull[temp_pull['Position'].isin(pos)]
        age = st.multiselect('Select Age Group', pd.unique(temp_pull['Age Group']), key='11')
    with col3:
        temp_pull = temp_pull[temp_pull['Age Group'].isin(age)]
        nat = st.multiselect('Select Nationality', pd.unique(temp_pull['Nat. Status']), key='8')
        temp_pull = temp_pull[temp_pull['Nat. Status'].isin(nat)]
        month = st.multiselect('Select Month', pd.unique(temp_pull['Month']), key='12')
        all_mos = st.checkbox('Select All Months', key='305')
        if all_mos:
            month = pd.unique(temp_pull['Month'])
    with col4:
        temp_pull = temp_pull[temp_pull['Month'].isin(month)]
        venue = st.multiselect('Select Venue', pd.unique(temp_pull['Home/Away']), key='9')
        temp_pull = temp_pull[temp_pull['Home/Away'].isin(venue)]
        gw = st.multiselect('Select Gameweek', pd.unique(temp_pull['Gameweek']), key='17')
        all_gws = st.checkbox('Select All GWs', key='306')
        if all_gws:
            gw = pd.unique(temp_pull['Gameweek'])
    with col5:
        mins = st.number_input('Input minimum mins. played', min_value=0,
                               max_value=3060, step=90, key=18)
        metrik = st.multiselect('Select Metrics', mlist, key='19')
    cat = st.selectbox('Select Category', ['Total', 'per 90'], key='16')
    show_player_data = data_player(fulldata, komp, team, pos, month, venue,
                                   gw, age, nat, metrik, mins, cat, df22)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        show_player_data.to_excel(writer, sheet_name='Sheet1', index=False)
    download = st.download_button(
        label="Download data as Excel",
        data=buffer.getvalue(),
        file_name='player-data_downloaded ('+date+').xlsx',
        mime='application/vnd.ms-excel', key = 1)
    st.write(show_player_data)
