import pandas as pd
import plotly.graph_objects as go
import numpy as np
import random
import plotly.express as px
from collections import defaultdict
import ast


def process_teams(Blue_Team, Red_Team, df):
    df['Champion'] = df['Champion'].str.lower()
    df['con_champ'] = df['con_champ'].str.lower()

    blue_champs = [k.lower() for k in Blue_Team]
    red_champs = [k.lower() for k in Red_Team]

    # 2. 기본 스탯 (Ban, Pick, Win_rate) 계산
    # Blue Team의 기본 스탯을 데이터프레임으로 추출
    blue_base_stats = df[df['Champion'].isin(blue_champs)][['Champion', 'Ban', 'Pick', 'Win_rate']].drop_duplicates()

    # Red Team의 기본 스탯을 데이터프레임으로 추출
    red_base_stats = df[df['Champion'].isin(red_champs)][['Champion', 'Ban', 'Pick', 'Win_rate']].drop_duplicates()


    # Blue Team: Duo_Score 계산
    blue_duo_df = df[df['Champion'].isin(blue_champs) & df['con_champ'].isin(blue_champs) & (df['Champion'] != df['con_champ'])]
    blue_duo_score = blue_duo_df.groupby('Champion')['Duo_Score'].sum().rename('Blue_Duoscore')

    # Blue Team: Count_Score (Red Team과의 카운터) 계산
    blue_count_df = df[df['Champion'].isin(blue_champs) & df['con_champ'].isin(red_champs)]
    blue_count_score = blue_count_df.groupby('Champion')['Count_Score'].sum().rename('Blue_Countscore')

    # Red Team: Duo_Score 계산
    red_duo_df = df[df['Champion'].isin(red_champs) & df['con_champ'].isin(red_champs) & (df['Champion'] != df['con_champ'])]
    red_duo_score = red_duo_df.groupby('Champion')['Duo_Score'].sum().rename('Red_Duoscore')

    # Red Team: Count_Score (Blue Team과의 카운터) 계산
    red_count_df = df[df['Champion'].isin(red_champs) & df['con_champ'].isin(blue_champs)]
    red_count_score = red_count_df.groupby('Champion')['Count_Score'].sum().rename('Red_Countscore')

    # 4. 결과 집계 및 통합 (NaN 값 처리)

    # Blue Team 최종 집계
    blue_summary = blue_base_stats.set_index('Champion')
    blue_summary = blue_summary.merge(blue_duo_score, left_index=True, right_index=True, how='left')
    blue_summary = blue_summary.merge(blue_count_score, left_index=True, right_index=True, how='left')

    # NaN 값 처리: Win_rate는 기본값 50, 나머지는 0 (원본 로직 반영)
    blue_summary['Win_rate'] = blue_summary['Win_rate'].fillna(50)
    blue_summary[['Ban', 'Pick', 'Blue_Duoscore', 'Blue_Countscore']] = \
        blue_summary[['Ban', 'Pick', 'Blue_Duoscore', 'Blue_Countscore']].fillna(0)

    # Red Team 최종 집계
    red_summary = red_base_stats.set_index('Champion')
    red_summary = red_summary.merge(red_duo_score, left_index=True, right_index=True, how='left')
    red_summary = red_summary.merge(red_count_score, left_index=True, right_index=True, how='left')

    # NaN 값 처리: Win_rate는 기본값 50, 나머지는 0 (원본 로직 반영)
    red_summary['Win_rate'] = red_summary['Win_rate'].fillna(50)
    red_summary[['Ban', 'Pick', 'Red_Duoscore', 'Red_Countscore']] = \
        red_summary[['Ban', 'Pick', 'Red_Duoscore', 'Red_Countscore']].fillna(0)

    # 5. 최종 합산 및 반환
    # Blue Team
    sum3 = blue_summary['Win_rate'].sum()
    sum4 = blue_summary['Blue_Duoscore'].sum()
    sum5 = blue_summary['Blue_Countscore'].sum()

    # Red Team
    sum8 = red_summary['Win_rate'].sum()
    sum9 = red_summary['Red_Duoscore'].sum()
    sum10 = red_summary['Red_Countscore'].sum()

    # 결과 데이터프레임 생성
    result = [[sum3, sum4, sum5, sum8, sum9, sum10]]
    features = pd.DataFrame(result)
    features.columns = ['Blue_Winrate','Blue_Duoscore','Blue_Countscore','Red_Winrate','Red_Duoscore','Red_Countscore']

    # Duo_Score와 Count_Score는 소수점 둘째 자리까지 반올림 (원본 로직 반영)
    features['Blue_Duoscore'] = features['Blue_Duoscore'].round(2)
    features['Blue_Countscore'] = features['Blue_Countscore'].round(2)
    features['Red_Duoscore'] = features['Red_Duoscore'].round(2)
    features['Red_Countscore'] = features['Red_Countscore'].round(2)

    return features

def gold(cham_list, power_df):
    temp_2 = []
    temp_3 = []
    for i in cham_list:
        i = i.lower()

        try:
            raw_data = power_df.loc[i, 'Gold_Data']
            gold_list = ast.literal_eval(raw_data)
            temp_2.append(gold_list)

        except KeyError:
            pass
        except (ValueError, TypeError):
            pass

    for k in range(0, 35):
        temp = []
        value = 0

        for u in temp_2:
            if k < len(u):
                temp.append(u[k])
        if len(temp) != 0:
            value = round(sum(temp) / len(temp), 2)
        temp_3.append([k, value])
    bins = [0, 10, 20, 35]
    labels = ['early', 'middle', 'late']
    temp_gold_result = pd.DataFrame(temp_3)
    temp_gold_result.columns = ['time', 'gold']
    temp_gold_result['TimeRange'] = pd.cut(
        temp_gold_result['time'],
        bins=bins,
        labels=labels,
        right=False # 0~10미만, 10~20미만, 20~35미만
    )
    temp_gold_result = temp_gold_result[~((temp_gold_result['TimeRange'] == 'late') & (temp_gold_result['gold'] == 0))]
    gold_result = temp_gold_result.groupby('TimeRange')['gold'].mean().reset_index()
    return gold_result





def duo_chart(blue_team,df):
    blue_duo=[]
    for i in blue_team:
        blue_duo_2=[]
        for j in blue_team:
            if i!=j:
                if len(df[(df['Champion'] == i) & (df['con_champ'] == j)]['Duo_Score']) != 0:
                    blue_duo_2.append(df[(df['Champion'] == i) & (df['con_champ'] == j)]['Duo_Score'].iloc[0])
                else :
                    blue_duo_2.append(0)
            else:
                blue_duo_2.append(0)
        blue_duo.append(blue_duo_2)
    custom_colorscale = [
        [0, '#FF6384'],      # 최소값
        [0.5, 'white'],      # 중간값 (0)
        [1, '#36A2EB']       # 최대값
    ]
    temp_chart_code = []
    temp_data=np.array(blue_duo)
    temp_df=pd.DataFrame(temp_data)
    temp_df.index = blue_team
    temp_df.columns = blue_team
    synergy_list=[]
    for i in range(0,len(temp_data)):
        for j in range(0,len(temp_data[i])) :
            if temp_data[i][j] > 0:
                if temp_data[j][i] > 0:
                    if temp_data[i][j]+temp_data[j][i] >= 20:
                        synergy_list.append([blue_team[i],blue_team[j],temp_data[i][j]+temp_data[j][i]])
    seen = set()
    synergy = []
    synergy_dict = defaultdict(set)
    seen = set()
    for champ1, champ2, value in synergy_list:
        key = tuple(sorted([champ1, champ2]))
        if key not in seen:
            seen.add(key)
            synergy_dict[champ1].add(champ2)
            synergy_dict[champ2].add(champ1)

    synergy = [[champ, list(partners)] for champ, partners in synergy_dict.items() if partners]

    fig = go.Figure(data=go.Heatmap(
        z=temp_df.values,
        x=temp_df.columns,
        y=temp_df.index,
        text=temp_df.values,
        texttemplate='%{text:.1f}',
        textfont={"size": 11,"family":"Arial"},
        colorscale=custom_colorscale,
        zmid=0,
        zmin=-50,
        zmax=50,
        showscale=True,
        xgap=3,  # x축 방향 간격 (픽셀)
        ygap=3   # y축 방향 간격 (픽셀)
    ))

    # 레이아웃 설정
    fig.update_layout(
        paper_bgcolor='#0a0e21',  # 전체 배경색
        plot_bgcolor='#1d1e33',   # 플롯 배경색
        width=500,                # figsize=(5, 3)과 비슷한 크기
        height=300,
        margin=dict(l=50, r=50, t=50, b=30),
        font=dict(
            family='Arial',
            color='white'         # 텍스트 색상
        ),
        xaxis=dict(
            side='top',  # x축을 위에 표시
            showgrid=False,
            showline=False,
            tickfont=dict(family="Arial")
        ),
        yaxis=dict(
            autorange='reversed',  # Y축 역순 설정
            showgrid=False,
            showline=False,
            tickfont=dict(family="Arial")
        )
    )

    # x축, y축 설정
    fig.update_xaxes(showgrid=False, showline=False)
    fig.update_yaxes(showgrid=False, showline=False)

    # HTML로 변환하여 저장
    temp_chart_code.append(fig.to_html(
        full_html=False,
        include_plotlyjs='cdn',
        div_id=f'THIS_IS_FIGID{random.random()}'
    ))
    return [temp_chart_code[0],synergy]

def count_chart(blue_team,red_team,df):
    blue_count=[]
    for i in blue_team:
        blue_count_2=[]
        for k in red_team:
            if len(df[(df['Champion'] == i) & (df['con_champ'] == k)]['Count_Score']) != 0:
                blue_count_2.append(df[(df['Champion'] == i) & (df['con_champ'] == k)]['Count_Score'].iloc[0])
            else :
                blue_count_2.append(0)
        blue_count.append(blue_count_2)
    custom_colorscale = [
        [0, '#FF6384'],      # 최소값
        [0.5, 'white'],      # 중간값 (0)
        [1, '#36A2EB']       # 최대값
    ]
    temp_chart_code = []
    temp_data=np.array(blue_count)
    temp_df=pd.DataFrame(temp_data)
    temp_df.index = blue_team
    temp_df.columns = red_team
    synergy_list=[]
    synergy_dict = defaultdict(set)
    for i in range(len(temp_data)):
        for j in range(len(temp_data[i])):
            value = temp_data[i][j]
            if value >= 15:
                champ1 = blue_team[i]
                champ2 = red_team[j]
                synergy_dict[champ1].add(champ2)
    synergy_list = [    [champ, list(partners)] for champ, partners in synergy_dict.items() if partners]
    fig = go.Figure(data=go.Heatmap(
        z=temp_df.values,
        x=temp_df.columns,
        y=temp_df.index,
        text=temp_df.values,
        texttemplate='%{text:.1f}',
        textfont={"size": 11,"family":"Arial"},
        colorscale=custom_colorscale,
        zmid=0,
        zmin=-50,
        zmax=50,
        showscale=True,
        xgap=3,  # x축 방향 간격 (픽셀)
        ygap=3   # y축 방향 간격 (픽셀)
    ))

    # 레이아웃 설정
    fig.update_layout(
        paper_bgcolor='#0a0e21',  # 전체 배경색
        plot_bgcolor='#1d1e33',   # 플롯 배경색
        width=500,                # figsize=(5, 3)과 비슷한 크기
        height=300,
        margin=dict(l=50, r=50, t=50, b=30),
        font=dict(
            family='Arial',
            color='white'         # 텍스트 색상
        ),
        xaxis=dict(
            side='top',  # x축을 위에 표시
            showgrid=False,
            showline=False,
            tickfont=dict(family="Arial")
        ),
        yaxis=dict(
            autorange='reversed',  # Y축 역순 설정
            showgrid=False,
            showline=False,
            tickfont=dict(family="Arial")
        )
    )

    # x축, y축 설정
    fig.update_xaxes(showgrid=False, showline=False)
    fig.update_yaxes(showgrid=False, showline=False)

    # HTML로 변환하여 저장
    temp_chart_code.append(fig.to_html(
        full_html=False,
        include_plotlyjs='cdn',
        div_id=f'THIS_IS_FIGID{random.random()}'
    ))
    return [temp_chart_code[0],synergy_list]

def count_carry_lines(dmg_ratios):
    return sum([1 for d in dmg_ratios if d >= 0.16])

def count_tank_lines(dmg_ratios):
    return sum([1 for d in dmg_ratios if d >= 0.18])

"""
def power_graph(Cham_list,power_df):
    powerdata_list=[]
    for i in Cham_list:
        if len(power_df[power_df['Champion']==i])!=0:
            temp_str=''
            temp_str=temp_str+power_df[power_df['Champion']==i].iloc[0][0]+str(power_df[power_df['Champion']==i].iloc[0][1])
            powerdata_list.append(temp_str)
    return powerdata_list
"""

def power_graph(Cham_list, power_df):
    powerdata_list = []
    for i in Cham_list:
        if i in power_df.index:
            temp_str = ''
            gold_data_str = str(power_df.loc[i, power_df.columns[0]])
            temp_str = temp_str + i + gold_data_str
            powerdata_list.append(temp_str)

    return powerdata_list



def create_dataframe(data_list):
    champion_data = {}
    for line in data_list:
        # 챔피언 이름과 데이터 분리
        champion_name = line.split('[')[0].strip()
        # 문자열 데이터를 숫자 리스트로 변환
        values = [float(x.strip()) for x in line.split('[')[1].strip(']').split(',')]
        champion_data[champion_name] = values

    # DataFrame 생성을 위한 리스트 만들기
    df_data = []
    for champion, values in champion_data.items():
        for time_point, value in enumerate(values,start=1):
            df_data.append({
                'Champion': champion,
                'Time': time_point,
                'Value': value
            })

    return pd.DataFrame(df_data)

def create_power_graph(power_data):
    # DataFrame 생성
    power_df2 = create_dataframe(power_data)

    max_value = max(power_df2['Value'])
    y_max = max(max_value, 4000)

    # 누적 영역 차트로 변경
    fig = px.area(
        power_df2,
        x='Time',
        y='Value',
        color='Champion',
        title='Champion Power Over Time (Stacked)',
        labels={'Time': 'Time', 'Value': 'Earn Gold', 'Champion': 'Champion'},
    )

    fig.update_layout(
        plot_bgcolor='#1d1e33',
        paper_bgcolor='#0a0e21',
        font=dict(family='Arial', color='white'),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02
        ),
        hovermode='x unified'
    )

    fig.update_xaxes(
        gridcolor='lightgrey',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='lightgrey'
    )

    fig.update_yaxes(
        gridcolor='lightgrey',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='lightgrey',
        range=[0, y_max * 1.1]
    )

    chart_code = fig.to_html(
        full_html=False,
        include_plotlyjs='cdn',
        div_id=f'THIS_IS_FIGID{random.random()}'
    )
    return chart_code

"""
def dmg_weight(cham_list,dmg_rate_df):
    dmg_weight = []
    cham_list[-1]=cham_list[-1]+'_support'
    for i in cham_list:
        i=i.lower()
        if len(dmg_rate_df[dmg_rate_df['Champion'] == i])==0:
            deal_norm_total=0
            tank_norm_total=0
        else:
            deal_norm_total = dmg_rate_df[dmg_rate_df['Champion'] == i]['deal_norm_total'].iloc[0]
            tank_norm_total = dmg_rate_df[dmg_rate_df['Champion'] == i]['tank_norm_total'].iloc[0]
        champ_name = i.replace('_support', '')  # '_support' 자동 제거
        dmg_weight.append([champ_name, deal_norm_total, tank_norm_total])
    cham_list[-1]=cham_list[-1].replace('_support','')
    return dmg_weight
"""

def dmg_weight(cham_list, dmg_rate_dict):
    dmg_weight = []

    current_cham_list = [c.lower() for c in cham_list]
    if current_cham_list and len(current_cham_list) == 5:
        current_cham_list[-1] = current_cham_list[-1] + '_support'

    for i in current_cham_list:
        champ_name_key = i
        stats = dmg_rate_dict.get(champ_name_key)

        if stats:
            deal_norm_total = stats[0]
            tank_norm_total = stats[1]
        else:
            deal_norm_total = 0
            tank_norm_total = 0
        champ_display_name = i.replace('_support', '')
        dmg_weight.append([champ_display_name, deal_norm_total, tank_norm_total])
    return dmg_weight


def dmg_weight_chart(dmg_weight):
    attribute = ['Defence', 'Attack']

    total_attack = round(sum([item[1] for item in dmg_weight]),2)
    total_defence = round(sum([item[2] for item in dmg_weight]),2)

    values = [[round(item[2], 1), round(item[1], 1)] for item in dmg_weight]
    ratios = [[round(item[2]/total_attack*100, 2), round(item[1]/total_defence*100, 2)] for item in dmg_weight]

    values = [[v[0], v[1]] for v in values]
    ratios = [[r[0], r[1]] for r in ratios]

    colors = ['#FF6F61', '#7DCEA0', '#5DADE2', '#AF7AC5', '#F4D03F']

    fig = go.Figure()
    for i, (champ, color) in enumerate(zip(dmg_weight, colors)):
        fig.add_trace(go.Bar(
            y=attribute,
            x=[values[i][0], values[i][1]],  # 공격, 방어 순으로 값 적용
            name=champ[0],
            orientation='h',
            marker=dict(color=color),
            text=[
                f'{champ[0]} <br> ({ratios[i][0]}%)',  # Attack
                f'{champ[0]} <br> ({ratios[i][1]}%)'   # Defence
            ],
            textposition='inside',
            insidetextanchor='middle'
        ))
    max_value = max(total_attack, total_defence)
    fig.update_layout(
        barmode='stack',
        title='Team Deal & Tank ratio',
        template='plotly_dark',
        plot_bgcolor='#0a0e21',
        paper_bgcolor='#0a0e21',
        font=dict(color='white'),
        showlegend=False,
        height=400
    )
    for i, attr in enumerate(attribute):
        total_value = total_attack if attr == 'Attack' else total_defence
        fig.add_annotation(
            x=max_value * 1.02,
            y=i+0.3,
            text=f"<b>Total: {total_value}</b>",
            showarrow=False,
            font=dict(color="white", size=14, family="Arial"),
            bgcolor="rgba(0, 0, 0, 0.5)",
        )

    chart_code=(fig.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            div_id=f'THIS_IS_FIGID{random.random()}'))
    return chart_code

def damage_distribution(champion_list,dmg_rate_df):
    champion_list[-1]=champion_list[-1]+'_support'
    selected_df = dmg_rate_df[dmg_rate_df['Champion'].isin(champion_list)]

    total_AD_p = selected_df['AD_p'].sum()
    total_AP_p = selected_df['AP_p'].sum()
    total_TD_p = selected_df['TD_p'].sum()
    all_sum=total_AD_p+total_AP_p+total_TD_p
    champion_list[-1] = champion_list[-1].replace('_support', '')
    # 40 <- 변경예정
    if total_AD_p/all_sum*100 >= 55 or total_AP_p/all_sum*100 <= 35 :
        comment='AD'
    elif total_AP_p/all_sum*100 >= 55 or total_AD_p/all_sum*100 <= 35 :
        comment='AP'
    else:
        comment='균형'
    # 데이터 준비
    values = [total_AD_p, total_AP_p, total_TD_p]
    labels = ['AD', 'AP', 'True Damage']
    colors = ['#FF6F61', '#5DADE2', '#F4D03F']  # AD(빨강), AP(파랑), TD(노랑)

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        textinfo='label+percent',
        insidetextorientation='radial',
        marker=dict(colors=colors)
    )])

    fig.update_layout(
        title="Damage Type Distribution",
        plot_bgcolor='#0a0e21',
        paper_bgcolor='#0a0e21',
        font=dict(color='white'),
        showlegend=False,
        width=500,
        height=400
    )

    chart_code=(fig.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            div_id=f'THIS_IS_FIGID{random.random()}'))
    return [chart_code,comment]


def ml_features(blue_team,red_team,gold_ml_df,df, dmg_rate_df):
    ml_temp_df=process_teams(blue_team,red_team,df)
    ml_temp_blue_df=dmg_weight(blue_team,dmg_rate_df)
    ml_temp_red_df=dmg_weight(red_team,dmg_rate_df)
    blue_total_atk = sum([item[1] for item in ml_temp_blue_df])
    blue_total_def = sum([item[2] for item in ml_temp_blue_df])
    red_total_atk = sum([item[1] for item in ml_temp_red_df])
    red_total_def = sum([item[2] for item in ml_temp_red_df])
    blue_temp_atk=[]
    blue_temp_def=[]
    red_temp_atk=[]
    red_temp_def=[]
    for blue_i in ml_temp_blue_df:
        blue_temp_atk.append(blue_i[1]/blue_total_atk)
        blue_temp_def.append(blue_i[2]/blue_total_def)
    for red_i in ml_temp_red_df:
        red_temp_atk.append(red_i[1]/red_total_atk)
        red_temp_def.append(red_i[2]/red_total_def)
    blue_atk_cnt=count_carry_lines(blue_temp_atk)
    blue_def_cnt=count_tank_lines(blue_temp_def)
    red_atk_cnt=count_carry_lines(red_temp_atk)
    red_def_cnt=count_tank_lines(red_temp_def)
    ml_temp_df2=pd.DataFrame([[blue_total_atk,blue_total_def,blue_atk_cnt,blue_def_cnt,red_total_atk,red_total_def,red_atk_cnt,red_def_cnt]])
    ml_temp_df3=pd.concat([ml_temp_df,ml_temp_df2],axis=1)
    ml_df=ml_temp_df3
    ml_df.columns=['Blue_Winrate','Blue_Duoscore','Blue_Countscore','Red_Winrate','Red_Duoscore','Red_Countscore','blue_total_atk','blue_total_def','blue_atk_cnt','blue_def_cnt','red_total_atk','red_total_def','red_atk_cnt','red_def_cnt']
    test_df=pd.DataFrame(list((ml_df['Blue_Winrate']-ml_df['Red_Winrate'])+(ml_df['Blue_Duoscore']-ml_df['Red_Duoscore'])+(ml_df['Blue_Countscore']-ml_df['Red_Countscore'])))
    test_df.columns = ['comb_score']
    test_df = test_df.reset_index(drop=True)
    ml_df = ml_df.reset_index(drop=True)
    test_df['over_atk']=ml_df['blue_total_atk']-ml_df['red_total_def']
    test_df['over_def']=ml_df['blue_total_def']-ml_df['red_total_atk']
    test_df['atk_cnt']=ml_df['blue_atk_cnt']-ml_df['red_atk_cnt']
    test_df['def_cnt']=ml_df['blue_def_cnt']-ml_df['red_def_cnt']
    test_df['gold']=gold_ml_df['middle_gold'] * gold_ml_df['late_gold']
    features=test_df
    print(f"ML Features calculation finished. Feature shape: {features.shape}. Features: {features.iloc[0].tolist()}")
    return features

def dmg_weight_chart_comment(blue_team,red_team,gold_ml_df,df,dmg_rate_df):
    comment_code=''
    # 1 <- 변경예정
    if ml_features(blue_team,red_team,gold_ml_df,df,dmg_rate_df)['over_atk'].iloc[0] >= 1 :
        comment_code='충만'
    elif ml_features(blue_team,red_team,gold_ml_df,df,dmg_rate_df)['over_atk'].iloc[0] <= -1:
        comment_code='부족'
    else:
        comment_code='적정'
    if ml_features(blue_team,red_team,gold_ml_df,df,dmg_rate_df)['over_def'].iloc[0] >= 1 :
        comment_code_3='충만'
    elif ml_features(blue_team,red_team,gold_ml_df,df,dmg_rate_df)['over_def'].iloc[0] <= -1:
        comment_code_3='부족'
    else:
        comment_code_3='적정'
    ml_temp_blue_df=dmg_weight(blue_team,dmg_rate_df)
    blue_total_atk = sum([item[1] for item in ml_temp_blue_df])
    blue_total_def = sum([item[2] for item in ml_temp_blue_df])
    blue_temp_atk=[]
    blue_temp_def=[]
    for blue_i in ml_temp_blue_df:
        blue_temp_atk.append(blue_i[1]/blue_total_atk)
        blue_temp_def.append(blue_i[2]/blue_total_def)
    blue_atk_cnt=count_carry_lines(blue_temp_atk)
    blue_def_cnt=count_tank_lines(blue_temp_def)
    if blue_atk_cnt >= 4:
        comment_code_2 = '균형'
    elif blue_atk_cnt >=3:
        comment_code_2 = '편향'
    else :
        comment_code_2 = '집중'
    if blue_def_cnt >= 4:
        comment_code_4 = '균형'
    elif blue_def_cnt >=3:
        comment_code_4 = '편향'
    else :
        comment_code_4 = '집중'
    return [comment_code,comment_code_2,comment_code_3,comment_code_4]
