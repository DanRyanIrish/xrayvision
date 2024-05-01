"""
Modules contains visibility related classes.

This contains classes to hold general visibilities and specialised classes hold visibilities from
certain spacecraft or instruments
"""

import abc
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as apu
from typing import Any
from types import SimpleNamespace
from collections.abc import Iterable
from astropy.time import Time


__all__ = ['Visibilities', 'VisMeta']


class VisMetaABC(abc.ABC): 
    @property
    @abc.abstractmethod   
    def energy_range(self) -> Iterable[apu.Quantity]:
        """
        Energy range over which the visibilities are computed.
        """

    @property
    @abc.abstractmethod   
    def time_range(self) -> Iterable[Time]:
        """
        Centre time over which the visibilities are computed.
        """ 

    @property
    @abc.abstractmethod   
    def center(self) -> SkyCoord:
        """
        Center of the image described by the visibilities.
        """

    @property
    @abc.abstractmethod   
    def observer_coordinate(self) -> SkyCoord:
        """
        Location of the observer.
        """


class VisibilitiesBaseABC(abc.ABC):
    @property
    @abc.abstractmethod   
    def visibilities(self) -> Iterable[apu.Quantity]:
        """
        Complex numbers representing the visibilities.
        """

    @property
    @abc.abstractmethod   
    def u(self) -> Iterable[apu.Quantity]:
        """
        u-coordinate on the complex plane of the visibilities.
        """

    @property
    @abc.abstractmethod   
    def v(self) -> Iterable[apu.Quantity]:
        """
        v-coordinate on the complex plane of the visibilities.
        """

    @property
    @abc.abstractmethod   
    def names(self) -> Iterable[str]:
        """
        Names for each visibility. 

        Must be same length as self.vis.
        """

    @property
    @abc.abstractmethod   
    def uncertainty(self) -> Any:
        """
        Uncertainties on visibilities values.
        """

    @property
    @abc.abstractmethod   
    def meta(self) -> Any:
        """
        Meta data.
        """

class VisibilitiesABC(VisibilitiesBaseABC):
    @property
    @abc.abstractmethod   
    def uncertainty(self) -> Iterable[apu.Quantity]:
        """
        Uncertainties on visibilities values.
        """

    @property
    @abc.abstractmethod
    def amplitude(self) -> np.ndarray:
        """
        Amplitudes of the visibilities.
        """
    
    @property
    @abc.abstractmethod   
    def phase(self) -> np.ndarray:
        """
        Phases of the visibilities.
        """
    @property
    @abc.abstractmethod
    def amplitude_uncertainty(self) -> np.ndarray:
        """
        Amplitude uncertainty of the visibilities.
        """
    
    @property
    @abc.abstractmethod   
    def phase_uncertainty(self) -> np.ndarray:
        """
        Phase uncertainty of the visibilities.
        """

    @property
    @abc.abstractmethod   
    def meta(self) -> VisMetaABC:
        """
        Meta data.
        """


class VisibilitiesBase(VisibilitiesBaseABC):
    r"""
    Hold a set of related visibilities and information.

    Attributes
    ----------
    vis : `numpy.ndarray`
        Array of N complex visibilities at coordinates in `uv`
    u : `numpy.ndarray`
        Array of `u` coordinates where visibilities will be evaluated
    v : `numpy.ndarray`
        Array of `v` coordinates where visibilities will be evaluated
    center : `float` (x, y), optional
        The x, y offset of phase center

    """
    @apu.quantity_input()
    def __init__(self,
                 visibilities: apu.Quantity,
                 u: apu.Quantity[1/apu.arcsec],
                 v: apu.Quantity[1/apu.arcsec],
                 names: Iterable[str],
                 uncertainty: Any = None,
                 meta: Any = None):
        r"""
        Initialise a new Visibility object.

        Parameters
        ----------
        vis : `numpy.ndarray`
            Array of N complex visibilities at coordinates in `uv`.
        u : `numpy.ndarray`
            Array of `u` coordinates where visibilities will be evaluated.
        v : `numpy.ndarray`
            Array of `v` coordinates where visibilities will be evaluated.
        center :
            Phase centre
        """
        if not isinstance(visibilities, apu.Quantity) or visibilities.isscalar:
            raise TypeError('visibilities must all be a non scalar Astropy quantity.')
        self._visibilities = visibilities
        nvis = len(self._visibilities)
        if len(u) != nvis: 
            raise ValueError('u must be the same length as visibilities.')
        self._u = u
        if len(v) != nvis: 
            raise ValueError('v must be the same length as visibilities.')
        self._v = v
        if len(names) != nvis: 
            raise ValueError('names must be the same length as visibilities.')
        if not np.array(isinstance(name, str) for name in names).all(): 
            raise TypeError('names must all be strings.')
        self._names = names
        if uncertainty is not None and not isinstance(uncertainty, apu.Quantity):
            raise TypeError('uncertainty must be None or same type as visibilities.')
        self._uncertainty = uncertainty
        self._meta = meta

    @property
    def visibilities(self): 
        return self._visibilities
    
    @property
    def u(self): 
        return self._u
    
    @property
    def v(self): 
        return self._v
    
    @property
    def names(self): 
        return self._names
     
    @property
    def uncertainty(self): 
        return self._uncertainty

    @property
    def meta(self): 
        return self._meta

    ################# Everything above is required by ABC, adding extra functionality below #################

    @property
    def amplitude(self):
        return np.sqrt(np.real(self.visibilities) ** 2 + np.imag(self.visibilities) ** 2)
   
    @property
    def amplitude_uncertainty(self): 
        amplitude = self.amplitude
        return np.sqrt((np.real(self.visibilities) / amplitude * np.real(self.uncertainty)) ** 2 
                       + (np.imag(self.visibilities) / amplitude * np.imag(self.uncertainty)) ** 2 )

    @property
    def phase(self):
        return np.arctan2(np.imag(self.visibilities), np.real(self.visibilities)).to(apu.deg)

    @property
    def phase_uncertainty(self):
        amplitude = self.amplitude
        return (np.sqrt(np.imag(self.visibilities) ** 2 / amplitude ** 4 * np.real(self.uncertainty) ** 2 
                        + np.real(self.visibilities) ** 2 / amplitude ** 4 * np.imag(self.uncertainty) ** 2 ) * apu.rad).to(apu.deg)

    def __getitem__(self, item):
        """Allow slicing/indexing by name, rather than integer."""
        if isinstance(item, str):
            new_item = np.where(self.names == item)[0][0]
        elif isinstance(item, slice):
            start = np.where(self.names == str(item.start))[0][0]
            stop = np.where(self.names == str(item.stop))[0][0]
            new_item = slice(start, stop, item.step)
        else:
            new_item = np.array([np.where(self.names == str(name))[0][0] for name in item])
        new_vis = self.visibilities[new_item]
        new_u = self.u[new_item]
        new_v = self.v[new_item]
        new_names = self.names[new_item]
        new_uncertainty = self.uncertainty[new_item] if isinstance(self.uncertainty, type(self.visibilities) else self.uncertainty
        return type(self)(new_visibilites, new_u, new_v, new_names, uncertainty=new_uncertainty, meta=new_meta)

    def __repr__(self):
        r"""
        Return a printable representation of the visibility.

        Returns
        -------
        `str`

        """
        return f"{self.__class__.__name__}< {self.u.size}, {self.visibilities}>"

    def __eq__(self, other):
        r"""
        Equality for Visibility class

        Parameters
        ----------
        other : `Visibility`
            The other visibility to compare

        Returns
        -------
        `boolean`

        """
        props_equal = []
        for key in self.__dict__.keys():
            props_equal.append(np.array_equal(self.__dict__[key], other.__dict__[key]))

        if all(props_equal):
            return True
        else:
            return False


class Visibilities(VisibilitiesABC, VisibilitiesBase):
    r"""
    Hold a set of related visibilities and information.

    Attributes
    ----------
    vis : `numpy.ndarray`
        Array of N complex visibilities at coordinates in `uv`
    u : `numpy.ndarray`
        Array of `u` coordinates where visibilities will be evaluated
    v : `numpy.ndarray`
        Array of `v` coordinates where visibilities will be evaluated
    center : `float` (x, y), optional
        The x, y offset of phase center

    """
    @apu.quantity_input(u=1/apu.arcsec, v=1/apu.arcsec)
    def __init__(self, visibilities, *, u, v, names, uncertainty=None, meta=None):
        r"""
        Initialise a new Visibility object.

        Parameters
        ----------
        vis : `numpy.ndarray`
            Array of N complex visibilities at coordinates in `uv`.
        u : `numpy.ndarray`
            Array of `u` coordinates where visibilities will be evaluated.
        v : `numpy.ndarray`
            Array of `v` coordinates where visibilities will be evaluated.
        center :
            Phase centre
        """
        nvis = len(visibilities)
        if not uncertainty.isscalar or len(uncertainty) != nvis:
            raise TypeError('uncertainty must be the same length as visibilities.')

        if not isinstance(meta, VisMetaABC):
            raise TypeError('Meta must be an instance of VisMetaABC.')
    
        super().__init__(visibilities, u, v, names, uncertainty=None, meta=None)


class VisMeta(VisMetaABC, SimpleNamespace):
    @apu.quantity_input(energy_range=apu.keV)
    def __init__(self, energy_range, time_range, center, observer_coordinate, **kwargs):
        if len(energy_range) != 2: 
            raise ValueError('energy_range must be length 2.')          
        if not isinstance(time_range, Time) or len(time_range) != 2: 
            raise ValueError('time_range must be a length 2 astropy time object.')   
        if not isinstance(center, SkyCoord) or not center.isscalar: 
            raise ValueError('center must be a scalar SkyCoord.') 
        if not isinstance(observer_coordinate, SkyCoord) or not observer_coordinate.isscalar: 
            raise ValueError('observer_coordinate must be a scalar SkyCoord.')  
        
        kwargs['energy_range'] = energy_range
        kwargs['time_range'] = time_range
        kwargs['center'] = center
        kwargs['observer_coordinate'] = observer_coordinate
        super().__init__(**kwargs)
