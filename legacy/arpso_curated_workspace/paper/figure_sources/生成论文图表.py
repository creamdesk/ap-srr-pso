# -*- coding: utf-8 -*-
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from benchmarks import CLASSICAL_BENCHMARKS, CLASSICAL_FUNCTIONS
from common import safe_read_csv
warnings.filterwarnings('ignore',category=RuntimeWarning)
ROOT=Path(__file__).resolve().parents[1]; RES=ROOT/'results'; FIG=ROOT/'paper_figures'; TAB=ROOT/'paper_tables'
FIG.mkdir(exist_ok=True); TAB.mkdir(exist_ok=True)
DIM=30; POP_SIZE=50; MAX_ITER=500; MAX_FES=POP_SIZE*MAX_ITER
ALGORITHMS=['PSO','PSO-AW','PSO-RS','CLPSO','HPSO-TVAC','ARPSO-v4','ARPSO-EIS','GA','DE']
FUNCTIONS=CLASSICAL_FUNCTIONS; REP_FUNCS=['Sphere','Rastrigin','Ackley','Schwefel']; BOX_FUNCS=['Rastrigin','Schwefel']
COL={'PSO':'#9E9E9E','PSO-AW':'#4C78A8','PSO-RS':'#B0B0B0','CLPSO':'#9467BD','HPSO-TVAC':'#8C564B','ARPSO-v4':'#72B7B2','ARPSO-EIS':'#D62728','GA':'#59A14F','DE':'#F28E2B'}

def style():
    plt.rcParams['font.family']='Times New Roman'; plt.rcParams['font.size']=10; plt.rcParams['axes.labelsize']=10; plt.rcParams['axes.titlesize']=11; plt.rcParams['legend.fontsize']=8; plt.rcParams['xtick.labelsize']=9; plt.rcParams['ytick.labelsize']=9; plt.rcParams['axes.unicode_minus']=False; plt.rcParams['pdf.fonttype']=42; plt.rcParams['ps.fonttype']=42

def save(fig,name):
    fig.savefig(FIG/f'{name}.pdf',bbox_inches='tight'); fig.savefig(FIG/f'{name}.png',bbox_inches='tight',dpi=300); plt.close(fig)

def sci(x,p=3):
    x=float(x)
    if np.isnan(x): return '--'
    if x==0: return '0'
    if abs(x)<1e-3 or abs(x)>=1e4:
        m,e=f'{x:.{p}e}'.split('e'); return f'${m}\\times 10^{{{int(e)}}}$'
    return f'{x:.{p}f}'
def ms(mean,std): return f'{sci(mean,3)} $\\pm$ {sci(std,2)}'
def write(path,lines): Path(path).write_text('\n'.join(lines),encoding='utf-8')

def load():
    data={
        'raw':safe_read_csv(RES/'raw_results.csv'),'summary':safe_read_csv(RES/'summary_results.csv'),
        'average_rank':safe_read_csv(RES/'average_rank.csv'),'restart_summary':safe_read_csv(RES/'restart_summary.csv'),
        'restart_details':safe_read_csv(RES/'restart_details.csv'),'mean_curves':safe_read_csv(RES/'mean_curves.csv')}
    for n,df in data.items():
        if 'Algorithm' in df.columns and 'ARPSO' in set(df['Algorithm'].unique()): raise ValueError(f'{n} contains invalid algorithm name ARPSO')
    return data

def table_bench():
    lines=[r'\begin{table}[t]',r'\centering',r'\caption{Benchmark functions used in the experiments}',r'\label{tab:benchmark_functions}',r'\small',r'\begin{tabular}{lccc p{4.0cm}}',r'\toprule',r'Function & Dimension & Search Range & Optimum & Characteristics \\',r'\midrule']
    for f in FUNCTIONS:
        info=CLASSICAL_BENCHMARKS[f]; lb,ub=info['bounds']; lines.append(f'{f} & {DIM} & [{lb}, {ub}] & {info["optimum"]:.0f} & {info["characteristics"]} \\\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']; write(TAB/'table1_benchmark_functions.tex',lines)

def table_params():
    rows=[['PSO','50','30',str(MAX_FES),'30',r'$w=0.7$, $c_1=c_2=2.0$'],['PSO-AW','50','30',str(MAX_FES),'30',r'$w_{\max}=0.9$, $w_{\min}=0.4$'],['PSO-RS','50','30',str(MAX_FES),'30','soft local restart'],['CLPSO','50','30',str(MAX_FES),'30','comprehensive learning strategy'],['HPSO-TVAC','50','30',str(MAX_FES),'30','time-varying acceleration coefficients'],['ARPSO-v4','50','30',str(MAX_FES),'30','adaptive restart with worst-particle selection'],['ARPSO-EIS','50','30',str(MAX_FES),'30','adaptive restart with inefficient-particle selection'],['GA','50','30',str(MAX_FES),'30','crossover rate = 0.8, mutation rate = 0.1'],['DE','50','30',str(MAX_FES),'30',r'$F=0.5$, $CR=0.9$']]
    lines=[r'\begin{table*}[t]',r'\centering',r'\caption{Parameter settings of the compared algorithms}',r'\label{tab:parameter_settings}',r'\small',r'\begin{tabular}{lccccp{6.5cm}}',r'\toprule',r'Algorithm & Population & Dimension & Max FEs & Runs & Main Parameters \\',r'\midrule']
    for r in rows: lines.append(' & '.join(r)+r' \\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table*}']; write(TAB/'table2_parameter_settings.tex',lines)

def table_main(summary):
    algs=[a for a in ALGORITHMS if a in summary['Algorithm'].unique()]
    lines=[r'\begin{table*}[t]',r'\centering',r'\caption{Optimization results on classical benchmark functions (mean $\pm$ standard deviation)}',r'\label{tab:main_results}',r'\scriptsize',r'\resizebox{\textwidth}{!}{%',r'\begin{tabular}{l'+'c'*len(algs)+r'}',r'\toprule','Function & '+' & '.join(algs)+r' \\',r'\midrule']
    for f in FUNCTIONS:
        sub=summary[summary['Function']==f].set_index('Algorithm').loc[algs].reset_index(); means=sub['Mean'].values; order=np.argsort(means); best=int(order[0]); second=int(order[1])
        cells=[]
        for i,r in sub.iterrows():
            cell=ms(r['Mean'],r['Std'])
            if i==best: cell=r'\textbf{'+cell+'}'
            elif i==second: cell=r'\underline{'+cell+'}'
            cells.append(cell)
        lines.append(f+' & '+' & '.join(cells)+r' \\')
    lines += [r'\bottomrule',r'\end{tabular}%',r'}',r'\end{table*}']; write(TAB/'table3_main_results.tex',lines)

def table_avg(avg):
    df=avg.sort_values('AverageRank'); lines=[r'\begin{table}[t]',r'\centering',r'\caption{Average rank comparison of all algorithms}',r'\label{tab:average_rank}',r'\small',r'\begin{tabular}{lc}',r'\toprule',r'Algorithm & Average Rank \\',r'\midrule']
    for _,r in df.iterrows():
        alg=r['Algorithm']; val=f'{r["AverageRank"]:.4f}'
        if alg=='ARPSO-EIS': alg=r'\textbf{ARPSO-EIS}'; val=r'\textbf{'+val+'}'
        lines.append(f'{alg} & {val} \\\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']; write(TAB/'table4_average_rank.tex',lines)

def optional_tables():
    p=RES/'ablation'/'ablation_summary_results.csv'
    if p.exists():
        df=safe_read_csv(p); funcs=list(df['Function'].unique()); algs=[a for a in ['ARPSO-v4','ARPSO-RC','ARPSO-RU','ARPSO-EIS'] if a in df['Algorithm'].unique()]
        lines=[r'\begin{table*}[t]',r'\centering',r'\caption{Ablation study of the inefficient-particle selection mechanism}',r'\label{tab:ablation_study}',r'\small',r'\resizebox{\textwidth}{!}{%',r'\begin{tabular}{l'+'c'*len(algs)+r'}',r'\toprule','Function & '+' & '.join(algs)+r' \\',r'\midrule']
        for f in funcs:
            sub=df[df['Function']==f].set_index('Algorithm').loc[algs].reset_index(); best=int(np.argmin(sub['Mean'].values)); cells=[]
            for i,r in sub.iterrows():
                cell=ms(r['Mean'],r['Std']); cells.append(r'\textbf{'+cell+'}' if i==best else cell)
            lines.append(f+' & '+' & '.join(cells)+r' \\')
        lines += [r'\bottomrule',r'\end{tabular}%',r'}',r'\end{table*}']; write(TAB/'table8_ablation_study.tex',lines)
    p=RES/'sensitivity'/'sensitivity_average_rank.csv'
    if p.exists():
        df=safe_read_csv(p).sort_values('AverageRank'); lines=[r'\begin{table}[t]',r'\centering',r'\caption{Parameter sensitivity analysis of weight coefficients in ARPSO-EIS}',r'\label{tab:sensitivity_analysis}',r'\small',r'\begin{tabular}{lcccc}',r'\toprule',r'Setting & $\lambda_1$ & $\lambda_2$ & $\lambda_3$ & Average Rank \\',r'\midrule']
        best_rank=float(df['AverageRank'].min())
        for _,r in df.iterrows():
            name=r['Algorithm']; rank=f'{r["AverageRank"]:.4f}'
            if abs(float(r['AverageRank'])-best_rank)<1e-12:
                name=r'\textbf{'+str(name)+'}'; rank=r'\textbf{'+rank+'}'
            lines.append(f'{name} & {r["Lambda1"]:.2f} & {r["Lambda2"]:.2f} & {r["Lambda3"]:.2f} & {rank} \\\\')
        lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']; write(TAB/'table9_sensitivity_analysis.tex',lines)

def fig_convergence(curves):
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.4)); axes=axes.flatten(); algs=[a for a in ALGORITHMS if a in curves['Algorithm'].unique()]
    for ax,f in zip(axes,REP_FUNCS):
        for a in algs:
            sub=curves[(curves['Function']==f)&(curves['Algorithm']==a)].sort_values('Iteration')
            if sub.empty: continue
            ax.plot(sub['Iteration'],np.maximum(sub['MeanBest'].values.astype(float),1e-300),label=a,color=COL.get(a),linewidth=2.0 if a=='ARPSO-EIS' else 1.1,alpha=1.0 if a=='ARPSO-EIS' else 0.82)
        ax.set_yscale('log'); ax.set_title(f); ax.set_xlabel('Iteration'); ax.set_ylabel('Best-so-far fitness'); ax.grid(True,linestyle='--',alpha=0.35)
    h,l=axes[0].get_legend_handles_labels(); fig.legend(h,l,loc='upper center',ncol=5,frameon=False,bbox_to_anchor=(0.5,1.02)); fig.tight_layout(rect=[0,0,1,0.92]); save(fig,'figure1_convergence_curves')

def fig_box(raw):
    algs=[a for a in ALGORITHMS if a in raw['Algorithm'].unique()]; fig,axes=plt.subplots(1,2,figsize=(7.2,3.6))
    for ax,f in zip(axes,BOX_FUNCS):
        data=[raw[(raw['Function']==f)&(raw['Algorithm']==a)]['BestValue'].values.astype(float) for a in algs]
        box=ax.boxplot(data,tick_labels=algs,showfliers=True,patch_artist=True,medianprops={'color':'black','linewidth':1.1})
        for patch,a in zip(box['boxes'],algs): patch.set_facecolor(COL.get(a,'#DDD')); patch.set_alpha(0.65); patch.set_linewidth(0.8)
        ax.set_title(f); ax.set_xlabel('Algorithm'); ax.set_ylabel('Final objective value'); ax.tick_params(axis='x',rotation=45); ax.grid(True,axis='y',linestyle='--',alpha=0.35)
    fig.tight_layout(); save(fig,'figure2_boxplots')

def fig_avg(avg):
    df=avg.sort_values('AverageRank'); fig,ax=plt.subplots(figsize=(6.4,3.8)); bars=ax.bar(df['Algorithm'],df['AverageRank'],color=[COL.get(a,'#999') for a in df['Algorithm']],edgecolor='black',linewidth=0.6,alpha=0.85)
    for b,a,v in zip(bars,df['Algorithm'],df['AverageRank']): ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.04,f'{v:.2f}',ha='center',va='bottom',fontsize=8,fontweight='bold' if a=='ARPSO-EIS' else 'normal')
    ax.set_xlabel('Algorithm'); ax.set_ylabel('Average rank'); ax.set_title('Average rank comparison of different algorithms'); ax.tick_params(axis='x',rotation=35); ax.grid(True,axis='y',linestyle='--',alpha=0.35); ax.set_ylim(0,max(df['AverageRank'])+0.8); fig.tight_layout(); save(fig,'figure3_average_rank')

def fig_restart(rs):
    targets=[a for a in ['PSO-RS','ARPSO-v4','ARPSO-EIS'] if a in rs['Algorithm'].unique()]; pivot=rs.pivot_table(index='Function',columns='Algorithm',values='AvgRestart',aggfunc='mean').reindex(FUNCTIONS)
    fig,ax=plt.subplots(figsize=(7.2,3.8)); x=np.arange(len(FUNCTIONS)); width=0.8/max(1,len(targets))
    for i,a in enumerate(targets): ax.bar(x+i*width-width*(len(targets)-1)/2,pivot[a].values,width=width,label=a,color=COL.get(a),edgecolor='black',linewidth=0.5,alpha=0.85)
    ax.set_xlabel('Benchmark function'); ax.set_ylabel('Average restart count'); ax.set_title('Average restart counts on different benchmark functions'); ax.set_xticks(x); ax.set_xticklabels(FUNCTIONS,rotation=25); ax.legend(frameon=False); ax.grid(True,axis='y',linestyle='--',alpha=0.35); fig.tight_layout(); save(fig,'figure4_restart_counts')

def fig_score(rd):
    df=rd[(rd['Algorithm']=='ARPSO-EIS')].dropna(subset=['RestartInefficiencyScore'])
    if df.empty: return
    s=df.groupby('Function')['RestartInefficiencyScore'].agg(['mean','std']).reindex(FUNCTIONS).reset_index()
    fig,ax=plt.subplots(figsize=(6.8,3.8)); ax.bar(s['Function'],s['mean'],yerr=s['std'],capsize=3,color=COL['ARPSO-EIS'],edgecolor='black',linewidth=0.6,alpha=0.85)
    ax.set_xlabel('Benchmark function'); ax.set_ylabel('Average inefficiency score'); ax.set_title('Inefficiency-score analysis of restarted particles in ARPSO-EIS'); ax.tick_params(axis='x',rotation=25); ax.grid(True,axis='y',linestyle='--',alpha=0.35); ax.set_ylim(0,min(1.05,max(s['mean']+s['std'])+0.08)); fig.tight_layout(); save(fig,'figure5_inefficiency_score')

def main():
    style(); d=load(); print('Generating English tables and figures...')
    table_bench(); table_params(); table_main(d['summary']); table_avg(d['average_rank']); optional_tables()
    fig_convergence(d['mean_curves']); fig_box(d['raw']); fig_avg(d['average_rank']); fig_restart(d['restart_summary']); fig_score(d['restart_details'])
    print('Done. Figures:', FIG); print('Tables:', TAB)
if __name__=='__main__': main()
