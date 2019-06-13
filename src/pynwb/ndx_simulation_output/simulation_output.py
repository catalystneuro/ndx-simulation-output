import os

from collections import Iterable

import numpy as np
from pynwb import register_class, docval
from pynwb.core import VectorIndex, VectorData, DynamicTable, ElementIdentifiers
from hdmf.utils import popargs, call_docval_func
from pynwb import load_namespaces
from pynwb.base import TimeSeries, _default_resolution, _default_conversion

name = 'ndx-simulation-output'

here = os.path.abspath(os.path.dirname(__file__))
ns_path = os.path.join(here, 'spec', name + '.namespace.yaml')

load_namespaces(ns_path)


def create_ragged_array(name, values):
    """
    :param values: list of lists
    :return:
    """
    vector_data = VectorData(
        name, 'indicates which compartments the data refers to',
        [item for sublist in values for item in sublist])
    vector_index = VectorIndex(
        name + '_index', np.cumsum([len(x) for x in values]), target=vector_data)
    return vector_data, vector_index


@register_class('Compartments', name)
class Compartments(DynamicTable):
    __columns__ = (
        {'name': 'number', 'index': True,
         'description': 'cell compartment ids corresponding to a each column in the data'},
        {'name': 'position', 'index': True,
         'description': 'the observation intervals for each unit'},
        {'name': 'label', 'description': 'the electrodes that each spike unit came from',
         'index': True, 'table': True}
    )

    @docval({'name': 'name', 'type': str, 'doc': 'Name of this Compartments object',
             'default': 'Compartments'},
            {'name': 'id', 'type': ('array_data', ElementIdentifiers),
             'doc': 'the identifiers for the units stored in this interface', 'default': None},
            {'name': 'columns', 'type': (tuple, list), 'doc': 'the columns in this table', 'default': None},
            {'name': 'colnames', 'type': 'array_data', 'doc': 'the names of the columns in this table',
             'default': None},
            {'name': 'description', 'type': str, 'doc': 'a description of what is in this table', 'default': None},
            )
    def __init__(self, **kwargs):
        if kwargs.get('description', None) is None:
            kwargs['description'] = "data on spiking units"
        call_docval_func(super(Compartments, self).__init__, kwargs)


@register_class('CompartmentSeries', name)
class CompartmentSeries(TimeSeries):
    __nwbfields__ = ('compartments',)

    @docval({'name': 'name', 'type': str, 'doc': 'name'},
            {'name': 'data', 'type': ('array_data', 'data', TimeSeries), 'shape': (None, None),
             'doc': 'The data this TimeSeries dataset stores.'},
            {'name': 'compartments', 'type': Compartments,
             'doc': 'meta-data for the compartments of this CompartmentSeries'},

            {'name': 'resolution', 'type': float,
             'doc': 'The smallest meaningful difference (in specified unit) between values in data',
             'default': _default_resolution},
            {'name': 'conversion', 'type': float,
             'doc': 'Scalar to multiply each element by to convert to volts', 'default': _default_conversion},

            {'name': 'timestamps', 'type': ('array_data', 'data', TimeSeries),
             'doc': 'Timestamps for samples stored in data', 'default': None},
            {'name': 'starting_time', 'type': float, 'doc': 'The timestamp of the first sample', 'default': None},
            {'name': 'rate', 'type': float, 'doc': 'Sampling rate in Hz', 'default': None},
            {'name': 'unit', 'type': str, 'doc': 'SI unit of measurement', 'default': 'no unit'},
            {'name': 'comments', 'type': str,
             'doc': 'Human-readable comments about this TimeSeries dataset', 'default': 'no comments'},
            {'name': 'description', 'type': str,
             'doc': 'Description of this TimeSeries dataset', 'default': 'no description'},
            {'name': 'control', 'type': Iterable,
             'doc': 'Numerical labels that apply to each element in data', 'default': None},
            {'name': 'control_description', 'type': Iterable,
             'doc': 'Description of each control value', 'default': None},
            {'name': 'parent', 'type': 'NWBContainer',
             'doc': 'The parent NWBContainer for this NWBContainer', 'default': None}
            )
    def __init__(self, **kwargs):
        compartments = popargs('compartments', kwargs)
        super(CompartmentSeries, self).__init__(**kwargs)
        self.compartments = compartments

    @staticmethod
    def _compartment_finder(cell_compartments, cond, dtype, start_ind):
        cell_compartments = np.array(cell_compartments)
        if isinstance(cond, dtype):
            return start_ind + np.where(cell_compartments == cond)[0]
        else:
            return np.array([start_ind + np.where(cell_compartments == x)[0] for x in cond]).ravel()

    def find_compartments(self, cell, compartment_numbers=None, compartment_labels=None):
        """

        Parameters
        ----------
        cell: int
            find indices of compartments of this cell
        compartment_numbers: int | Iterable(int) (optional)
            where these are (this is) the compartment(s)
        compartment_labels: str | Iterable(str) (optional)
            or where these are (this is) the label(s)

        Returns
        -------

        np.array(dtype=int)

        """
        if compartment_numbers is not None and compartment_labels is not None:
            raise ValueError('you cannot specify both compartments and compartment_labels')
        if cell == 0:
            start_ind = 0
        else:
            start_ind = self.compartments['number_index'].data[cell-1]
        cell_compartments = self.compartments['number'][cell]
        if compartment_numbers is not None:
            return self._compartment_finder(cell_compartments, compartment_numbers, int, start_ind)
        elif compartment_labels is not None:
            return self._compartment_finder(cell_compartments, compartment_labels, str, start_ind)
        else:
            return np.arange(start_ind, start_ind + len(cell_compartments), dtype=int)
