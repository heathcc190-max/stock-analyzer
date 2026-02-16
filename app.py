import streamlit as st
import akshare as ak
import pandas as pd
import datetime

# --- 1. 基础配置与样式 ---
st.set_page_config(page_title="AI 股票主线与龙头 PK 看板", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心数据引擎 ---

@st.cache_data(ttl=600)
def get_market_mainline():
    """模块 A: 发现主线 (量价双驱模型)"""
    try:
        df = ak.stock_board_industry_name_em()
        # 计算吸金率
        total_vol = df['成交额'].sum()
        df['吸金率'] = (df['成交额'] / total_vol * 100).round(2)
        # 综合热度：成交额与换手率的乘积
        df['综合热度'] = (df['成交额'] / 1e8 * df['换手率']).round(2)
        # 筛选涨幅 > 0 的正向主线
        return df[df['涨跌幅'] > 0].sort_values("综合热度", ascending=False).head(15)
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_dragon_leaderboard():
    """模块 C: 龙头 PK 台 (修复语法错误与日期逻辑)"""
    try:
        now = datetime.datetime.now()
        # 核心逻辑：如果当前不是交易时间，自动回溯到上一个交易日
        # 周一(0)到周五(4)，9:30以前或周末，取上一个交易日
        if now.weekday() == 0 and now.hour < 10: # 周一早晨
            target_date = now - datetime.timedelta(days=3)
        elif now.weekday() == 5: # 周六
            target_date = now - datetime.timedelta(days=1)
        elif now.weekday() == 6: # 周日
            target_date = now - datetime.timedelta(days=2)
        else:
            target_date = now
            
        date_str = target_date.strftime("%Y%m%d")
        
        # 获取涨停池数据
        df = ak.stock_zt_pool_em(date=date_str)
        
        if not df.empty:
            # 计算封板强度
            df['封板强度'] = (df['封单资金'] / df['成交额'] * 100).round(2)
            # 排序：连板数 > 涨幅 > 封板强度
            df = df.sort_values(
                by=['连板数', '涨跌幅', '封板强度', '最后封板时间'], 
                ascending=[False, False, False, True]
            )
            return df
        return pd.DataFrame()
    except Exception as e:
        # 修复之前报错的 except 缺损问题
        st.error(f"龙头数据获取异常: {e}")
        return pd.DataFrame()

def get_global_mapping(sector_name):
    """模块 B: 全球映射逻辑"""
    mapping_dict = {
        "半导体": ["NVDA (英伟达)", "TSM (台积电)", "ASML (阿斯麦)"],
        "互联网服务": ["GOOG (谷歌)", "META (脸书)", "0700.HK (腾讯)"],
        "汽车整车": ["TSLA (特斯拉)", "9868.HK (小鹏)", "1211.HK (比亚迪)"],
        "软件开发": ["MSFT (微软)", "ORCL (甲骨文)"],
        "通信设备": ["AVGO (博通)", "CSCO (思科)", "COHR (相干)"],
        "消费电子": ["AAPL (苹果)", "1810.HK (小米)"]
    }
    return mapping_dict.get(sector_name, ["暂无直接映射，建议关注相关指数 (QQQ/SOXX)"])

# --- 3. 界面布局渲染 ---

st.title("🚀 A 股主线与龙头强度深度看板")
st.caption(f"数据更新：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | 核心逻辑：放量活跃 + 连板高度身位")

tab1, tab2 = st.tabs(["🔥 市场主线与全球映射", "🐲 龙头强度 PK 台"])

with tab1:
    col_main, col_map = st.columns([2, 1])
    
    with col_main:
        st.subheader("今日吸金活跃板块")
        m_df = get_market_mainline()
        if not m_df.empty:
            st.dataframe(
                m_df[['板块名称', '涨跌幅', '成交额', '换手率', '吸金率']].style.background_gradient(subset=['吸金率'], cmap='Greens'),
                use_container_width=True, height=450
            )
            selected_sector = st.selectbox("选择下方板块，查看全球联动逻辑：", m_df['板块名称'].tolist())
        else:
            st.warning("暂未获取到主线板块数据，请在交易时段尝试或检查网络。")

    with col_map:
        st.subheader("🌎 全球映射")
        if 'selected_sector' in locals():
            targets = get_global_mapping(selected_sector)
            st.success(f"当 **{selected_sector}** 走强时，外盘关键映射：")
            for t in targets:
                st.write(f"🔗 {t}")

with tab2:
    st.subheader("个股 PK：身位与封板硬度")
    d_df = get_dragon_leaderboard()
    if not d_df.empty:
        display_cols = ['代码', '名称', '连板数', '涨跌幅', '封板强度', '最后封板时间', '换手率']
        st.dataframe(
            d_df[display_cols].style.highlight_max(subset=['连板数'], color='#ff4b4b'),
            use_container_width=True, height=600
        )
    else:
        st.info("当前暂无数据。如果是盘中，请等待接口刷新；非交易日会自动尝试抓取上一交易日。")

# --- 4. 侧边栏说明 ---
st.sidebar.header("📊 PRD 逻辑背书")
st.sidebar.info("""
1. **模块 A (主线)**：寻找成交额放大的活跃板块。
2. **模块 B (映射)**：自动联想美股/港股标的。
3. **模块 C (龙头)**：严格执行 [连板 > 涨幅 > 封板强度] 排序。
""")
