# -*- coding: utf-8 -*-
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

def stable_seed(*items):
    text='_'.join(str(x) for x in items)
    return int(hashlib.md5(text.encode('utf-8')).hexdigest()[:8],16)

def safe_read_csv(path):
    path=Path(path)
    if not path.exists(): raise FileNotFoundError(f'Missing file: {path}')
    for enc in ['utf-8-sig','utf-8','gbk']:
        try: return pd.read_csv(path,encoding=enc)
        except UnicodeDecodeError: pass
    raise RuntimeError(f'Cannot read CSV: {path}')

def summarize_results(raw_df,function_order):
    summary=(raw_df.groupby(['Function','Algorithm']).agg(
        Mean=('BestValue','mean'),Std=('BestValue','std'),Best=('BestValue','min'),
        Worst=('BestValue','max'),Median=('BestValue','median'),AvgRestart=('RestartCount','mean')).reset_index())
    rows=[]
    for f in function_order:
        sub=summary[summary['Function']==f].copy()
        if sub.empty: continue
        sub['Rank']=sub['Mean'].rank(method='average',ascending=True)
        for _,r in sub.iterrows():
            rows.append({'Function':f,'Algorithm':r['Algorithm'],'Rank':r['Rank'],'Mean':r['Mean'],'Std':r['Std']})
    rank_detail=pd.DataFrame(rows)
    avg=(rank_detail.groupby('Algorithm').agg(AverageRank=('Rank','mean')).reset_index().sort_values('AverageRank'))
    return summary,rank_detail,avg

def mean_curve_dataframe(records, key='Curve', value_name='MeanBest'):
    rows=[]
    df=pd.DataFrame(records)
    if df.empty: return pd.DataFrame(columns=['Function','Algorithm','Iteration',value_name])
    for (f,a),items in df.groupby(['Function','Algorithm']):
        curves=[np.asarray(c,dtype=float) for c in items[key] if len(c)>0]
        if not curves: continue
        n=min(len(c) for c in curves)
        mean=np.mean(np.array([c[:n] for c in curves]),axis=0)
        for i,v in enumerate(mean): rows.append({'Function':f,'Algorithm':a,'Iteration':i+1,value_name:float(v)})
    return pd.DataFrame(rows)
