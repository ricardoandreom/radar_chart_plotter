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
import lxml

font_normal = FontManager('https://raw.githubusercontent.com/google/fonts/main/apache/roboto/'
                          'Roboto%5Bwdth,wght%5D.ttf')
font_italic = FontManager('https://raw.githubusercontent.com/google/fonts/main/apache/roboto/'
                          'Roboto-Italic%5Bwdth,wght%5D.ttf')
font_bold = FontManager('https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/'
                        'RobotoSlab%5Bwght%5D.ttf')


# default fontname
def make_html(fontname):
    return "<p>{font}: <span style='font-family:{font}; font-size: 24px;'>{font}</p>".format(font=fontname)


# creating dataframe function
def get_df(url_df, columns_remaining_list):
    df = pd.read_html(url_df)[0]
    df.columns = [' '.join(col).strip() for col in df.columns]
    df = df.reset_index(drop=True)

    # creating a list with new names
    new_columns = []
    for col in df.columns:
        if 'level_0' in col:
            new_col = col.split()[-1]  # takes the last name
        else:
            new_col = col
        new_columns.append(new_col)

    # rename columns
    df.columns = new_columns
    df = df.fillna(0)

    if 'Playing Time 90s' in new_columns:
        df = df.rename(columns={'Playing Time 90s': '90s'})
    else:
        df = df.rename(columns={'90s': '90s'})

    df = df[['Rk', 'Player', 'Nation', 'Pos', 'Squad', 'Comp', 'Age', 'Born', '90s'] +
            columns_remaining_list]

    df['Age'] = df['Age'].str[:2]
    df['Position_2'] = df['Pos'].str[3:]
    df['Position'] = df['Pos'].str[:2]
    df['Nation'] = df['Nation'].str.split(' ').str.get(1)
    df['League'] = df['Comp'].str.split(' ').str.get(1)
    df['League_'] = df['Comp'].str.split(' ').str.get(2)
    df['League'] = df['League'] + ' ' + df['League_']
    df = df.drop(columns=['League_', 'Comp', 'Rk', 'Pos', 'Born'])

    df['Position'] = df['Position'].replace({'MF': 'Midfielder', 'DF': 'Defender', 'FW': 'Forward', 'GK': 'Goalkeeper'})
    df['Position_2'] = df['Position_2'].replace({'MF': 'Midfielder', 'DF': 'Defender',
                                                 'FW': 'Forward', 'GK': 'Goalkeeper'})
    df['League'] = df['League'].fillna('Bundesliga')

    return df


# function to edit the df resulted by the concatenation
def edit_df(df_concatenated):
    df_concatenated = df_concatenated.rename(columns={'Per 90 Minutes G-PK': 'Non-penalty goals',
                                                      'SCA SCA': 'Shot creation actions',
                                                      'Aerial Duels Won%': 'Aerial duels won %',
                                                      'Performance Fld': 'Fouls won',
                                                      'Performance Crs': 'Crosses',
                                                      'Performance Recov': 'Ball recoveries',
                                                      'Expected npxG': 'npxG',
                                                      'Expected npxG/Sh': 'npxG/shot',
                                                      'Standard SoT': 'Shots on target',
                                                      'Total Cmp': 'Passes completed',
                                                      'KP': 'Key passes',
                                                      '1/3': 'Final 3rd passes',
                                                      'Long Att': 'Long passes',
                                                      'PrgP': 'Progressive passes',
                                                      'Total Cmp%': 'Pass completion %',
                                                      'Tkl+Int': 'Tackles + interceptions',
                                                      'Blocks Sh': 'Shots blocked',
                                                      'Clr': 'Clearances',
                                                      'Take-Ons Att': 'Dribbles attempted',
                                                      'Take-Ons Succ%': 'Dribbles success %',
                                                      'Carries CPA': 'Carries into penalty area',
                                                      'Receiving Rec': 'Passes received',
                                                      'Receiving PrgR': 'Progressive passes received',
                                                      'Carries PrgC': 'Progressive carries'
                                                      })

    numeric_columns = ['Age', '90s', 'Non-penalty goals', 'Shot creation actions', 'Aerial duels won %', 'Fouls won',
                       'Crosses', 'Ball recoveries', 'npxG', 'npxG/shot', 'Shots on target', 'Passes completed',
                       'Key passes', 'xA', 'Final 3rd passes', 'Long passes', 'Progressive passes', 'Pass completion %',
                       'Tackles + interceptions', 'Shots blocked', 'Clearances', 'Dribbles attempted',
                       'Dribbles success %', 'Carries into penalty area', 'Passes received',
                       'Progressive passes received', 'Progressive carries']

    for j in numeric_columns:
        df_concatenated[j] = pd.to_numeric(df_concatenated[j], errors='coerce')

    ninety_columns = ['Non-penalty goals', 'Shot creation actions', 'Fouls won',
                      'Crosses', 'Ball recoveries', 'npxG', 'Shots on target',
                      'Passes completed', 'Key passes', 'xA', 'Final 3rd passes',
                      'Long passes', 'Progressive passes', 'Tackles + interceptions',
                      'Shots blocked', 'Clearances', 'Dribbles attempted',
                      'Carries into penalty area', 'Passes received',
                      'Progressive passes received', 'Progressive carries']
    # age filter
    df_concatenated = df_concatenated[df_concatenated['90s'] > 0]

    for i in ninety_columns:
        df_concatenated[i] = (df_concatenated[i]/df_concatenated['90s']).round(2)

    return df_concatenated


# calculating and adding percentile columns to df function
def percentiles_df(df_filtered_player_position):
    # percentile columns list
    df_cols_pct = ['Non-penalty goals', 'Shot creation actions', 'Aerial duels won %', 'Fouls won', 'Crosses',
                   'Ball recoveries', 'npxG', 'npxG/shot', 'Shots on target', 'Passes completed', 'Key passes', 'xA',
                   'Final 3rd passes', 'Long passes', 'Progressive passes', 'Pass completion %',
                   'Tackles + interceptions', 'Shots blocked', 'Clearances', 'Dribbles attempted', 'Dribbles success %',
                   'Carries into penalty area', 'Passes received', 'Progressive passes received', 'Progressive carries']
    for col in df_cols_pct:
        # Calculate the percentiles for each 'param' column
        percentiles = np.percentile(df_filtered_player_position[col], np.linspace(0, 100, num=101))
        df_filtered_player_position[col + '_pct'] = np.searchsorted(percentiles, df_filtered_player_position[col])*(100 / (len(percentiles) - 1))

    return df_filtered_player_position


def templates_position_params_legend(player_position):
    params = []
    if player_position == 'Goalkeeper':
        params = []
    elif player_position == 'Defender':
        params_legend = ['Non-penalty\ngoals', 'Shot creation\nactions', 'Progressive passes\nreceived',
                         'Carries into\npenalty area', 'Progressive\ncarries',
                         'Dribbles\nattempted', 'Dribbles\nsuccess %',
                         'Tackles\n+\ninterceptions', 'Shots\nblocked', 'Clearances', 'Aerial duels\nwon %',
                         'Ball\nrecoveries', 'Final 3rd\npasses', 'Long\npasses', 'Progressive\npasses', 'xA']

    elif player_position == 'Midfielder':
        params_legend = ['Non-penalty\ngoals', 'Shot creation\nactions',
                         'Progressive\ncarries', 'Dribbles\nattempted', 'Dribbles\nsuccess %',
                         'Tackles +\ninterceptions', 'Aerial duels\nwon %', 'Fouls\nwon',
                         'Ball\nrecoveries', 'Passes\ncompleted', 'Pass\ncompletion %', 'Key\npasses',
                         'Final 3rd\npasses', 'Long\npasses', 'Progressive\npasses', 'xA']

    else:
        params_legend = ['Non-penalty\ngoals', 'npxG', 'npxG/shot', 'Shots on\ntarget',
                         'Shot creation\nactions', 'Dribbles\nattempted', 'Dribbles\nsuccess %',
                         'Carries into\npenalty area', 'Tackles +\ninterceptions', 'Aerial duels\nwon %',
                         'Passes\nreceived', 'Passes\ncompleted', 'Crosses', 'Key\npasses', 'xA']

    return params_legend


def templates_position_params(player_position):
    params = []
    if player_position == 'Goalkeeper':
        params = []
    elif player_position == 'Defender':
        params = ['Non-penalty goals_pct', 'Shot creation actions_pct', 'Progressive passes received_pct',
                  'Carries into penalty area_pct', 'Progressive carries_pct',
                  'Dribbles attempted_pct', 'Dribbles success %_pct',
                  'Tackles + interceptions_pct', 'Shots blocked_pct', 'Clearances_pct', 'Aerial duels won %_pct',
                  'Ball recoveries_pct', 'Final 3rd passes_pct', 'Long passes_pct',
                  'Progressive passes_pct',
                  'xA_pct']

    elif player_position == 'Midfielder':
        params = ['Non-penalty goals_pct', 'Shot creation actions_pct',
                  'Progressive carries_pct', 'Dribbles attempted_pct', 'Dribbles success %_pct',
                  'Tackles + interceptions_pct', 'Aerial duels won %_pct', 'Fouls won_pct',
                  'Ball recoveries_pct', 'Passes completed_pct', 'Pass completion %_pct', 'Key passes_pct',
                  'Final 3rd passes_pct', 'Long passes_pct', 'Progressive passes_pct', 'xA_pct']

    else:
        params = ['Non-penalty goals_pct', 'npxG_pct', 'npxG/shot_pct', 'Shots on target_pct',
                  'Shot creation actions_pct', 'Dribbles attempted_pct', 'Dribbles success %_pct',
                  'Carries into penalty area_pct', 'Tackles + interceptions_pct', 'Aerial duels won %_pct',
                  'Passes received_pct', 'Passes completed_pct', 'Crosses_pct', 'Key passes_pct', 'xA_pct']

    return params


def templates_position_slice_colors(player_position):
    if player_position == 'Goalkeeper':
        slice_colors = []
    elif player_position == 'Defender':
        slice_colors = ["#4DB3F7"] * 3 + ["#E25A5A"] * 4 + ["#7DE55D"] * 5 + ["#FDE050"] * 4
    elif player_position == 'Midfielder':
        slice_colors = ["#4DB3F7"] * 2 + ["#E25A5A"] * 3 + ["#7DE55D"] * 4 + ["#FDE050"] * 7
    else:
        slice_colors = ["#4DB3F7"] * 5 + ["#E25A5A"] * 3 + ["#7DE55D"] * 2 + ["#FDE050"] * 5

    return slice_colors


def templates_position_text_colors(player_position):
    if player_position == 'Goalkeeper':
        text_colors = []
    elif player_position == 'Defender':
        text_colors = ["#000000"] * 10 + ["black"] * 6

    elif player_position == 'Midfielder':
        text_colors = ["#000000"] * 10 + ["black"] * 6

    else:
        text_colors = ["#000000"] * 10 + ["black"] * 5


# create radar chart plot
def show_radar_chart(player_values, df, player_position, player, nineties_played, circle_logo):
    # instantiate PyPizza class
    baker = PyPizza(
        params=templates_position_params_legend(player_position),                  # list of parameters
        background_color="white",         # background color
        straight_line_color="white",      # color for straight lines
        straight_line_lw=2.5,             # linewidth for straight lines
        last_circle_lw=0,                 # linewidth of last circle
        other_circle_ls="-.",             # linewidth for other circles
        other_circle_lw=2,
        inner_circle_size=19.5            # size of inner circle
    )

    # plot pizza
    fig, ax = baker.make_pizza(
        player_values,                          # list of values
        figsize=(12, 12),                       # adjust figsize according to your need
        color_blank_space="same",               # use same color to fill blank space
        slice_colors=templates_position_slice_colors(player_position),       # color for individual slices
        value_colors=templates_position_text_colors(player_position),                   # color for the value-text
        value_bck_colors=templates_position_slice_colors(player_position),   # color for the blank spaces
        blank_alpha=0.2,                        # alpha for blank-space colors
        kwargs_slices=dict(
            edgecolor="#F2F2F2", zorder=2, linewidth=1
        ),                                      # values to be used when plotting slices
        kwargs_params=dict(
            color="#000000", fontsize=18,
            fontproperties=font_bold.prop, va="center"
        ),                                      # values to be used when adding parameter
        kwargs_values=dict(
            color="black", fontsize=15,
            fontproperties=font_bold.prop, zorder=3,
            bbox=dict(
                edgecolor="#000000", facecolor="cornflowerblue",
                boxstyle="round,pad=0.2", lw=2
            )
        )                                      # values to be used when adding parameter-values
    )

    # add title
    fig.text(
        0.515, 1.04, player + " - " + df.set_index('Player').loc[player, 'Squad'], size=40,
        ha="center", fontproperties=font_bold.prop, fontweight='heavy', color="black"
    )

    # add subtitle
    fig.text(
        0.515, 0.995,
        "Percentile Rank vs Top-Five League " + player_position + "s",
        size=22,
        ha="center", fontproperties=font_bold.prop, color="black"
    )

    # add text
    fig.text(0.5, 0.955, player_position + " player stats/90" + "   | 90s played:  " +
             str(df.set_index('Player').loc[player, '90s']) +
             "    | Age:  " + str(int(df.set_index('Player').loc[player, 'Age'])) +
             '   | Season 2023/24', size=20, ha='center', fontproperties=font_bold.prop, color="black")

    # add text
    text1 = "Only players with >=" + str(nineties_played) + "'s played"
    text2 = "Data from FBREF"

    # add text
    fig.text(
        0.68, 0.02, f"{text1}\n{text2}", size=16,
        fontproperties=font_bold.prop, color="#000000",
        ha="left"
    )

    # add text
    fig.text(
        0.05, 0.02, "Made by @ricardoandreom / @HspaceAnalytics", size=12,
        fontproperties=font_bold.prop, color="black",
        ha="left"
    )

    # add image
    ax_image = add_image(
        circle_logo, fig, left=0.417, bottom=0.41, width=0.12, height=.1
    )

    # plot image
    buf = io.BytesIO()
    plt.savefig(buf, dpi=500, bbox_inches='tight', facecolor='white', format="png")
    st.image(buf.getvalue())


# Save image function
def save_image():
    buf1 = io.BytesIO()
    plt.savefig(buf1, dpi=500, bbox_inches='tight', facecolor='white', format="png")
    # Return buffer content
    return buf1.getvalue()

