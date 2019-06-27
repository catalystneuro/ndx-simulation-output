from h5py import File
from datetime import datetime
from pynwb import NWBFile, NWBHDF5IO
from ndx_simulation_output import CompartmentSeries, Compartments, SimulationMetaData
from tqdm import tqdm


def sonata2nwb(sonata_fpath, save_path, stub=False, description='description', id='id', **kwargs):
    """

    Parameters
    ----------
    sonata_fpath: str
    save_path: str
    stub: bool
        Only save a small amount of data to test reading of meta-data
    description: str
        NWBFile.description
    id: str
        NWBFile.id
    kwargs: fed into NWBFile

    Returns
    -------

    """
    with File(sonata_fpath, 'r') as file:
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

        nwbfile = NWBFile(description, id, datetime.now().astimezone(), **kwargs)

        compartments = Compartments()
        nwbfile.add_lab_meta_data(SimulationMetaData(name='simulation', compartments=compartments))

        for i_start, i_stop, node_id in tqdm(zip(index_pointer, index_pointer[1:], node_ids), total=len(node_ids),
                                             desc='setting up NWBFile'):
            compartments.add_row(id=int(node_id),
                                 number=elem_ids[i_start:i_stop].astype('int'),
                                 position=elem_pos[i_start:i_stop])

        cs = CompartmentSeries('membrane_potential', data, compartments=compartments, unit='mV', rate=timestep/1000)

        nwbfile.add_acquisition(cs)
        print('writing NWB file...', flush=True)
        with NWBHDF5IO(save_path, 'w') as io:
            io.write(nwbfile, cache_spec=True)
        print('done.')
