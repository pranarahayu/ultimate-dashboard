import sys
import pandas as pd
import numpy as np
import streamlit as st
import io

import openpyxl, yattag
from openpyxl import load_workbook
from yattag import Doc, indent

st.set_page_config(page_title='Match Center', layout='wide')
st.markdown('# Match Center')

col1, col2, col3 = st.columns(3)
with col1:
  komp = st.selectbox('Select Competition', ['Liga 1', 'Liga 2'], key='1')
with col2:
  #smt = fulldata[fulldata['Kompetisi']==komp]
  gw = st.selectbox('Select GW', [1, 2, 3], key='2')
  all_gws = st.checkbox('Select All GWs', key='5')
if all_gws:
  with col3:
    team = st.selectbox('Select Team', ['Bali', 'PERSIB'], key='3')
else:
  with col3:
    mat = st.selectbox('Select Match', ['Bali vs PSS', 'PERSIB vs Madura'], key='3')

#st.image("./data/poster3.jpg")
df = pd.read_json('./data/timelines_upd2024-04-22.json')
df2 = df[df['Team']=='Bali United FC']
df2 = df2[df2['GW']==1].reset_index(drop=True)
st.write(df2)
