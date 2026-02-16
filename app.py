import streamlit as st
import akshare as ak
import pandas as pd
import datetime

# --- 1. 基础配置 ---
st.set_page_config(page_title="AI 股票主线与龙头 PK 看板", layout="wide")

# --- 2. 核心工具函数 ---
def safe_calc_strength(df):
    """安全计算封板强度，兼容不同列名"""
    # 尝试匹配不同的成交额和封单列名
    vol_col = next((c for c in df.columns if '成交额' in c), None)
    ord_col = next((c for c in df.columns if '封单资金' in c), None)
    
    if vol_col and ord_col:
        df['封板强度'] = (pd.to_numeric(df[ord_col], errors='coerce') / 
                        pd.to_numeric(df[vol_col], errors='coerce') * 100).round(2)
    else:
        df['封板强度'] = 0
    return df

# --- 3. 数据引擎 ---

@st.cache_data(ttl=600)
def get_market_mainline():
    """模块 A: 发现主线"""
    try:
        df = ak.stock_board_industry_name_em()
        if df.empty: return pd.DataFrame()
        
        # 兼容性处理列名
        v_col = next((c for c in df.columns if '成交额' in c), '成交额')
        m_col = next((c for c in df.columns if '总市值' in c or '市值' in c), None)
        
        # 计算热度指标
        total_vol = df[v_col].sum()
        df['吸金率'] = (df[v_col] / total_vol * 100).round(2)
        df['综合热度'] = (df[v_col] / 1e8 * df.get('换手率', 0)).round(2)
        
        return df.sort_values("综合热度", ascending=False).head(15)
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_dragon_leaderboard():
    """模块 C: 龙头 PK 台 (增强容错版)"""
    now = datetime.datetime.now()
    # 自动回溯最近 5 天寻找有数据的交易日
    for i in range(5):
        target_date = now - datetime.timedelta(days=i)
        if target_date.weekday() >= 5: continue
        
        try:
            date_str = target_date.strftime("%Y%m%d")
            df = ak.stock_zt_pool_em(date=date_str)
            
            if df is not None and not df.empty:
                df = safe_calc_strength(df)
                # 排序逻辑
                sort_cols = ['连板数', '涨跌幅', '封板强度']
                existing_sort = [c for c in sort_cols if c in df.columns]
                if existing_sort:
                    df = df.sort_values(by=existing_sort, ascending=False)
                return df
        except:
            continue
    return pd.DataFrame()

def get_global_mapping(sector_name):
    """模块 B: 全球映射逻辑"""
    mapping_dict = {
        "半导体": ["NVDA (英伟达)", "TSM (台积电)", "SOXX (ETF)"],
        "互联网服务": ["GOOG (谷歌)", "700.HK (腾讯)", "META (脸书)"],
        "汽车整车": ["TSLA (特斯拉)", "1211.HK (比亚迪)", "9868.HK (小鹏)"],
        "软件开发": ["MSFT (微软)", "CRM (赛富时)"],
        "通信设备": ["AVGO (博通)", "CSCO (思科)"]
    }
    return mapping_dict.get(sector_name, ["观察全球主流科技股指数"])

# --- 4. UI 界面 ---

st.title("📊 A 股主线与龙头强度深度看板")
st.caption(f"运行状态：全自动化数据对齐模式 | 更新时间：{datetime.datetime.now().strftime('%H:%M')}")

tab1, tab2 = st.tabs(["🔥 市场主线与全球映射", "🐲 龙头强度 PK 台"])

with tab1:
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.subheader("活跃吸金板块")
        m_df = get_market_mainline()
        if not m_df.empty:
            st.dataframe(m_df[['板块名称', '涨跌幅', '成交额', '吸金率']].head(10), use_container_width=True)
            sel = st.selectbox("查看联动映射：", m_df['板块名称'].tolist())
        else:
            st.info("盘前或接口维护中，暂无实时板块热度。")
    with col_r:
        if 'sel' in locals():
            st.success(f"**{sel}** 全球映射：")
            for t in get_global_mapping(sel): st.write(f"🔗 {t}")

with tab2:
    st.subheader("龙头强度对比 (最近交易日)")
    d_df = get_dragon_leaderboard()
    if not d_df.empty:
        # 动态展示存在的列
        view_cols = [c for c in ['代码', '名称', '连板数', '涨跌幅', '封板强度', '最后封板时间'] if c in d_df.columns]
        st.dataframe(d_df[view_cols], use_container_width=True)
    else:
        st.warning("未能获取到近期涨停池数据，可能接口暂时不可用。")

st.sidebar.markdown("### 📊 PRD 核心逻辑\n1. **主线**：热度 = 成交 × 换手\n2. **龙头**：连板 > 涨幅 > 封板强度")
