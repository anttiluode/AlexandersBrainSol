"""Finite 1D overdamped complex GL ring; no external state-setting operation.

F = dx sum(|D psi|^2 / 2 + |psi|^4 / 4 - mu |psi|^2 / 2).
Real and imaginary components each follow -grad(F)/dx + sqrt(2T/dx)dW.
The controller supplies bond phases a, not the stored winding.
"""
import numpy as np


def initial_state(labels, sites=64, dx=.5):
    labels = np.asarray(labels)
    q = 2*np.pi*labels/sites
    amplitude = np.sqrt(np.maximum(0, 1-4*np.sin(q/2)**2/dx**2))
    return amplitude[:,None]*np.exp(1j*q[:,None]*np.arange(sites))


def laplacian(z, a, dx):
    a = np.asarray(a)
    left_a = np.roll(a, 1, axis=-1) if a.ndim and a.shape[-1] != 1 else a
    return (np.exp(-1j*a)*np.roll(z,-1,axis=-1)
            + np.exp(1j*left_a)*np.roll(z,1,axis=-1)-2*z)/dx**2


def energy(z, mu, a, dx):
    d = (np.exp(-1j*np.asarray(a))*np.roll(z,-1,axis=-1)-z)/dx
    power = np.abs(z)**2
    return dx*np.sum(.5*np.abs(d)**2 + .25*power**2 - .5*mu*power,axis=-1)


def winding(z):
    """Full-field audit only. Reject near-zero fields and aliased phase jumps."""
    phase = np.angle(np.conj(z)*np.roll(z,-1,axis=-1))
    w = np.rint(np.sum(phase,axis=-1)/(2*np.pi)).astype(int)
    valid = ((np.min(np.abs(z),axis=-1) >= .15)
             & (np.max(np.abs(phase),axis=-1) < .8*np.pi)
             & np.all(np.isfinite(z),axis=-1))
    return w, valid


def current(z, bond, dx, a=0):
    """One local bond, no target label or global winding available."""
    return np.imag(np.conj(z[:,bond])*np.exp(-1j*a)*z[:,(bond+1)%z.shape[-1]])/dx


def evolve(z, mu, a, temperature, duration, dt, dx, rng, monitor=None, increments=None):
    if (dt <= 0 or dx <= 0 or dt > .2*dx**2 or temperature < 0
            or duration < 0 or not np.isclose(duration/dt, round(duration/dt))):
        raise ValueError('invalid explicit time step, temperature, or duration')
    z = np.asarray(z, dtype=complex).copy()
    noise_scale = np.sqrt(2*temperature*dt/dx)
    # Precompute fixed control factors; the field is never overwritten by a label.
    a = np.asarray(a)
    left_a = np.roll(a,1,axis=-1) if a.ndim and a.shape[-1] != 1 else a
    forward, backward = np.exp(-1j*a)/dx**2, np.exp(1j*left_a)/dx**2
    if increments is not None and increments.shape != (round(duration/dt),*z.shape):
        raise ValueError("Brownian increment shape mismatch")
    for step in range(round(duration/dt)):
        drift = (forward*np.roll(z,-1,axis=-1)+backward*np.roll(z,1,axis=-1)
                 - 2*z/dx**2 + (mu-np.abs(z)**2)*z)
        z += dt*drift
        if increments is not None:
            z += increments[step]
        elif temperature:
            z += noise_scale*(rng.normal(size=z.shape)+1j*rng.normal(size=z.shape))
        if monitor is not None:
            w, valid = winding(z)
            monitor['changed'] |= (w != monitor['reference']) | ~valid
            monitor['minimum_amplitude'] = np.minimum(monitor['minimum_amplitude'],np.min(np.abs(z),axis=-1))
    if not np.all(np.isfinite(z)):
        raise FloatingPointError('non-finite field')
    return z
