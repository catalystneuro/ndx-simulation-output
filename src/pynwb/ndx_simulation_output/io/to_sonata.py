import os

import numpy as np
from h5py import File
from pynwb import NWBHDF5IO


def nwb2sonata(nwb_path, save_dir):
    """Example of a conversion from from NWB to SONATA

    Parameters
    ----------
    nwb_path: str
    save_dir: str

    """

    with NWBHDF5IO(nwb_path, 'r') as io:
        os.mkdir(save_dir)
        nwb = io.read()
        export_spikes(nwb.units, save_dir)
        export_electrode_positions(nwb.electrodes, save_dir)
        export_electrode_recordings(nwb.acquisition['ElectricalSeries'], save_dir)
        export_membrane_potential(nwb.acquisition['membrane_potential'], save_dir)

    print('done.')


def convert_time(group, time_series):
    """

    Parameters
    ----------
    group: h5py.Group
    time_series: pynwb.TimeSeries

    Returns
    -------
    h5py.Dataset

    """
    start = time_series.starting_time
    timestep = 1 / time_series.rate * 1000
    stop = timestep * time_series.data.shape[0]
    time_dset = group.create_dataset('time', dtype=float, data=[start, stop, timestep])
    time_dset.attrs['units'] = 'ms'

    return time_dset


def export_spikes(units, save_dir, save_fname='spikes.h5'):
    """read spike times from an NWB file and outputs them to a SONATA spikes file

    Parameters
    ----------
    units: pynwb.Units
    save_dir: str
    save_fname: str, optional

    """
    save_fpath = os.path.join(save_dir, save_fname)

    tt = units['spike_times'].target.data[:]
    index_array = np.argsort(tt)

    indexes = units['spike_times'].data
    nodes = np.zeros((indexes[0],))
    for i, (x, y) in enumerate(zip(indexes, indexes[1:])):
        nodes = np.hstack((nodes, np.ones((y - x,)) * (i + 1))).astype('int')

    with File(save_fpath, 'w') as file:
        group = file.create_group('spikes/internal')
        group.attrs['sorting'] = 'by_time'
        group.create_dataset('node_ids', dtype='uint64', data=nodes[index_array])
        timestamps_dset = group.create_dataset('timestamps', dtype='float', data=tt[index_array])
        timestamps_dset.attrs['units'] = 'ms'


def export_electrode_positions(electrodes, save_dir, save_fname='electrodes_300cells.csv'):
    """

    Parameters
    ----------
    electrodes: pynwb.DynamicTable
    save_dir: str
    save_fname: str, optional

    """

    fpath = os.path.join(save_dir, save_fname)

    df = electrodes.to_dataframe()[['x', 'y', 'z']]
    df.columns = ['x_pos', 'y_pos', 'z_pos']
    df.index.name = 'channel'
    df.to_csv(fpath, sep=' ')


def export_electrode_recordings(electrical_series, save_dir, save_fname='ecp.h5'):
    """

    Parameters
    ----------
    electrical_series: pynwb.ElectricalSeries
    save_dir: str
    save_fname: str, optional

    """

    fpath = os.path.join(save_dir, save_fname)

    with File(fpath, 'w') as file:
        group = file.create_group('ecp')
        group.create_dataset('channel_id', dtype='int64', data=electrical_series.electrodes.data[:].ravel())
        data_dset = group.create_dataset(
            'data', dtype='float32', maxshape=(None, electrical_series.data.shape[1]), data=electrical_series.data[:] * 1000)
        data_dset.attrs['units'] = 'mV'

        convert_time(group, electrical_series)


def export_membrane_potential(membrane_potential, save_dir, save_fname='membrane_potential.h5'):
    """

    Parameters
    ----------
    membrane_potential: ndx_simulation_output.CompartmentSeries
    save_dir: str
    save_fname: str, optional

    """
    fpath = os.path.join(save_dir, save_fname)

    with File(fpath, 'a') as file:
        cortex_group = file.create_group('report/cortex')
        data_dset = cortex_group.create_dataset(
            'data', dtype=float,
            data=membrane_potential.data, chunks=True)
        data_dset.attrs['units'] = 'mV'

        mapping_group = cortex_group.create_group('mapping')
        mapping_group.create_dataset(
            'element_pos', dtype=float,
            data=membrane_potential.compartments['position'].target.data)
        mapping_group.create_dataset(
            'element_ids', dtype='uint64',
            data=membrane_potential.compartments['number'].target.data)
        mapping_group.create_dataset(
            'index_pointer', dtype='uint64',
            data=np.hstack((0, membrane_potential.compartments['position'].data[:])))
        mapping_group.create_dataset(
            'node_ids', dtype='uint64',
            data=np.arange(len(membrane_potential.compartments['position'].data)))

        convert_time(mapping_group, membrane_potential)
