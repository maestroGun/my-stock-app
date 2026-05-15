import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import FinanceDataReader as fdr

# ----------------------------------------------------
# ⚙️ 페이지 기본 설정
# ----------------------------------------------------
st.set_page_config(page_title="Ultimate 퀀트 대시보드", layout="wide", initial_sidebar_state="expanded")

# ----------------------------------------------------
# 🎨 UI/UX 디자인 (홈 화면 + 상세 화면 공통)
# ----------------------------------------------------
st.markdown("""
    <style>
    .stock-title { font-size: 1.8rem; font-weight: 700; color: #111; margin-bottom: -15px; }
    .stock-code { font-size: 0.9rem; color: #888; margin-bottom: 10px; }
    .price-up { font-size: 2.8rem; font-weight: 800; color: #EF4444; }
    .price-down { font-size: 2.8rem; font-weight: 800; color: #3B82F6; }
    .price-flat { font-size: 2.8rem; font-weight: 800; color: #111; }
    .change-up { font-size: 1.2rem; font-weight: 600; color: #EF4444; }
    .change-down { font-size: 1.2rem; font-weight: 600; color: #3B82F6; }
    
    .info-card { background-color: #FAFAFA; padding: 20px; border-radius: 12px; border: 1px solid #EAEAEA; margin-bottom: 15px; }
    .quant-card { background-color: #FFFFFF; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 15px; }
    .card-title { font-size: 0.85rem; color: #666; font-weight: 600; margin-bottom: 5px; }
    .card-value { font-size: 1.1rem; font-weight: 700; color: #222; }
    
    /* 홈 화면 미니 카드용 스타일 */
    .mini-card { background-color: #1E293B; padding: 15px; border-radius: 12px; color: white; margin-bottom: 15px; border: 1px solid #334155; }
    .mini-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 2px; }
    .mini-code { font-size: 0.75rem; color: #94A3B8; margin-bottom: 8px; }
    .badge-hot { background-color: #EF4444; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: bold; }
    .badge-good { background-color: #10B981; color: white; padding: 3px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: bold; }
    
    div.row-widget.stRadio > div{ flex-direction:row; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 🔍 종목 매핑 및 공통 데이터 로드
# ----------------------------------------------------
@st.cache_data(ttl=86400)
def get_krx_list():
    df = fdr.StockListing('KRX')
    return {row['Name']: f"{row['Code']}.KQ" if row['Market'] == 'KOSDAQ' else f"{row['Code']}.KS" for _, row in df.iterrows()}

krx_dict = get_krx_list()

@st.cache_data(ttl=300)
def fetch_chart_data(ticker_symbol, is_intraday=False):
    s = yf.Ticker(ticker_symbol)
    if is_intraday:
        hist = s.history(period="5d", interval="5m") 
    else:
        hist = s.history(period="max", interval="1d")
    info = s.info
    return hist, info

# ====================================================
# 🏠 페이지 1: 대시보드 홈 (오늘의 핫픽 / 급등주)
# ====================================================
def render_home():
    st.markdown('<p style="font-size: 2rem; font-weight: 800; color: #111;">🔥 오늘의 Hot 픽</p>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-top:-10px;">알고리즘이 선정한 강력한 모멘텀(급등/정배열) 종목 6선</p>', unsafe_allow_html=True)
    
    target_stocks = ["SK하이닉스", "삼양식품", "알테오젠", "HD현대일렉트릭", "한화에어로스페이스", "삼성전자"]
    cols = st.columns(3) 
    
    for idx, stock_name in enumerate(target_stocks):
        ticker = krx_dict.get(stock_name, "")
        if not ticker: continue
        s = yf.Ticker(ticker)
        hist = s.history(period="3mo", interval="1d")
        if hist.empty: continue
        cur_p = hist['Close'].iloc[-1]
        ma20 = hist['Close'].rolling(20).mean().iloc[-1]
        
        if cur_p > ma20 * 1.05: 
            badge, line_color = '<span class="badge-hot">🚀 단기 급등</span>', '#EF4444'
        elif cur_p > ma20:
            badge, line_color = '<span class="badge-good">✨ 정배열 추세</span>', '#10B981'
        else:
            badge, line_color = '<span style="background-color:#64748B; color:white; padding:3px 8px; border-radius:10px; font-size:0.7rem;">분할 매수</span>', '#3B82F6'

        fig = go.Figure(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', line=dict(color=line_color, width=2.5)))
        fig.update_layout(height=100, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False, dragmode=False)
        
        with cols[idx % 3]:
            st.markdown(f'<div class="mini-card"><div style="display:flex; justify-content:space-between; align-items:flex-start;"><div><div class="mini-title">{stock_name}</div><div class="mini-code">{ticker.split(".")[0]}</div></div><div>{badge}</div></div></div>', unsafe_allow_html=True)
            st.markdown('<div style="margin-top:-35px; margin-bottom: 10px;">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

# ====================================================
# 🔍 페이지 2: 종목 상세 분석 (하이브리드 정보 포함)
# ====================================================
def render_detail():
    st.markdown('<p style="font-size: 2rem; font-weight: 800; color: #111;">📊 종목 상세 분석</p>', unsafe_allow_html=True)
    search_input = st.text_input("🔍 분석할 종목명 또는 코드 입력", "SK하이닉스")
    ticker = krx_dict.get(search_input, search_input.upper())

    if ticker:
        try:
            st.markdown(f'<p class="stock-title">{search_input}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="stock-code">{ticker}</p>', unsafe_allow_html=True)
            selected_period = st.radio("조회 기간", ['1일', '3개월', '1년', '3년', '10년', '최대'], horizontal=True, label_visibility="collapsed")
            is_intraday = selected_period == '1일'
            hist_raw, info = fetch_chart_data(ticker, is_intraday)
            
            if hist_raw.empty:
                st.error("데이터를 불러올 수 없습니다.")
                return

            last_date = hist_raw.index[-1]
            if is_intraday:
                today_date = last_date.date()
                hist = hist_raw[hist_raw.index.date == today_date]
                quant_df, _ = fetch_chart_data(ticker, is_intraday=False)
                start_date = hist.index[0]
                try: prev_p = hist_raw[hist_raw.index.date < today_date]['Close'].iloc[-1]
                except: prev_p = info.get('previousClose', hist['Close'].iloc[0])
                compare_label = "전일 대비"
            else:
                hist, quant_df = hist_raw, hist_raw
                if selected_period == '3개월': start_date = last_date - pd.DateOffset(months=3); compare_label = "3개월 전 대비"
                elif selected_period == '1년': start_date = last_date - pd.DateOffset(years=1); compare_label = "1년 전 대비"
                elif selected_period == '3년': start_date = last_date - pd.DateOffset(years=3); compare_label = "3년 전 대비"
                elif selected_period == '10년': start_date = last_date - pd.DateOffset(years=10); compare_label = "10년 전 대비"
                else: start_date = hist.index[0]; compare_label = "상장일 대비"
                visible_hist = hist[hist.index >= start_date]
                prev_p = visible_hist['Close'].iloc[0] if not visible_hist.empty else hist['Close'].iloc[0]
                
            cur_p = hist['Close'].iloc[-1]
            chg, chg_pct = cur_p - prev_p, ((cur_p - prev_p) / prev_p) * 100 if prev_p != 0 else 0
            currency = "₩" if ".K" in ticker else "$"
            
            if chg > 0: price_class, change_text, chg_class = "price-up", f"▲ {abs(chg):,.0f} (+{chg_pct:.2f}%)", "change-up"
            elif chg < 0: price_class, change_text, chg_class = "price-down", f"▼ {abs(chg):,.0f} ({chg_pct:.2f}%)", "change-down"
            else: price_class, change_text, chg_class = "price-flat", "0 (0.00%)", "change-flat"
                
            st.markdown(f'<div style="display: flex; align-items: baseline;"><span class="{price_class}">{cur_p:,.0f}</span><span style="font-size: 1.2rem; font-weight:600; color:#111; margin-right: 15px;">{currency}</span><span class="{chg_class}">{change_text}</span><span style="font-size: 0.9rem; color: #888; margin-left: 8px; font-weight: 500;">({compare_label})</span></div>', unsafe_allow_html=True)
            st.write("")

            if len(quant_df) >= 60:
                ma60 = quant_df['Close'].rolling(window=60).mean().iloc[-1]
                buy_min, buy_max = ma60 * 0.95, ma60 * 1.02
                ma20, std20 = quant_df['Close'].rolling(window=20).mean().iloc[-1], quant_df['Close'].rolling(window=20).std().iloc[-1]
                lower_bb, upper_bb = ma20 - (std20 * 2), ma20 + (std20 * 2)
                delta = quant_df['Close'].diff()
                gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean().iloc[-1]
                loss = -1 * delta.clip(upper=0).ewm(alpha=1/14, adjust=False).mean().iloc[-1]
                rsi = 100 - (100 / (1 + (gain / loss if loss != 0 else 0)))
                if cur_p <= (lower_bb * 1.02) and rsi < 40: tech_signal, tech_color = "🟢 적극 매수 (바닥/과매도)", "#10B981"
                elif cur_p >= (upper_bb * 0.98) and rsi > 70: tech_signal, tech_color = "🔴 비중 축소 (단기 고점)", "#EF4444"
                elif cur_p <= buy_max: tech_signal, tech_color = "🔵 분할 매수 구간", "#3B82F6"
                else: tech_signal, tech_color = "⚪ 관망 (추세 대기)", "#64748B"
            else: buy_min, buy_max, rsi, tech_signal, tech_color = 0, 0, 50, "데이터 부족", "#888"

            if is_intraday:
                y_min, y_max = min(hist['Low'].min(), prev_p), max(hist['High'].max(), prev_p)
                margin = (y_max - y_min) * 0.1 if (y_max - y_min) != 0 else cur_p * 0.05
                y_min, y_max = y_min - margin, y_max + margin
                start_str, end_str = f"{last_date.strftime('%Y-%m-%d')} 09:00:00", f"{last_date.strftime('%Y-%m-%d')} 15:30:00"
            else:
                y_min, y_max = (visible_hist['Low'].min() * 0.95, visible_hist['High'].max() * 1.05) if not visible_hist.empty and selected_period != '최대' else (None, None)
                start_str, end_str = start_date.strftime('%Y-%m-%d'), (last_date + pd.DateOffset(days=1)).strftime('%Y-%m-%d')

            col_left, col_right = st.columns([7, 3])
            with col_left:
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
                if is_intraday:
                    color = '#EF4444' if cur_p >= prev_p else '#3B82F6'
                    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', line=dict(color=color, width=2), fill='tozeroy', fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}'), row=1, col=1)
                    fig.add_hline(y=prev_p, line_dash="dot", line_color="#555", line_width=1.5, annotation_text="전일 종가", annotation_position="top left", row=1, col=1)
                else:
                    fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], increasing_line_color='#EF4444', decreasing_line_color='#3B82F6'), row=1, col=1)
                    if not quant_df.empty: fig.add_trace(go.Scatter(x=quant_df.index, y=quant_df['Close'].rolling(20).mean(), line=dict(color='orange', width=1)), row=1, col=1)
                fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], marker_color=['#A1A1AA']*len(hist) if is_intraday else ['#EF4444' if o<c else '#3B82F6' for o,c in zip(hist['Open'], hist['Close'])], opacity=0.7), row=2, col=1)
                fig.update_layout(height=520, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor='white', dragmode='pan', showlegend=False, xaxis=dict(range=[start_str, end_str], autorange=False, showgrid=True, gridcolor='#F5F5F5', type="date", rangebreaks=[dict(bounds=["sat", "mon"])]), yaxis=dict(range=[y_min, y_max], autorange=False if y_min else True, side="right", showgrid=True, gridcolor='#F5F5F5', fixedrange=is_intraday))
                if is_intraday: fig.update_xaxes(tickformat="%H:%M", dtick=3600000, row=1, col=1); fig.update_xaxes(tickformat="%H:%M", dtick=3600000, row=2, col=1)
                st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': not is_intraday, 'displayModeBar': False})

            with col_right:
                target_mean = info.get('targetMeanPrice', 0)
                recom_dict = {'BUY': '🟢 매수', 'STRONG_BUY': '🔥 적극 매수', 'HOLD': '⚪ 보유(관망)', 'SELL': '🔴 매도', 'STRONG_SELL': '🔻 적극 매도'}
                analyst_recom = recom_dict.get(info.get('recommendationKey', 'none').upper(), '데이터 없음')
                upside_pct = ((target_mean - cur_p) / cur_p) * 100 if target_mean > 0 else 0
                
                st.markdown(f"""
                <div class="quant-card" style="border-top: 4px solid #111;">
                    <p style="font-size: 1.1rem; font-weight: 800; margin-bottom: 15px; color: #111;">💡 K-Stocks 종합 진단</p>
                    <div style="background-color: #F8FAFC; padding: 12px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #E2E8F0;">
                        <p style="font-size: 0.8rem; color: #64748B; font-weight: 600; margin-bottom: 3px;">🤖 알고리즘 (차트)</p>
                        <p style="color: {tech_color}; font-size: 1.1rem; font-weight: 700; margin: 0;">{tech_signal}</p>
                    </div>
                    <div style="background-color: #F8FAFC; padding: 12px; border-radius: 8px; border: 1px solid #E2E8F0;">
                        <p style="font-size: 0.8rem; color: #64748B; font-weight: 600; margin-bottom: 3px;">👔 증권사 평균 (실적)</p>
                        <p style="color: #111; font-size: 1.1rem; font-weight: 700; margin: 0;">{analyst_recom}</p>
                        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 4px;">
                            <span style="font-size: 0.75rem; color: #888;">목표가: {currency}{target_mean:,.0f}</span>
                            <span style="font-size: 0.85rem; font-weight: 700; color: {'#EF4444' if upside_pct > 0 else '#3B82F6'};">{upside_pct:+.1f}%</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                h52, l52 = info.get("fiftyTwoWeekHigh", cur_p), info.get("fiftyTwoWeekLow", cur_p)
                pos = max(0, min(100, ((cur_p - l52) / (h52 - l52)) * 100)) if h52 != l52 else 50
                st.markdown(f'<div class="info-card"><p style="font-size: 0.85rem; font-weight: 600; color: #666; margin-bottom: 8px;">52주 변동폭</p><div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #888; margin-bottom: 5px;"><span>최저 {l52:,.0f}</span><span>최고 {h52:,.0f}</span></div><div style="position: relative; width: 100%; height: 6px; background-color: #EAEAEA; border-radius: 3px;"><div style="position: absolute; left: {pos}%; top: -4px; width: 14px; height: 14px; background-color: #111; border-radius: 50%; transform: translateX(-50%);"></div></div></div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                c1.markdown(f'<div class="info-card"><p class="card-title">시가총액</p><p class="card-value">{info.get("marketCap", 0)/1e12:.1f}조</p></div>', unsafe_allow_html=True)
                c1.markdown(f'<div class="info-card"><p class="card-title">PER</p><p class="card-value">{info.get("trailingPE", "N/A")}</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="info-card"><p class="card-title">외인소진율</p><p class="card-value">{info.get("heldPercentInstitutions", 0)*100:.1f}%</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="info-card"><p class="card-title">PBR</p><p class="card-value">{info.get("priceToBook", "N/A")}</p></div>', unsafe_allow_html=True)
        except Exception as e: st.error(f"오류: {e}")

# ====================================================
# 🧭 사이드바 라우팅
# ====================================================
st.sidebar.title("K-Stocks 메뉴")
page = st.sidebar.radio("이동할 페이지", ["🏠 대시보드 홈", "🔍 종목 상세 분석"])
if page == "🏠 대시보드 홈": render_home()
else: render_detail()
