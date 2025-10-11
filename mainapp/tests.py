          full_data_query = """
          SELECT t1.Game_ID
               , t1.Blue_Result
               , t1.Red_Result
               , t2.Team_Div
               , t2.Role
               , t2.Champion
            FROM banpick.a_game t1
                 INNER JOIN banpick.a_game_stat t2 
              ON t1.Game_ID = t2.Game_ID
           WHERE t1.Ver LIKE 'v15%'
           ORDER BY t1.Game_ID
               , t2.Team_Div
               , t2.Role;
          """
          
          # DB에서 모든 데이터를 한 번에 로드합니다.
          df_full = pd.read_sql(full_data_query, connection)
          
          # 필요한 열의 이름을 소문자로 표준화하는 것이 좋습니다.
          df_full.columns = df_full.columns.str.lower()
          
          df_champs = df_full.groupby(['game_id', 'team_div'])['champion'].apply(list).reset_index(name='team_composition')
          
          # 결과(Result) 열을 각 팀별로 가져옵니다.
          df_results = df_full[['game_id', 'team_div', 'blue_result', 'red_result']].drop_duplicates()
          df_results['game_result'] = df_results.apply(
              lambda row: row['blue_result'] if row['team_div'] == 'BLUE' else row['red_result'], axis=1
          )
          df_results = df_results[['game_id', 'team_div', 'game_result']]
          
          # 두 데이터프레임을 병합합니다.
          df_final = pd.merge(df_champs, df_results, on=['game_id', 'team_div'])
          
          # 최종 'result' 딕셔너리 형태로 변환합니다.
          # (이 부분이 원래 코드의 최종 목적과 가장 비슷하게 데이터를 재구성합니다.)
          result = {}
          for game_id in df_final['game_id'].unique():
              game_data = df_final[df_final['game_id'] == game_id]
              
              team_data = {}
              for team in ['blue', 'red']:
                  team_row = game_data[game_data['team_div'] == team.upper()]
                  
                  if not team_row.empty:
                      # [챔피언 리스트, 결과] 형태로 저장
                      composition = team_row['team_composition'].values[0]
                      game_result = team_row['game_result'].values[0]
                      team_data[team.upper()] = [composition, game_result]
                      
              if team_data:
                  result[game_id] = team_data
          game_list = list(result.keys())
          query = """
          SELECT M1.Champion
              , M1.con_champ
              , MAX(M1.BP) AS BP
              , MAX(M1.Ban) AS Ban
              , MAX(M1.Pick) AS Pick
              , MAX(M1.total_WIN_rate) AS WIN_rate
              , CASE WHEN MAX(M1.duo_score) = 0 THEN min(M1.duo_score) ELSE Max(M1.duo_score) end AS duo_score
              , CASE WHEN MAX(M1.count_score) = 0 THEN Min(M1.count_score) ELSE max(M1.count_score) END AS count_score
           FROM ( SELECT M.Champion
                       , M.con_champ
                       , M.Team_YN
                       , M.BP
                       , M.Ban
                       , M.Pick
                       , M.total_WIN_cnt
                       , M.total_WIN_rate
                       , M.duo_play_cnt
                       , M.duo_WIN_cnt
                       , M.duo_WIN_rate
                       , CASE WHEN Team_YN = 'Y' THEN M.duo_WIN_rate - M.total_WIN_rate ELSE 0 END AS duo_score
                       , CASE WHEN Team_YN = 'N' THEN M.duo_WIN_rate - M.total_WIN_rate ELSE 0 END AS count_score
                    FROM ( SELECT T1.Champion
                                , T2.con_champ
                                , T2.Team_YN
                                , T1.BP
                                , T1.Ban
                                , T1.Pick
                                , COALESCE(T3.WIN_cnt,0) AS total_WIN_cnt
                                , CASE WHEN T1.Pick = 0 THEN 0 ELSE ROUND(COALESCE(CAST(T3.WIN_cnt AS NUMERIC),0)/T1.Pick*100,2) END AS total_WIN_rate
                                , COALESCE(T2.play_cnt,0) AS duo_play_cnt
                                , COALESCE(T2.WIN_cnt,0) AS duo_WIN_cnt
                                , CASE WHEN T2.play_cnt = 0 THEN 0 ELSE ROUND(COALESCE(CAST(T2.WIN_cnt AS NUMERIC),0)/COALESCE(T2.play_cnt,0)*100,2) END AS duo_WIN_rate
                             FROM ( SELECT Champion
                                         , count(Champion) AS BP
                                         , SUM(CASE WHEN BP_DIV = 'Ban' THEN 1 ELSE 0 END) AS Ban
                                         , SUM(CASE WHEN BP_DIV = 'Pick' THEN 1 ELSE 0 END) AS Pick
                                      FROM ( SELECT 'Ban' AS BP_DIV
                                                   , Ban AS Champion
                                                FROM banpick.a_game_ban A
                                                     INNER JOIN banpick.a_game B
                                                  ON A.Game_ID = B.Game_ID
                                               WHERE B.Ver like 'v15%'
                                               UNION ALL
                                              SELECT 'Pick' AS BP_DIV
                                                   , Pick AS Champion
                                                FROM banpick.a_game_ban A
                                                     INNER JOIN banpick.a_game B
                                                  ON A.Game_ID = B.Game_ID
                                               WHERE B.Ver like 'v15%'
                                           ) A
                                     GROUP BY Champion
                                  ) T1
                                  LEFT OUTER JOIN
                                  ( SELECT A.Champion AS stan_champ
                                         , B.Champion AS con_champ
                                         , CASE WHEN A.Team_Div = B.Team_Div THEN 'Y' ELSE 'N' END AS Team_YN
                                         , count(DISTINCT A.Game_ID) AS play_cnt
                                         , count(DISTINCT CASE WHEN A.RESULT = 'WIN' THEN A.Game_ID ELSE NULL END) AS WIN_cnt
                                      FROM ( SELECT A.Game_ID
                                                  , A.Champion
                                                  , A.Team_Div
                                                  , CASE WHEN A.Team_Div = 'BLUE' THEN Blue_Result ELSE Red_Result END AS Result
                                               FROM banpick.a_game_stat A
                                                    INNER JOIN banpick.a_game B
                                                 ON A.Game_ID = B.Game_ID
                                              WHERE B.Ver like 'v15%'
                                           ) A
                                           LEFT OUTER JOIN
                                           ( SELECT A.Game_ID
                                                  , A.Champion
                                                  , A.Team_Div
                                                  , CASE WHEN A.Team_Div = 'BLUE' THEN Blue_Result ELSE Red_Result END AS Result
                                               FROM banpick.a_game_stat A
                                                    INNER JOIN banpick.a_game B
                                                 ON A.Game_ID = B.Game_ID
                                              WHERE B.Ver like 'v15%'
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
                                         , sum(CASE WHEN A.Team_Div = 'BLUE' AND B.Blue_Result = 'WIN' THEN 1
                                                    WHEN A.Team_Div = 'RED' AND B.Red_result = 'WIN' THEN 1 ELSE 0 END) AS WIN_cnt
                                      FROM banpick.a_game_stat A
                                           INNER JOIN banpick.a_game B
                                        ON A.Game_ID = B.Game_ID
                                     WHERE B.Ver like 'v15%'
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
          df['champion'] = df['champion'].str.lower()
          df['con_champ'] = df['con_champ'].str.lower()

          query2="""SELECT B.Champion
              , A.Gold_Data
              , A.CS_Data
           FROM banpick.a_game_timeline A
                INNER JOIN banpick.a_game_stat B
             ON A.game_ID = B.Game_ID
            AND A.Team_Div = B.Team_Div
            AND A.ROLE = B.Role
            WHERE A.Game_ID IN (SELECT game_ID FROM banpick.a_game WHERE Ver like 'v15%') """
          df2 = pd.read_sql(query2, connection)
          df2['champion'] = df2['champion'].str.lower()

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
                       , round(SUM(A."Physical Damage") / SUM(A."Total damage to Champion"),2) AS AD_rate
                       , round(SUM(A."Magic Damage") / SUM(A."Total damage to Champion") ,2) AS AP_rate
                       , round(SUM(A."True Damage") / SUM(A."Total damage to Champion") ,2) AS TD_rate
                       , SUM(CASE WHEN A.ROLE = 'JUNGLE' THEN A."Total damage taken" * 0.7 ELSE A."Total damage taken" END) / (SUM(A.Deaths) + count(A.Champion))  AS tank_death
                       , avg(ROUND(CASE WHEN A.ROLE = 'JUNGLE' THEN A."Total damage taken" * 0.7 ELSE A."Total damage taken" END / ROUND((CAST(LEFT(B.Game_Time,2) AS NUMERIC)*60 + CAST(RIGHT(B.Game_Time,2) AS NUMERIC)) / 60,2))) AS tank_time
                       , SUM(A."Total damage to Champion") / (SUM(A.Deaths) + count(A.Champion))  AS deal_death
                       , round(avg(A.DPM),2) AS deal_time
                    FROM banpick.a_game_stat A
                         INNER JOIN banpick.a_game B
                      ON A.Game_ID = B.Game_ID 
                   WHERE B.Ver like 'v15%'
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
           FROM banpick.a_game A
                INNER JOIN 
                banpick.a_game_stat B
             ON A.Game_ID = B.Game_ID 
          WHERE A.Ver like 'v15%'
          """
          dmg_rate_df=pd.read_sql_query(query3,connection)
          dmg_rate_df['champion'] = dmg_rate_df['champion'].str.lower()
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
          dmg_rate_df['champion']=dmg_rate_df['champion'].str.lower()

          cham_powergraph=[]
          champion_list=df2['champion'].unique()
          for cham in champion_list:
             gold_df=df2[df2['champion']==cham]
             time_gold=[]
             for i in gold_df['gold_data']:
                 data=eval(i)
                 temp_list=[]
                 for j in range(0,len(data)-1):
                     if j != 0:
                         temp_list.append(int(data[j])-int(data[j-1]))
                 time_gold.append(temp_list)
             power_graph=[]
             for k in range(0,30):
                 temp=[]
                 value=0
                 for u in time_gold:
                     try:
                         temp.append(u[k])
                     except:
                         pass
                 if len(temp) != 0:
                     value=round(sum(temp)/len(temp),2)
                 power_graph.append(value)
             cham_powergraph.append([cham,power_graph])
          power_df=pd.DataFrame(cham_powergraph)
          power_df.columns = ['champion','gold_data']

          edu_ml=[]
          for i in game_list:
             sample_ml=[]
             sample=''
             blue_gold=utils.gold(result[i]['BLUE'][0],power_df)
             red_gold=utils.gold(result[i]['RED'][0],power_df)
             sample=pd.concat([blue_gold,red_gold],axis=1)
             sample.columns=['Time','blue_gold','-','red_gold']
             sample['diff_gold']=sample['blue_gold']-sample['red_gold']
          #    sample_ml.append(round(sample[sample['Time']=='early']['diff_gold'].iloc[0],2))
             sample_ml.append(round(sample[sample['Time']=='middle']['diff_gold'].iloc[0],2))
             try:
                 sample_ml.append(round(sample[sample['Time']=='late']['diff_gold'].iloc[0],2))
             except:
                 sample_ml.append(0)
             edu_ml.append(sample_ml)
          gold_ml_df=pd.DataFrame(edu_ml)
          gold_ml_df.columns = ['middle_gold','late_gold']
          gold_ml_df
