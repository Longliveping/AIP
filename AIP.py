import tushare as ts
from datetime import datetime
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
# 利用plotly绘图
import plotly.offline as of
import plotly.graph_objs as go

# 解决中文显示问题，Mac
plt.rcParams['figure.figsize'] = (10.0, 4.0)  # 设置figure_size尺寸
plt.rcParams['image.interpolation'] = 'nearest'  # 设置 interpolation style
plt.rcParams['image.cmap'] = 'gray'  # 设置 颜色 style
plt.rcParams['savefig.dpi'] = 100  # 图片像素
plt.rcParams['figure.dpi'] = 100  # 分辨率
# plt.rcParams['font.family']=['STZhongsong']
plt.rcParams['font.family'] = ['Microsoft Yahei']

# 设置token
ts.set_token('089694a758f6d1b028af007f1bd12906a2e7954a804ec42217ae680f')

# 初始化接口
pro = ts.pro_api()

# 获取基本信息
sh_basic = pro.index_basic(market='SSE')  # 上交所
sz_basic = pro.index_basic(market='SZSE')  # 深交所

'''
13名称:描述
14ts_code:TS指数代码
15trade_date:交易日
16close:收盘点位
17open:开盘点位
18high:最高点位
19low:最低点位
20pre_close:昨日收盘点
21change:涨跌点
22pct_chg:涨跌幅（%）
23vol:成交量（手）
24amount:成交额（千元）
'''

# 000001.SH 上证综指
# 399001.SZ 深证成指
data_sh = pro.index_daily(ts_code='000001.SH', start_date='19901219', end_date='20190401')
data_sz = pro.index_daily(ts_code='399001.SZ', start_date='19901219', end_date='20190401')
data_sh.head()

data = data_sh.copy()
data = data.loc[:, ['open', 'trade_date']]
data['date'] = data['trade_date'].apply(lambda x: datetime.strptime(x, '%Y%m%d'))
data = data.set_index('date').sort_index()
data['理财利率'] = (4.0 / 100 + 1) ** (1.0 / 250) - 1  # 假设理财产品的年化收益率为 5%
data['理财收益_净值'] = (data['理财利率'] + 1).cumprod()

# 选择每个月的最后一个交易日进行定投
trading_day = data.resample('M', kind='date').last()

# 定投指数基金
AIP = pd.DataFrame(index=trading_day.index)
AIP['定投金额'] = 2000

# 以基金当天的开盘价作为当天买入的价格
AIP['基金价格'] = trading_day['open']
AIP['购买基金份额'] = AIP['定投金额'] / AIP['基金价格']
AIP['累计基金份额'] = AIP['购买基金份额'].cumsum()

# 定期购买理财产品
AIP['购买理财产品份额'] = AIP['定投金额'] / trading_day['理财收益_净值']
AIP['累计理财产品份额'] = AIP['购买理财产品份额'].cumsum()

# 累计投入本金
AIP['累计定投本金'] = AIP['定投金额'].cumsum()

# 计算每个交易日的本息（即本金+利息，公式=当天的份额 X 当天的基金价格）
result = pd.concat([trading_day, AIP], axis=1)
result['基金本息'] = (result['open'] * result['累计基金份额']).astype('int')
result['理财本息'] = (result['理财收益_净值'] * result['累计理财产品份额']).astype('int')
result.head(10)

# 开始画图
x_axix = result.index

fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
ax1.plot(x_axix, result['open'], color='green', label='大盘走势')
ax2.plot(x_axix, result['基金本息'], color='skyblue', label='指数基金收益')
ax2.plot(x_axix, result['理财本息'], color='blue', label='理财产品收益')
ax2.plot(x_axix, result['累计定投本金'], color='yellow', label='累计定投本金')

plt.legend()  # 显示图例

ax1.set_xlabel('定投日期')
ax1.set_ylabel('大盘指数', color='g')
ax2.set_ylabel('投资收益', color='b')
plt.show()

x_label = ['1-基金本息同比本金', '2-理财本息同比本金', '3-本金同比本金', '4-基金本息同比理财本息']
y_value = [round(result['基金本息'][-1] / result['累计定投本金'][-1] - 1, 2),
           round(result['理财本息'][-1] / result['累计定投本金'][-1] - 1, 2),
           round(result['累计定投本金'][-1] / result['累计定投本金'][-1] - 1, 2),
           round(result['基金本息'][-1] / result['理财本息'][-1] - 1, 2)]

plt.plot(x_label, y_value)
plt.xlabel("同比项目")
plt.ylabel("比值")
plt.title("收益同比比较图")

# 设置数字标签
for a, b in zip(x_label, y_value):
    plt.text(a, b, b, ha='center', va='bottom', fontsize=13)
plt.show()