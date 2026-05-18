# -*- coding: utf-8 -*-
from pathlib import Path
import warnings
import pandas as pd
import matplotlib.pyplot as plt
from benchmarks import CLASSICAL_BENCHMARKS
from common import stable_seed, summarize_results
from 优化算法 import run_algorithm
warnings.filterwarnings('ignore',category=RuntimeWarning)
ROOT=Path(__file__).resolve().parents[1]; RES=ROOT/'results'/'sensitivity'; FIG=ROOT/'paper_figures'; RES.mkdir(parents=True,exist_ok=True); FIG.mkdir(exist_ok=True)
DIM=30; POP_SIZE=50; MAX_ITER=500; N_RUNS=30
FUNCTIONS=['Rastrigin','Rosenbrock','Ackley','Griewank','Schwefel']
WEIGHTS={'W1':(0.70,0.20,0.10),'W2':(0.60,0.20,0.20),'W3':(0.50,0.30,0.20),'W4':(0.40,0.40,0.20),'W5':(0.40,0.20,0.40),'W6':(0.33,0.33,0.34)}

def main():
    plt.rcParams['font.family']='Times New Roman'; plt.rcParams['axes.unicode_minus']=False; plt.rcParams['pdf.fonttype']=42; plt.rcParams['ps.fonttype']=42
    rows=[]; total=len(FUNCTIONS)*len(WEIGHTS)*N_RUNS; k=0
    print('='*100); print('Weight sensitivity analysis'); print('='*100)
    for fname in FUNCTIONS:
        func=CLASSICAL_BENCHMARKS[fname]['func']; bounds=CLASSICAL_BENCHMARKS[fname]['bounds']
        for setting,w in WEIGHTS.items():
            for run in range(1,N_RUNS+1):
                k+=1; seed=stable_seed('sensitivity',fname,setting,run,DIM,POP_SIZE,MAX_ITER)
                r=run_algorithm('ARPSO-EIS',func,bounds,dim=DIM,pop_size=POP_SIZE,max_iter=MAX_ITER,seed=seed,eis_weights=w)
                best=float(r['best_value'])
                rows.append({'Function':fname,'Algorithm':setting,'Run':run,'BestValue':best,'RestartCount':int(r.get('restart_count',0)),'Lambda1':w[0],'Lambda2':w[1],'Lambda3':w[2],'Seed':seed})
                print(f'[{k:04d}/{total}] {fname:<10s} | {setting:<3s} | Run={run:02d} | Best={best:.6e}')
    raw=pd.DataFrame(rows); summary,rank,avg=summarize_results(raw,FUNCTIONS)
    wdf=pd.DataFrame([{'Algorithm':k,'Lambda1':v[0],'Lambda2':v[1],'Lambda3':v[2]} for k,v in WEIGHTS.items()]); avg=avg.merge(wdf,on='Algorithm',how='left')
    raw.to_csv(RES/'sensitivity_raw_results.csv',index=False,encoding='utf-8-sig'); summary.to_csv(RES/'sensitivity_summary_results.csv',index=False,encoding='utf-8-sig')
    rank.to_csv(RES/'sensitivity_rank_detail.csv',index=False,encoding='utf-8-sig'); avg.to_csv(RES/'sensitivity_average_rank.csv',index=False,encoding='utf-8-sig')
    df=avg.sort_values('AverageRank')
    fig,ax=plt.subplots(figsize=(6.2,3.6)); bars=ax.bar(df['Algorithm'],df['AverageRank'],color='#4C78A8',edgecolor='black',linewidth=0.6)
    for b,v in zip(bars,df['AverageRank']): ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.03,f'{v:.2f}',ha='center',va='bottom',fontsize=8)
    ax.set_xlabel('Weight setting'); ax.set_ylabel('Average rank'); ax.set_title('Parameter sensitivity of EIS weights'); ax.grid(True,axis='y',linestyle='--',alpha=0.35); fig.tight_layout()
    fig.savefig(FIG/'figure7_sensitivity_average_rank.pdf',bbox_inches='tight'); fig.savefig(FIG/'figure7_sensitivity_average_rank.png',bbox_inches='tight',dpi=300); plt.close(fig)
    print('\nSensitivity average rank:'); print(avg.to_string(index=False))
if __name__=='__main__': main()
