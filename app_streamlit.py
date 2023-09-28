# libraries
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import io
from urllib.request import urlopen
from PIL import Image
from mplsoccer import PyPizza, add_image, FontManager
import matplotlib.font_manager
from IPython.core.display import HTML
from pathlib import Path
import app_functions as app
import lxml

# data urls list
url_standard = 'https://fbref.com/en/comps/Big5/stats/players/Big-5-European-Leagues-Stats#stats_standard'
url_shotcreation = 'https://fbref.com/en/comps/Big5/gca/players/Big-5-European-Leagues-Stats#stats_gca'
url_misc = 'https://fbref.com/en/comps/Big5/misc/players/Big-5-European-Leagues-Stats#stats_misc'
url_shoot = 'https://fbref.com/en/comps/Big5/shooting/players/Big-5-European-Leagues-Stats#stats_shooting'
url_passing = 'https://fbref.com/en/comps/Big5/passing/players/Big-5-European-Leagues-Stats#stats_passing'
url_def = 'https://fbref.com/en/comps/Big5/defense/players/Big-5-European-Leagues-Stats#stats_defense'
url_poss = 'https://fbref.com/en/comps/Big5/possession/players/Big-5-European-Leagues-Stats#stats_possession'

# white Logo
white_logo_url = \
    "https://raw.githubusercontent.com/ricardoandreom/Data/master/Images/Personal%20Logos/Half%20Space%20Branco.png"

# black logo
black_logo_url = "https://raw.githubusercontent.com/ricardoandreom/Data/master/Images/Personal%20Logos/Half%20Space%20Preto.png"

# LANDING PAGE LINK
SOCIAL_MEDIA = {
    "Portfolio page": "https://ricardoandreom.github.io/ricardo_portfolio_page/",
    "Digital CV": "https://ricardo-marques-digital-cv.streamlit.app/"
}

# set default colors
text_color = 'white'
background = 'black'

font_normal = FontManager('https://raw.githubusercontent.com/google/fonts/main/apache/roboto/'
                          'Roboto%5Bwdth,wght%5D.ttf')
font_italic = FontManager('https://raw.githubusercontent.com/google/fonts/main/apache/roboto/'
                          'Roboto-Italic%5Bwdth,wght%5D.ttf')
font_bold = FontManager('https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/'
                        'RobotoSlab%5Bwght%5D.ttf')

# --- PATH SETTINGS ---
current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
css_file = current_dir / "styles" / "main.css"


code = "\n".\
    join([app.make_html(font) for font in sorted(set([f.name for f in matplotlib.font_manager.fontManager.ttflist]))])

# creating the stats dfs
df_standard = app.get_df(url_standard, ['Per 90 Minutes G-PK'])
df_shotcreation = app.get_df(url_shotcreation, ['SCA SCA'])
df_misc = app.get_df(url_misc, ['Aerial Duels Won%', 'Performance Fld', 'Performance Crs', 'Performance Recov'])
df_shoot = app.get_df(url_shoot, ['Expected npxG', 'Expected npxG/Sh', 'Standard SoT'])
df_passing = app.get_df(url_passing, ['Total Cmp', 'KP', 'xA', '1/3', 'Long Att', 'PrgP', 'Total Cmp%'])
df_def = app.get_df(url_def, ['Tkl+Int', 'Blocks Sh', 'Clr'])
df_poss = app.get_df(url_poss, ['Take-Ons Att', 'Take-Ons Succ%', 'Carries CPA', 'Receiving Rec', 'Receiving PrgR',
                                'Carries PrgC'])

# Define a list of dataframes
dfs = [df_shotcreation, df_misc, df_shoot, df_passing, df_def, df_poss]

# Loop through the list and drop the columns
for df in dfs:
    df.drop(columns=['Player', 'Squad', 'Age', 'Nation', 'Position', 'League', '90s', 'Position_2'], inplace=True)

# concatenate all dat
frames = [df_standard, df_shotcreation, df_misc, df_shoot, df_passing, df_def, df_poss]
df = pd.concat(frames, axis=1, join='outer')

########################################################################################################

df = app.edit_df(df)

# STREAMLIT APP

# minutes filter
# Getting the max value for the slider
max_value = int(df['90s'].max()) # - 5)

# APP TITLE
st.title('Radar chart plotter ⚽📈')

st.markdown("""
    <p style='font-size: 20px; font-weight: bold; color: black;'> 🔴 Create percentile rank radar charts for any 
    player in Europe's Top-5 Leagues</p>
""", unsafe_allow_html=True)

st.markdown("""
    <p style='font-size: 19px; font-weight: bold; color: black;'> 🔴 Compare a player stats with players who play in 
    the same position</p>
""", unsafe_allow_html=True)

st.markdown("""
    <p style='font-size: 18px; font-weight: bold; color: black;'>Set the mininum 90's played to make the results
     more representative of the reality.</p>
""", unsafe_allow_html=True)

st.write('#')
# MAIN LOGO (WHITE)
st.sidebar.image(white_logo_url, use_column_width=True)

st.sidebar.markdown("***")

st.sidebar.markdown("""
    <p style='font-size: 26px; font-weight: bold; color: black;'>Radar chart inputs:</p>
""", unsafe_allow_html=True)

# Creating a slider that allows user to select an integer between 1 and max value minus 5
nineties_played = st.sidebar.slider("**Select mininum 90s played:**", 1, max_value - 5, 1)

player = st.sidebar.selectbox("**Name of the player:**", df['Player'])

# GK note missing data
st.sidebar.write('Note: No radar charts displayed for goalkeepers yet!')

# portfolio url
st.sidebar.write("#")
st.sidebar.write('**Made by @ricardoandreom 🚀⚽**')
cols = st.sidebar.columns(len(SOCIAL_MEDIA))
for index, (platform, link) in enumerate(SOCIAL_MEDIA.items()):
    cols[index].write(f"[{platform}]({link})\n")

#############################################################################################


# filtering df by mininum 90s played
df = df[df['90s'] >= nineties_played]

# country filter
country = 'POR'
# df = df[df['Nation']=='country']

# getting player main position
player_position = df.set_index('Player').loc[player, 'Position']

# filtering the df by player's position in order to make the comparison only this position players itself
df = df[(df['Position'] == player_position)]


df = app.percentiles_df(df)


# getting the logo
circle_logo = Image.open(urlopen(black_logo_url))

# getting a list of player values
player_values = list(df.set_index('Player').loc[player, app.templates_position_params(player_position)].values)

app.show_radar_chart(player_values, df, player_position, player, nineties_played, circle_logo)


# Save image button
if st.download_button(label="Save image", data=app.save_image(), file_name=player + "_radar_chart.png", mime="image/png"):
    st.write("Image saved successfully!")


st.write('#')
st.markdown("""
    <p style='font-size: 20px; font-weight: bold; color: white;'>Data:</p>
""", unsafe_allow_html=True)

# plot dataframe
all_cols = ['Nation', 'Squad', 'Age', '90s', 'Position', 'Position_2', 'League'] + \
           app.templates_position_params(player_position)
int_columns = ['Age'] + app.templates_position_params(player_position)
df_plot_app = df.set_index('Player')[all_cols]
df_plot_app['90s'] = df_plot_app['90s'].round(1)
df_plot_app['League'] = df_plot_app['League'].fillna('Bundesliga')
df_plot_app[int_columns] = df_plot_app[int_columns].astype(int)

st.dataframe(df_plot_app)
