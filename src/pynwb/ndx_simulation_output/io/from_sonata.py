import os
from datetime import datetime
from glob import glob

import numpy as np
import pandas as pd
from h5py import File
from ndx_simulation_output import (CompartmentSeries, Compartments,
                                   SimulationMetaData)
from pynwb import NWBFile, NWBHDF5IO
from pynwb.ecephys import ElectricalSeries
from tqdm import tqdm


def add_continuous_compartments(nwbfile, data_fpath, name='membrane_potential',
                                unit='mV', stub=False):
    """

    Parameters
    ----------
    nwbfile: pynwb.NWBFile
    data_fpath: str
    name: str
        name that will be used for the saved data object
    unit:
        unit of measurement for the
    stub: bool

    Returns
    -------
    pynwb.NWBFile
    """
    with File(data_fpath, 'r') as file:
        cortex = file['report/cortex']
        if stub:
            data = cortex['data'][:10]
        else:
            data = cortex['data'][:]
        mapping = cortex['mapping']
        elem_ids = mapping['element_ids'][:]
        elem_pos = mapping['element_pos'][:]
        index_pointer = mapping['index_pointer'][:]
        node_ids = mapping['node_ids'][:]
        start, stop, timestep = mapping['time'][:]

        compartments = Compartments()
        nwbfile.add_lab_meta_data(SimulationMetaData(compartments=compartments))

        for i_start, i_stop, node_id in tqdm(zip(index_pointer,
                                                 index_pointer[1:], node_ids),
                                             total=len(node_ids),
                                             desc='reading continuous data'):
            compartments.add_row(id=int(node_id),
                                 number=elem_ids[i_start:i_stop].astype('int'),
                                 position=elem_pos[i_start:i_stop])

        cs = CompartmentSeries(name, data,
                               compartments=compartments,
                               unit=unit, rate=1 / timestep * 1000)

        nwbfile.add_acquisition(cs)

        return nwbfile


def add_spikes(nwbfile, spikes_fpath):
    """

    Parameters
    ----------
    nwbfile: NWBFile
    spikes_fpath: str

    Returns
    -------
    pynwb.NWBFile

    """
    with File(spikes_fpath, 'r') as file:
        node_ids = file['spikes/internal/node_ids'][:]
        timestamps = file['spikes/internal/timestamps'][:]

    for i in tqdm(np.unique(node_ids), desc='reading units'):
        nwbfile.add_unit(spike_times=timestamps[node_ids == i], id=int(i))

    return nwbfile


def add_electrodes(nwbfile, electrode_positions_file, electrodes_data_file):
    """

    Parameters
    ----------
    nwbfile: pynwb.NWBFile
    electrode_positions_file: str
    electrodes_data_file: str

    Returns
    -------
    pnwb.NWBFile

    """

    electrodes_df = pd.read_csv(electrode_positions_file, sep=' ')

    with File(electrodes_data_file, 'r') as file:
        electrode_ids = file['ecp/channel_id'][:]
        data = file['ecp/data'][:]
        start, stop, timestep = file['ecp/time'][:]

    device = nwbfile.create_device('simulated_implant')
    electrode_group = nwbfile.create_electrode_group(
        'simulated_implant', 'description', 'unknown', device)

    for (id, x, y, z) in electrodes_df.values:
        nwbfile.add_electrode(x=x, y=y, z=z, imp=np.nan, id=int(id),
                              location='unknown', filtering='none',
                              group=electrode_group)

    match_electrodes = [np.where(electrode_ids == x)[0] for x in electrodes_df['channel']]

    electrodes = nwbfile.create_electrode_table_region(match_electrodes, 'all electrodes')

    nwbfile.add_acquisition(
        ElectricalSeries('ElectricalSeries', data / 1000, starting_time=start,
                         rate=1 / timestep * 1000, electrodes=electrodes))
    return nwbfile


def sonata2nwb(data_dir, save_path=None, stub=False, description='description',
               identifier='id', **kwargs):
    """Example of a conversion from sonata to NWB

    Parameters
    ----------
    data_dir: str
    save_path: str, optional
    stub: bool, optional
        Only save a small amount of data to test reading of meta-data
    description: str, optional
        NWBFile.description
    identifier: str, optional
        NWBFile.id
    kwargs: fed into NWBFile

    """

    if save_path is None:
        save_path = data_dir + '.nwb'

    nwbfile = NWBFile(description, identifier, datetime.now().astimezone(), **kwargs)

    membrane_fpath = os.path.join(data_dir, 'membrane_potential.h5')
    nwbfile = add_continuous_compartments(nwbfile, membrane_fpath, stub=stub)

    spikes_fpath = os.path.join(data_dir, 'spikes.h5')
    nwbfile = add_spikes(nwbfile, spikes_fpath)

    electrode_pos_path = glob(os.path.join(data_dir, 'electrodes*.csv'))[0]
    ecp_fpath = os.path.join(data_dir, 'ecp.h5')
    nwbfile = add_electrodes(nwbfile, electrode_pos_path, ecp_fpath)

    print('writing NWB file...', flush=True)
    with NWBHDF5IO(save_path, 'w') as io:
        io.write(nwbfile, cache_spec=True)
    print('done.')
