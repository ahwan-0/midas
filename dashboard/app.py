import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html
import random

# ── SYNTHETIC DATA ────────────────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

USERS = ['Alice', 'Bob', 'Charlie', 'Diana', 'Ethan',
         'Fiona', 'George', 'Hannah', 'Ivan', 'Julia']
INIT_BALANCES = [5200, 3800, 6100, 4400, 7200, 2900, 5500, 3200, 4800, 6600]

# Simulate 50 transactions
transactions = []
balances = INIT_BALANCES[:]

for i in range(50):
    sender = random.randint(0, 9)
    recipient = random.randint(0, 9)
    while recipient == sender:
        recipient = random.randint(0, 9)
    amount    = round(random.uniform(50, 800), 2)
    incentive = round(random.uniform(5, 80), 2)
    valid     = balances[sender] >= amount
    if valid:
        balances[sender]    -= amount
        balances[recipient] += amount + incentive
    transactions.append({
        'id'        : i + 1,
        'sender'    : USERS[sender],
        'recipient' : USERS[recipient],
        'amount'    : amount,
        'incentive' : incentive if valid else 0,
        'valid'     : valid,
        'minute'    : i // 5,
        'sender_idx': sender,
    })

# ── PRECOMPUTE METRICS ────────────────────────────────────────────────────────
valid_txns    = [t for t in transactions if t['valid']]
rejected_txns = [t for t in transactions if not t['valid']]

TOTAL_VALID      = len(valid_txns)
TOTAL_REJECTED   = len(rejected_txns)
TOTAL_INCENTIVES = round(sum(t['incentive'] for t in valid_txns), 2)
TOTAL_VOLUME     = round(sum(t['amount'] for t in valid_txns), 2)

# Volume by minute
volume_by_minute = [0] * 10
for t in valid_txns:
    volume_by_minute[t['minute']] += 1

# Sent per user
sent_by_user = {u: 0.0 for u in USERS}
for t in valid_txns:
    sent_by_user[t['sender']] += t['amount']
sent_sorted = sorted(sent_by_user.items(), key=lambda x: x[1], reverse=True)

# ── THEME ─────────────────────────────────────────────────────────────────────
GOLD        = '#C9A84C'
GOLD_BRIGHT = '#F0C040'
GOLD_DIM    = '#7A6030'
BG          = '#080A0E'
BG2         = '#0E1118'
SURFACE     = '#1A1F2E'
TEXT        = '#E8E0CC'
TEXT_DIM    = '#8A8070'
GREEN       = '#4CAF82'
RED         = '#CF6679'
BLUE        = '#2A6496'
BORDER      = 'rgba(201,168,76,0.15)'

PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='JetBrains Mono, monospace', color=TEXT_DIM, size=10),
    margin=dict(t=20, r=20, b=40, l=55),
    xaxis=dict(gridcolor='rgba(201,168,76,0.08)', zerolinecolor='rgba(201,168,76,0.15)'),
    yaxis=dict(gridcolor='rgba(201,168,76,0.08)', zerolinecolor='rgba(201,168,76,0.15)'),
)

# ── CHARTS ────────────────────────────────────────────────────────────────────
def fig_volume():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[f'T+{i}m' for i in range(10)],
        y=volume_by_minute,
        mode='lines+markers',
        line=dict(color=GOLD, width=2, shape='spline'),
        marker=dict(color=GOLD_BRIGHT, size=7),
        fill='tozeroy',
        fillcolor='rgba(201,168,76,0.07)',
        name='Transactions',
    ))
    fig.update_layout(**PLOT_LAYOUT, height=280,
        yaxis_title='Transactions', xaxis_title='Time')
    return fig


def fig_balances():
    colors = [GOLD if b > 5000 else GOLD_DIM if b > 3000 else '#4A3810' for b in balances]
    fig = go.Figure(go.Bar(
        x=USERS, y=[round(b, 2) for b in balances],
        marker=dict(color=colors, line=dict(color=BORDER, width=1)),
        text=[f'${b:,.0f}' for b in balances],
        textposition='outside',
        textfont=dict(size=9, color=TEXT_DIM),
    ))
    fig.update_layout(**PLOT_LAYOUT, height=300,
        yaxis_tickprefix='$', yaxis_title='Balance')
    return fig


def fig_hist():
    amounts = [t['amount'] for t in valid_txns]
    fig = go.Figure(go.Histogram(
        x=amounts, nbinsx=15,
        marker=dict(color='rgba(201,168,76,0.5)',
                    line=dict(color=GOLD, width=1)),
    ))
    fig.update_layout(**PLOT_LAYOUT, height=280,
        xaxis_tickprefix='$', yaxis_title='Count',
        xaxis_title='Transfer Amount')
    return fig


def fig_scatter():
    fig = go.Figure(go.Scatter(
        x=[t['amount'] for t in valid_txns],
        y=[t['incentive'] for t in valid_txns],
        mode='markers',
        marker=dict(color=GREEN, size=8, opacity=0.75,
                    line=dict(color='rgba(76,175,130,0.3)', width=1)),
        text=[f"{t['sender']} → {t['recipient']}" for t in valid_txns],
        hovertemplate='Transfer: $%{x}<br>Incentive: $%{y}<br>%{text}<extra></extra>',
    ))
    fig.update_layout(**PLOT_LAYOUT, height=280,
        xaxis_title='Transfer Amount ($)',
        yaxis_title='Incentive ($)')
    return fig


def fig_pie():
    fig = go.Figure(go.Pie(
        values=[TOTAL_VALID, TOTAL_REJECTED],
        labels=['Valid', 'Rejected'],
        hole=0.55,
        marker=dict(colors=[GOLD, RED], line=dict(color=BG, width=3)),
        textfont=dict(family='JetBrains Mono', size=10),
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='JetBrains Mono', color=TEXT_DIM, size=10),
        showlegend=True,
        legend=dict(font=dict(size=10), bgcolor='rgba(0,0,0,0)'),
        height=280, margin=dict(t=20, r=20, b=20, l=20),
    )
    return fig


def fig_top_senders():
    names = [s[0] for s in sent_sorted[:6]]
    vals  = [round(s[1], 2) for s in sent_sorted[:6]]
    fig = go.Figure(go.Bar(
        x=vals, y=names,
        orientation='h',
        marker=dict(color=BLUE, line=dict(color='rgba(42,100,150,0.4)', width=1)),
        text=[f'${v:,.0f}' for v in vals],
        textposition='outside',
        textfont=dict(size=9, color=TEXT_DIM),
    ))
    
    fig.update_layout(**PLOT_LAYOUT, height=280,
    xaxis_tickprefix='$', xaxis_title='Total Sent')
    return fig


# ── CARD COMPONENT ────────────────────────────────────────────────────────────
def kpi_card(value, label, color=GOLD_BRIGHT):
    return html.Div([
        html.Span(str(value), style={
            'display': 'block', 'fontSize': '2.2rem', 'fontWeight': '600',
            'color': color, 'marginBottom': '6px',
        }),
        html.Span(label.upper(), style={
            'fontSize': '0.6rem', 'letterSpacing': '0.2em', 'color': TEXT_DIM,
        }),
    ], style={
        'background': BG2, 'padding': '1.8rem',
        'borderRight': f'1px solid {BORDER}', 'textAlign': 'center', 'flex': '1',
    })


def chart_card(title, subtitle, figure):
    return html.Div([
        html.Div(title.upper(), style={
            'fontSize': '0.65rem', 'letterSpacing': '0.2em',
            'color': GOLD, 'marginBottom': '4px',
        }),
        html.Div(subtitle, style={
            'fontFamily': 'Crimson Pro, serif', 'fontSize': '0.9rem',
            'fontStyle': 'italic', 'color': TEXT_DIM, 'marginBottom': '0.5rem',
        }),
        dcc.Graph(figure=figure, config={'displayModeBar': False}),
    ], style={
        'background': SURFACE, 'border': f'1px solid {BORDER}',
        'padding': '1.2rem', 'flex': '1',
    })


# ── TASK CARD ─────────────────────────────────────────────────────────────────
def task_card(num, title, desc, tags):
    return html.Div([
        html.Div(f'TASK {num:02d}', style={
            'fontSize': '0.6rem', 'letterSpacing': '0.2em',
            'color': GOLD_DIM, 'marginBottom': '8px',
        }),
        html.Div(title, style={
            'fontFamily': 'Playfair Display, serif', 'fontSize': '1.05rem',
            'marginBottom': '6px', 'color': TEXT,
        }),
        html.Div(desc, style={
            'fontFamily': 'Crimson Pro, serif', 'fontSize': '0.9rem',
            'color': TEXT_DIM, 'fontStyle': 'italic',
            'lineHeight': '1.6', 'marginBottom': '10px',
        }),
        html.Div([
            html.Span(t, style={
                'fontSize': '0.58rem', 'letterSpacing': '0.1em',
                'padding': '3px 8px', 'marginRight': '6px',
                'border': f'1px solid {GOLD_DIM}', 'color': GOLD,
            }) for t in tags
        ] + [html.Span('✓ PASSING', style={
            'fontSize': '0.58rem', 'letterSpacing': '0.1em',
            'padding': '3px 8px', 'border': f'1px solid rgba(76,175,130,0.4)',
            'color': GREEN,
        })]),
    ], style={
        'background': BG2, 'padding': '1.8rem',
        'borderLeft': f'3px solid {GOLD_DIM}',
        'transition': 'border-color 0.3s',
    })


# ── LAYOUT ────────────────────────────────────────────────────────────────────
app = Dash(__name__)
app.title = 'Midas Base — JPMorgan Forage'

app.layout = html.Div(style={
    'background': BG, 'color': TEXT, 'minHeight': '100vh',
    'fontFamily': 'JetBrains Mono, monospace',
}, children=[

    # Google Fonts
    html.Link(rel='preconnect', href='https://fonts.googleapis.com'),
    html.Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=JetBrains+Mono:wght@300;400;600&family=Crimson+Pro:ital,wght@0,300;1,300&display=swap'),

    # ── HERO ──────────────────────────────────────────────────────────
    html.Div([
        html.Div('JPMorgan Chase · Forage · Spring Boot 3.2', style={
            'fontSize': '0.65rem', 'letterSpacing': '0.2em', 'color': GOLD,
            'border': f'1px solid {GOLD_DIM}', 'padding': '6px 14px',
            'display': 'inline-block', 'marginBottom': '2rem',
        }),
        html.H1([
            html.Span('Midas', style={'display': 'block'}),
            html.Span('Base', style={'color': GOLD, 'display': 'block'}),
        ], style={
            'fontFamily': 'Playfair Display, serif',
            'fontSize': 'clamp(4rem, 10vw, 8rem)',
            'fontWeight': '900', 'lineHeight': '0.9',
            'letterSpacing': '-0.02em', 'marginBottom': '1.5rem',
        }),
        html.P('A complete implementation of the JPMorgan Chase Forage virtual internship  building a real-time transaction processing system from scratch.', style={
            'fontFamily': 'Crimson Pro, serif', 'fontSize': '1.2rem',
            'fontStyle': 'italic', 'color': TEXT_DIM,
            'maxWidth': '500px', 'lineHeight': '1.7', 'marginBottom': '2rem',
        }),
        # Mini KPI row in hero
        html.Div([
            html.Div([html.Span('5', style={'fontSize': '2rem', 'color': GOLD_BRIGHT, 'display': 'block'}), html.Span('TASKS', style={'fontSize': '0.6rem', 'color': TEXT_DIM, 'letterSpacing': '0.15em'})], style={'marginRight': '3rem'}),
            html.Div([html.Span('10', style={'fontSize': '2rem', 'color': GOLD_BRIGHT, 'display': 'block'}), html.Span('USERS', style={'fontSize': '0.6rem', 'color': TEXT_DIM, 'letterSpacing': '0.15em'})], style={'marginRight': '3rem'}),
            html.Div([html.Span('100%', style={'fontSize': '2rem', 'color': GOLD_BRIGHT, 'display': 'block'}), html.Span('TESTS PASSING', style={'fontSize': '0.6rem', 'color': TEXT_DIM, 'letterSpacing': '0.15em'})], style={'marginRight': '3rem'}),
            html.Div([html.Span('Java 17', style={'fontSize': '2rem', 'color': GOLD_BRIGHT, 'display': 'block', 'fontSize': '1.5rem'}), html.Span('SPRING BOOT 3.2', style={'fontSize': '0.6rem', 'color': TEXT_DIM, 'letterSpacing': '0.15em'})]),
        ], style={'display': 'flex', 'alignItems': 'flex-start'}),
    ], style={
        'padding': '8rem 8vw 5rem',
        'borderBottom': f'1px solid {BORDER}',
        'background': f'radial-gradient(ellipse 80% 60% at 70% 50%, rgba(201,168,76,0.05) 0%, transparent 60%)',
    }),

    # ── TASKS ─────────────────────────────────────────────────────────
    html.Div([
        html.Div('// 01 — IMPLEMENTATION', style={'fontSize': '0.65rem', 'letterSpacing': '0.25em', 'color': GOLD, 'marginBottom': '0.75rem'}),
        html.H2('Five Tasks. One System.', style={'fontFamily': 'Playfair Display, serif', 'fontSize': 'clamp(2rem, 4vw, 3rem)', 'marginBottom': '0.75rem'}),
        html.P('Each task builds on the last, culminating in a fully operational Kafka-powered transaction engine with incentive logic and REST endpoints.', style={
            'fontFamily': 'Crimson Pro, serif', 'fontSize': '1.05rem',
            'fontStyle': 'italic', 'color': TEXT_DIM, 'maxWidth': '600px',
            'lineHeight': '1.7', 'marginBottom': '2.5rem',
        }),
        html.Div([
            task_card(1, 'Kafka Consumer Setup',   'Wired Spring Boot to consume messages from the trader-updates topic using @KafkaListener and JsonDeserializer.',          ['Kafka', '@KafkaListener']),
            task_card(2, 'User Persistence',        'Implemented JPA repositories with H2 in-memory database. Built UserRecord entity with balance tracking.',                ['JPA', 'H2', 'Hibernate']),
            task_card(3, 'Transaction Validation',  'Validated sender/recipient existence and enforced sufficient balance checks before processing any transfer.',             ['@Transactional', 'BigDecimal']),
            task_card(4, 'Incentive Engine',        'Integrated external IncentiveService to compute and apply bonus amounts on top of each valid transaction.',               ['REST Client', 'IncentiveService']),
            task_card(5, 'Balance REST API',        'Exposed GET /balance endpoint returning real-time user balances. Full end-to-end integration test passing.',             ['@RestController', 'GET /balance']),
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(260px, 1fr))', 'gap': '1px', 'background': BORDER}),
    ], style={'padding': '5rem 8vw', 'borderBottom': f'1px solid {BORDER}'}),

    # ── KPI ROW ───────────────────────────────────────────────────────
    html.Div([
        html.Div('// 02 — SIMULATION METRICS', style={'fontSize': '0.65rem', 'letterSpacing': '0.25em', 'color': GOLD, 'marginBottom': '2rem'}),
        html.Div([
            kpi_card(TOTAL_VALID, 'Valid Transactions', GOLD_BRIGHT),
            kpi_card(TOTAL_REJECTED, 'Rejected', RED),
            kpi_card(f'${TOTAL_INCENTIVES:,.0f}', 'Incentives Paid', GREEN),
            kpi_card(f'${TOTAL_VOLUME:,.0f}', 'Total Volume', BLUE),
        ], style={'display': 'flex', 'border': f'1px solid {BORDER}'}),
    ], style={'padding': '5rem 8vw', 'borderBottom': f'1px solid {BORDER}'}),

    # ── CHARTS ROW 1 ──────────────────────────────────────────────────
    html.Div([
        html.Div('// 03 — ANALYTICS', style={'fontSize': '0.65rem', 'letterSpacing': '0.25em', 'color': GOLD, 'marginBottom': '0.75rem'}),
        html.H2('Transaction Analytics', style={'fontFamily': 'Playfair Display, serif', 'fontSize': 'clamp(2rem, 4vw, 3rem)', 'marginBottom': '0.75rem'}),
        html.P('Synthetic data simulating 10 users across 50 transactions with incentive payouts.', style={
            'fontFamily': 'Crimson Pro, serif', 'fontSize': '1.05rem',
            'fontStyle': 'italic', 'color': TEXT_DIM, 'marginBottom': '2rem',
        }),

        # Volume — full width
        html.Div([
            chart_card('Transaction Volume Over Time', 'Messages processed per minute during simulation run', fig_volume()),
        ], style={'display': 'flex', 'gap': '1.5rem', 'marginBottom': '1.5rem'}),

        # Balances + Histogram
        html.Div([
            chart_card('User Final Balances', 'Balance after all transactions + incentives applied', fig_balances()),
            chart_card('Transaction Amount Distribution', 'Histogram of transfer amounts across the session', fig_hist()),
        ], style={'display': 'flex', 'gap': '1.5rem', 'marginBottom': '1.5rem'}),

        # Scatter + Pie + Top Senders
        html.Div([
            chart_card('Incentive vs Transfer Amount', 'Correlation between transfer size and incentive paid', fig_scatter()),
            chart_card('Transaction Status Breakdown', 'Valid vs rejected transactions', fig_pie()),
            chart_card('Top Senders by Volume', 'Total amount sent per user', fig_top_senders()),
        ], style={'display': 'flex', 'gap': '1.5rem'}),

    ], style={'padding': '5rem 8vw', 'borderBottom': f'1px solid {BORDER}'}),

 # ── MIDAS EXTENDED CTA ────────────────────────────────────────────────
html.Div([
    html.Div('// NEXT LEVEL', style={'fontSize': '0.65rem', 'letterSpacing': '0.25em', 'color': GOLD, 'marginBottom': '0.75rem'}),
    html.H2('This was just the beginning.', style={
        'fontFamily': 'Playfair Display, serif',
        'fontSize': 'clamp(2rem, 4vw, 3rem)', 'marginBottom': '0.75rem',
    }),
    html.P('Midas Extended takes this foundation and builds a production grade ML/Data Engineering system on top. Apache Kafka pipelines, PostgreSQL, Apache Superset dashboards, and a real-time fraud detection engine powered by XGBoost and Isolation Forest.', style={
        'fontFamily': 'Crimson Pro, serif', 'fontSize': '1.05rem',
        'fontStyle': 'italic', 'color': TEXT_DIM, 'maxWidth': '640px',
        'lineHeight': '1.8', 'marginBottom': '2rem',
    }),
    html.A('Explore Midas Extended →', href='https://github.com/ahwan-0/midas-extended', target='_blank', style={
        'display': 'inline-block', 'padding': '12px 28px',
        'border': f'1px solid {GOLD}', 'color': GOLD,
        'textDecoration': 'none', 'fontSize': '0.7rem',
        'letterSpacing': '0.2em', 'textTransform': 'uppercase',
        'transition': 'all 0.3s',
    }),
], style={'padding': '5rem 8vw', 'borderBottom': f'1px solid {BORDER}'}),


    # ── FOOTER ────────────────────────────────────────────────────────
    html.Div([
        html.Span('Midas Base', style={'fontFamily': 'Playfair Display, serif', 'fontSize': '1.5rem', 'color': GOLD}),
        html.Div([
            html.A('GitHub → Midas', href='https://github.com/ahwan-0/midas', target='_blank',
                   style={'color': TEXT_DIM, 'textDecoration': 'none', 'fontSize': '0.65rem', 'letterSpacing': '0.15em', 'marginRight': '2rem'}),
            html.A('GitHub → Extended', href='https://github.com/ahwan-0/midas-extended', target='_blank',
                   style={'color': TEXT_DIM, 'textDecoration': 'none', 'fontSize': '0.65rem', 'letterSpacing': '0.15em', 'marginRight': '2rem'}),
            html.A('Forage Program', href='https://forage.com', target='_blank',
                   style={'color': TEXT_DIM, 'textDecoration': 'none', 'fontSize': '0.65rem', 'letterSpacing': '0.15em'}),
        ]),
    ], style={
        'padding': '2.5rem 8vw', 'display': 'flex',
        'justifyContent': 'space-between', 'alignItems': 'center',
    }),
])


server = app.server

if __name__ == "__main__":
    app.run(debug=True)
