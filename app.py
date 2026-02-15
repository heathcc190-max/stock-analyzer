import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(page_title="专业 A 股分析助手", layout="wide")

st.title("📊 专业 A 股行情分析看板")

# 侧边栏输入
st.sidebar.header("查询参数")
stock_code = st.sidebar.text_input("请输入 A 股代码 (如: 600519)", "600519")

@st.cache_data(ttl=600)  # 缓存10分钟
def load_stock_data(code):
    # 获取个股历史行情 (东财接口)
    df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20230101", adjust="qfq")
    df['日期'] = pd.to_datetime(df['日期'])
    return df

@st.cache_data(ttl=3600)
def load_stock_news(code):
    # 获取个股新闻
    try:
        news_df = ak.stock_news_em(symbol=code)
        return news_df.head(10)
    except:
        return pd.DataFrame()

try:
    # 1. 加载数据
    df = load_stock_data(stock_code)
    
    if not df.empty:
        # 2. 顶部指标卡片
        last_row = df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新价格", f"{last_row['收盘']}")
        col2.metric("涨跌幅", f"{last_row['涨跌幅']}%")
        col3.metric("成交量 (手)", f"{last_row['成交量']:,}")
        col4.metric("成交额 (元)", f"{last_row['成交额']:,}")

        # 3. K线图
        fig = go.Figure(data=[go.Candlestick(
            x=df['日期'],
            open=df['开盘'], high=df['最高'],
            low=df['最低'], close=df['收盘'],
            name='K线'
        )])
        fig.update_layout(title=f"股票 {stock_code} 历史行情", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # 4. 财经新闻与基本面
        tab1, tab2 = st.tabs(["🔥 相关新闻", "📑 财务简报"])
        
        with tab1:
            news = load_stock_news(stock_code)
            if not news.empty:
                for idx, row in news.iterrows():
                    # 使用 .get() 方法，如果找不到字段就显示“无”，避免程序崩溃
                    title = row.get('新闻标题', '无标题')
                    time = row.get('发布时间', '未知时间')
                    url = row.get('文章链接', row.get('url', '#')) # 尝试匹配不同的链接字段名
                    
                    st.write(f"**[{time}]** {title}")
                    if url != '#':
                        st.caption(f"[查看原文]({url})")
                    st.divider()
            else:
                st.info("暂无相关新闻")
        
        with tab2:
            st.info("正在调取财务报表数据...")
            # 这里可以根据需要添加 ak.stock_financial_report_sinker 等接口
            st.write("提示：A 股财报数据量大，建议先关注核心指标。")

    else:
        st.error("未找到数据，请输入正确的 6 位数字代码。")
except Exception as e:
    st.error(f"发生错误: {e}")
