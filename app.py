import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "money_studio.db"

st.set_page_config(page_title="EarnFlow — Money, in your flow", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

# ── Earnflow design system ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--bg:#0B0D12;--surface:#12151D;--card:#171B25;--border:#292E3A;--purple:#8B5CF6;--violet:#A78BFA;--text:#F5F5F7;--muted:#9298A6;--green:#55C99A;--red:#E47C87;--amber:#D8B46A}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:var(--bg);color:var(--text)}
[data-testid="stHeader"]{background:rgba(11,13,18,.92)}
.block-container{max-width:1500px;padding:1.1rem 2.2rem 3rem}
h1,h2,h3,h4{font-family:'Manrope',sans-serif!important;letter-spacing:-.035em;color:var(--text)}
h1{font-weight:800;font-size:2rem!important} h2{font-weight:700;font-size:1.35rem!important} h3{font-weight:700;font-size:1.02rem!important}
p,label,span{color:#C3C7D1}
[data-testid="stCaptionContainer"]{color:var(--muted)}
[data-testid="stSidebar"]{background:var(--surface);border-right:1px solid var(--border)}
[data-testid="stMetric"]{background:var(--card);border:1px solid var(--border);border-radius:15px;padding:17px 18px;min-height:122px}
[data-testid="stMetricLabel"] p{color:var(--muted)!important;font-size:.82rem;font-weight:600}
[data-testid="stMetricValue"]{font-family:'Manrope',sans-serif;color:var(--text)!important;font-size:1.65rem}
[data-testid="stMetricDelta"]{font-size:.78rem}
div[data-testid="stForm"],div[data-testid="stExpander"]{background:var(--surface);border:1px solid var(--border);border-radius:14px}
div[data-testid="stForm"]{padding:18px}
.stButton button,.stDownloadButton button,button[kind="primary"],[data-testid="stFormSubmitButton"] button{border-radius:10px;border:1px solid #8B5CF6;background:#8B5CF6;color:white;font-weight:700;min-height:2.55rem;transition:all .18s ease}
.stButton button:hover,.stDownloadButton button:hover{background:#9B75FA;border-color:#9B75FA;transform:translateY(-1px)}
button[kind="secondary"]{background:#1C202B;border:1px solid var(--border);color:var(--text)}
input,textarea,[data-baseweb="select"]>div{background:#171B25!important;border-color:#343A48!important;border-radius:9px!important;color:var(--text)!important}
[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:12px;overflow:hidden}
hr{border-color:var(--border)}
[data-testid="stTabs"] button{color:var(--muted)}
[data-testid="stTabs"] button[aria-selected="true"]{color:var(--violet)}
div[data-testid="stAlert"]{border-radius:12px}
.ef-brand{display:flex;align-items:center;gap:10px;margin:0 0 22px}
.ef-mark{width:36px;height:36px;border-radius:11px;background:linear-gradient(145deg,#A78BFA,#7042D8);display:flex;align-items:center;justify-content:center;box-shadow:0 5px 20px #8B5CF633;overflow:hidden}.ef-mark svg{width:25px;height:25px;display:block}
.ef-word{font-family:Manrope;font-weight:800;font-size:21px;letter-spacing:-.8px;color:#F5F5F7}
.ef-word span{color:#A78BFA}
.eyebrow{color:#A78BFA;font-size:11px;font-weight:700;letter-spacing:.13em;text-transform:uppercase}
.hero{padding:10px 0 18px}
.hero-sub{color:var(--muted);font-size:14px;margin-top:5px}
.panel{background:var(--card);border:1px solid var(--border);border-radius:15px;padding:18px 20px}
.panel-title{font-family:Manrope;font-weight:700;font-size:15px;color:var(--text);margin-bottom:2px}
.panel-sub{color:var(--muted);font-size:12px;margin-bottom:12px}
.kpi-note{font-size:12px;color:var(--muted);margin-top:4px}
.insight{background:#151925;border:1px solid #2A3040;border-radius:12px;padding:14px 15px;height:100%}
.insight-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-weight:700}
.insight-value{font-family:Manrope;font-size:18px;color:var(--text);font-weight:700;margin:7px 0 3px}
.insight-copy{font-size:12px;color:var(--muted)}
.topline{display:flex;justify-content:space-between;align-items:center}
[data-testid="stRadio"]>div{gap:4px}
[data-testid="stRadio"] label{background:#151923;border:1px solid #272D39;padding:7px 13px;border-radius:9px}
[data-testid="stRadio"] label:has(input:checked){background:#29203F;border-color:#7652C7}
div[data-testid="stNotification"],.stToast{border-radius:12px}
@media(max-width:800px){.block-container{padding:1rem .8rem 2rem}.ef-word{font-size:19px}h1{font-size:1.6rem!important}}
</style>
""", unsafe_allow_html=True)

# ── Data layer (keeps existing SQLite tables and adds safe migrations) ─────────
def connect():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("""CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, tx_date TEXT NOT NULL,
        category TEXT NOT NULL, source TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
        amount REAL NOT NULL, status TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '')""")
    c.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
    existing = {r[1] for r in c.execute("PRAGMA table_info(transactions)").fetchall()}
    if "payment_method" not in existing:
        c.execute("ALTER TABLE transactions ADD COLUMN payment_method TEXT NOT NULL DEFAULT ''")
    defaults={"opening_cash":"0","tax_pct":"15","emergency_pct":"10","buffer_pct":"5","currency":"USD ($)"}
    for k,v in defaults.items(): c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,v))
    c.commit()
    return c

conn=connect()
def setting(k):
    r=conn.execute("SELECT value FROM settings WHERE key=?",(k,)).fetchone()
    return r[0] if r else ""
def set_setting(k,v):
    conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",(k,str(v)));conn.commit()
def load_data():
    d=pd.read_sql_query("SELECT id,kind,tx_date,category,source,description,amount,status,notes,payment_method FROM transactions ORDER BY tx_date DESC,id DESC",conn)
    if not d.empty: d["tx_date"]=pd.to_datetime(d["tx_date"])
    return d
def sym_for(c): return {"USD ($)":"$","GBP (£)":"£","EUR (€)":"€","INR (₹)":"₹","CAD ($)":"CA$","AUD ($)":"A$"}.get(c,"$")
def cash(v): return f"{symbol}{v:,.2f}"
def total(d,kind,statuses=None):
    x=d[d.kind==kind] if not d.empty else d
    if statuses: x=x[x.status.isin(statuses)]
    return float(x.amount.sum()) if not x.empty else 0.0
def month_frame(d,key):
    return d[d.tx_date.dt.strftime("%Y-%m")==key].copy() if not d.empty else d.copy()
def pct_delta(cur,prev):
    if prev==0: return None if cur==0 else 100.0
    return (cur-prev)/abs(prev)*100
def plot_theme(fig,height=300):
    fig.update_layout(height=height,margin=dict(l=5,r=5,t=12,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans",color="#9298A6",size=11),legend=dict(font=dict(color="#BFC4CE"),bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#202431",bordercolor="#343B4B",font_color="#F5F5F7"))
    fig.update_xaxes(showgrid=False,color="#9298A6",linecolor="#292E3A")
    fig.update_yaxes(showgrid=True,gridcolor="#252B36",zerolinecolor="#3A4150",color="#9298A6")
    return fig

today=date.today()
currency_options=["USD ($)","GBP (£)","EUR (€)","INR (₹)","CAD ($)","AUD ($)"]
currency=st.session_state.get("currency",setting("currency") if setting("currency") in currency_options else "USD ($)")
symbol=sym_for(currency)
data=load_data()
month_list=pd.date_range(end=today.replace(day=1),periods=24,freq="MS").strftime("%Y-%m").tolist()
default_month=today.strftime("%Y-%m")
if "report_month" not in st.session_state: st.session_state.report_month=default_month

# ── Header / Navigation ───────────────────────────────────────────────────────
st.markdown("<div class='ef-brand'><div class='ef-mark'><svg viewBox='0 0 32 32' fill='none' aria-hidden='true'><path d='M25 5H12.5C8.4 5 5 8.4 5 12.5S8.4 20 12.5 20H25' stroke='white' stroke-width='3.2' stroke-linecap='round'/><path d='M25 12H13.5C10.5 12 8 14.5 8 17.5S10.5 23 13.5 23H25' stroke='white' stroke-width='3.2' stroke-linecap='round' opacity='.82'/><path d='M25 19H15C13.1 19 11.5 20.6 11.5 22.5S13.1 26 15 26H25' stroke='white' stroke-width='3.2' stroke-linecap='round' opacity='.64'/></svg></div><div class='ef-word'>Earn<span>Flow</span></div></div>",unsafe_allow_html=True)
nav_items=["Overview","Transactions","Income","Expenses","Analytics","Allocations","Income forecast","Settings"]
if "page" not in st.session_state: st.session_state.page="Overview"
nav_cols=st.columns([1.05,1.05,0.8,0.9,0.9,1.0,1.25,0.75])
for col,item in zip(nav_cols,nav_items):
    with col:
        if st.button(item, key="nav_"+item, use_container_width=True, type="primary" if st.session_state.page==item else "secondary"):
            st.session_state.page=item;st.rerun()
st.markdown("<hr style='margin:10px 0 22px'>",unsafe_allow_html=True)

# Shared helpers
def header(title,sub,tag="YOUR MONEY, IN YOUR FLOW"):
    st.markdown(f"<div class='hero'><div class='eyebrow'>{tag}</div><h1 style='margin:7px 0 0'>{title}</h1><div class='hero-sub'>{sub}</div></div>",unsafe_allow_html=True)
def month_picker():
    a,b=st.columns([1,4])
    with a:
        chosen=st.selectbox("Reporting month",month_list[::-1],index=month_list[::-1].index(st.session_state.report_month) if st.session_state.report_month in month_list else 0,key="month_select")
        st.session_state.report_month=chosen
    return st.session_state.report_month
def transaction_form(kind,form_key):
    is_income=kind=="Income"
    categories=(["Freelance client","Creator / sponsorship","Gig platform","Contract / retainer","Affiliate / royalties","Other"] if is_income else
                ["Housing","Utilities","Groceries","Transport","Software & subscriptions","Equipment","Marketing","Insurance","Taxes","Other"])
    with st.form(form_key,clear_on_submit=True):
        st.markdown(f"**{kind} details**")
        c1,c2=st.columns(2)
        amount=c1.number_input(f"Amount ({symbol})",min_value=0.0,step=50.0 if is_income else 25.0,format="%.2f")
        txdate=c2.date_input("Date",value=today)
        c3,c4=st.columns(2)
        category=c3.selectbox("Category",categories)
        status=c4.selectbox("Status",["Received","Pending"] if is_income else ["Paid","Unpaid"])
        desc=st.text_input("Description",placeholder="e.g. Website redesign milestone" if is_income else "e.g. Monthly software subscription")
        source=st.text_input("Client / platform / payee",placeholder="e.g. Upwork, YouTube, client name" if is_income else "e.g. Adobe, landlord, utility provider")
        c5,c6=st.columns(2)
        method=c5.selectbox("Payment method",["Bank transfer","Card","Cash","PayPal","Stripe","UPI","Platform payout","Other"])
        notes=c6.text_input("Notes (optional)",placeholder="Add a detail you'll want to remember")
        submitted=st.form_submit_button(f"＋ Save {kind.lower()}",type="primary",use_container_width=True)
        if submitted:
            if amount<=0: st.error("Enter an amount greater than zero.")
            elif not desc.strip(): st.error("Add a short description so you can recognize this entry.")
            else:
                conn.execute("INSERT INTO transactions(kind,tx_date,category,source,description,amount,status,notes,payment_method) VALUES(?,?,?,?,?,?,?,?,?)",
                    (kind,txdate.isoformat(),category,source.strip(),desc.strip(),amount,status,notes.strip(),method))
                conn.commit();st.toast(f"{kind} saved successfully.",icon="✓");st.rerun()

def transaction_table(frame,keyprefix="tbl",allow_delete=False):
    if frame.empty:
        st.info("Nothing here yet. Add your first entry to start building a clear picture of your money.")
        return
    search=st.text_input("Search transactions",placeholder="Search description, category, client or payee…",key=keyprefix+"_search")
    c1,c2=st.columns(2)
    kinds=c1.multiselect("Type",["Income","Expense"],default=["Income","Expense"],key=keyprefix+"_kind")
    statuses=c2.multiselect("Status",sorted(frame.status.dropna().unique().tolist()),default=sorted(frame.status.dropna().unique().tolist()),key=keyprefix+"_status")
    f=frame[frame.kind.isin(kinds)&frame.status.isin(statuses)].copy()
    if search:
        mask=f[["description","category","source","notes"]].fillna("").astype(str).agg(" ".join,axis=1).str.contains(search,case=False,na=False)
        f=f[mask]
    view=f.copy()
    view["Date"]=view.tx_date.dt.strftime("%d %b %Y")
    view["Amount"]=view.apply(lambda r:("+" if r.kind=="Income" else "−")+cash(float(r.amount)),axis=1)
    view=view.rename(columns={"kind":"Type","category":"Category","description":"Description","source":"Client / payee","status":"Status","payment_method":"Payment method"})
    st.dataframe(view[["Date","Type","Description","Category","Client / payee","Status","Amount","Payment method"]],use_container_width=True,hide_index=True)
    if allow_delete:
        with st.expander("Manage an entry"):
            options={f"#{int(r.id)} · {r.description} · {cash(float(r.amount))}":int(r.id) for r in f.itertuples()}
            if options:
                selected=st.selectbox("Choose an entry",list(options),key=keyprefix+"_delete")
                st.warning("Deleting a transaction cannot be undone.")
                if st.button("Delete selected transaction",key=keyprefix+"_delete_btn"):
                    conn.execute("DELETE FROM transactions WHERE id=?",(options[selected],));conn.commit();st.toast("Transaction deleted.",icon="✓");st.rerun()

page=st.session_state.page
if page=="Overview":
    header("Your money, made clearer.","A simple view of what came in, what went out, and what remains available.")
    chosen=month_picker(); current=month_frame(data,chosen)
    previous_key=(pd.Period(chosen)-1).strftime("%Y-%m"); previous=month_frame(data,previous_key)
    inc=total(current,"Income",["Received"]);exp=total(current,"Expense",["Paid","Unpaid"])
    net=inc-total(current,"Expense",["Paid"]); savings=(net/inc*100) if inc else 0
    p_inc=total(previous,"Income",["Received"]);p_exp=total(previous,"Expense",["Paid","Unpaid"])
    p_net=p_inc-total(previous,"Expense",["Paid"]);p_sav=(p_net/p_inc*100) if p_inc else 0
    a,b=st.columns([3,1])
    with a:
        st.markdown(f"<div class='eyebrow'>MONTHLY SNAPSHOT · {pd.Period(chosen).strftime('%B %Y').upper()}</div>",unsafe_allow_html=True)
    with b:
        if st.button("＋ Add transaction",type="primary",use_container_width=True): st.session_state.quick_add=True
    if st.session_state.get("quick_add",False):
        with st.expander("Add a transaction",expanded=True):
            kind=st.radio("Transaction type",["Income","Expense"],horizontal=True,key="quick_kind")
            transaction_form(kind,"quick_transaction_form")
    k1,k2,k3,k4=st.columns(4)
    for col,label,val,prev,fmt in [(k1,"Total income",inc,p_inc,"money"),(k2,"Total expenses",exp,p_exp,"money"),(k3,"Net profit",net,p_net,"money"),(k4,"Savings rate",savings,p_sav,"pct")]:
        delta=pct_delta(val,prev)
        dtext=("No prior month comparison" if delta is None else f"{delta:+.1f}% vs last month")
        col.metric(label,cash(val) if fmt=="money" else f"{val:.1f}%",dtext,delta_color="normal" if (label=="Total income" or label=="Net profit" or label=="Savings rate") else "inverse",
                   help="Compared with the previous calendar month. Net profit uses received income minus paid expenses; savings rate is net profit divided by received income.")
    st.caption("Your net profit is received income minus paid expenses. Unpaid bills are shown separately in the cash-flow view.")
    # Cash flow chart
    st.markdown("### Cash flow")
    chart_filter=st.radio("View",["Daily","Weekly","Monthly","Yearly"],horizontal=True,key="cashflow_period")
    if not data.empty:
        if chart_filter=="Daily":
            start=pd.Period(chosen).start_time;end=pd.Period(chosen).end_time
            plot=data[(data.tx_date>=start)&(data.tx_date<=end)].copy();plot["Period"]=plot.tx_date.dt.strftime("%d %b")
        elif chart_filter=="Weekly":
            start=pd.Period(chosen).start_time;end=pd.Period(chosen).end_time
            plot=data[(data.tx_date>=start)&(data.tx_date<=end)].copy();plot["Period"]=plot.tx_date.dt.to_period("W").apply(lambda x:x.start_time.strftime("%d %b"))
        elif chart_filter=="Monthly":
            plot=data[data.tx_date>=today-timedelta(days=365)].copy();plot["Period"]=plot.tx_date.dt.to_period("M").astype(str)
        else:
            plot=data.copy();plot["Period"]=plot.tx_date.dt.to_period("Y").astype(str)
        if not plot.empty:
            agg=plot.assign(value=plot.apply(lambda r: r.amount if ((r.kind=="Income" and r.status=="Received") or (r.kind=="Expense" and r.status=="Paid")) else 0,axis=1))
            agg=agg.groupby(["Period","kind"],as_index=False).value.sum()
            fig=px.area(agg,x="Period",y="value",color="kind",markers=True,color_discrete_map={"Income":"#8B5CF6","Expense":"#55C99A"},labels={"value":f"Amount ({symbol})","kind":"Flow"})
            fig.update_traces(line=dict(width=2.5),fill="tozeroy",opacity=.78,hovertemplate="%{x}<br>%{fullData.name}: "+symbol+"%{y:,.2f}<extra></extra>")
            st.plotly_chart(plot_theme(fig,310),use_container_width=True,config={"displayModeBar":False})
        else: st.info("Add transactions in this period to see your cash-flow trend.")
    else: st.info("Your cash-flow chart will appear once you add a few transactions.")
    # Split breakdowns
    left,right=st.columns([1.05,1])
    with left:
        st.markdown("### Where income comes from")
        src=current[(current.kind=="Income")&(current.status=="Received")]
        if not src.empty:
            breakdown=src.groupby("category",as_index=False).amount.sum().sort_values("amount",ascending=False)
            fig=px.pie(breakdown,names="category",values="amount",hole=.72,color_discrete_sequence=["#8B5CF6","#A78BFA","#55C99A","#D8B46A","#6B9CEB","#D47F9B"])
            fig.update_traces(textinfo="percent",hovertemplate="%{label}<br>"+symbol+"%{value:,.2f}<extra></extra>")
            fig.update_layout(showlegend=True,legend=dict(orientation="h",y=-.12))
            st.plotly_chart(plot_theme(fig,260),use_container_width=True,config={"displayModeBar":False})
            st.caption(f"Total received: **{cash(inc)}**")
        else: st.info("Received income by source will appear here.")
    with right:
        st.markdown("### Financial insights")
        expenses=current[(current.kind=="Expense")&(current.status.isin(["Paid","Unpaid"]))]
        if not expenses.empty:
            bycat=expenses.groupby("category").amount.sum().sort_values(ascending=False)
            topcat=bycat.index[0]
            st.markdown(f"<div class='insight'><div class='insight-label'>Highest spending category</div><div class='insight-value'>{topcat}</div><div class='insight-copy'>{cash(float(bycat.iloc[0]))} recorded this month</div></div>",unsafe_allow_html=True)
        else: st.markdown("<div class='insight'><div class='insight-label'>Spending patterns</div><div class='insight-value'>Waiting for data</div><div class='insight-copy'>Add expenses to discover your largest categories.</div></div>",unsafe_allow_html=True)
        growth=pct_delta(inc,p_inc)
        insight="No previous month data yet" if growth is None else f"Income is {abs(growth):.1f}% {'up' if growth>=0 else 'down'} from last month"
        st.markdown(f"<div class='insight' style='margin-top:10px'><div class='insight-label'>Income momentum</div><div class='insight-value'>{cash(inc)}</div><div class='insight-copy'>{insight}</div></div>",unsafe_allow_html=True)
    st.markdown("### Recent transactions")
    transaction_table(current.sort_values("tx_date",ascending=False).head(7),"overview_recent",False)
    st.caption("Earnflow is an organizational tool. It does not provide tax, investment or financial advice.")

elif page=="Transactions":
    header("Transactions","Every payment and purchase, in one searchable place.")
    c1,c2=st.columns([1,1])
    with c1:
        with st.expander("＋ Add a transaction",expanded=True):
            kind=st.radio("Type",["Income","Expense"],horizontal=True,key="all_tx_kind")
            transaction_form(kind,"all_tx_form")
    with c2:
        st.markdown("<div class='panel'><div class='panel-title'>Your activity</div><div class='panel-sub'>Search, filter and manage saved entries.</div></div>",unsafe_allow_html=True)
        st.metric("Total records",len(data))
        st.metric("All-time income received",cash(total(data,"Income",["Received"])))
        st.metric("All-time expenses paid",cash(total(data,"Expense",["Paid"])))
    st.markdown("### All transactions")
    transaction_table(data,"all_transactions",True)

elif page=="Income":
    header("Income","Keep track of client payments, platform payouts, retainers and creator earnings.")
    with st.expander("＋ Add income",expanded=True): transaction_form("Income","income_form_new")
    incdata=data[data.kind=="Income"].copy()
    st.markdown("### Income history")
    transaction_table(incdata,"income_history",True)

elif page=="Expenses":
    header("Expenses","Track bills, subscriptions and business costs without the spreadsheet clutter.")
    with st.expander("＋ Add expense",expanded=True): transaction_form("Expense","expense_form_new")
    expdata=data[data.kind=="Expense"].copy()
    st.markdown("### Expense history")
    transaction_table(expdata,"expense_history",True)

elif page=="Analytics":
    header("Analytics","Spot trends in your earnings and spending over time.")
    if not data.empty:
        monthly=data.copy();monthly["Month"]=monthly.tx_date.dt.to_period("M").astype(str)
        agg=monthly.assign(Received=monthly.apply(lambda r:r.amount if r.kind=="Income" and r.status=="Received" else 0,axis=1),
                           Spent=monthly.apply(lambda r:r.amount if r.kind=="Expense" and r.status=="Paid" else 0,axis=1))
        agg=agg.groupby("Month",as_index=False)[["Received","Spent"]].sum()
        fig=go.Figure()
        fig.add_trace(go.Bar(x=agg.Month,y=agg.Received,name="Income",marker_color="#8B5CF6"))
        fig.add_trace(go.Bar(x=agg.Month,y=agg.Spent,name="Expenses",marker_color="#55C99A"))
        fig.update_layout(barmode="group",yaxis_title=f"Amount ({symbol})")
        st.plotly_chart(plot_theme(fig,350),use_container_width=True)
        l,r=st.columns(2)
        with l:
            st.markdown("### Expense categories")
            cat=data[(data.kind=="Expense")&(data.status=="Paid")].groupby("category",as_index=False).amount.sum().sort_values("amount",ascending=False)
            if not cat.empty:
                f=px.bar(cat,x="amount",y="category",orientation="h",color="amount",color_continuous_scale=["#34254F","#A78BFA"],labels={"amount":f"Amount ({symbol})","category":""})
                f.update_layout(coloraxis_showscale=False);st.plotly_chart(plot_theme(f,300),use_container_width=True)
            else: st.info("Paid expense categories will appear here.")
        with r:
            st.markdown("### Income sources")
            src=data[(data.kind=="Income")&(data.status=="Received")].groupby("source",as_index=False).amount.sum().sort_values("amount",ascending=False)
            if not src.empty:
                f=px.bar(src,x="amount",y="source",orientation="h",color="amount",color_continuous_scale=["#35264F","#8B5CF6"],labels={"amount":f"Amount ({symbol})","source":""})
                f.update_layout(coloraxis_showscale=False);st.plotly_chart(plot_theme(f,300),use_container_width=True)
            else: st.info("Received income sources will appear here.")
    else: st.info("Analytics will become available after you add transactions.")

elif page=="Allocations":
    header("Pay yourself with a plan","Choose how much of received income you want to set aside before treating the remainder as personal pay.")
    st.info("Allocation percentages are customizable planning choices, not tax recommendations.")
    tax=float(setting("tax_pct") or 0);emergency=float(setting("emergency_pct") or 0);buffer=float(setting("buffer_pct") or 0)
    with st.form("allocation_form"):
        a,b,c=st.columns(3)
        tax_new=a.number_input("Tax reserve (%)",0.0,100.0,tax,.5)
        emergency_new=b.number_input("Emergency fund (%)",0.0,100.0,emergency,.5)
        buffer_new=c.number_input("Business buffer (%)",0.0,100.0,buffer,.5)
        reserved=tax_new+emergency_new+buffer_new
        st.metric("Reserved",f"{reserved:.1f}%")
        st.caption(f"Personal pay: {max(0,100-reserved):.1f}%")
        if st.form_submit_button("Save allocation plan",type="primary",use_container_width=True):
            if reserved>100: st.error("Your reserve percentages cannot exceed 100% in total.")
            else:
                set_setting("tax_pct",tax_new);set_setting("emergency_pct",emergency_new);set_setting("buffer_pct",buffer_new)
                st.toast("Allocation plan saved.",icon="✓");st.rerun()
    chosen=st.session_state.report_month;cur=month_frame(data,chosen);received=total(cur,"Income",["Received"])
    st.markdown("### Your current plan")
    buckets=[("Tax reserve",tax_new if "tax_new" in locals() else tax, "#8B5CF6"),("Emergency fund",emergency_new if "emergency_new" in locals() else emergency,"#55C99A"),("Business buffer",buffer_new if "buffer_new" in locals() else buffer,"#D8B46A"),("Personal pay",max(0,100-(tax+emergency+buffer)),"#6B9CEB")]
    for name,p,color in buckets:
        amount=received*p/100
        st.markdown(f"**{name}** · {p:.1f}% · {cash(amount)}")
        st.progress(min(1,p/100))

elif page=="Income forecast":
    header("Income forecast","Try a quieter month scenario and see how much room your plan leaves.")
    opening=float(setting("opening_cash") or 0);tax=float(setting("tax_pct") or 0);em=float(setting("emergency_pct") or 0);buf=float(setting("buffer_pct") or 0)
    chosen=st.session_state.report_month;cur=month_frame(data,chosen)
    a,b=st.columns(2)
    forecast=a.number_input(f"Expected income ({symbol})",min_value=0.0,value=total(cur,"Income",["Received"]),step=100.0)
    essentials=b.number_input(f"Essential expenses ({symbol})",min_value=0.0,value=total(cur,"Expense",["Paid","Unpaid"]),step=100.0)
    reserves=forecast*(tax+em+buf)/100;balance=opening+forecast-essentials-reserves
    x,y,z=st.columns(3);x.metric("Forecast income",cash(forecast));y.metric("Planned reserves",cash(reserves));z.metric("Estimated remaining",cash(balance))
    if balance<0: st.error("This scenario shows a shortfall. Consider adjusting the forecast or reviewing discretionary costs.")
    else: st.success("This scenario covers the expenses and reserves you entered.")
    st.caption("This is a scenario estimate, not a prediction. Pending income is not guaranteed.")

elif page=="Settings":
    header("Settings","Make Earnflow feel like yours and keep a portable copy of your records.")
    with st.form("settings_form"):
        currency_new=st.selectbox("Display currency",currency_options,index=currency_options.index(setting("currency")) if setting("currency") in currency_options else 0)
        opening=float(setting("opening_cash") or 0)
        opening_new=st.number_input(f"Opening available cash ({sym_for(currency_new)})",min_value=0.0,value=opening,step=50.0)
        if st.form_submit_button("Save settings",type="primary",use_container_width=True):
            set_setting("currency",currency_new);set_setting("opening_cash",opening_new)
            st.session_state.currency=currency_new;st.toast("Settings saved.",icon="✓");st.rerun()
    st.markdown("### Data backup")
    if not data.empty:
        export=data.copy();export["tx_date"]=export.tx_date.dt.strftime("%Y-%m-%d")
        st.download_button("↓ Download transaction backup (CSV)",export.to_csv(index=False).encode("utf-8"),"earnflow_transactions.csv","text/csv")
    else: st.info("Your records will be available to export once you add transactions.")
    st.markdown("### About your data")
    st.warning("This version stores data in a local SQLite database on the machine running the app. It has no sign-in or per-user data separation. Do not deploy it publicly with real customer financial data until authentication, isolated cloud storage, backups and a security review are in place.")
    st.caption(f"Database file: {DB_PATH.name}")

st.markdown("<hr><div style='text-align:center;color:#727987;font-size:11px;padding:12px 0'>EARNFLOW · MONEY, IN YOUR FLOW · AN ORGANIZATIONAL TOOL, NOT TAX OR INVESTMENT ADVICE</div>",unsafe_allow_html=True)
