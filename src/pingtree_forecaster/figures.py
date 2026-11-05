"""Regenerate every figure of the paper from results/results.json (itself computed from data/).

Run:  python -m pingtree_forecaster.figures
"""
import json
from pathlib import Path
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'paper' / 'fig'
D = json.load(open(ROOT / 'results' / 'results.json'))
B,G,A,Rd,Gy,Pu='#2f6fe0','#12905a','#c47d0c','#c8372f','#6d7690','#7c5ce0'
plt.rcParams.update({'font.size':8.5,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.25,'grid.linewidth':.5,'figure.dpi':150,'savefig.bbox':'tight','font.family':'DejaVu Sans','legend.frameon':False})
OUT.mkdir(parents=True, exist_ok=True)
def sv(n): plt.savefig(OUT / f'{n}.pdf'); plt.close()
k=lambda v,p=None:f'{v/1000:.0f}k'
# ================= P1
p=D['p1']; rows=p['rows']; n=len(rows); lab=[f'P{r["pos"]}' for r in rows]
fig,ax=plt.subplots(figsize=(6.4,3)); ax.bar(lab,[r['accepted'] for r in rows],color=B); ax.set_ylabel('Accepted leads'); ax2=ax.twinx(); ax2.plot(lab,[100000-sum(r['accepted'] for r in rows[:i+1]) for i in range(n)],color=A,marker='o',ms=3); ax2.set_ylabel('Unplaced leads'); ax2.grid(False); ax2.spines['right'].set_visible(True); ax.set_xlabel('Pingtree position'); sv('p1_flow')
fig,ax=plt.subplots(figsize=(6.4,3)); rv=[r['rev'] for r in rows]; ax.bar(lab,rv,color=B); ax.set_ylabel('Revenue (EUR)'); ax.yaxis.set_major_formatter(k); ax2=ax.twinx(); ax2.plot(lab,np.cumsum(rv)/sum(rv)*100,color=G,marker='o',ms=3); ax2.set_ylim(0,102); ax2.set_ylabel('Cumulative share (%)'); ax2.grid(False); ax2.spines['right'].set_visible(True); ax.set_xlabel('Pingtree position'); sv('p1_rev')
fig,ax=plt.subplots(figsize=(6.4,3)); m=p['marg']; x=np.arange(1,len(m)+1); ax.plot(x,m,color=B,marker='o',ms=3,label='Total revenue'); ax.axvline(20,color=Gy,ls='--',lw=.8); ax.set_xlabel('Number of offers in the pingtree'); ax.set_ylabel('Monthly revenue (EUR)'); ax.yaxis.set_major_formatter(k); ax2=ax.twinx(); ax2.bar(x,np.diff([0]+m),color=A,alpha=.5); ax2.set_ylabel('Marginal revenue of the offer (EUR)'); ax2.grid(False); ax2.spines['right'].set_visible(True); sv('p1_marg')
o=p['order']; names=['EPL desc.\n(proposed)','Acceptance\ndesc.','Historical\nrevenue desc.','Random\n(mean of 2,000)','EPL asc.']; vals=[o['epl_desc'],o['acc_desc'],o['rev_hist'],o['random'],o['epl_asc']]
fig,ax=plt.subplots(figsize=(6.4,2.8)); ax.bar(names,vals,color=[B,Gy,Gy,Gy,Rd]); ax.set_ylabel('Monthly revenue (EUR)'); ax.yaxis.set_major_formatter(k)
for i,v in enumerate(vals): ax.text(i,v+1500,f'{v:,.0f}',ha='center',fontsize=7.5)
sv('p1_order')
fig,ax=plt.subplots(figsize=(6.4,2.8)); ax.hist(p['mc']['samples'],bins=24,color=B,alpha=.85); [ax.axvline(p['mc'][q],color=c,ls='--',lw=1) for q,c in [('p10',Gy),('p50',A),('p90',Gy)]]; ax.set_xlabel('Monthly revenue (EUR)'); ax.set_ylabel('Simulations (1 in 10 shown)'); ax.xaxis.set_major_formatter(k); sv('p1_mc')
fig,ax=plt.subplots(figsize=(6.4,3)); ax.scatter([r['acc']*100 for r in rows],[r['epl'] for r in rows],s=[10+400*r['rev']/max(rv) for r in rows],color=B,alpha=.6)
for r in rows[:6]: ax.annotate(f'P{r["pos"]}',(r['acc']*100,r['epl']),fontsize=7,xytext=(3,3),textcoords='offset points')
ax.set_xscale('log'); ax.set_xlabel('Acceptance rate (%), log scale'); ax.set_ylabel('EPL (EUR)'); sv('p1_bubble')
s=p['sens']; lab2=['Acceptance +10%','Acceptance -10%','EPL +10%','EPL -10%','Position penalty 30%','10 offers','30 offers']; v2=[s['acc_up'],s['acc_dn'],s['epl_up'],s['epl_dn'],s['pen30'],s['n10'],s['n30']]; idx=np.argsort(v2)
fig,ax=plt.subplots(figsize=(6.4,2.8)); ax.barh([lab2[i] for i in idx],[v2[i] for i in idx],color=[G if v2[i]>=0 else Rd for i in idx]); ax.set_xlabel('Change in forecast revenue (%)'); sv('p1_sens')

# ---- backtest figure
bt=p['backtest']['walk_forward']; fig,ax=plt.subplots(figsize=(6.4,2.8)); x=range(len(bt))
ax.plot(x,[r['actual'] for r in bt],color='k',marker='o',ms=3,label='Realised revenue'); ax.plot(x,[r['model'] for r in bt],color=B,marker='o',ms=3,label='Reach-adjusted flow'); ax.plot(x,[r['naive'] for r in bt],color=Gy,ls='--',label='Naive run rate')
ax.set_xticks(list(x)); ax.set_xticklabels([r['month'] for r in bt],rotation=45,ha='right'); ax.set_ylabel('Monthly revenue (EUR)'); ax.yaxis.set_major_formatter(k); ax.legend(fontsize=7); sv('p1_backtest')
def main(): print('figures written to', OUT)
if __name__=='__main__': main()
