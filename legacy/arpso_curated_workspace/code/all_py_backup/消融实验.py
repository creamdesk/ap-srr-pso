# -*- coding: utf-8 -*-
from pathlib import Path
import warnings
import pandas as pd
import matplotlib.pyplot as plt
from benchmarks import CLASSICAL_BENCHMARKS
from common import stable_seed, summarize_results
from 优化算法 import run_algorithm
warnings.filterwarnings('ignore',category=RuntimeWarning)
ROOT=Path(__file__).resolve().parents[1]; RES=ROOT/'results'/'ablation'; FIG=ROOT/'paper_figures'; RES.mkdir(parents=True,exist_ok=True); FIG.mkdir(exist_ok=True)
DIM=30; POP_SIZE=50; MAX_ITER=500; N_RUNS=30
ALGORITHMS=['ARPSO-v4','ARPSO-RC','ARPSO-RU','ARPSO-EIS']
FUNCTIONS=['Rastrigin','Rosenbrock','Ackley','Griewank','Schwefel']
COLORS={'ARPSO-v4':'#72B7B2','ARPSO-RC':'#4C78A8','ARPSO-RU':'#59A14F','ARPSO-EIS':'#D62728'}

def main():
    plt.rcParams['font.family']='Times New Roman'; plt.rcParams['axes.unicode_minus']=False; plt.rcParams['pdf.fonttype']=42; plt.rcParams['ps.fonttype']=42
    rows=[]; total=len(FUNCTIONS)*len(ALGORITHMS)*N_RUNS; k=0
    print('='*100); print('Ablation study'); print('='*100)
    for fname in FUNCTIONS:
        func=CLASSICAL_BENCHMARKS[fname]['func']; bounds=CLASSICAL_BENCHMARKS[fname]['bounds']
        for alg in ALGORITHMS:
            for run in range(1,N_RUNS+1):
                k+=1; seed=stable_seed('ablation',fname,alg,run,DIM,POP_SIZE,MAX_ITER)
                r=run_algorithm(alg,func,bounds,dim=DIM,pop_size=POP_SIZE,max_iter=MAX_ITER,seed=seed)
                best=float(r['best_value'])
                rows.append({'Function':fname,'Algorithm':alg,'Run':run,'BestValue':best,'RestartCount':int(r.get('restart_count',0)),'Seed':seed})
                print(f'[{k:04d}/{total}] {fname:<10s} | {alg:<10s} | Run={run:02d} | Best={best:.6e}')
    raw=pd.DataFrame(rows); summary,rank,avg=summarize_results(raw,FUNCTIONS)
    raw.to_csv(RES/'ablation_raw_results.csv',index=False,encoding='utf-8-sig'); summary.to_csv(RES/'ablation_summary_results.csv',index=False,encoding='utf-8-sig')
    rank.to_csv(RES/'ablation_rank_detail.csv',index=False,encoding='utf-8-sig'); avg.to_csv(RES/'ablation_average_rank.csv',index=False,encoding='utf-8-sig')
    df=avg.sort_values('AverageRank')
    fig,ax=plt.subplots(figsize=(5.8,3.6)); bars=ax.bar(df['Algorithm'],df['AverageRank'],color=[COLORS.get(a,'#999999') for a in df['Algorithm']],edgecolor='black',linewidth=0.6)
    for b,v in zip(bars,df['AverageRank']): ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.03,f'{v:.2f}',ha='center',va='bottom',fontsize=8)
    ax.set_xlabel('Ablation variant'); ax.set_ylabel('Average rank'); ax.set_title('Average rank in ablation study'); ax.grid(True,axis='y',linestyle='--',alpha=0.35); fig.tight_layout()
    fig.savefig(FIG/'figure6_ablation_average_rank.pdf',bbox_inches='tight'); fig.savefig(FIG/'figure6_ablation_average_rank.png',bbox_inches='tight',dpi=300); plt.close(fig)
    print('\nAblation average rank:'); print(avg.to_string(index=False))
if __name__=='__main__': main()
