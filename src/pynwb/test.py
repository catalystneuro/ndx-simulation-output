from pynwb import NWBHDF5IO, NWBFile
from datetime import datetime
from nwbext_simulation_output import CompartmentSeries, Compartments
import numpy as np


compartments = Compartments()
compartments.add_row(number=[0, 1, 2, 3, 4], position=[0.1, 0.2, 0.3, 0.4, 0.5])
compartments.add_row(number=[0], position=[np.nan])
cs = CompartmentSeries('membrane_potential', np.random.randn(10, 6),
                       compartments=compartments,
                       unit='V', rate=100.)
nwbfile = NWBFile('description', 'id', datetime.now().astimezone())
nwbfile.add_acquisition(compartments)
nwbfile.add_acquisition(cs)

with NWBHDF5IO('test_compartment_series.nwb', 'w') as io:
    io.write(nwbfile)

with NWBHDF5IO('test_compartment_series.nwb', mode='r') as io:
    io.read()

assert(all(cs.find_compartments(0, [1, 3]) == [1, 3]))
assert(all(cs.find_compartments(1) == 5))
