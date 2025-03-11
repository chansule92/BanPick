from django.db import connection
import pandas as pd
from .models import champion_index
from django.shortcuts import render
import plotly.graph_objects as go
import numpy as np
import random
import plotly.express as px

#conn = MySQLdb.connect(host='ChocoPi.mysql.pythonanywhere-services.com', user='ChocoPi', password='glemfk12@', database='ChocoPi$loldb')
game_list_query ="""SELECT Game_ID,Blue_Result, Red_Result
  FROM a_game
 WHERE Ver in ('v15.1','v15.2','v15.3','v15.4','v15.5')"""

game_list_df = pd.read_sql(game_list_query, connection)


game_list=game_list_df['Game_ID'].to_list()
result={}
Team_div = ['BLUE','RED']
Position_div = ['TOP','JUNGLE','MID','ADC','SUPPORT']
result={}
for i in game_list:
    team_id={}
    for j in Team_div:
        temp_list=[]
        if j =='BLUE':
            game_result=game_list_df[game_list_df['Game_ID']==i]['Blue_Result'].values[0]
        else :
            game_result=game_list_df[game_list_df['Game_ID']==i]['Red_Result'].values[0]
        for k in Position_div:
            champ_query="""SELECT Champion FROM a_game_stat where Game_ID = '{}' and Team_Div = '{}' and Role = '{}';""".format(i,j,k)
            champ_df=pd.read_sql(champ_query, connection)
            temp_list.append((champ_df['Champion'].values)[0])
            team_id[j]=[temp_list,game_result]
            result[i]=team_id
query = """
SELECT M1.Champion
     , M1.con_champ
     , MAX(M1.BP) AS BP
     , MAX(M1.Ban) AS Ban
     , MAX(M1.Pick) AS Pick
     , MAX(M1.total_win_rate) AS Win_rate
     , CASE WHEN MAX(M1.duo_score) = 0 THEN min(M1.duo_score) ELSE Max(M1.duo_score) end AS Duo_Score
     , CASE WHEN MAX(M1.count_score) = 0 THEN Min(M1.count_score) ELSE max(M1.count_score) END AS Count_Score
  FROM ( SELECT M.Champion
              , M.con_champ
              , M.Team_YN
              , M.BP
              , M.Ban
              , M.Pick
              , M.total_win_cnt
              , M.total_win_rate
              , M.duo_play_cnt
              , M.duo_win_cnt
              , M.duo_win_rate
              , CASE WHEN Team_YN = 'Y' THEN M.duo_win_rate - M.total_win_rate ELSE 0 END AS duo_score
              , CASE WHEN Team_YN = 'N' THEN M.duo_win_rate - M.total_win_rate ELSE 0 END AS count_score
           FROM ( SELECT T1.Champion
                       , T2.con_champ
                       , T2.Team_YN
                       , T1.BP
                       , T1.Ban
                       , T1.Pick
                       , ifnull(T3.win_cnt,0) AS total_win_cnt
                       , ROUND(ifnull(T3.win_cnt,0)/T1.Pick*100,2) AS total_win_rate
                       , ifnull(T2.play_cnt,0) AS duo_play_cnt
                       , ifnull(T2.win_cnt,0) AS duo_win_cnt
                       , ROUND(ifnull(T2.win_cnt,0)/ifnull(T2.play_cnt,0)*100,2) AS duo_win_rate
                    FROM ( SELECT Champion
                                , count(Champion) AS BP
                                , SUM(CASE WHEN BP_DIV = 'Ban' THEN 1 ELSE 0 END) AS Ban
                                , SUM(CASE WHEN BP_DIV = 'Pick' THEN 1 ELSE 0 END) AS Pick
                             FROM ( SELECT 'Ban' AS BP_DIV
                                          , Ban AS Champion
                                       FROM a_game_ban A
                                            INNER JOIN a_game B
                                         ON A.Game_ID = B.Game_ID
                                      WHERE B.Ver in ('v15.1','v15.2','v15.3','v15.4','v15.5') 
                                      UNION ALL
                                     SELECT 'Pick' AS BP_DIV
                                          , Pick AS Champion
                                       FROM a_game_ban A
                                            INNER JOIN a_game B
                                         ON A.Game_ID = B.Game_ID
                                      WHERE B.Ver in ('v15.1','v15.2','v15.3','v15.4','v15.5') 
                                  ) A
                            GROUP BY Champion
                         ) T1
                         LEFT OUTER JOIN
                         ( SELECT A.Champion AS stan_champ
                                , B.Champion AS con_champ
                                , CASE WHEN A.Team_Div = B.Team_Div THEN 'Y' ELSE 'N' END AS Team_YN
                                , count(DISTINCT A.Game_ID) AS play_cnt
                                , count(DISTINCT CASE WHEN A.RESULT = 'Win' THEN A.Game_ID ELSE NULL END) AS win_cnt
                             FROM ( SELECT A.Game_ID
                                         , A.Champion
                                         , A.Team_Div
                                         , CASE WHEN A.Team_Div = 'Blue' THEN Blue_Result ELSE Red_Result END AS Result
                                      FROM a_game_stat A
                                           INNER JOIN a_game B
                                        ON A.Game_ID = B.Game_ID
                                     WHERE B.Ver in ('v15.1','v15.2','v15.3','v15.4','v15.5') 
                                  ) A
                                  LEFT OUTER JOIN
                                  ( SELECT A.Game_ID
                                         , A.Champion
                                         , A.Team_Div
                                         , CASE WHEN A.Team_Div = 'Blue' THEN Blue_Result ELSE Red_Result END AS Result
                                      FROM a_game_stat A
                                           INNER JOIN a_game B
                                        ON A.Game_ID = B.Game_ID
                                     WHERE B.Ver in ('v15.1','v15.2','v15.3','v15.4','v15.5') 
                                  ) B
                               ON A.Game_ID = B.Game_ID
                              AND A.Champion != B.Champion
                            GROUP BY A.Champion
                                , B.Champion
                                , CASE WHEN A.Team_Div = B.Team_Div THEN 'Y' ELSE 'N' END
                         ) T2
                      ON T1.Champion = T2.stan_Champ
                         LEFT OUTER JOIN
                         ( SELECT A.Champion
                                , sum(CASE WHEN A.Team_Div = 'Blue' AND B.Blue_Result = 'Win' THEN 1
                                           WHEN A.Team_Div = 'Red' AND B.Red_result = 'Win' THEN 1 ELSE 0 END) AS win_cnt
                             FROM a_game_stat A
                                  INNER JOIN a_game B
                               ON A.Game_ID = B.Game_ID
                            WHERE B.Ver in ('v15.1','v15.2','v15.3','v15.4','v15.5') 
                            GROUP BY A.Champion
                         ) T3
                      ON T1.Champion = T3.Champion
                ) M
          WHERE 1=1
            /* AND duo_play_cnt > 2
            AND BP > 9 */
       ) M1
 GROUP BY M1.Champion
      , M1.con_champ
"""
df = pd.read_sql(query.replace('\n',' '), connection)

df['Champion'] = df['Champion'].str.lower()
df['con_champ'] = df['con_champ'].str.lower()


query2="""SELECT B.Champion
     , A.Gold_Data
     , A.CS_Data
  FROM a_game_timeline A
       INNER JOIN a_game_stat B
    ON A.game_ID = B.Game_ID
   AND A.Team_Div = B.Team_Div
   AND A.ROLE = B.Role
 WHERE A.Game_ID IN (SELECT game_ID FROM a_game WHERE Ver IN ('v15.1','v15.2','v15.3','v15.4','v15.5')) """
df2 = pd.read_sql(query2, connection)
df2['Champion'] = df2['Champion'].str.lower()

query3="""
SELECT F.Champion
     , F.avg_dpm * Ad_rate AS AD_p
     , F.avg_dpm * AP_rate AS AP_p
     , F.avg_dpm * TD_rate AS TD_p
     , F.avg_dpm
     , F.tank_death
     , F.tank_time
     , F.deal_death
     , F.deal_time
  FROM ( SELECT CASE WHEN A.ROLE = 'SUPPORT' THEN concat(A.Champion,'_',A.ROLE) ELSE A.Champion end AS Champion
              , round(avg(A.DPM),2) AS avg_dpm
              , round(SUM(A.`Physical Damage`) / SUM(A.`Total damage to Champion`),2) AS AD_rate
              , round(SUM(A.`Magic Damage`) / SUM(A.`Total damage to Champion`) ,2) AS AP_rate
              , round(SUM(A.`True Damage`) / SUM(A.`Total damage to Champion`) ,2) AS TD_rate
              , SUM(CASE WHEN A.ROLE = 'JUNGLE' THEN A.`Total damage taken` * 0.7 ELSE A.`Total damage taken` END) / (SUM(A.Deaths) + count(A.Champion))  AS tank_death
              , avg(ROUND(CASE WHEN A.ROLE = 'JUNGLE' THEN A.`Total damage taken` * 0.7 ELSE A.`Total damage taken` END / ROUND((LEFT(B.Game_Time,2)*60 + RIGHT(B.Game_Time,2)) / 60,2))) AS tank_time
              , SUM(A.`Total damage to Champion`) / (SUM(A.Deaths) + count(A.Champion))  AS deal_death
              , round(avg(A.DPM),2) AS deal_time
           FROM a_game_stat A
                INNER JOIN a_game B
             ON A.Game_ID = B.Game_ID 
          WHERE B.Ver IN ('v15.1','v15.2','v15.3','v15.4','v15.5')
          GROUP BY CASE WHEN A.ROLE = 'SUPPORT' THEN concat(A.Champion,'_',A.ROLE) ELSE A.Champion end
       ) F
"""
sql2 = """
SELECT A.Game_ID 
     , B.Champion 
     , B.Team_Div 
     , B.Role
     , A.Blue_Result 
     , A.Red_Result 
  FROM a_game A
       INNER JOIN 
       a_game_stat B
    ON A.Game_ID = B.Game_ID 
 WHERE A.Ver IN ('v15.1','v15.2','v15.3','v15.4','v15.5')
"""
dmg_rate_df=pd.read_sql_query(query3,connection)
dmg_rate_df['Champion'] = dmg_rate_df['Champion'].str.lower()
avg_tank_death = dmg_rate_df['tank_death'].sum()/dmg_rate_df['tank_death'].count()
avg_tank_time = dmg_rate_df['tank_time'].sum()/dmg_rate_df['tank_time'].count()
dmg_rate_df['tank_death_norm']=dmg_rate_df['tank_death']/avg_tank_death
dmg_rate_df['tank_time_norm']=dmg_rate_df['tank_time']/avg_tank_time
dmg_rate_df['tank_norm_total'] = dmg_rate_df['tank_death_norm'] + dmg_rate_df['tank_time_norm']
avg_deal_death = dmg_rate_df['deal_death'].sum()/dmg_rate_df['deal_death'].count()
avg_deal_time = dmg_rate_df['deal_time'].sum()/dmg_rate_df['deal_time'].count()
dmg_rate_df['deal_death_norm']=dmg_rate_df['deal_death']/avg_deal_death
dmg_rate_df['deal_time_norm']=dmg_rate_df['deal_time']/avg_deal_time
dmg_rate_df['deal_norm_total'] = dmg_rate_df['deal_death_norm'] + dmg_rate_df['deal_time_norm']
dmg_rate_df['Champion']=dmg_rate_df['Champion'].str.lower()

df_list=[]
for game in game_list_df['Game_ID'].values:
    Blue_Team=result[game]['BLUE'][0]
    Red_Team=result[game]['RED'][0]
    blue_temp_list=[]
    for k in Blue_Team:
        k=k.lower()
        try:
            Ban=max(df[df['Champion']==k]['Ban'])
        except ValueError:
            Ban=0
        try:
            Pick=max(df[df['Champion']==k]['Pick'])
        except ValueError:
            Pick=0
        try:
            Win_rate=max(df[df['Champion']==k]['Win_rate'])
        except ValueError:
            Win_rate=50
        Duo_score=0
        Count_score=0
        for i in Blue_Team:
            i=i.lower()
            if k==i:
                pass
            else :
                if len(df[(df['Champion']==k)&(df['con_champ']==i)]['Duo_Score']) == 0:
                    pass
                else:
                    try:
                        Duo_score = Duo_score + float(df[(df['Champion']==k)&(df['con_champ']==i)]['Duo_Score'].iloc[0])
                    except IndexError:
                        Duo_score = 0
        for j in Red_Team:
            j=j.lower()
            if k==j:
                pass
            else :
                if len(df[(df['Champion']==k)&(df['con_champ']==j)]['Count_Score']) == 0:
                    pass
                else:
                    try:
                        Count_score = Count_score+ float(df[(df['Champion']==k)&(df['con_champ']==j)]['Count_Score'].iloc[0])
                    except IndexError:
                        Count_score = 0
        blue_temp_list.append([Ban,Pick,Win_rate,round(Duo_score,2),round(Count_score,2)])
    sum1=0
    sum2=0
    sum3=0
    sum4=0
    sum5=0
    for i in blue_temp_list:
        sum1+=i[0]
        sum2+=i[1]
        sum3+=i[2]
        sum4+=i[3]
        sum5+=i[4]
    red_temp_list=[]
    for k in Red_Team:
        k=k.lower()
        try:
            Ban=max(df[df['Champion']==k]['Ban'])
        except ValueError:
            Ban=0
        try:
            Pick=max(df[df['Champion']==k]['Pick'])
        except ValueError:
            Pick=0
        try:
            Win_rate=max(df[df['Champion']==k]['Win_rate'])
        except ValueError:
            Win_rate=50
        Duo_score=0
        Count_score=0
        for i in Red_Team:
            i=i.lower()
            if k==i:
                pass
            else :
                if len(df[(df['Champion']==k)&(df['con_champ']==i)]['Duo_Score']) == 0:
                    pass
                else:
                    try:
                        Duo_score = Duo_score + float(df[(df['Champion']==k)&(df['con_champ']==i)]['Duo_Score'].iloc[0])
                    except IndexError:
                        Duo_score = 0
        for j in Blue_Team:
            j=j.lower()
            if k==j:
                pass
            else :
                if len(df[(df['Champion']==k)&(df['con_champ']==j)]['Count_Score']) == 0:
                    pass
                else:
                    try:
                        Count_score = Count_score+ float(df[(df['Champion']==k)&(df['con_champ']==j)]['Count_Score'].iloc[0])
                    except IndexError:
                        Count_score = 0
        red_temp_list.append([Ban,Pick,Win_rate,round(Duo_score,2),round(Count_score,2)])
    sum6=0
    sum7=0
    sum8=0
    sum9=0
    sum10=0
    for i in red_temp_list:
        sum6+=i[0]
        sum7+=i[1]
        sum8+=i[2]
        sum9+=i[3]
        sum10+=i[4]
    if result[game]['BLUE'][1] == 'WIN':
        game_result=1
    else :
        game_result=0
    result_list=[sum3,sum4,sum5,sum8,sum9,sum10,game_result]
    df_list.append(result_list)
df_list
final_df=pd.DataFrame(df_list)
final_df.columns=['Blue_Winrate','Blue_Duoscore','Blue_Countscore','Red_Winrate','Red_Duoscore','Red_Countscore','Result']
features=final_df[['Blue_Winrate','Blue_Duoscore','Blue_Countscore','Red_Winrate','Red_Duoscore','Red_Countscore']]
result=final_df['Result']




cham_powergraph=[]
champion_list=df2['Champion'].unique()
for cham in champion_list:
    gold_df=df2[df2['Champion']==cham]
    time_gold=[]
    for i in gold_df['Gold_Data']:
        data=eval(i)
        temp_list=[]
        for j in range(0,len(data)-1):
            if j != 0:
                temp_list.append(int(data[j])-int(data[j-1]))
        time_gold.append(temp_list)
    power_graph=[]
    for k in range(0,30):
        temp=[]
        for u in time_gold:
            try:
                temp.append(u[k])
            except:
                break
        if len(temp) != 0:
            value=round(sum(temp)/len(temp),2)
        power_graph.append(value)
    cham_powergraph.append([cham,power_graph])
power_df=pd.DataFrame(cham_powergraph)
power_df.columns = ['Champion','Gold_Data']

"""
from sklearn.model_selection import train_test_split

train_features, test_features, train_labels, test_labels = train_test_split(features, result)

from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()

train_features = scaler.fit_transform(train_features)
test_features = scaler.transform(test_features)

from sklearn.linear_model import LogisticRegression

model = LogisticRegression()
model.fit(train_features, train_labels)

def process_teams(Blue_Team, Red_Team):
    blue_temp_list=[]
    for k in Blue_Team:
        try:
            Ban=max(df[df['Champion']==k]['Ban'])
        except ValueError:
            Ban=0
        try:
            Pick=max(df[df['Champion']==k]['Pick'])
        except ValueError:
            Pick=0
        try:
            Win_rate=max(df[df['Champion']==k]['Win_rate'])
        except ValueError:
            Win_rate=50
        Duo_score=0
        Count_score=0
        for i in Blue_Team:
            if k==i:
                pass
            else :
                if len(df[(df['Champion']==k)&(df['con_champ']==i)]['Duo_Score']) == 0:
                    pass
                else:
                    try:
                        Duo_score = Duo_score + float(df[(df['Champion']==k)&(df['con_champ']==i)]['Duo_Score'].iloc[0])
                    except IndexError:
                        Duo_score = 0
        for j in Red_Team:
            if k==j:
                pass
            else :
                if len(df[(df['Champion']==k)&(df['con_champ']==j)]['Count_Score']) == 0:
                    pass
                else:
                    try:
                        Count_score = Count_score+ float(df[(df['Champion']==k)&(df['con_champ']==j)]['Count_Score'].iloc[0])
                    except IndexError:
                        Count_score = 0
        blue_temp_list.append([Ban,Pick,Win_rate,round(Duo_score,2),round(Count_score,2)])
    #blue_temp_list=[0 if pd.isna(x) else x for x in blue_temp_list]
    sum1=0
    sum2=0
    sum3=0
    sum4=0
    sum5=0
    for i in blue_temp_list:
        sum1+=i[0]
        sum2+=i[1]
        sum3+=i[2]
        sum4+=i[3]
        sum5+=i[4]
    red_temp_list=[]
    for k in Red_Team:
        try:
            Ban=max(df[df['Champion']==k]['Ban'])
        except ValueError:
            Ban=0
        try:
            Pick=max(df[df['Champion']==k]['Pick'])
        except ValueError:
            Pick=0
        try:
            Win_rate=max(df[df['Champion']==k]['Win_rate'])
        except ValueError:
            Win_rate=50
        Duo_score=0
        Count_score=0
        for i in Red_Team:
            if k==i:
                pass
            else :
                if len(df[(df['Champion']==k)&(df['con_champ']==i)]['Duo_Score']) == 0:
                    pass
                else:
                    try:
                        Duo_score = Duo_score + float(df[(df['Champion']==k)&(df['con_champ']==i)]['Duo_Score'].iloc[0])
                    except IndexError:
                        Duo_score = 0
        for j in Blue_Team:
            if k==j:
                pass
            else :
                if len(df[(df['Champion']==k)&(df['con_champ']==j)]['Count_Score']) == 0:
                    pass
                else:
                    try:
                        Count_score = Count_score+ float(df[(df['Champion']==k)&(df['con_champ']==j)]['Count_Score'].iloc[0])
                    except IndexError:
                        Count_score = 0
        red_temp_list.append([Ban,Pick,Win_rate,round(Duo_score,2),round(Count_score,2)])
    sum6=0
    sum7=0
    sum8=0
    sum9=0
    sum10=0
    for i in red_temp_list:
        sum6+=i[0]
        sum7+=i[1]
        sum8+=i[2]
        sum9+=i[3]
        sum10+=i[4]
    result = [[sum3,sum4,sum5,sum8,sum9,sum10]]
    result
    features=pd.DataFrame(result)
    features.columns=['Blue_Winrate','Blue_Duoscore','Blue_Countscore','Red_Winrate','Red_Duoscore','Red_Countscore']
    ml_features=scaler.transform(features)
    result=model.predict_proba(ml_features)
    return [round(result[0][0]*100,2),round(result[0][1]*100,2),features]
"""
def power_graph(Cham_list):
    powerdata_list=[]
    for i in Cham_list:
        if len(power_df[power_df['Champion']==i])!=0:
            temp_str=''
            temp_str=temp_str+power_df[power_df['Champion']==i].iloc[0][0]+str(power_df[power_df['Champion']==i].iloc[0][1])
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
    # Plotly를 사용한 라인 차트 생성

    max_value = max(power_df2['Value'])
    # Y축 최대값을 데이터 최대값과 1000 중 큰 값으로 설정
    y_max = max(max_value, 1000)
    fig = px.line(power_df2,
                  x='Time',
                  y='Value',
                  color='Champion',
                  title='Champion Power Over Time(30min)',
                  labels={'Time': 'Time',
                         'Value': 'Earn Gold',
                         'Champion': 'Champion'},
                  markers=True)
    # 차트 레이아웃 커스터마이징
    fig.update_layout(
        plot_bgcolor='#1d1e33',
        paper_bgcolor='#0a0e21',
        font=dict(
                family='Arial',
                color='white'         # 텍스트 색상
            ),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02
        ),
        hovermode='x unified'
    )
    # 축 스타일 설정
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
    chart_code=(fig.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            div_id='THIS_IS_FIGID'+str(random.random())))
    return chart_code

def dmg_weight(cham_list):
    dmg_weight = []
    cham_list[-1]=cham_list[-1]+'_support'
    for i in cham_list:
        deal_norm_total = dmg_rate_df[dmg_rate_df['Champion'] == i]['deal_norm_total'].iloc[0]
        tank_norm_total = dmg_rate_df[dmg_rate_df['Champion'] == i]['tank_norm_total'].iloc[0]
        champ_name = i.replace('_support', '')  # '_support' 자동 제거
        dmg_weight.append([champ_name, deal_norm_total, tank_norm_total])
    
    # 'Attack'이 'Defence' 위로 표시되도록 순서 조정
    attribute = ['Defence', 'Attack']
    
    # 총합 계산
    total_attack = round(sum([item[1] for item in dmg_weight]),2)
    total_defence = round(sum([item[2] for item in dmg_weight]),2)
    
    # 공격과 방어 데이터를 각각 [공격, 방어] 순으로 저장
    values = [[round(item[2], 1), round(item[1], 1)] for item in dmg_weight]
    ratios = [[round(item[2]/total_attack*100, 2), round(item[1]/total_defence*100, 2)] for item in dmg_weight]
    
    # 'Attack'이 첫 번째, 'Defence'가 두 번째로 위치하도록 값 순서 재배열
    values = [[v[0], v[1]] for v in values]
    ratios = [[r[0], r[1]] for r in ratios]
    
    # 포지션 및 색상 설정
    colors = ['#FF6F61', '#7DCEA0', '#5DADE2', '#AF7AC5', '#F4D03F']
    
    fig = go.Figure()
    
    # 스택형 바 차트 생성
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
    # 레이아웃 설정
    fig.update_layout(
        barmode='stack',
        title='Team Deal & Tank ratio',
        template='plotly_dark',
        plot_bgcolor='#0a0e21',
        paper_bgcolor='#0a0e21',
        font=dict(color='white'),
        showlegend=False,  # 범례 숨김
        height=400
    )
    for i, attr in enumerate(attribute):  # Attack / Defence 각각 처리
        total_value = total_attack if attr == 'Attack' else total_defence
        fig.add_annotation(
            x=max_value * 1.02,  # 바 끝보다 살짝 오른쪽
            y=i+0.3,  # 해당 바의 y 위치
            text=f"Total: {total_value}",  # 표시할 텍스트
            showarrow=False,  # 화살표 제거
            font=dict(color="white", size=14, family="Arial", weight="bold"),
            bgcolor="rgba(0, 0, 0, 0.5)",  # 배경 투명한 검은색으로 가독성 증가
        )
    
    chart_code=(fig.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            div_id='THIS_IS_FIGID'+str(random.random())))
    return chart_code

def damage_distribution(champion_list):
    # 챔피언 필터링
    champion_list[-1]=champion_list[-1]+'_support'
    selected_df = dmg_rate_df[dmg_rate_df['Champion'].isin(champion_list)]
    
    # 총합 계산
    total_AD_p = selected_df['AD_p'].sum()
    total_AP_p = selected_df['AP_p'].sum()
    total_TD_p = selected_df['TD_p'].sum()
    
    # 데이터 준비
    values = [total_AD_p, total_AP_p, total_TD_p]
    labels = ['AD', 'AP', 'True Damage']
    colors = ['#FF6F61', '#5DADE2', '#F4D03F']  # AD(빨강), AP(파랑), TD(노랑)

    # 파이 차트 생성
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        textinfo='label+percent',
        insidetextorientation='radial',
        marker=dict(colors=colors)
    )])

    # 레이아웃 설정
    fig.update_layout(
        title="Damage Type Distribution",
        plot_bgcolor='#0a0e21',
        paper_bgcolor='#0a0e21',
        font=dict(color='white'),
        showlegend=False,
        width=500,  # 너비 조절
        height=400  # 높이 조절
    )

    chart_code=(fig.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            div_id='THIS_IS_FIGID'+str(random.random())))
    return chart_code

def index(request):
    student_information = champion_index.objects.values('EN', 'KR')
    pick = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    blue_team = []
    red_team = []

    if request.method == 'POST':
        for i in range(5):
            blue_team.append(request.POST.get(f'champion{i}'))
        for i in range(5, 10):
            red_team.append(request.POST.get(f'champion{i}'))

    context = {
        "student_information": student_information,
        "pick": pick,
        "blue_team": blue_team,
        "red_team": red_team
    }
    return render(request, 'mainapp/index.html', context)

def result(request):
    if request.method == 'POST':
        selected_champions = request.POST.getlist('champion')
    stats = []
    for i in selected_champions:
        stats.append([df[df['Champion']==i.replace('%20',' ')]['Ban'].head(1).values,df[df['Champion']==i.replace('%20',' ')]['Pick'].head(1).values,df[df['Champion']==i.replace('%20',' ')]['Win_rate'].head(1).values])
    temp_chart_code=[]
    count=0
    blue_team = []
    red_team = []
    for i in selected_champions:
        if count < 5:
            blue_team.append(i.replace('%20',' '))
        else:
            red_team.append(i.replace('%20',' '))
        count=count+1
    blue_duo=[]
    blue_count=[]
    result_df = []
#    result_df = process_teams(blue_team, red_team)  # Replace this with your existing logic to process the teams
    for i in blue_team:
        blue_duo_2=[]
        blue_count_2=[]
        for j in blue_team:
            if i!=j:
                if len(df[(df['Champion'] == i) & (df['con_champ'] == j)]['Duo_Score']) != 0:
                    blue_duo_2.append(df[(df['Champion'] == i) & (df['con_champ'] == j)]['Duo_Score'].iloc[0])
                else :
                    blue_duo_2.append(0)
            else:
                blue_duo_2.append(0)
        blue_duo.append(blue_duo_2)
        for k in red_team:
            if len(df[(df['Champion'] == i) & (df['con_champ'] == k)]['Count_Score']) != 0:
                blue_count_2.append(df[(df['Champion'] == i) & (df['con_champ'] == k)]['Count_Score'].iloc[0])
            else :
                blue_count_2.append(0)
        blue_count.append(blue_count_2)
    red_duo=[]
    red_count=[]
    for i in red_team:
        red_duo_2=[]
        red_count_2=[]
        for j in red_team:
            if i!=j:
                if len(df[(df['Champion'] == i) & (df['con_champ'] == j)]['Duo_Score']) != 0:
                    red_duo_2.append(df[(df['Champion'] == i) & (df['con_champ'] == j)]['Duo_Score'].iloc[0])
                else :
                    red_duo_2.append(0)
            else:
                red_duo_2.append(0)
        red_duo.append(red_duo_2)
        for k in blue_team:
            if len(df[(df['Champion'] == i) & (df['con_champ'] == k)]['Count_Score']) != 0:
                red_count_2.append(df[(df['Champion'] == i) & (df['con_champ'] == k)]['Count_Score'].iloc[0])
            else :
                red_count_2.append(0)
        red_count.append(red_count_2)
    chart_num=0
    custom_colorscale = [
        [0, '#FF6384'],      # 최소값
        [0.5, 'white'],      # 중간값 (0)
        [1, '#36A2EB']       # 최대값
    ]
    temp_chart_code = []
    chart_num = -1  # 0부터 시작하도록 -1로 초기화

    for i in [blue_duo, blue_count, red_duo, red_count]:
        chart_num = chart_num + 1
        temp_data = np.array(i)
        temp_df = pd.DataFrame(temp_data)

        # 열과 행 이름 설정
        if chart_num in (0, 1):
            temp_df.index = blue_team
        else:
            temp_df.index = red_team

        if chart_num in (1, 2):
            temp_df.columns = red_team
        else:
            temp_df.columns = blue_team

        # Plotly figure 생성
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
            div_id=f'THIS_IS_FIGID{chart_num}'
        ))
    temp_chart_code.append(create_power_graph(power_graph(blue_team)))
    temp_chart_code.append(create_power_graph(power_graph(red_team)))
    temp_chart_code.append(dmg_weight(blue_team))
    temp_chart_code.append(dmg_weight(red_team))
    temp_chart_code.append(damage_distribution(blue_team))
    temp_chart_code.append(damage_distribution(red_team))
    test=power_df

    context = {
        'champions': selected_champions,
        'stats': stats,
        'temp_chart_code': temp_chart_code,
        "value": result_df,
        "test":test
    }
    return render(request, 'mainapp/result.html', context)


