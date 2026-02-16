import streamlit as st
import akshare as ak
import pandas as pd
import datetime

# --- 1. 基础配置 ---
st.set_page_config(page_title="AI 股票主线与龙头 PK 看板", layout="wide")

# --- 2. 核心数据引擎 (增加回溯逻辑) ---

@st.cache_data(ttl=600)
def get_market_mainline():
    """模块 A: 发现主线 (量价双驱)"""
    try:
        # 获取行业板块行情
        df = ak.stock_board_industry_name_em()
        if df.empty: return pd.DataFrame()
        
        # 计算吸金率与热度
        total_vol = df['成交额'].sum()
        df['吸金率'] = (df['成交额'] / total_vol * 100).round(2)
        df['综合热度'] = (df['成交额'] / 1e8 * df['换手率']).round(2)
        
        # 排序：综合热度越高越靠前
        return df.sort_values("综合热度", ascending=False).head(15)
    except Exception as e:
        st.error(f"主线接口调用异常: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_dragon_leaderboard():
    """模块 C: 龙头 PK 台 (自动回溯交易日)"""
    # 定义回溯获取函数，防止当日无数据
    def fetch_data(target_date):
        date_str = target_date.strftime("%Y%m%d")
        try:
            return ak.stock_zt_pool_em(date=date_str)
        except:
            return pd.DataFrame()

    now = datetime.datetime.now()
    # 依次尝试：今日 -> 昨日 -> 前日 -> 大前日
    for i in range(4):
        check_date = now - datetime.timedelta(days=i)
        # 跳过周末
        if check_date.weekday() >= 5: continue 
        
        df = fetch_data(check_date)
        if not df.empty:
            # 补全 PRD 逻辑：连板 > 涨幅 > 封板强度
            df['封板强度'] = (df['封单资金'] / df['成交额'] * 100).round(2)
            return df.sort_values(
                by=['连板数', '涨跌幅', '封板强度', '最后封板时间'], 
                ascending=[False, False, False, True]
            )
    return pd.DataFrame()

def get_global_mapping(sector_name):
    """模块 B: 全球映射逻辑"""
    mapping_dict = {
        "半导体": ["NVDA (英伟达)", "TSM (台积电)", "SOXX (半导体ETF)"],
        "互联网服务": ["GOOG (谷歌)", "META (脸书)", "700.HK (腾讯控股)"],
        "汽车整车": ["TSLA (特斯拉)", "9868.HK (小鹏汽车)", "1211.HK (比亚迪股份)"],
        "软件开发": ["MSFT (微软)", "CRM (赛富时)"],
        "通信设备": ["AVGO (博通)", "CSCO (思科)", "COHR (相干)"]
    }
    return mapping_dict.get(sector_name, ["暂无直接映射，建议关注纳斯达克100 (QQQ)"])

# --- 3. UI 界面渲染 ---

st.title("🚀 A 股主线与龙头强度深度看板")
st.caption(f"数据状态：全时段自动回溯模式 | 逻辑核心：连板身位 > 封板强度")

tab1, tab2 = st.tabs(["🔥 市场主线与全球映射", "🐲 龙头强度 PK 台"])

with tab1:
    col_main, col_map = st.columns([2, 1])
    with col_main:
        st.subheader("今日/近期吸金活跃板块")
        m_df = get_market_mainline()
        if not m_df.empty:
            # 过滤掉涨幅为负的，保留进攻性板块
            m_df_up = m_df[m_df['涨跌幅'] > 0]
            st.dataframe(
                m_df_up[['板块名称', '涨跌幅', '成交额', '换手率', '吸金率']].style.background_gradient(subset=['吸金率'], cmap='Greens'),
                use_container_width=True, height=450
            )
            selected_sector = st.selectbox("点击下方板块查看全球映射：", m_df_up['板块名称'].tolist())
        else:
            st.warning("主线数据获取失败，可能由于接口限制，请尝试重启应用。")

    with col_map:
        st.subheader("🌎 全球映射映射")
        if 'selected_sector' in locals() and selected_sector:
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
            d_df[display_cols].style.background_gradient(subset=['连板数'], cmap='Reds'),
            use_container_width=True, height=600
        )
    else:
        st.info("当前日期及回溯日期均无涨停数据，请确认是否为交易日收盘后。")

# --- 4. 侧边栏 ---
st.sidebar.markdown("### 📊 PRD 逻辑背书")
st.sidebar.info("1. **主线**: 综合热度(成交×换手)\n2. **龙头**: 连板 > 涨幅 > 封板强度")
