from tex_common import *
p=D['p1']; rows=p['rows']; o=p['order']; s=p['sens']; mc=p['mc']
tot=sum(r['rev'] for r in rows); top3=sum(r['rev'] for r in rows[:3])/tot; top1=rows[0]['rev']/tot
cum=0; k80=0
for i,r in enumerate(rows):
    cum+=r['rev']
    if cum/tot>=.8: k80=i+1; break
last5=p['marg'][19]-p['marg'][14]
tabrows='\n'.join(f'P{r["pos"]} & {n0(r["in"])} & {r["acc"]*100:.2f} & {n0(r["accepted"])} & {r["epl"]:.2f} & {n0(r["rev"])} & {r["rev"]/tot*100:.1f}\\\\' for r in rows)
ms=p['minsweep']; pen=p['pen']
abstract=r'''Lead-generation businesses in consumer finance sell each lead through a \emph{pingtree}: an ordered list of buyers who are offered the lead in sequence until one accepts. We present a forecasting model that turns a client's lead volume into expected monthly revenue by propagating leads through a pingtree built from the buyers' observed acceptance rates and earnings per lead (EPL). We prove that ordering buyers by decreasing EPL maximises expected revenue when acceptances are independent and offers are free, quantify the forecast on anonymised data for January--February 2026, and reconcile it with realised revenue. The unadjusted flow, in which every buyer is offered every leftover lead, gives @@REV@@ per 100{,}000 leads, but this is a ceiling: buyers are only queried for a fraction of leads. Adjusting for each buyer's observed reach gives @@REACHREV@@ and reproduces realised monthly revenue (in-sample ratio @@INS@@; walk-forward mean absolute percentage error @@MAPE@@). We also show how concentration, diminishing returns, sample-size filters and Monte Carlo uncertainty shape the result, and where the independence assumption is likely to fail.'''
body=r'''
\section{Introduction}
A \emph{pingtree} (or waterfall) sells a lead to the first buyer in an ordered list that accepts it. The order matters because every lead accepted early is no longer available to later buyers. A seller that holds a pool of leads therefore needs two answers: how much revenue will the pool generate, and in which order should buyers be called. This paper describes a small forecasting tool, the \emph{Revenue Forecaster}, that answers both from historical acceptance and revenue statistics, and documents the mathematics behind it.

The contribution is deliberately modest. We give (i) a clean sequential-flow model, (ii) a short proof that EPL-descending order is optimal under stated assumptions, (iii) an empirical illustration on anonymised data, and (iv) an honest list of the assumptions that real deployments will violate.

\section{Model}
Let $N$ be the number of leads entering the pingtree and let buyers be indexed by their position $i=1,\dots,n$. For buyer $i$ let $a_i\in[0,1]$ be the \emph{acceptance rate} (accepted leads divided by leads offered) and $e_i\ge 0$ the \emph{earnings per lead} (revenue divided by accepted leads). The number of leads reaching position $i$ is
\begin{equation}
 L_i = N\prod_{j<i}(1-a_j),
\end{equation}
so buyer $i$ accepts $A_i=a_iL_i$ leads and generates revenue $A_ie_i$. Expected total revenue is
\begin{equation}
 R(\pi)=N\sum_{i=1}^{n} a_i e_i \prod_{j<i}(1-a_j),
\end{equation}
where $\pi$ denotes the ordering. The share of leads placed is $1-\prod_i(1-a_i)$, which does not depend on the order.

\begin{proposition}\label{prop:order}
Assume acceptances are independent across buyers, an offer to a buyer costs nothing, and $a_i,e_i$ do not depend on position. Then $R(\pi)$ is maximised by ordering buyers by non-increasing $e_i$.
\end{proposition}
\begin{proof}
Consider two adjacent buyers at positions $k$ and $k+1$ with parameters $(a,e)$ and $(a',e')$, and let $\Pi=\prod_{j<k}(1-a_j)$. Their contribution to $R/N$ in the order $(a,e),(a',e')$ is $\Pi\,[\,ae+(1-a)a'e'\,]$. Swapping them gives $\Pi\,[\,a'e'+(1-a')ae\,]$. The difference is
\begin{equation}
 \Pi\,[\,ae+(1-a)a'e'-a'e'-(1-a')ae\,]=\Pi\,aa'(e-e').
\end{equation}
The leads that continue past both buyers are the same in either order, so later terms are unchanged. Hence swapping adjacent buyers never lowers revenue when the one with the higher EPL is moved forward. Any ordering can be sorted into EPL-descending order by adjacent swaps, each of which weakly increases $R$. \qedhere
\end{proof}
The result is a local index rule in the spirit of sequential search problems \cite{weitzman}. It breaks down when offers are costly, when buyers have monthly caps, or when acceptance depends on position, which we discuss in Section~\ref{sec:limits}. The tool includes a \emph{position penalty} $\rho\in[0,1]$ that scales the acceptance of the buyer at position $i$ by $1-\rho\,(i-1)/(n-1)$ to probe the last case.

\subsection{Reach adjustment}\label{sec:reach}
The flow above implicitly offers every unplaced lead to every buyer. In practice a buyer only receives requests for a subset of leads (eligibility rules, caps, product fit), and its observed acceptance rate is measured on that subset. Let $q_i=\min(1,R_i/N_{\mathrm{ref}})$ be the share of leads for which buyer $i$ is queried, where $R_i$ is the buyer's requests and $N_{\mathrm{ref}}$ is the lead volume (the largest request volume in each month, summed over the aggregated months). Replacing $a_i$ by $q_ia_i$ in the flow gives the \emph{reach-adjusted} forecast. Proposition~\ref{prop:order} still applies with $q_ia_i$ as the effective acceptance, so EPL-descending order remains optimal. With $q_i=1$ for all buyers we recover the \emph{full-reach} forecast, which is an upper bound.

\subsection{Uncertainty}
Monthly acceptance and EPL fluctuate. For each buyer we estimate the coefficient of variation of both quantities over the monthly observations from @@VOLFROM@@ onwards (bounded between 3\% and 80\%, with a default of 20\% when fewer than two months exist) and draw multiplicative log-normal noise with unit mean. Accepted leads at each position are drawn from a normal approximation to the binomial. We report the 10th, 50th and 90th percentiles of @@SIMS@@ simulations (fixed seed).

\section{Data and calibration}
The reference data are anonymised sources: for each of 42 buyers and 14 months (January 2025 to February 2026), the number of requests, accepted leads, sales and revenue; buyer identifiers are pseudonymised. The dataset and its data dictionary ship with the repository. Buyer statistics for the forecast are pooled over @@AGGM@@, so $a_i$ is total accepted over total requests and $e_i$ is total revenue over total accepted; coefficients of variation for the Monte Carlo use the six monthly observations from @@VOLFROM@@. Both windows are parameters of a single configuration file used by the code, the tests and this paper. Buyers with no revenue, or with fewer than @@MINACC@@ accepted leads, are excluded; this leaves @@ELIG@@ eligible buyers, of which the top @@NOFFERS@@ by EPL form the pingtree. Buyers are labelled P1--P@@NOFFERS@@ by position. Some buyers are paid per accepted lead rather than per sale, so their conversion rate is not defined and is shown as unavailable in the tool.

\section{Results}
\subsection{Baseline forecast}
For $N=100{,}000$ leads per month and a 20-offer pingtree, the full-reach model forecasts @@REV@@ per month, or @@PERLEAD@@ per lead; this is the ceiling discussed in Section~\ref{sec:recon}. @@COV@@ of leads are placed and the average EPL is @@EPLAVG@@. Table~\ref{tab:tree} lists the pingtree and Figure~\ref{fig:flow} shows how leads are consumed along it.
\begin{table}[H]\centering\small
\caption{Forecast pingtree for 100{,}000 leads per month. Acc.\ is the acceptance rate in \%, EPL is in euros and revenue in euros.}\label{tab:tree}
\begin{tabular}{lrrrrrr}\toprule
Buyer & Leads in & Acc.\ (\%) & Accepted & EPL & Revenue & Share (\%)\\\midrule
@@TAB@@
\bottomrule\end{tabular}\end{table}
@@FLOW@@
The first buyer sees every lead, but because acceptance rates are low (most below 10\%) the pool decays slowly, and about two thirds of leads are still unplaced after the twentieth buyer.

\subsection{Concentration and diminishing returns}
Revenue is concentrated: the top buyer produces @@TOP1@@ of the total and the top three @@TOP3@@; the first @@K80@@ buyers reach 80\% of revenue (Herfindahl--Hirschman index @@HHI@@). Figure~\ref{fig:rev} shows revenue by position. Adding offers has diminishing returns (Figure~\ref{fig:marg}): going from 15 to 20 offers adds @@LAST5@@ per month, and revenue with 10 offers is @@N10@@ lower than with 20.
@@REVFIG@@
@@MARGFIG@@
\subsection{Does order matter?}
Figure~\ref{fig:order} compares the proposed order with alternatives for the same 20 buyers. Ordering by EPL gives @@O1@@; ordering by acceptance rate gives @@O2@@, by historical revenue @@O3@@, and a random order averages @@O4@@. The worst case, ascending EPL, yields @@O5@@. EPL-descending order is therefore @@GAIN@@ better than a random order, consistent with Proposition~\ref{prop:order}.
@@ORDFIG@@
\subsection{Uncertainty and sensitivity}
The Monte Carlo simulation gives a median of @@MC50@@ with a 10th--90th percentile range of @@MC10@@ to @@MC90@@ (Figure~\ref{fig:mc}). Figure~\ref{fig:sens} shows that a 10\% change in either acceptance or EPL moves the forecast by about 9--10\%, a 30\% position penalty costs @@PEN30@@, and cutting the pingtree to 10 offers costs @@N10@@.
@@MCFIG@@
@@SENSFIG@@
\subsection{Sample-size filter and month-to-month variation}
Small samples are dangerous. Without any minimum on accepted leads the forecast rises to @@MIN0@@, because a handful of buyers with very few accepted leads show an implausibly high EPL and move to the top of the tree. With a minimum of 50, 200 and 1{,}000 accepted leads the forecasts are @@MIN50@@, @@MIN200@@ and @@MIN1000@@. The default of 50 is a compromise, not a recommendation: the right threshold should be chosen by cross-validating forecasts against realised revenue. Forecasts based on January alone and February alone are @@JAN@@ and @@FEB@@, a spread that the Monte Carlo range only partly captures and that is a reminder that two months of data are a thin base.
\begin{figure}[H]\centering\includegraphics[width=0.78\linewidth]{fig/p1_bubble.pdf}\caption{EPL against acceptance rate for the 20 buyers. Bubble area is forecast revenue; the horizontal axis is logarithmic.}\label{fig:bubble}\end{figure}

\section{Reconciliation with realised revenue}\label{sec:recon}
The full-reach figure is an upper bound and should not be read as a prediction of what a pingtree earns today. To test this we use realised revenue, the sum of the revenue column over buyers, and the monthly lead volume $N_t$ (largest request volume of any buyer in month $t$). Month by month, the reach-adjusted flow fed with the same month's rates and ordered by requests (a proxy for the observed order) reaches on average @@INS@@ of realised revenue (range @@INSMIN@@ to @@INSMAX@@). A walk-forward backtest estimates rates on the previous @@TRAIN@@ months, orders buyers by EPL, uses the realised $N_t$ and compares the forecast with realised revenue over @@NBT@@ months: the mean absolute percentage error is @@MAPE@@ (bias @@BIAS@@), against @@MAPENAIVE@@ for a naive run-rate forecast, while the full-reach flow overstates realised revenue by a median factor of @@FULLX@@. For 100{,}000 leads the reach-adjusted forecast is @@REACHREV@@ (P10--P90 @@RP10@@ to @@RP90@@), roughly @@CEIL@@ times lower than the ceiling.
\begin{table}[H]\centering\small
\caption{Walk-forward backtest. Forecasts use rates from the previous @@TRAIN@@ months and the realised lead volume of the target month.}\label{tab:bt}
\begin{tabular}{lrrr}\toprule
Month & Realised (EUR) & Reach-adjusted (EUR) & Error (\%)\\\midrule
@@BTTAB@@
\bottomrule\end{tabular}\end{table}
@@BTFIG@@
The reach-adjusted model is slightly better than a naive run rate, so it adds little accuracy at the aggregate level; its value is structural: it explains revenue by buyer and position and it is the right base for what-if questions such as changing the order or adding offers. Two caveats apply. The lead volume is an input, so the backtest does not test volume forecasting; and the observed order is only approximated.

\section{Limitations and extensions}\label{sec:limits}
\paragraph{Position-dependent acceptance.} Acceptance rates were measured in the positions buyers actually occupied. Buyers placed lower see leads already rejected by others, which may have lower quality, so their acceptance in a new tree could be smaller. The position-penalty parameter lets users test this, but the correct approach is to estimate acceptance by position from experiments.
\paragraph{Caps and costs.} Many buyers impose monthly caps. With caps the optimal order is no longer an index rule and a small optimisation problem must be solved. If pings have a cost, buyers with low acceptance and moderate EPL may not be worth calling.
\paragraph{Lead types.} The quality adjustments for lead types in the tool are editable hypotheses. They are not estimated from data and should be replaced by segment-level statistics.
\paragraph{Independence.} Acceptance decisions are modelled as independent. In practice buyers use similar eligibility rules, so a lead rejected by one is more likely to be rejected by another, which would make the forecast optimistic. The reach adjustment partly absorbs this effect, because it scales acceptance to the leads each buyer actually receives, but it does not model correlation between buyers.
\paragraph{Forecast, not guarantee.} The output is an expected value under stated assumptions, not a commitment.

\section{Conclusion}
A sequential-flow model with a simple ordering theorem is enough to build a transparent revenue forecaster for lead pingtrees. On anonymised data the full-reach forecast for 100{,}000 leads is @@REV@@ per month (Monte Carlo range @@MC10@@ to @@MC90@@), a ceiling; the reach-adjusted forecast of @@REACHREV@@ reconciles with realised revenue. The main practical risks are small samples, position effects and caps; each can be addressed with the extensions above.
'''
refs=r'''\bibitem{weitzman} M.~L. Weitzman. Optimal search for the best alternative. \emph{Econometrica}, 47(3):641--654, 1979.
\bibitem{glasserman} P.~Glasserman. \emph{Monte Carlo Methods in Financial Engineering}. Springer, 2004.'''
def rep(t):
    d={'REV':E(p['rev']),'PERLEAD':E(p['perLead']).replace('\\,\\texteuro{}','')+'\\,\\texteuro{}' if False else f'{p["perLead"]:.2f}\\,\\texteuro{{}}','COV':pc(p['cov']),'EPLAVG':f'{p["eplAvg"]:.2f}\\,\\texteuro{{}}','ELIG':str(p['eligible']),
       'TAB':tabrows,'TOP1':pc(top1),'TOP3':pc(top3),'K80':str(k80),'HHI':n0(p['hhi']),'LAST5':E(last5),'N10':f'{abs(s["n10"]):.0f}\\%','O1':E(o['epl_desc']),'O2':E(o['acc_desc']),'O3':E(o['rev_hist']),'O4':E(o['random']),'O5':E(o['epl_asc']),
       'GAIN':pc(o['epl_desc']/o['random']-1,0),'MC50':E(mc['p50']),'MC10':E(mc['p10']),'MC90':E(mc['p90']),'PEN30':f'{abs(s["pen30"]):.0f}\\%',
       'MIN0':E(ms[0][1]),'MIN50':E(ms[1][1]),'MIN200':E(ms[2][1]),'MIN1000':E(ms[3][1]),'JAN':E(p['months'][0]),'FEB':E(p['months'][1]),
       'FLOW':fig('p1_flow','Leads accepted by each buyer (bars) and leads still unplaced after each position (line), for 100{,}000 leads.').replace('\\end{figure}','\\label{fig:flow}\\end{figure}') if False else fig('p1_flow','Leads accepted by each buyer (bars) and leads still unplaced after each position (line).').replace('\\caption','\\label{fig:flow}\\caption'),
       'REVFIG':fig('p1_rev','Forecast revenue by position (bars) and cumulative share of the total (line).').replace('\\caption','\\label{fig:rev}\\caption'),
       'MARGFIG':fig('p1_marg','Total revenue as the number of offers grows (line) and marginal revenue of each added offer (bars).').replace('\\caption','\\label{fig:marg}\\caption'),
       'ORDFIG':fig('p1_order','Forecast revenue of the same 20 buyers under different ordering criteria.',"0.8").replace('\\caption','\\label{fig:order}\\caption'),
       'MCFIG':fig('p1_mc','Distribution of monthly revenue over 2{,}000 simulations; dashed lines mark the 10th, 50th and 90th percentiles.',"0.8").replace('\\caption','\\label{fig:mc}\\caption'),
       'SENSFIG':fig('p1_sens','Sensitivity of the forecast to changes in assumptions.',"0.8").replace('\\caption','\\label{fig:sens}\\caption')}
    bt=p['backtest']; ws=bt['walk_forward_summary']; ins=bt['in_sample']; rch=p['reach']
    d.update({'REACHREV':E(rch['rev']),'RP10':E(rch['p10']),'RP90':E(rch['p90']),'CEIL':f"{rch['ceiling_ratio']:.1f}",
       'INS':pc(bt['in_sample_ratio_mean'],0),'INSMIN':pc(min(r['ratio'] for r in ins),0),'INSMAX':pc(max(r['ratio'] for r in ins),0),
       'MAPE':pc(ws['reach_adjusted']['mape'],1),'BIAS':f"{ws['reach_adjusted']['bias']*100:+.1f}\\%",'MAPENAIVE':pc(ws['naive_run_rate']['mape'],1),'MAPEFULL':pc(ws['full_reach']['mape'],0),
       'FULLX':f"{bt['full_reach_median_ratio']:.1f}",'TRAIN':str(PAR['backtest']['train_months']),'NBT':str(ws['reach_adjusted']['n']),
       'BTTAB':'\n'.join(f"{r['month']} & {n0(r['actual'])} & {n0(r['model'])} & {(r['model']/r['actual']-1)*100:+.1f}\\\\" for r in bt['walk_forward']),
       'VOLFROM':PAR['volatility_from'],'SIMS':f"{PAR['monte_carlo']['sims']:,}".replace(',','{,}'),'MINACC':str(PAR['min_accepted']),'NOFFERS':str(PAR['offers']),
       'AGGM':' and '.join(m for m in PAR['aggregation_months']),
       'BTFIG':fig('p1_backtest','Realised monthly revenue and walk-forward forecasts (reach-adjusted flow and naive run rate).','0.85').replace('\\caption','\\label{fig:bt}\\caption')})
    for k,v in d.items(): t=t.replace('@@'+k+'@@',v)
    return t
tex=make('Revenue Forecaster: a Sequential-Flow Model for Financial Lead Pingtrees','Forecasting revenue and choosing the order of buyers',rep(abstract),rep(body),refs)
open(ROOT/'paper'/'paper.tex','w').write(tex)
