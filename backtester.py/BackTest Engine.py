#!/usr/bin/env python
# coding: utf-8

# In[22]:


import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt

#====================
# PARAMETERS
#====================

atr_period = 14
atr = 80
atr_multiplier = 2

fsma = 5
ssma = 25

gap = 80


account_balance=10000

cost = 23


#position size

risk_per_trade = 0.02


#====================
# DATAFRAME
#====================



instruments ={

    "us100" :  r'C:\Users\FumaniBonganiMbata\Desktop\GER40Cash.csv',
    "ger40" :  r'C:\Users\FumaniBonganiMbata\Desktop\US100Cash.csv'
    }


def create_dataframe(file_source):

    df = pd.read_csv(file_source, header=None)
    df = df.drop(0)
    df = df[0].str.split('\t', expand=True)

    df['DateTime'] = pd.to_datetime(df[0].astype(str) + ' ' + df[1].astype(str), errors='coerce')

    df = df.drop(columns=[1,7,8])
    df = df.rename(columns={0:'Date',2:'Open',3:'High',4:'Low',5:'Close',6:'Volume'})

    df.index = pd.to_datetime(df['DateTime'], errors='coerce')
    df = df.sort_index()

    for col in ['Open','High','Low','Close','Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    #df = df.drop(columns=['DateTime'])

    return df

#====================
# INDICATORS
#====================

def create_atr(df, period):
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L','H-PC','L-PC']].max(axis=1)

    df['ATR'] = df['TR'].ewm(alpha=1/period, adjust=False).mean()

    df = df.drop(columns=['H-L','H-PC','L-PC','TR'])
    return df

def create_sma(df, fsma, ssma):
    df['fsma'] = df['Close'].rolling(fsma).mean()
    df['ssma'] = df['Close'].rolling(ssma).mean()
    return df

#====================
# ENHANCEMENTS
#====================

def enhancements(df):
    df['PC'] = df['Close'].shift(1)
    df['PO'] = df['Open'].shift(1)
    df['ssma_slope'] = df['ssma'].diff()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Trading_year'] = df['Date'].dt.year
    df = df.dropna()
    return df

#====================
# SIGNAL
#====================

def generate_signal(df):
    return (
        (df['Close'] >= df['fsma']) &
        (df['Close'] < df['ssma']) &
        (df['Open'] < df['fsma']) &

        (df['PC'] < df['fsma']) &
        (df['PO'] < df['fsma']) &

        (df['ATR'] > atr) &
        #(df['ATR'] < 100) &
        ((df['ssma'] - df['fsma']) > gap) &
        (df['ssma_slope'] < 0)
    )

#====================
# BACKTEST
#====================
def backtest(df):
    current_balance=10000
    trade_log = []

    i = 2
    signals = generate_signal(df)

    while i < len(df) - 1:

        if not signals.iloc[i]:
            i += 1
            continue

        entry = df['Close'].iloc[i]
        stop_loss = entry - (atr_multiplier * df['ATR'].iloc[i])
        risk = entry - stop_loss


        dollar_risk=current_balance * risk_per_trade
        position_size= dollar_risk/risk

        if risk <= 0:
            i += 1
            continue

        take_profit = entry + 2 * risk

        # CREATE NEW TRADE OBJECT
        trade = {
            'instrument':None,
            'entry_time': df['DateTime'].iloc[i],
            'entry_price': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk': risk,
            'exit_time': None,
            'exit_price': None,
            'return': None,
            'result': None,
            'r_multiple' :None,
            'time_frame' : 'Hourly',
            'position_size' :None,
            'price_movement' :None
        }

        trade_closed = False

        for j in range(i + 1, len(df)):

            high = df['High'].iloc[j]
            low = df['Low'].iloc[j]

            # TAKE PROFIT HIT
            if high >= take_profit:



                price_movement=take_profit-entry
                pnl = (price_movement) * position_size - cost



                trade['exit_time'] = df['DateTime'].iloc[j]
                trade['exit_price'] = take_profit
                trade['return'] = pnl
                trade['result'] = 1
                trade['r_multiple']=pnl/risk
                trade['position_size']=position_size
                trade['price_movement']=price_movement

                trade_log.append(trade)
                current_balance +=pnl

                i = j
                trade_closed = True
                break

            # STOP LOSS HIT
            if low <= stop_loss:


                price_movement=stop_loss-entry
                pnl = (price_movement )* position_size- cost



                trade['exit_time'] = df['DateTime'].iloc[j]
                trade['exit_price'] = stop_loss
                trade['return'] = pnl
                trade['result'] = 0
                trade['r_multiple']=-1
                trade['position_size']=position_size
                trade['price_movement']=price_movement

                trade_log.append(trade)
                current_balance +=pnl

                i = j
                trade_closed = True
                break

        # TRADE NEVER CLOSED
        if not trade_closed:



            trade['exit_time'] = df['DateTime'].iloc[-1]
            trade['exit_price'] = df['Close'].iloc[-1]
            trade['return'] = 0
            trade['result'] = 0
            trade['r_multiple']=0
            trade['position_size']=0
            trade['position_size']=0
            trade['price_movement']=0

            trade_log.append(trade)

            i += 1

    return pd.DataFrame(trade_log)

#====================
# BUILD DATA
#====================

dataframes = {}

for instrument, path in instruments.items():
    dataframes[instrument]=enhancements(create_sma(create_atr(create_dataframe(path), atr_period), fsma, ssma))

#====================
# RUN BACKTESTS
#====================

portfolio=[]
trades={}

all_trades= {}
for key in instruments.keys():
    all_trades[key]=[]

for year in [2021,2022,2023,2024,2025,2026]:

    for instrument,chart in dataframes.items():

        trades[instrument] = backtest(dataframes[instrument][dataframes[instrument] ['Trading_year']  == year])
        trades[instrument]['instrument']=instrument
        portfolio.append(trades.get(instrument))

        #print('METRICS')
        #print(f'Year: {year}')
        #print(f'Trades (US100 / GER40): {len(res)} / {len(res_ger)}')
        #print(f'Return (US100 / GER40): {sum(tr)} / {sum(tr_ger)}')
        #print('')


portfolio=pd.concat(portfolio)
portfolio=portfolio.sort_values('entry_time')
portfolio=portfolio.reset_index()

portfolio['holding_time']=portfolio['exit_time']- portfolio['entry_time']
portfolio['account_balance']= portfolio['return'].cumsum() + account_balance

#print(portfolio.head())
#portfolio.to_csv( r'C:\Users\FumaniBonganiMbata\Desktop\output2.csv')

#====================
# MONTE CARLO
#====================

def monte_carlo(simulations, portfolio):

    final_returns = []
    max_drawdowns = []

    trade_returns = portfolio['return'].values

    for i in range(simulations):

        # Randomize trade order
        shuffled = np.random.choice(trade_returns, size=len(trade_returns), replace=True)


        # Build equity curve
        equity = account_balance + np.cumsum(shuffled)

        # Final return
        final_returns.append(equity[-1])

        # Drawdown
        peak = np.maximum.accumulate(equity)
        drawdown = equity - peak

        max_drawdowns.append(drawdown.min())

    return pd.DataFrame({
        'final_return': final_returns,
        'max_drawdown': max_drawdowns
    })

mc = monte_carlo(1000, portfolio)

#====================
# FINAL COMBINED PERFORMANCE
#====================


# Equity curve
Equity_curve=pd.DataFrame()
Equity_curve['equity'] = portfolio['account_balance']

# Drawdown
Equity_curve['peak'] = Equity_curve['equity'].cummax()
Equity_curve['drawdown'] = (Equity_curve['equity'] - Equity_curve['peak'])

max_drawdown=Equity_curve['drawdown'].min()

peak_value= Equity_curve['equity'][ Equity_curve['drawdown']==max_drawdown].iloc[0]

max_drawdown_pct = (abs(max_drawdown)/peak_value)*100


#Expectancy
win_rate=(len(portfolio[portfolio['result']==1]))/len(portfolio)
loss_rate=1-win_rate

avg_win=portfolio[portfolio['result']==1]['return'].mean()
avg_loss=portfolio[portfolio['result']==0]['return'].mean()


#Correlation
df_wide = portfolio.pivot(index='entry_time', columns='instrument', values='return')

correlation = df_wide['us100'].corr(df_wide['ger40'])



#====================
# COST SENSITIVITY
#====================

costs = range(0, 31)

results = []

for c in costs:
    cost = c

    portfolio = backtest()

    results.append({
        'cost': c,
        'return': portfolio['return'].sum(),
        'max_dd': calculate_dd(portfolio)
    })

results = pd.DataFrame(results)




#====================
# FINAL METRICS
#====================

print('===== FINAL METRICS =====')
print('Total Trades           :', len(portfolio))
print('Opening Balance        :', account_balance)
print('Closing Balance        :', account_balance + portfolio['return'].sum())
print('Total Return           :', portfolio['return'].sum())
print('Win Rate               :', (len(portfolio[portfolio['result']==1]))/len(portfolio))
print('Expected win           :', avg_win)
print('Expected loss          :', avg_loss)
print('Expectancy per trade   :', avg_win*win_rate + avg_loss*loss_rate )
print('Standard Deviation     :', portfolio['return'].std())
print('Sharper Ratio          :', (portfolio['return'].mean()/portfolio['return'].std())*np.sqrt(252))
print('Profit factor          :', abs(portfolio[portfolio['result']==1]['return'].sum()/portfolio[portfolio['result']==0]['return'].sum()))
print('Total Max Drawdown     :', max_drawdown)
print('Total Max Drawdown %   :', (abs(max_drawdown)/peak_value)*100)
print('Correlation            :', correlation)
print('Worst Case Scenario')
print('MC Return 5% quantile  :', mc['final_return'].quantile([0.05]).values)
print('MC Max DD 5% quantile  :', mc['max_drawdown'].quantile([0.05]).values)
print(' ')
print('*****Strategy is statistically solid******')



# =========================
# VISUALIZATION
# =========================


fig, axes = plt.subplots(3, 2, figsize=(15, 10))

#trade return disstribution
axes[0,0].hist(portfolio['return'],bins=min(30, len(portfolio)),alpha=0.7,color='blue',edgecolor='black')
axes[0,0].axvline(x=0, color='red', linestyle='--', linewidth=2, label='Breakeven')
axes[0,0].axvline(x=portfolio['return'].mean(), color='green', linestyle='-', linewidth=2,
                             label=f'Mean: ${portfolio['return'].mean():.2f}')
axes[0,0].set_title('Trade Returns Distribution', fontsize=12, fontweight='bold')
axes[0,0].set_xlabel('Return ($)')
axes[0,0].set_ylabel('Frequency')
axes[0,0].legend()
axes[0,0].grid(True, alpha=0.3)

#trade result distrivution
# 1. Capture the patches (bars) by adding ', patches' to the assignment
n, bins, patches = axes[0,1].hist(
    portfolio['result'], bins=2, range=(-0.5, 1.5), rwidth=0.8, alpha=0.7, edgecolor='black'
)

# 2. Assign specific colors to each individual bar
patches[0].set_facecolor('red')    # Left bar (Losses)
patches[1].set_facecolor('green')  # Right bar (Wins)

# 3. Apply titles, labels, and formatting
axes[0,1].set_title('Trade Result Distribution', fontsize=12, fontweight='bold')
axes[0,1].set_xlabel('Result')
axes[0,1].set_ylabel('Frequency')
axes[0,1].set_xticks([0, 1]) 
axes[0,1].set_xticklabels(['Loss (0)', 'Win (1)']) 
axes[0,1].grid(True, axis='y', alpha=0.3)


 # Equity curve
axes[1,1].plot(Equity_curve['equity'], linewidth=2, color='green')
axes[1,1].axhline(y=10000, color='black', linestyle='--', alpha=0.5, label='Start ($10,000)')
axes[1,1].fill_between(range(len(Equity_curve['equity'])), 10000, Equity_curve['equity'], 
                               where=np.array(Equity_curve['equity']) >= 10000, color='green', alpha=0.3,
                               interpolate=True, label='Profit')
axes[1,1].fill_between(range(len(Equity_curve['equity'])), 10000, Equity_curve['equity'],
                               where=np.array(Equity_curve['equity']) < 10000, color='red', alpha=0.3,
                               interpolate=True, label='Loss')
axes[1,1].set_title('Equity Curve ($10,000 Starting Capital)', fontsize=12, fontweight='bold')
axes[1,1].set_xlabel('Trade Number')
axes[1,1].set_ylabel('Equity ($)')
axes[1,1].legend()
axes[1,1].grid(True, alpha=0.3)


# Drawdon
axes[1,0].fill_between(range(len(Equity_curve['drawdown'])), 0, Equity_curve['drawdown'], alpha=0.3, color='red')
axes[1,0].set_title(f'Maximum Drawdown: {max_drawdown_pct:.1f}%')
axes[1,0].set_xlabel('Trade Number')
axes[1,0].set_ylabel('Drawdown (%)')
axes[1,0].grid(True, alpha=0.3)

# Monte Carlo return distribution
axes[2,0].hist(mc['final_return'],bins=min(30, len(mc)),alpha=0.7,color='blue',edgecolor='black')
axes[2,0].axvline(x=mc['final_return'].mean(), color='green', linestyle='-', linewidth=2,
                             label=f'Mean: ${mc['final_return'].mean():.2f}')
axes[2,0].axvline(x=10000, color='red', linestyle='--', linewidth=2, label='Breakeven')
axes[2,0].set_title('Monte Carlo Trade Returns Distribution', fontsize=12, fontweight='bold')
axes[2,0].set_xlabel('Return ($)')
axes[2,0].set_ylabel('Frequency')
axes[2,0].legend()
axes[2,0].grid(True, alpha=0.3)

# Monte Carlo  distribution

axes[2,1].hist(mc['max_drawdown'] ,bins=min(30,len(mc)),alpha=0.7,color='red',edgecolor='black')
axes[2,1].axvline(x=mc['max_drawdown'].mean(),
                  color='green', 
                  linestyle='-',
                  linewidth=2,
                  label=f'Mean : {mc['max_drawdown'].mean():.2f}')
axes[2,1].set_title('Monte Carlo  distribution', fontsize=12, fontweight='bold')
axes[2,1].set_xlabel('Return ($)')
axes[2,1].set_ylabel('Frequency')
axes[2,1].legend()
axes[2,1].grid(True, alpha=0.3)










# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




