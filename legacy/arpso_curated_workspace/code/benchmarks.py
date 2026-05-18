# -*- coding: utf-8 -*-
import numpy as np

def sphere(x):
    x=np.asarray(x,dtype=float); return np.sum(x**2,axis=1)

def rastrigin(x):
    x=np.asarray(x,dtype=float); d=x.shape[1]
    return 10*d+np.sum(x**2-10*np.cos(2*np.pi*x),axis=1)

def rosenbrock(x):
    x=np.asarray(x,dtype=float)
    return np.sum(100*(x[:,1:]-x[:,:-1]**2)**2+(x[:,:-1]-1)**2,axis=1)

def ackley(x):
    x=np.asarray(x,dtype=float); d=x.shape[1]
    return -20*np.exp(-0.2*np.sqrt(np.sum(x**2,axis=1)/d))-np.exp(np.sum(np.cos(2*np.pi*x),axis=1)/d)+20+np.e

def griewank(x):
    x=np.asarray(x,dtype=float); d=x.shape[1]
    return np.sum(x**2,axis=1)/4000-np.prod(np.cos(x/np.sqrt(np.arange(1,d+1))),axis=1)+1

def schwefel(x):
    x=np.asarray(x,dtype=float); d=x.shape[1]
    return 418.9829*d-np.sum(x*np.sin(np.sqrt(np.abs(x))),axis=1)

CLASSICAL_BENCHMARKS={
    'Sphere':{'func':sphere,'bounds':(-100,100),'optimum':0.0,'characteristics':'Unimodal, separable'},
    'Rastrigin':{'func':rastrigin,'bounds':(-5.12,5.12),'optimum':0.0,'characteristics':'Multimodal, separable'},
    'Rosenbrock':{'func':rosenbrock,'bounds':(-30,30),'optimum':0.0,'characteristics':'Unimodal, non-separable, narrow valley'},
    'Ackley':{'func':ackley,'bounds':(-32,32),'optimum':0.0,'characteristics':'Multimodal, non-separable'},
    'Griewank':{'func':griewank,'bounds':(-600,600),'optimum':0.0,'characteristics':'Multimodal, non-separable'},
    'Schwefel':{'func':schwefel,'bounds':(-500,500),'optimum':0.0,'characteristics':'Multimodal, deceptive'},
}
CLASSICAL_FUNCTIONS=list(CLASSICAL_BENCHMARKS.keys())
