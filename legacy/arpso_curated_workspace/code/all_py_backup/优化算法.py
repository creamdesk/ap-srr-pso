# -*- coding: utf-8 -*-
import numpy as np

# W2：由权重敏感性分析选出的默认 EIS 权重
DEFAULT_EIS_WEIGHTS = (0.60, 0.20, 0.20)

def init_pop(rng,n,d,lb,ub): return rng.uniform(lb,ub,size=(n,d))
def bound(x,lb,ub): return np.clip(x,lb,ub)
def vclip(v,vmax): return np.clip(v,-vmax,vmax)
def eval_batch(func,x):
    x=np.asarray(x,dtype=float)
    if x.ndim==1: x=x.reshape(1,-1)
    return func(x)
def norm_arr(v):
    v=np.asarray(v,dtype=float); mn=np.min(v); mx=np.max(v)
    if abs(mx-mn)<1e-30: return np.zeros_like(v)
    return (v-mn)/(mx-mn+1e-30)
def diversity(x,lb,ub):
    n,d=x.shape; c=np.mean(x,axis=0); dist=np.linalg.norm(x-c,axis=1)
    return float(np.mean(dist)/(np.sqrt(d)*(ub-lb)+1e-30))

def select_particles(x,pbest_fit,contribution,k,mode='eis',weights=DEFAULT_EIS_WEIGHTS):
    n=x.shape[0]
    order=np.argsort(pbest_fit)
    r=np.empty(n); r[order]=np.linspace(0,1,n)  # fitness disadvantage
    center=np.mean(x,axis=0)
    c=1-norm_arr(np.linalg.norm(x-center,axis=1))  # spatial crowding
    u=1-norm_arr(contribution)  # low contribution
    if mode=='worst':
        score=r; idx=order[-k:]
    elif mode=='rc':
        score=0.6*r+0.4*c
    elif mode=='ru':
        score=0.6*r+0.4*u
    elif mode=='eis':
        w1,w2,w3=weights; s=w1+w2+w3; w1,w2,w3=w1/s,w2/s,w3/s
        score=w1*r+w2*c+w3*u
    else:
        raise ValueError(f'Unknown selection mode: {mode}')
    score=score.copy(); score[np.argmin(pbest_fit)]=-np.inf
    if mode!='worst': idx=np.argsort(-score)[:k]
    return idx,score

def run_pso(func,bounds,dim=30,pop_size=50,max_iter=500,seed=None,w=0.7,c1=2.0,c2=2.0,
            adaptive_weight=False,w_max=0.9,w_min=0.4,restart=False,restart_mode='none',
            selection_mode='worst',eis_weights=DEFAULT_EIS_WEIGHTS,stagnation_window=80,
            restart_ratio=0.1,epsilon=1e-10,velocity_ratio=0.2,min_restart_iter_ratio=0.45,
            diversity_threshold=0.04,alpha_min=0.05,alpha_max=0.18,sigma_min=0.002,
            sigma_max=0.06,restart_cooldown=45,low_diversity_patience=15):
    rng=np.random.default_rng(seed); lb,ub=bounds; span=ub-lb; vmax=velocity_ratio*span
    x=init_pop(rng,pop_size,dim,lb,ub); v=rng.uniform(-vmax,vmax,size=(pop_size,dim))
    fit=eval_batch(func,x); pbest=x.copy(); pbest_fit=fit.copy(); contrib=np.zeros(pop_size)
    bi=np.argmin(pbest_fit); gbest=pbest[bi].copy(); gbest_fit=float(pbest_fit[bi])
    curve=[]; div_curve=[]; restart_count=0; restart_iters=[]; restart_ratios=[]; restart_sigmas=[]; restart_scores=[]
    stag=0; low_div=0; last_restart=-(10**9); ref_best=gbest_fit
    for t in range(max_iter):
        prog=t/max_iter; cur_w=w_min+(w_max-w_min)*((1-prog)**1.5) if adaptive_weight else w
        r1=rng.random((pop_size,dim)); r2=rng.random((pop_size,dim))
        v=cur_w*v+c1*r1*(pbest-x)+c2*r2*(gbest-x); v=vclip(v,vmax)
        x=bound(x+v,lb,ub); fit=eval_batch(func,x)
        improved=fit<pbest_fit; contrib*=0.995; contrib[improved]+=1.0
        pbest[improved]=x[improved]; pbest_fit[improved]=fit[improved]
        bi=np.argmin(pbest_fit)
        if pbest_fit[bi]<gbest_fit: gbest_fit=float(pbest_fit[bi]); gbest=pbest[bi].copy()
        imp=ref_best-gbest_fit; eps=epsilon*(abs(ref_best)+1.0)
        if imp>eps: stag=0; ref_best=gbest_fit
        else: stag+=1
        div=diversity(x,lb,ub); div_curve.append(div)
        low_div=low_div+1 if div<diversity_threshold else 0
        mid=t>=int(max_iter*min_restart_iter_ratio); cool=(t-last_restart)>=restart_cooldown
        trig_adapt=restart and restart_mode in ['adaptive_diversity','adaptive_eis'] and mid and cool and (low_div>=low_diversity_patience or stag>=stagnation_window)
        trig_std=restart and restart_mode in ['soft_local','global'] and mid and cool and stag>=stagnation_window
        if trig_adapt:
            dloss=max(0.0,(diversity_threshold-div)/(diversity_threshold+1e-30))
            slevel=min(1.0,stag/(stagnation_window+1e-30))
            ratio=float(np.clip(alpha_min+(alpha_max-alpha_min)*max(dloss,0.5*slevel),alpha_min,alpha_max))
            k=max(1,int(np.floor(ratio*pop_size)))
            idx,score=select_particles(x,pbest_fit,contrib,k,selection_mode,eis_weights)
            restart_scores.append(np.nan if selection_mode=='worst' else float(np.mean(score[idx])))
            gnum=max(1,int(0.25*k)); lnum=k-gnum; gidx=idx[:gnum]; lidx=idx[gnum:]
            x[gidx]=init_pop(rng,len(gidx),dim,lb,ub)
            sigma=span*max(sigma_min,sigma_max*(1-prog)*(0.5+dloss))
            if lnum>0: x[lidx]=bound(gbest+rng.normal(0,sigma,size=(lnum,dim)),lb,ub)
            v[idx]=rng.uniform(-0.15*vmax,0.15*vmax,size=(k,dim))
            fit[idx]=eval_batch(func,x[idx]); pbest[idx]=x[idx]; pbest_fit[idx]=fit[idx]; contrib[idx]=0.0
            bi=np.argmin(pbest_fit)
            if pbest_fit[bi]<gbest_fit: gbest_fit=float(pbest_fit[bi]); gbest=pbest[bi].copy()
            restart_count+=1; restart_iters.append(t); restart_ratios.append(ratio); restart_sigmas.append(float(sigma))
            last_restart=t; stag=0; low_div=0; ref_best=gbest_fit
        elif trig_std:
            k=max(1,int(np.floor(restart_ratio*pop_size))); order=np.argsort(pbest_fit); idx=order[-k:]
            if restart_mode=='soft_local':
                sigma=span*max(0.003,0.05*(1-prog)); x[idx]=bound(gbest+rng.normal(0,sigma,size=(k,dim)),lb,ub)
            else:
                sigma=span; x[idx]=init_pop(rng,k,dim,lb,ub)
            v[idx]=rng.uniform(-0.1*vmax,0.1*vmax,size=(k,dim))
            fit[idx]=eval_batch(func,x[idx]); pbest[idx]=x[idx]; pbest_fit[idx]=fit[idx]; contrib[idx]=0.0
            bi=np.argmin(pbest_fit)
            if pbest_fit[bi]<gbest_fit: gbest_fit=float(pbest_fit[bi]); gbest=pbest[bi].copy()
            restart_count+=1; restart_iters.append(t); restart_ratios.append(restart_ratio); restart_sigmas.append(float(sigma)); restart_scores.append(np.nan)
            last_restart=t; stag=0; low_div=0; ref_best=gbest_fit
        curve.append(gbest_fit)
    return {'best_value':float(gbest_fit),'best_position':gbest,'curve':np.array(curve),'diversity_curve':np.array(div_curve),
            'restart_count':restart_count,'restart_iters':restart_iters,'restart_ratios':restart_ratios,
            'restart_sigmas':restart_sigmas,'restart_inefficiency_scores':restart_scores}

def run_clpso(func,bounds,dim=30,pop_size=50,max_iter=500,seed=None):
    rng=np.random.default_rng(seed); lb,ub=bounds; span=ub-lb; vmax=0.2*span
    x=init_pop(rng,pop_size,dim,lb,ub); v=rng.uniform(-vmax,vmax,size=(pop_size,dim)); fit=eval_batch(func,x)
    pbest=x.copy(); pbest_fit=fit.copy(); gbest=pbest[np.argmin(pbest_fit)].copy(); gbest_fit=float(np.min(pbest_fit)); curve=[]
    pc=0.05+0.45*(np.exp(10*np.arange(pop_size)/max(1,pop_size-1))-1)/(np.exp(10)-1)
    exemplar=np.tile(np.arange(pop_size).reshape(-1,1),(1,dim)); noimp=np.zeros(pop_size,dtype=int)
    def refresh(i):
        for j in range(dim):
            if rng.random()<pc[i]:
                a,b=rng.choice(pop_size,2,replace=False); exemplar[i,j]=a if pbest_fit[a]<pbest_fit[b] else b
            else: exemplar[i,j]=i
    for i in range(pop_size): refresh(i)
    for t in range(max_iter):
        w=0.9-0.5*(t/max_iter); c=1.5
        for i in range(pop_size):
            if noimp[i]>=7: refresh(i); noimp[i]=0
        ex=np.zeros_like(x)
        for i in range(pop_size): ex[i]=pbest[exemplar[i],np.arange(dim)]
        v=w*v+c*rng.random((pop_size,dim))*(ex-x); v=vclip(v,vmax); x=bound(x+v,lb,ub); fit=eval_batch(func,x)
        imp=fit<pbest_fit; noimp[~imp]+=1; noimp[imp]=0; pbest[imp]=x[imp]; pbest_fit[imp]=fit[imp]
        bi=np.argmin(pbest_fit)
        if pbest_fit[bi]<gbest_fit: gbest_fit=float(pbest_fit[bi]); gbest=pbest[bi].copy()
        curve.append(gbest_fit)
    return {'best_value':float(gbest_fit),'best_position':gbest,'curve':np.array(curve),'diversity_curve':np.array([]),'restart_count':0,'restart_iters':[],'restart_ratios':[],'restart_sigmas':[],'restart_inefficiency_scores':[]}

def run_hpso_tvac(func,bounds,dim=30,pop_size=50,max_iter=500,seed=None):
    rng=np.random.default_rng(seed); lb,ub=bounds; span=ub-lb; vmax=0.2*span
    x=init_pop(rng,pop_size,dim,lb,ub); v=rng.uniform(-vmax,vmax,size=(pop_size,dim)); fit=eval_batch(func,x)
    pbest=x.copy(); pbest_fit=fit.copy(); gbest=pbest[np.argmin(pbest_fit)].copy(); gbest_fit=float(np.min(pbest_fit)); curve=[]; div_curve=[]
    for t in range(max_iter):
        p=t/max_iter; w=0.9-0.5*p; c1=2.5-2.0*p; c2=0.5+2.0*p
        v=w*v+c1*rng.random((pop_size,dim))*(pbest-x)+c2*rng.random((pop_size,dim))*(gbest-x); v=vclip(v,vmax)
        x=bound(x+v,lb,ub); fit=eval_batch(func,x); imp=fit<pbest_fit; pbest[imp]=x[imp]; pbest_fit[imp]=fit[imp]
        bi=np.argmin(pbest_fit)
        if pbest_fit[bi]<gbest_fit: gbest_fit=float(pbest_fit[bi]); gbest=pbest[bi].copy()
        div_curve.append(diversity(x,lb,ub)); curve.append(gbest_fit)
    return {'best_value':float(gbest_fit),'best_position':gbest,'curve':np.array(curve),'diversity_curve':np.array(div_curve),'restart_count':0,'restart_iters':[],'restart_ratios':[],'restart_sigmas':[],'restart_inefficiency_scores':[]}

def run_ga(func,bounds,dim=30,pop_size=50,max_iter=500,seed=None,crossover_rate=0.8,mutation_rate=0.1):
    rng=np.random.default_rng(seed); lb,ub=bounds; span=ub-lb
    pop=init_pop(rng,pop_size,dim,lb,ub); fit=eval_batch(func,pop); bi=np.argmin(fit); best=float(fit[bi]); bestpos=pop[bi].copy(); curve=[]
    def select():
        cand=rng.choice(pop_size,3,replace=False); return pop[cand[np.argmin(fit[cand])]].copy()
    for _ in range(max_iter):
        new=[pop[np.argmin(fit)].copy()]
        while len(new)<pop_size:
            p1,p2=select(),select()
            if rng.random()<crossover_rate:
                a=rng.random(dim); c1=a*p1+(1-a)*p2; c2=a*p2+(1-a)*p1
            else: c1,c2=p1.copy(),p2.copy()
            m1=rng.random(dim)<mutation_rate; m2=rng.random(dim)<mutation_rate
            c1[m1]+=rng.normal(0,0.1*span,size=np.sum(m1)); c2[m2]+=rng.normal(0,0.1*span,size=np.sum(m2))
            new.append(bound(c1,lb,ub))
            if len(new)<pop_size: new.append(bound(c2,lb,ub))
        pop=np.array(new); fit=eval_batch(func,pop); bi=np.argmin(fit)
        if fit[bi]<best: best=float(fit[bi]); bestpos=pop[bi].copy()
        curve.append(best)
    return {'best_value':float(best),'best_position':bestpos,'curve':np.array(curve),'diversity_curve':np.array([]),'restart_count':0,'restart_iters':[],'restart_ratios':[],'restart_sigmas':[],'restart_inefficiency_scores':[]}

def run_de(func,bounds,dim=30,pop_size=50,max_iter=500,seed=None,F=0.5,CR=0.9):
    rng=np.random.default_rng(seed); lb,ub=bounds
    pop=init_pop(rng,pop_size,dim,lb,ub); fit=eval_batch(func,pop); bi=np.argmin(fit); best=float(fit[bi]); bestpos=pop[bi].copy(); curve=[]
    for _ in range(max_iter):
        for i in range(pop_size):
            cand=[j for j in range(pop_size) if j!=i]; a,b,c=rng.choice(cand,3,replace=False)
            mutant=bound(pop[a]+F*(pop[b]-pop[c]),lb,ub); cross=rng.random(dim)<CR
            if not np.any(cross): cross[rng.integers(0,dim)]=True
            trial=np.where(cross,mutant,pop[i]); tf=float(eval_batch(func,trial)[0])
            if tf<fit[i]:
                pop[i]=trial; fit[i]=tf
                if tf<best: best=tf; bestpos=trial.copy()
        curve.append(best)
    return {'best_value':float(best),'best_position':bestpos,'curve':np.array(curve),'diversity_curve':np.array([]),'restart_count':0,'restart_iters':[],'restart_ratios':[],'restart_sigmas':[],'restart_inefficiency_scores':[]}

def run_algorithm(algorithm_name,func,bounds,dim=30,pop_size=50,max_iter=500,seed=None,eis_weights=DEFAULT_EIS_WEIGHTS):
    if algorithm_name=='PSO': return run_pso(func,bounds,dim,pop_size,max_iter,seed,w=0.7,adaptive_weight=False,restart=False)
    if algorithm_name=='PSO-AW': return run_pso(func,bounds,dim,pop_size,max_iter,seed,adaptive_weight=True,restart=False)
    if algorithm_name=='PSO-RS': return run_pso(func,bounds,dim,pop_size,max_iter,seed,w=0.7,adaptive_weight=False,restart=True,restart_mode='soft_local',stagnation_window=80,min_restart_iter_ratio=0.55,restart_cooldown=45)
    if algorithm_name=='CLPSO': return run_clpso(func,bounds,dim,pop_size,max_iter,seed)
    if algorithm_name=='HPSO-TVAC': return run_hpso_tvac(func,bounds,dim,pop_size,max_iter,seed)
    if algorithm_name=='ARPSO-v4': return run_pso(func,bounds,dim,pop_size,max_iter,seed,adaptive_weight=True,restart=True,restart_mode='adaptive_diversity',selection_mode='worst',stagnation_window=70,min_restart_iter_ratio=0.45,diversity_threshold=0.04,restart_cooldown=45,low_diversity_patience=15)
    if algorithm_name=='ARPSO-RC': return run_pso(func,bounds,dim,pop_size,max_iter,seed,adaptive_weight=True,restart=True,restart_mode='adaptive_eis',selection_mode='rc',stagnation_window=70,min_restart_iter_ratio=0.45,diversity_threshold=0.04,restart_cooldown=45,low_diversity_patience=15)
    if algorithm_name=='ARPSO-RU': return run_pso(func,bounds,dim,pop_size,max_iter,seed,adaptive_weight=True,restart=True,restart_mode='adaptive_eis',selection_mode='ru',stagnation_window=70,min_restart_iter_ratio=0.45,diversity_threshold=0.04,restart_cooldown=45,low_diversity_patience=15)
    if algorithm_name=='ARPSO-EIS': return run_pso(func,bounds,dim,pop_size,max_iter,seed,adaptive_weight=True,restart=True,restart_mode='adaptive_eis',selection_mode='eis',eis_weights=eis_weights,stagnation_window=70,min_restart_iter_ratio=0.45,diversity_threshold=0.04,restart_cooldown=45,low_diversity_patience=15)
    if algorithm_name=='GA': return run_ga(func,bounds,dim,pop_size,max_iter,seed)
    if algorithm_name=='DE': return run_de(func,bounds,dim,pop_size,max_iter,seed)
    raise ValueError(f'Unknown algorithm name: {algorithm_name}')
