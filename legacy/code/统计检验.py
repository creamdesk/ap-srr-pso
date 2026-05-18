# -*- coding: utf-8 -*-
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata, wilcoxon
from common import safe_read_csv
ROOT=Path(__file__).resolve().parents[1]; RES=ROOT/'results'; TAB=ROOT/'paper_tables'; TAB.mkdir(exist_ok=True)
BASE='ARPSO-EIS'
ALG_ORDER=['PSO','PSO-AW','PSO-RS','CLPSO','HPSO-TVAC','ARPSO-v4','ARPSO-EIS','GA','DE']
FUNC_ORDER=['Sphere','Rastrigin','Rosenbrock','Ackley','Griewank','Schwefel']

def sci(x,p=3):
    x=float(x)
    if np.isnan(x): return '--'
    if x==0: return '0'
    if abs(x)<1e-3 or abs(x)>=1e4:
        m,e=f'{x:.{p}e}'.split('e'); return f'${m}\\times 10^{{{int(e)}}}$'
    return f'{x:.{p}f}'
def pf(p): return '$<10^{-4}$' if float(p)<1e-4 else f'{float(p):.4f}'

def main():
    raw=safe_read_csv(RES/'raw_results.csv'); summ=safe_read_csv(RES/'summary_results.csv')
    algs=[a for a in ALG_ORDER if a in raw['Algorithm'].unique()]; funcs=[f for f in FUNC_ORDER if f in raw['Function'].unique()]
    if BASE not in algs: raise ValueError(f'{BASE} not found')
    if 'ARPSO' in set(raw['Algorithm'].unique()): raise ValueError('Invalid name ARPSO found')
    mat=summ.pivot_table(index='Function',columns='Algorithm',values='Mean',aggfunc='mean').loc[funcs,algs].dropna()
    stat,p=friedmanchisquare(*[mat[a].values for a in algs])
    rankmat=mat.apply(lambda row: pd.Series(rankdata(row.values,method='average'),index=algs),axis=1)
    avg_rank=rankmat.mean(axis=0).reset_index().rename(columns={'index':'Algorithm',0:'AverageRank'}).sort_values('AverageRank')
    fried=pd.DataFrame([{'Test':'Friedman','Statistic':stat,'PValue':p,'NumBlocks':len(mat),'NumAlgorithms':len(algs)}])
    fried.to_csv(RES/'friedman_function_level.csv',index=False,encoding='utf-8-sig'); avg_rank.to_csv(RES/'friedman_average_rank_function_level.csv',index=False,encoding='utf-8-sig')
    # Function-level Wilcoxon over function means
    rows=[]
    for a in algs:
        if a==BASE: continue
        bv=mat[BASE].values; ov=mat[a].values
        try: st,pv=wilcoxon(bv,ov,alternative='two-sided',zero_method='wilcox')
        except ValueError: st,pv=np.nan,1.0
        result='NSD' if pv>=0.05 else ('Win' if np.mean(bv)<np.mean(ov) else 'Loss')
        rows.append({'BaseAlgorithm':BASE,'ComparedAlgorithm':a,'Statistic':st,'PValue':pv,'Result':result})
    pd.DataFrame(rows).to_csv(RES/'wilcoxon_function_level.csv',index=False,encoding='utf-8-sig')
    # Per-function Wilcoxon over 30 runs
    details=[]
    for f in funcs:
        for a in algs:
            if a==BASE: continue
            bv=raw[(raw['Function']==f)&(raw['Algorithm']==BASE)].sort_values('Run')['BestValue'].values
            ov=raw[(raw['Function']==f)&(raw['Algorithm']==a)].sort_values('Run')['BestValue'].values
            try: st,pv=wilcoxon(bv,ov,alternative='two-sided',zero_method='wilcox')
            except ValueError: st,pv=np.nan,1.0
            result='NSD' if pv>=0.05 else ('Win' if np.mean(bv)<np.mean(ov) else 'Loss')
            details.append({'Function':f,'BaseAlgorithm':BASE,'ComparedAlgorithm':a,'BaseMean':np.mean(bv),'ComparedMean':np.mean(ov),'Statistic':st,'PValue':pv,'Result':result})
    det=pd.DataFrame(details); det.to_csv(RES/'wilcoxon_per_function_details.csv',index=False,encoding='utf-8-sig')
    ws=det.groupby('ComparedAlgorithm')['Result'].value_counts().unstack(fill_value=0).reset_index()
    for c in ['Win','NSD','Loss']:
        if c not in ws.columns: ws[c]=0
    ws=ws[['ComparedAlgorithm','Win','NSD','Loss']]; ws.to_csv(RES/'wilcoxon_summary_nsd.csv',index=False,encoding='utf-8-sig')
    lines=[r'\begin{table}[t]',r'\centering',r'\caption{Function-level Friedman test results}',r'\label{tab:friedman_function_level}',r'\small',r'\begin{tabular}{lcccc}',r'\toprule',r'Test & Statistic & $p$-value & Blocks & Conclusion \\',r'\midrule',f'Friedman & {sci(stat)} & {pf(p)} & {len(mat)} & {"Significant" if p<0.05 else "Not significant"} \\',r'\bottomrule',r'\end{tabular}',r'\end{table}']
    (TAB/'table_friedman_function_level.tex').write_text('\n'.join(lines),encoding='utf-8')
    lines=[r'\begin{table}[t]',r'\centering',r'\caption{Wilcoxon signed-rank test summary of ARPSO-EIS against other algorithms}',r'\label{tab:wilcoxon_summary_nsd}',r'\small',r'\begin{tabular}{lccc}',r'\toprule',r'Compared Algorithm & Win & NSD & Loss \\',r'\midrule']
    for a in [x for x in ALG_ORDER if x!=BASE and x in list(ws['ComparedAlgorithm'])]:
        r=ws[ws['ComparedAlgorithm']==a].iloc[0]; lines.append(f'{a} & {int(r.Win)} & {int(r.NSD)} & {int(r.Loss)} \\\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']; (TAB/'table_wilcoxon_summary_nsd.tex').write_text('\n'.join(lines),encoding='utf-8')
    print('Friedman function-level:'); print(fried.to_string(index=False)); print('\nAverage ranks:'); print(avg_rank.to_string(index=False)); print('\nWilcoxon summary:'); print(ws.to_string(index=False))
if __name__=='__main__': main()
