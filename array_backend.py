"""Compiled implementation of ring.evolve, checked against its NumPy reference.

Random increments are still drawn by NumPy, in the reference step/component
order. No fastmath. Monitoring uses a proven safe positive-half-plane shortcut;
ambiguous steps use the complete winding sum. Changed flags remain sticky.
"""
import numpy as np
from numba import njit
import ring
import experiment as ex


@njit(cache=True)
def _advance(z,mu,forward,backward,noise,dt,dx2,reference,changed,minimum,monitored):
    rows,sites=z.shape
    for step in range(noise.shape[0]):
        new=np.empty_like(z)
        for r in range(rows):
            for j in range(sites):
                amplitude=abs(z[r,j])
                drift=(forward[r,j]*z[r,(j+1)%sites]+backward[r,j]*z[r,(j-1)%sites]-2*z[r,j]/dx2+(mu[r,j]-amplitude**2)*z[r,j])
                new[r,j]=z[r,j]+dt*drift+noise[step,r,j]
        if monitored:
            for r in range(rows):
                smallest=1e300
                shortcut=(step!=0)
                for j in range(sites):
                    smallest=min(smallest,abs(new[r,j]))
                    # Node phase increment <pi/2 and both old/new bond phases in
                    # (-pi/2,pi/2) exclude a missed branch crossing at this step.
                    if ((np.conj(z[r,j])*new[r,j]).real<=0 or
                        (np.conj(z[r,j])*z[r,(j+1)%sites]).real<=0 or
                        (np.conj(new[r,j])*new[r,(j+1)%sites]).real<=0):shortcut=False
                minimum[r]=min(minimum[r],smallest)
                if changed[r]:continue
                if smallest<.15:
                    changed[r]=True;continue
                if shortcut:continue
                phase=0.;largest=0.
                for j in range(sites):
                    angle=np.angle(np.conj(new[r,j])*new[r,(j+1)%sites])
                    phase+=angle;largest=max(largest,abs(angle))
                winding=int(np.rint(phase/(2*np.pi)))
                if winding!=reference[r] or largest>=.8*np.pi:changed[r]=True
        z=new
    return z


def evolve(z,mu,a,temperature,duration,dt,dx,rng,monitor=None,increments=None):
    if dt<=0 or dx<=0 or dt>.2*dx**2 or temperature<0 or duration<0 or not np.isclose(duration/dt,round(duration/dt)):
        raise ValueError('invalid step or duration')
    z=np.ascontiguousarray(z,dtype=complex).copy();a=np.asarray(a)
    left=np.roll(a,1,axis=-1) if a.ndim and a.shape[-1]!=1 else a
    forward=np.ascontiguousarray(np.broadcast_to(np.exp(-1j*a)/dx**2,z.shape))
    backward=np.ascontiguousarray(np.broadcast_to(np.exp(1j*left)/dx**2,z.shape))
    mu=np.ascontiguousarray(np.broadcast_to(mu,z.shape),dtype=float)
    steps=round(duration/dt)
    if increments is not None and increments.shape!=(steps,*z.shape):raise ValueError('increment shape')
    if monitor is None:
        reference=np.zeros(len(z),np.int64);changed=np.zeros(len(z),bool);minimum=np.zeros(len(z))
    else:
        reference=monitor['reference'];changed=monitor['changed'];minimum=monitor['minimum_amplitude']
    for offset in range(0,steps,256):
        count=min(256,steps-offset)
        if increments is not None:noise=np.ascontiguousarray(increments[offset:offset+count])
        elif temperature:
            values=rng.normal(size=(count,2,*z.shape))
            noise=np.ascontiguousarray(np.sqrt(2*temperature*dt/dx)*(values[:,0]+1j*values[:,1]))
        else:noise=np.zeros((count,*z.shape),complex)
        z=_advance(z,mu,forward,backward,noise,dt,dx**2,reference,changed,minimum,monitor is not None)
    if not np.all(np.isfinite(z)):raise FloatingPointError('non-finite field')
    return z


def read_ring(z,p,rng,sensor_rng,means,probe=True,count=None):
    original,valid=ring.winding(z)
    monitor=dict(reference=original,changed=~valid,minimum_amplitude=np.min(np.abs(z),axis=1))
    a=np.zeros(p['sites']);a[p['sensor_bond']]=p['read_phase'] if probe else 0
    readings=[];analog=[]
    for _ in range(p['read_count'] if count is None else count):
        samples=[]
        for _ in range(p['samples_per_read']):
            z=evolve(z,np.ones(p['sites']),a,p['temperature'],p['read_time']/p['samples_per_read'],p['dt'],p['dx'],rng,monitor)
            samples.append(ring.current(z,p['sensor_bond'],p['dx'],a[p['sensor_bond']]))
        x=np.mean(samples,axis=0)+sensor_rng.normal(0,p['sensor_noise'],len(z))
        analog.append(x);readings.append(ex.decode(x,means))
    return z,np.asarray(readings).T,np.asarray(analog).T,monitor


@njit(cache=True)
def _rotor(theta,barrier,target,has_target,force,noise,dt,reference,bad,read_phase):
    for step in range(noise.shape[0]):
        for i in range(theta.shape[0]):
            for j in range(theta.shape[1]):
                x=theta[i,j]
                drift=-3*barrier[i,j]*np.sin(3*x)-read_phase*np.sin(x)
                if has_target:drift+=force*np.sin(target[i,j]-x)
                x+=dt*drift+noise[step,i,j];theta[i,j]=x
                phase=np.arctan2(np.sin(x),np.cos(x))
                label=int(np.rint(phase/(2*np.pi/3)))
                if label!=reference[i,j]:bad[i,j]=True
    return theta


def rotor_evolve(theta,barrier,target,force,temperature,duration,dt,rng,reference,bad,read_phase=0.):
    theta=np.asarray(theta,dtype=float).copy()
    barrier=np.ascontiguousarray(np.broadcast_to(barrier,theta.shape))
    has_target=target is not None
    target=np.ascontiguousarray(np.broadcast_to(target if has_target else 0.,theta.shape))
    for offset in range(0,round(duration/dt),256):
        count=min(256,round(duration/dt)-offset)
        noise=np.sqrt(2*temperature*dt)*rng.normal(size=(count,*theta.shape)) if temperature else np.zeros((count,*theta.shape))
        theta=_rotor(theta,barrier,target,has_target,force,noise,dt,reference,bad,read_phase)
    return theta
