# -*- coding: utf-8 -*-
from pathlib import Path
import warnings
import time
import numpy as np
import pandas as pd
from benchmarks import CLASSICAL_BENCHMARKS, CLASSICAL_FUNCTIONS
from common import stable_seed, summarize_results, mean_curve_dataframe
from 优化算法 import run_algorithm
warnings.filterwarnings('ignore',category=RuntimeWarning)
ROOT=Path(__file__).resolve().parents[1]; RES=ROOT/'results'; RES.mkdir(exist_ok=True)
DIM=30; POP_SIZE=50; MAX_ITER=500; N_RUNS=30
ALGORITHMS=['PSO','PSO-AW','PSO-RS','CLPSO','HPSO-TVAC','ARPSO-v4','ARPSO-EIS','GA','DE']
FUNCTIONS=CLASSICAL_FUNCTIONS

def main():
    raw=[]; curves=[]; divs=[]; details=[]; total=len(FUNCTIONS)*len(ALGORITHMS)*N_RUNS; k=0
    print('='*100); print('Main experiment: ARPSO-EIS'); print('Algorithms:', ', '.join(ALGORITHMS)); print('='*100)
    for fname in FUNCTIONS:
        func=CLASSICAL_BENCHMARKS[fname]['func']; bounds=CLASSICAL_BENCHMARKS[fname]['bounds']
        for alg in ALGORITHMS:
            for run in range(1,N_RUNS+1):
                k+=1; seed=stable_seed('main_experiment',fname,alg,run,DIM,POP_SIZE,MAX_ITER)
                r=run_algorithm(alg,func,bounds,dim=DIM,pop_size=POP_SIZE,max_iter=MAX_ITER,seed=seed)
                best=float(r['best_value']); rc=int(r.get('restart_count',0))
                raw.append({'Function':fname,'Algorithm':alg,'Run':run,'BestValue':best,'RestartCount':rc,'Seed':seed})
                curves.append({'Function':fname,'Algorithm':alg,'Run':run,'Curve':np.asarray(r.get('curve',[]),dtype=float)})
                divs.append({'Function':fname,'Algorithm':alg,'Run':run,'Curve':np.asarray(r.get('diversity_curve',[]),dtype=float)})
                iters=r.get('restart_iters',[]); ratios=r.get('restart_ratios',[]); sigmas=r.get('restart_sigmas',[]); scores=r.get('restart_inefficiency_scores',[])
                for i in range(max(len(iters),len(ratios),len(sigmas),len(scores),0)):
                    details.append({'Function':fname,'Algorithm':alg,'Run':run,'RestartIndex':i+1,'RestartIter':iters[i] if i<len(iters) else np.nan,'RestartRatio':ratios[i] if i<len(ratios) else np.nan,'RestartSigma':sigmas[i] if i<len(sigmas) else np.nan,'RestartInefficiencyScore':scores[i] if i<len(scores) else np.nan})
                print(f'[{k:04d}/{total}] {fname:<10s} | {alg:<10s} | Run={run:02d} | Best={best:.6e} | Restart={rc}')
    rawdf=pd.DataFrame(raw); detdf=pd.DataFrame(details)
    summary,rank,avg=summarize_results(rawdf,FUNCTIONS)
    restart_summary=rawdf.groupby(['Function','Algorithm']).agg(AvgRestart=('RestartCount','mean'),StdRestart=('RestartCount','std'),MaxRestart=('RestartCount','max'),MinRestart=('RestartCount','min')).reset_index()
    mean_curves=mean_curve_dataframe(curves,key='Curve',value_name='MeanBest')
    mean_div=mean_curve_dataframe(divs,key='Curve',value_name='MeanDiversity')
    rawdf.to_csv(RES/'raw_results.csv',index=False,encoding='utf-8-sig'); summary.to_csv(RES/'summary_results.csv',index=False,encoding='utf-8-sig')
    rank.to_csv(RES/'rank_detail.csv',index=False,encoding='utf-8-sig'); avg.to_csv(RES/'average_rank.csv',index=False,encoding='utf-8-sig')
    restart_summary.to_csv(RES/'restart_summary.csv',index=False,encoding='utf-8-sig'); detdf.to_csv(RES/'restart_details.csv',index=False,encoding='utf-8-sig')
    mean_curves.to_csv(RES/'mean_curves.csv',index=False,encoding='utf-8-sig'); mean_div.to_csv(RES/'mean_diversity_curves.csv',index=False,encoding='utf-8-sig')
    print('\nAverage rank:'); print(avg.to_string(index=False)); print('='*100)
if __name__=='__main__': main()
