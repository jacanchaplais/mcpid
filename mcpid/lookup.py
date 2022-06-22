from functools import partial
from fractions import Fraction
import os
import warnings

import numpy as np
import numpy.typing as npt
from numpy.lib import recfunctions as rfn


CURRENT_DIR = str(os.path.dirname(os.path.realpath(__file__)))


def frac(num_str, obj_mode=False):
    """Converts string formatted fraction into number.

    Keyword arguments:
        num_str (str) -- string rep of rational number, eg. '1/2'
        obj_mod (bool) -- if True returns a fractions.Fraction object,
            if False returns a float

    example:
        In [1]: frac('1/2')
        Out [1]: 0.5

    Note on missing data:
        if passed empty string, will return 0,
        if passed '?', will return NaN
        other edge cases will raise a ValueError

    """
    if obj_mode is False:
        cast_frac = lambda inp: float(Fraction(inp))
    elif obj_mode is True:
        cast_frac = Fraction
    try:
        return cast_frac(num_str)
    except ValueError:
        if num_str == "":
            return cast_frac("0/1")
        elif num_str == "?":
            return np.nan


class PdgRecords:
    def __init__(self, frac_obj=False):
        import pandas as pd

        frac_cols = ["i", "g", "p", "c", "charge"]
        cast_frac = partial(frac, obj_mode=frac_obj)
        converters = dict.fromkeys(frac_cols, cast_frac)
        lookup_table: pd.DataFrame = pd.read_csv(  # type: ignore
                CURRENT_DIR + "/_mcpid.csv", sep=",", comment="#",
                converters=converters)
        self.__lookup = lookup_table.set_index("id")

    @property
    def table(self):
        return self.__lookup

    def properties(self, pdgs: npt.ArrayLike, props: list) -> np.ndarray:
        """Returns the physical properties of a sequence of particles
        based on their pdg code.

        Parameters
        ----------
        pdgs : iterable of integers
            The pdg codes of the particles to query.
        props : iterable of strings
            The properties you wish to obtain for the particles.
            Valid options are:
                - name
                - charge
                - mass
                - massupper
                - masslower
                - quarks
                - width
                - widthupper
                - widthlower
                - i (isospin)
                - g (G-parity)
                - p (space-parity)
                - c (charge-parity)
                - latex
        
        Returns
        -------
        pdg_properties : numpy record array
            Record array containing requested data for each particle in
            the order given by input pdgs, subscriptable by string field
            names or using object oriented dot notation.

        Examples
        --------
        >>> from heparchy.read import HepReader

        >>> with HepReader('showers.hdf5') as f:
        ...     with f.read_process(name='top') as process:
        ...         event = process.read_event(0)
        ...             pdg = event.pdg
        >>> pdg
        array([2212,   21,   21, ...,   22,   22,   22])

        >>> from heparchy.pdg import LookupPDG
        """
        props = list(props)
        pdg_ids, pdg_inv_idxs = np.unique(pdgs, return_inverse=True)
        contains_pythia = np.any(self.__lookup.loc[pdg_ids]["pythia"])
        valid_pythia = {"name", "charge", "mass", "width"}
        if contains_pythia and (not valid_pythia.issuperset(props)):
            warnings.warn(
                    "Some PDG codes in the query are missing from the records "
                    "compiled by Scikit-HEP's Particle library. This is "
                    "usually because the particles are so unstable that they "
                    "are unobserved or unobservable. mcpid has filled in the "
                    "gaps using Pythia's records, but only name, charge, "
                    "mass, and width data are available. "
                    "Please ensure, if you wish to access other properties, "
                    "that you explicitly handle missing data."
                    )
        uniq_data = self.__lookup.loc[pdg_ids][props]
        uniq_data = uniq_data.to_records()
        uniq_data = rfn.drop_fields(uniq_data, "id")
        data = uniq_data[pdg_inv_idxs]
        return data
