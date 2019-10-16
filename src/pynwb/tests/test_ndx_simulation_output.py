import os
import numpy as np
import unittest
from datetime import datetime
from pynwb import NWBHDF5IO, NWBFile
from ndx_simulation_output import SimulationMetaData, CompartmentSeries, Compartments


class CompartmentsTest(unittest.TestCase):

    def setUp(self):
        self.nwbfile = NWBFile('description', 'id', datetime.now().astimezone())

    def test_add_compartments(self):
        compartments = Compartments()
        compartments.add_row(number=[0, 1, 2, 3, 4], position=[0.1, 0.2, 0.3, 0.4, 0.5])
        compartments.add_row(number=[0], position=[np.nan])

        self.nwbfile.add_lab_meta_data(SimulationMetaData(compartments=compartments))
        cs = CompartmentSeries('membrane_potential',
                               np.random.randn(10, 6),
                               compartments=compartments,
                               unit='V',
                               rate=100.)
        self.nwbfile.add_acquisition(cs)

        filename = 'test_compartment_series.nwb'

        with NWBHDF5IO(filename, 'w') as io:
            io.write(self.nwbfile)

        with NWBHDF5IO(filename, mode='r') as io:
            io.read()

        assert(all(cs.find_compartments(0, [1, 3]) == [1, 3]))
        assert(all(cs.find_compartments(1) == 5))

        os.remove(filename)
