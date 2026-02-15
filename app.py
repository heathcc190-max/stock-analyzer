import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 页面配置
st.set_page_config(page_title="我的 AI 股票分析助手", layout="wide")

st.title("📈 全球股票行情分析看板")
st.sidebar.header("查询参数")

# 1. 输入股票代码
symbol = st.sidebar.text_input("请输入股票代码 (如: AAPL, 000001.SS, 0700.HK)", "AAPL")

# 2. 获取数据
@st.cache_data(ttl=3600) # 缓存数据，避免重复加载
def get_data(ticker):
    data = yf.download(ticker, period="6mo", interval="1d")
    return data

try:
    df = get_data(symbol)
    
    if not df.empty:
        # 顶部指标卡片
        last_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        delta = ((last_price - prev_price) / prev_price) * 100
        
        col1, col2, col3 = st.columns(3)
        # 将数据显式转换为浮点数，避免格式化错误
        current_price = float(last_price)
        change_percent = float(delta)
        last_volume = int(df['Volume'].iloc[-1])
        col1.metric("最新价格", f"{current_price:.2f}", f"{change_percent:.2f}%")
        col2.metric("当日成交量", f"{last_volume:,}")
        col3.metric("市场范围", "美股/港股/A股(雅虎源)")

        # K线图
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                        open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'])])
        fig.update_layout(title=f"{symbol} 历史行情", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # 基本面信息
        st.subheader("🏢 公司基本面 (简版)")
        info = yf.Ticker(symbol).info
        st.write(f"**公司名称:** {info.get('longName', 'N/A')}")
        st.write(f"**行业:** {info.get('industry', 'N/A')}")
        st.write(f"**市盈率 (PE):** {info.get('trailingPE', 'N/A')}")
        st.write(f"**摘要:** {info.get('longBusinessSummary', 'N/A')[:300]}...")
        
    else:
        st.error("未找到数据，请检查代码格式是否正确（A股需后缀 .SS 或 .SZ）。")
except Exception as e:
    st.error(f"发生错误: {e}")
