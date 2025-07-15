from django.db import connection
import pandas as pd
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    """데이터 로딩과 캐싱을 담당하는 클래스"""
    
    # 게임 버전 리스트를 상수로 정의
    GAME_VERSIONS = ['v15.1','v15.2','v15.3','v15.4','v15.5','v15.6','v15.7','v15.8','v15.9','v15.10','v15.11','v15.12','v15.13']
    
    def __init__(self):
        self.cache_timeout = 3600  # 1시간 캐시
    
    def _get_version_condition(self):
        """버전 조건을 문자열로 반환"""
        versions_str = "','".join(self.GAME_VERSIONS)
        return f"('{versions_str}')"
    
    def load_game_data(self):
        """게임 기본 데이터 로드"""
        cache_key = 'game_data'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        try:
            query = f"""SELECT Game_ID, Blue_Result, Red_Result
                       FROM a_game
                       WHERE Ver in {self._get_version_condition()}"""
            
            df = pd.read_sql(query, connection)
            cache.set(cache_key, df, self.cache_timeout)
            return df
        except Exception as e:
            logger.error(f"게임 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def load_champion_stats(self):
        """챔피언 통계 데이터 로드"""
        cache_key = 'champion_stats'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        try:
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
                                                  WHERE B.Ver in {self._get_version_condition()}
                                                  UNION ALL
                                                 SELECT 'Pick' AS BP_DIV
                                                      , Pick AS Champion
                                                   FROM a_game_ban A
                                                        INNER JOIN a_game B
                                                     ON A.Game_ID = B.Game_ID
                                                  WHERE B.Ver in {self._get_version_condition()}
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
                                                 WHERE B.Ver in {self._get_version_condition()}
                                              ) A
                                              LEFT OUTER JOIN
                                              ( SELECT A.Game_ID
                                                     , A.Champion
                                                     , A.Team_Div
                                                     , CASE WHEN A.Team_Div = 'Blue' THEN Blue_Result ELSE Red_Result END AS Result
                                                  FROM a_game_stat A
                                                       INNER JOIN a_game B
                                                    ON A.Game_ID = B.Game_ID
                                                 WHERE B.Ver in {self._get_version_condition()}
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
                                        WHERE B.Ver in {self._get_version_condition()}
                                        GROUP BY A.Champion
                                     ) T3
                                  ON T1.Champion = T3.Champion
                            ) M
                      WHERE 1=1
                   ) M1
             GROUP BY M1.Champion
                  , M1.con_champ
            """
            
            df = pd.read_sql(query.replace('\n',' '), connection)
            df['Champion'] = df['Champion'].str.lower()
            df['con_champ'] = df['con_champ'].str.lower()
            
            cache.set(cache_key, df, self.cache_timeout)
            return df
        except Exception as e:
            logger.error(f"챔피언 통계 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def load_timeline_data(self):
        """타임라인 데이터 로드"""
        cache_key = 'timeline_data'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        try:
            query = f"""SELECT B.Champion
                     , A.Gold_Data
                     , A.CS_Data
                  FROM a_game_timeline A
                       INNER JOIN a_game_stat B
                    ON A.game_ID = B.Game_ID
                   AND A.Team_Div = B.Team_Div
                   AND A.ROLE = B.Role
                 WHERE A.Game_ID IN (SELECT game_ID FROM a_game WHERE Ver IN {self._get_version_condition()})"""
            
            df = pd.read_sql(query, connection)
            df['Champion'] = df['Champion'].str.lower()
            
            cache.set(cache_key, df, self.cache_timeout)
            return df
        except Exception as e:
            logger.error(f"타임라인 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def load_damage_data(self):
        """데미지 관련 데이터 로드"""
        cache_key = 'damage_data'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        try:
            query = f"""
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
                      WHERE B.Ver IN {self._get_version_condition()}
                      GROUP BY CASE WHEN A.ROLE = 'SUPPORT' THEN concat(A.Champion,'_',A.ROLE) ELSE A.Champion end
                   ) F
            """
            
            df = pd.read_sql_query(query, connection)
            df['Champion'] = df['Champion'].str.lower()
            
            # 정규화 계산
            avg_tank_death = df['tank_death'].sum() / df['tank_death'].count()
            avg_tank_time = df['tank_time'].sum() / df['tank_time'].count()
            df['tank_death_norm'] = df['tank_death'] / avg_tank_death
            df['tank_time_norm'] = df['tank_time'] / avg_tank_time
            df['tank_norm_total'] = df['tank_death_norm'] + df['tank_time_norm']
            
            avg_deal_death = df['deal_death'].sum() / df['deal_death'].count()
            avg_deal_time = df['deal_time'].sum() / df['deal_time'].count()
            df['deal_death_norm'] = df['deal_death'] / avg_deal_death
            df['deal_time_norm'] = df['deal_time'] / avg_deal_time
            df['deal_norm_total'] = df['deal_death_norm'] + df['deal_time_norm']
            
            cache.set(cache_key, df, self.cache_timeout)
            return df
        except Exception as e:
            logger.error(f"데미지 데이터 로드 실패: {e}")
            return pd.DataFrame()
    
    def load_team_data(self):
        """팀 데이터 로드"""
        cache_key = 'team_data'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        try:
            game_df = self.load_game_data()
            game_list = game_df['Game_ID'].to_list()
            team_div = ['BLUE', 'RED']
            position_div = ['TOP', 'JUNGLE', 'MID', 'ADC', 'SUPPORT']
            
            result = {}
            for game_id in game_list:
                team_id = {}
                for team in team_div:
                    temp_list = []
                    if team == 'BLUE':
                        game_result = game_df[game_df['Game_ID'] == game_id]['Blue_Result'].values[0]
                    else:
                        game_result = game_df[game_df['Game_ID'] == game_id]['Red_Result'].values[0]
                    
                    for position in position_div:
                        champ_query = f"""SELECT Champion FROM a_game_stat 
                                        WHERE Game_ID = '{game_id}' AND Team_Div = '{team}' AND Role = '{position}';"""
                        champ_df = pd.read_sql(champ_query, connection)
                        temp_list.append((champ_df['Champion'].values)[0])
                    
                    team_id[team] = [temp_list, game_result]
                result[game_id] = team_id
            
            cache.set(cache_key, result, self.cache_timeout)
            return result
        except Exception as e:
            logger.error(f"팀 데이터 로드 실패: {e}")
            return {}
    
    def clear_cache(self):
        """캐시 초기화"""
        cache_keys = ['game_data', 'champion_stats', 'timeline_data', 'damage_data', 'team_data']
        for key in cache_keys:
            cache.delete(key)

# 싱글톤 인스턴스
data_loader = DataLoader() 