import os
import sys
from datetime import datetime
from glob import glob

import numpy as np
import pandas as pd
import h5py
from ndx_simulation_output import (CompartmentSeries, Compartments,
                                   SimulationMetaData)
from pynwb import NWBFile, NWBHDF5IO
from pynwb.ecephys import ElectricalSeries
from tqdm import tqdm


def add_continuous_compartments(nwbfile, data_fpath, name='membrane_potential', population=None, unit='mV', stub=False):
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
    population: str
        Name of the sonata node-population to convert. If not specified or set to None will try to guess the correct
        population to convert.

    Returns
    -------
    pynwb.NWBFile
    """
    with h5py.File(data_fpath, 'r') as h5:
        pop, report_grp, _, _ = __parse_h5_tree(h5, data_fpath, population)
        nwbfile = __add_spikes_helper(nwbfile, report_grp, population=pop, name=name, unit=unit, stub=stub)
    return nwbfile


def add_spikes(nwbfile, spikes_fpath, population=None):
    """

    Parameters
    ----------
    nwbfile: NWBFile
    spikes_fpath: str
    population: str
        Name of the sonata node-population to convert. If not specified or set to None will try to guess the correct
        population to convert.

    Returns
    -------
    pynwb.NWBFile

    """
    with h5py.File(spikes_fpath, 'r') as h5:
        pop, _, spikes_grp, _ = __parse_h5_tree(h5, spikes_fpath, population)
        nwbfile = __add_spikes_helper(nwbfile, spikes_grp, pop)

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
    with h5py.File(electrodes_data_file, 'r') as h5:
        _, _, _, ecp_grp = __parse_h5_tree(h5, electrodes_data_file)
        nwbfile = __add_electrodes_helper(nwbfile, electrodes_data_file, electrode_positions_file)

    return nwbfile


def sonata2nwb(data_path, save_path, electrodes_file=None, stub=False, description='description',
               identifier='id', population=None, compartment_report_name=None, **kwargs):
    """

    Parameters
    ----------
    data_path: list, str
        The path of the sonata file(s) to convert to nwb. If the path is to a directory then the function will attempt
        to find and convert all sonata files within the directory.
    save_path: str
        Path to the NWB file to save converted data.
    electrodes_file: str
        Path to the location of the electrodes csv containing locations of all the channels in the electrodes, required
        for converting /ecp into EletricalSeries table.
    stub: bool
        Only save a small amount of data to test reading of meta-data
    description: str
        NWBFile.description
    identifier: str
        NWBFile.id
    population: str
        Name of the sonata node-population to convert. If not specified or set to None will try to guess the correct
        population to convert.
    compartment_report_name: str
        Name of Compartments table. If not specified will try to guess from file-name.
    kwargs: fed into NWBFile

    """
    # Get the sonata file(s)
    nwbfile = NWBFile(description, identifier, datetime.now().astimezone(), **kwargs)
    if isinstance(data_path, (list, tuple)):
        sonata_files = data_path

    elif os.path.isfile(data_path):
        sonata_files = [data_path]

    elif os.path.isdir(data_path):
        sonata_files = [fn for fn in glob('{}/*'.format(data_path)) if os.path.isfile(fn) and fn.endswith(('hdf5', 'h5', 'sonata'))]
        if not sonata_files:
            raise Exception('Unable to find any hdf5/sonata files in the {} path. Please specify files to convert directly.'.format(data_path))

    else:
        # TODO: Find a better exception
        raise Exception('Unable to read data_path {}. Please specify a directory '.format(data_path))

    if electrodes_file is None:
        # See if there exists an electrodes.csv file containg channel positions
        # TODO: parse the csv file to make sure it's actually an appropiately formatted electrodes file
        csv_files = [fn for fn in glob('{}/*'.format(data_path)) if os.path.isfile(fn) and fn.endswith('.csv')]
        if csv_files:
            electrodes_file = csv_files[0]

    for file_name in sonata_files:
        with h5py.File(file_name, 'r') as h5:
            pop, report_grp, spikes_grp, ecp_grp = __parse_h5_tree(h5, file_name, population)
            if report_grp:
                # If the compartment report name is not specified by the user, get it from the file name
                name = compartment_report_name or os.path.splitext(os.path.basename(file_name))[0]  # /path/to/membrane.h5 --> membrane
                # convert the sonata /report/<population> group and insert into nwbfile
                nwbfile = __add_continuous_compartments_helper(nwbfile, report_grp, pop, name=name, stub=stub)

            if spikes_grp:
                # convert sonata spikes and insert into nwbfile
                nwbfile = __add_spikes_helper(nwbfile, spikes_grp, pop)

            if ecp_grp and electrodes_file:
                # convert the /ecp report to nwb, but only if there exists a
                nwbfile = __add_electrodes_helper(nwbfile, ecp_grp, electrodes_file)

    with NWBHDF5IO(save_path, 'w') as io:
        io.write(nwbfile, cache_spec=True)


def __parse_h5_tree(h5_handle, file_name, population=None):
    """Parses the hdf5 file for the appropiate groups containing /report/<population>, /spikes/<population> and /ecp for
    the given node population,

    :param h5_handle:
    :param file_name:
    :param population:
    :return: population (str), /report/<population> (h5py.Group), /spikes/<population> (h5py.Group) and /ecp (h5py.Group).
        If the file doesn't contain a report/spikes/ecp section it will pass back null.
    """
    ecp_handle = None
    report_handle = None
    spikes_handle = None

    if 'ecp' in h5_handle.keys() and isinstance(h5_handle['ecp'], h5py.Group):
        ecp_handle = h5_handle['ecp']

    def check_pop(report_type):
        if report_type in h5_handle.keys():
            grp_root = h5_handle[report_type]
            pops = [k for k, g in grp_root.items() if isinstance(g, h5py.Group)]

            # find the appropiate population subgroup. If user specifies population in parameters make sure it exists.
            # otherwise determine the correct population to convert
            if population is not None and population not in pops:
                raise Exception('Could not find node population group {} in {} (valid populations: {})'.format(population, file_name, ' '.join(pops)))
            elif population is None and len(pops) > 1:
                # If more than one population in report raise error to user
                raise Exception('Found mulitple node populations {}, please specify (valid populations: {}'.format(file_name, ' '.join(pops)))
            else:
                grp_pop = population or pops[0]
                return grp_pop, grp_root[grp_pop]

        return population, None

    population, report_handle = check_pop('report')
    population, spikes_handle = check_pop('spikes')
    return population, report_handle, spikes_handle, ecp_handle


def __add_continuous_compartments_helper(nwbfile, h5_grp, population_name=None, name='membrane_potential', unit='mV',
                                         stub=False):
    """Helper function for parsing a /report/<population>/ sonata group and coverting into a nwb Compartments table"""
    data = h5_grp['data'][:10] if stub else h5_grp['data'][:]
    unit = __get_attrs(h5_grp['data'], 'units', unit)  # See if the units attributes exists, otherwise use the default.

    mapping = h5_grp['mapping']
    elem_ids = mapping['element_ids'][:]
    elem_pos = mapping['element_pos'][:]
    index_pointer = mapping['index_pointer'][:]
    node_ids = mapping['node_ids'][:]
    start, stop, timestep = mapping['time'][:]
    time_units = __get_attrs(mapping['time'], 'units', 'ms').lower()
    if time_units == 's':
        t_conv = 1.0
    else:
        t_conv = 1.0/1000.0

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
                           unit=unit, rate=1 / (timestep*t_conv))

    nwbfile.add_acquisition(cs)

    return nwbfile


def __add_spikes_helper(nwbfile, h5_handle, population=None):
    """Parse the sonata /spikes/<population> group and add the units + spike times to the nwb file"""
    node_ids = h5_handle['node_ids'][:]
    timestamps = h5_handle['timestamps'][:]

    for i in tqdm(np.unique(node_ids), desc='reading units'):
        nwbfile.add_unit(spike_times=timestamps[node_ids == i], id=int(i))

    return nwbfile


def __add_electrodes_helper(nwbfile, h5_grp, positions_csv):
    electrodes_df = pd.read_csv(positions_csv, sep=' ')

    electrode_ids = h5_grp['channel_id'][:]
    data = h5_grp['data'][:]
    start, stop, timestep = h5_grp['time'][:]

    # Check sonata file attributes for time units
    time_units = __get_attrs(h5_grp['time'], 'units', 'ms').lower()
    if time_units == 's':
        t_conv = 1.0
    else:
        t_conv = 1.0/1000.0

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
        ElectricalSeries('ElectricalSeries', data, starting_time=start*t_conv,
                         rate=1 / (timestep*t_conv), electrodes=electrodes))
    return nwbfile


def __get_attrs(h5_obj, attr_key, default=None):
    """Helper function to make sure attribute values in h5py are returned as strings and not bytes."""
    val = h5_obj.attrs.get(attr_key, default)
    if sys.version_info[0] >= 3 and isinstance(val, bytes):
        val = val.decode()

    return val
