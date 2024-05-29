from django.http import HttpResponse
from django.template import loader
from django.db.models import Count, Sum, Subquery, OuterRef, Avg, Max,F, Q
import pandas as pd
from .models import champion_index
import MySQLdb

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
conn.close()


df_list=[]
for game in game_list_df['Game_ID'].values:
    Blue_Team=result[game]['BLUE'][0]
    Red_Team=result[game]['RED'][0]
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
    blue_final_list=[sum1,sum2,sum3,sum4,sum5]
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
    sum1=0
    sum2=0
    sum3=0
    sum4=0
    sum5=0
    red_final_list=[]
    for i in red_temp_list:
        sum1+=i[0]
        sum2+=i[1]
        sum3+=i[2]
        sum4+=i[3]
        sum5+=i[4]
    red_final_list.append(sum1)
    red_final_list.append(sum2)
    red_final_list.append(sum3)
    red_final_list.append(sum4)
    red_final_list.append(sum5)
    if result[game]['BLUE'][1] == 'WIN':
        blue_final_list.append(1)
        red_final_list.append(0)
    else :
        blue_final_list.append(0)
        red_final_list.append(1)
    df_list.append(blue_final_list)
    df_list.append(red_final_list)
final_df=pd.DataFrame(df_list)
final_df.columns=['Ban','Pick','Win_rate','Duo_Score','Count_Score','Result']
final_df
features=final_df[['Pick','Win_rate','Duo_Score','Count_Score']]
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


def index(request):
    student_information=champion_index.objects.values('EN','KR')
    template = loader.get_template("mainapp/index.html")
    pick = [0,1,2,3,4,5,6,7,8,9]
    champion0 = request.POST.get('champion0')
    champion1 = request.POST.get('champion1')
    champion2 = request.POST.get('champion2')
    champion3 = request.POST.get('champion3')
    champion4 = request.POST.get('champion4')
    champion5 = request.POST.get('champion5')
    champion6 = request.POST.get('champion6')
    champion7 = request.POST.get('champion7')
    champion8 = request.POST.get('champion8')
    champion9 = request.POST.get('champion9')
    Blue_Team = [champion0,champion1,champion2,champion3,champion4]
    Red_Team = [champion5,champion6,champion7,champion8,champion9]
    result_df={}
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
    blue_final_list=[sum1,sum2,sum3,sum4,sum5]
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
    sum1=0
    sum2=0
    sum3=0
    sum4=0
    sum5=0
    red_final_list=[]
    for i in red_temp_list:
        sum1+=i[0]
        sum2+=i[1]
        sum3+=i[2]
        sum4+=i[3]
        sum5+=i[4]
    red_final_list.append(sum1)
    red_final_list.append(sum2)
    red_final_list.append(sum3)
    red_final_list.append(sum4)
    red_final_list.append(sum5)
    blue_df=pd.DataFrame([blue_final_list])
    red_df=pd.DataFrame([red_final_list])
    blue_df.columns=['Ban','Pick','Win_rate','Duo_Score','Count_Score']
    red_df.columns=['Ban','Pick','Win_rate','Duo_Score','Count_Score']
    result_df={'BLUE': blue_df, 'RED': red_df}
    ml_result=[]
    temp_list=[]
    blue_features=result_df['BLUE'][['Pick','Win_rate','Duo_Score','Count_Score']]
    blue_features=scaler.transform(blue_features)
    temp_list.append(model.predict_proba(blue_features)[0][0])
    red_features=result_df['RED'][['Pick','Win_rate','Duo_Score','Count_Score']]
    red_features=scaler.transform(red_features)
    temp_list.append(model.predict_proba(red_features)[0][0])
    ml_result.append(temp_list)
    ml_result
    context = {
        "student_information":student_information,
        "pick":pick,
        "value" : ml_result
    }
    return HttpResponse(template.render(context,request))

