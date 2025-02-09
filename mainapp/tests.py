import pandas as pd
import pymysql
game_list_query ="""SELECT B.Champion
     , A.Gold_Data
     , A.CS_Data 
  FROM a_game_timeline A
       INNER JOIN a_game_stat B
    ON A.game_ID = B.Game_ID 
   AND A.Team_Div = B.Team_Div 
   AND A.ROLE = B.Role
 WHERE A.Game_ID IN (SELECT game_ID FROM a_game WHERE Ver IN ('v15.1','v15.2'))"""

game_list_df = pd.read_sql(game_list_query, conn)

conn.close()
champion_list=game_list_df['Champion'].unique()
cham_powergraph=[]
for cham in champion_list:
    df=game_list_df[game_list_df['Champion']==cham]
    result=[]
    for i in df['Gold_Data']:
        data=eval(i)
        temp_list=[]
        for j in range(0,len(data)-1):
            if j != 0:
                temp_list.append(int(data[j])-int(data[j-1]))
        result.append(temp_list)
    power_graph=[]    
    for k in range(0,30):
        temp=[]
        for u in result:
            try:
                temp.append(u[k])
            except:
                break
        if len(temp) != 0:
            value=round(sum(temp)/len(temp),2)
        power_graph.append(value)
    cham_powergraph.append([cham,power_graph])
power_df=pd.DataFrame(cham_powergraph)
power_df.columns=['Champion','Value']
power_df.head()
temp_data=power_df.head(10)
data_list=[]
for q in range(0,10):
    temp_str=''
    temp_str= temp_str+temp_data.iloc[q][0]+str(temp_data.iloc[q][1])
    data_list.append(temp_str)
data_list
data_list=['Corki[0.17, 113.17, 321.74, 373.89, 348.87, 332.57, 389.24, 400.37, 315.28, 407.37, 406.22, 401.11, 427.13, 428.72, 389.96, 443.43, 494.61, 432.28, 458.15, 477.78, 417.37, 512.67, 378.48, 419.94, 431.52, 427.21, 383.56, 479.32, 287.87, 437.83]',
 'Jayce[0.89, 80.0, 275.93, 335.13, 338.64, 316.0, 365.96, 346.16, 339.69, 366.89, 365.36, 380.6, 404.04, 432.73, 369.53, 446.78, 412.24, 423.27, 431.04, 442.11, 399.87, 425.47, 499.44, 382.62, 477.33, 336.67, 403.33, 381.0, 234.0, 278.0]',
 'KSante[0.53, 71.37, 266.87, 324.21, 299.63, 321.26, 381.58, 332.97, 323.34, 385.29, 339.5, 376.71, 372.92, 364.58, 356.71, 394.79, 386.87, 384.63, 406.11, 354.5, 353.66, 357.05, 312.71, 314.97, 327.76, 398.71, 437.03, 419.42, 708.5, 273.0]',
 'Leona[1.92, 56.53, 216.66, 220.13, 201.08, 202.82, 231.84, 207.82, 214.84, 252.32, 257.55, 266.0, 234.95, 235.26, 229.24, 274.32, 239.03, 237.21, 213.74, 214.21, 208.82, 235.68, 271.71, 239.32, 238.0, 200.0, 280.5, 187.5, 190.0, 82.0]',
 'Miss Fortune[0.0, 98.53, 370.27, 343.0, 315.8, 343.6, 407.93, 370.2, 341.87, 441.27, 398.0, 407.67, 531.6, 509.87, 364.27, 400.33, 536.47, 463.93, 529.0, 477.53, 497.87, 407.27, 368.0, 397.87, 358.4, 484.93, 544.4, 433.27, 792.75, 5.0]',
 'Rell[1.8, 57.88, 210.7, 222.56, 197.42, 210.78, 235.44, 225.68, 229.8, 222.4, 241.7, 246.08, 247.54, 252.14, 246.04, 258.16, 230.98, 229.94, 238.0, 226.4, 219.12, 242.22, 251.1, 247.74, 198.67, 329.0, 342.0, 385.0, 551.5, 87.5]',
 'Sejuani[0.74, 122.82, 362.38, 387.59, 302.76, 297.68, 297.24, 361.15, 354.32, 307.91, 318.97, 322.59, 341.29, 322.44, 370.88, 329.26, 306.97, 371.41, 326.24, 328.59, 277.82, 301.74, 328.35, 300.32, 267.08, 371.88, 330.92, 315.28, 262.92, 175.25]',
 'Skarner[3.0, 126.0, 359.8, 359.0, 323.2, 247.0, 401.6, 403.0, 289.4, 404.2, 271.0, 427.4, 321.0, 354.8, 504.6, 450.4, 479.4, 334.6, 390.8, 439.0, 325.0, 309.0, 295.0, 321.4, 346.0, 318.8, 724.8, 546.6, 667.0, 5.0]',
 'Viktor[0.36, 154.54, 316.57, 360.25, 361.64, 314.39, 350.96, 354.14, 331.54, 396.43, 395.36, 373.79, 446.96, 379.0, 373.68, 422.75, 373.96, 448.96, 460.14, 357.18, 400.61, 379.25, 445.68, 345.04, 401.57, 537.04, 421.69, 398.81, 136.0, 259.5]',
 'Yone[0.19, 118.65, 311.15, 371.31, 370.38, 298.92, 375.38, 370.19, 308.85, 396.46, 407.85, 403.31, 409.58, 371.65, 357.54, 426.58, 416.81, 440.88, 429.19, 437.92, 406.65, 354.31, 358.08, 367.33, 653.0, 370.0, 841.33, 446.67, 1052.67, 374.33]']
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 데이터를 DataFrame으로 변환
# 주어진 데이터를 적절한 형태로 변환
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
        for time_point, value in enumerate(values):
            df_data.append({
                'Champion': champion,
                'Time': time_point,
                'Value': value
            })
    
    return pd.DataFrame(df_data)

# 예시 데이터
data_list = data_list

# DataFrame 생성
df = create_dataframe(data_list)

# Plotly를 사용한 라인 차트 생성
fig = px.line(df, 
              x='Time', 
              y='Value', 
              color='Champion',
              title='Champion Performance Over Time',
              labels={'Time': 'Time Point', 
                     'Value': 'Performance Value',
                     'Champion': 'Champion Name'},
              markers=True)

# 차트 레이아웃 커스터마이징
fig.update_layout(
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(size=12),
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
    zerolinecolor='lightgrey'
)

# 차트 표시
fig.show()
