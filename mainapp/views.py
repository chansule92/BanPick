from django.http import HttpResponse
from django.template import loader
from django.db.models import Count, Sum, Subquery, OuterRef, Avg, Max,F, Q
import pandas as pd
from .models import champion_index
import MySQLdb
from django.shortcuts import render


conn = MySQLdb.connect(host='localhost', user='root', password='glemfk12', database='loldb')
game_list_query ="""SELECT Game_ID,Blue_Result, Red_Result
  FROM a_game
 WHERE League in ('LCK Spring 2024','LEC Spring Season 2024','LCS Spring 2024')"""

game_list_df = pd.read_sql(game_list_query, conn)


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
            champ_df=pd.read_sql(champ_query, conn)
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
                                       FROM a_game_ban
                                      UNION ALL 
                                     SELECT 'Pick' AS BP_DIV
                                          , Pick AS Champion
                                       FROM a_game_ban
                                  ) A
                            GROUP BY Champion
                         ) T1
                         LEFT OUTER JOIN 
                         ( WITH t1 AS
                           ( SELECT A.Game_ID
                                  , A.Champion
                                  , A.Team_Div
                                  , CASE WHEN A.Team_Div = 'Blue' THEN Blue_Result ELSE Red_Result END AS Result
                               FROM a_game_stat A
                                    INNER JOIN a_game B
                                 ON A.Game_ID = B.Game_ID 
                              WHERE A.Game_ID LIKE '%LCKSpring2024%'
                           )
                           SELECT A.Champion AS stan_champ
                                , B.Champion AS con_champ
                                , CASE WHEN A.Team_Div = B.Team_Div THEN 'Y' ELSE 'N' END AS Team_YN
                                , count(DISTINCT A.Game_ID) AS play_cnt
                                , count(DISTINCT CASE WHEN A.RESULT = 'Win' THEN A.Game_ID ELSE NULL END) AS win_cnt
                             FROM t1 A
                                  LEFT OUTER JOIN 
                                  t1 B
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
                            WHERE B.League in ('LCK Spring 2024','LEC Spring Season 2024','LCS Spring 2024')
                            GROUP BY A.Champion
                         ) T3
                      ON T1.Champion = T3.Champion
                ) M
          WHERE duo_play_cnt > 2
            AND BP > 9
       ) M1
 GROUP BY M1.Champion
      , M1.con_champ
"""
df = pd.read_sql(query, conn)
df['Champion'] = df['Champion'].str.lower()
df['con_champ'] = df['con_champ'].str.lower()
conn.close()


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
            Win_rate=0
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
            Win_rate=0
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
    if result[game]['BLUE'][1] == 'WIN':
        game_result=1
    else :
        game_result=0
    result_list=[sum1,sum2,sum3,sum4,sum5,sum6,sum7,sum8,sum9,sum10,game_result]
    df_list.append(result_list)
df_list
final_df=pd.DataFrame(df_list)
final_df.columns=['Blue_Ban','Blue_Pick','Blue_Winrate','Blue_Duoscore','Blue_Countscore','Red_Ban','Red_Pick','Red_Winrate','Red_Duoscore','Red_Countscore','Result']
features=final_df[['Blue_Ban','Blue_Pick','Blue_Winrate','Blue_Duoscore','Blue_Countscore','Red_Ban','Red_Pick','Red_Winrate','Red_Duoscore','Red_Countscore']]
result=final_df['Result']

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
            Win_rate=0
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
            Win_rate=0
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
    result = [[sum1,sum2,sum3,sum4,sum5,sum6,sum7,sum8,sum9,sum10]]
    result
    features=pd.DataFrame(result)
    features.columns=['Blue_Ban','Blue_Pick','Blue_Winrate','Blue_Duoscore','Blue_Countscore','Red_Ban','Red_Pick','Red_Winrate','Red_Duoscore','Red_Countscore']
    ml_features=scaler.transform(features)
    result=model.predict_proba(ml_features)
    return [round(result[0][0]*100,2),round(result[0][1]*100,2)]

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
    print(blue_team)
    print(red_team)
    result_df = []
    result_df = process_teams(blue_team, red_team)  # Replace this with your existing logic to process the teams
    print(result_df)
    context = {
        "student_information": student_information,
        "pick": pick,
        "blue_team": blue_team,
        "red_team": red_team,
        "value": result_df,
    }
    return render(request, 'mainapp/index.html', context)


