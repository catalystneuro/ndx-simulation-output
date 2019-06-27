
from pynwb.spec import NWBNamespaceBuilder, NWBGroupSpec
from export_spec import export_spec


def main():
    ns_builder = NWBNamespaceBuilder(doc='Holds structures for recording data from multiple compartments of multiple '
                                         'neurons in a single TimeSeries',
                                     name='ndx-simulation-output',
                                     version='0.2.2',
                                     author='Ben Dichter',
                                     contact='ben.dichter@gmail.com')

    Compartments = NWBGroupSpec(default_name='compartments', neurodata_type_def='Compartments',
                                neurodata_type_inc='DynamicTable',
                                doc='table that holds information about what places are being recorded')
    Compartments.add_dataset(name='number', neurodata_type_inc='VectorData', dtype='int',
                             doc='cell compartment ids corresponding to a each column in the data')
    Compartments.add_dataset(name='number_index', neurodata_type_inc='VectorIndex',
                             doc='maps cell to compartments', quantity='?')
    Compartments.add_dataset(name='position', neurodata_type_inc='VectorData', dtype='float', quantity='?',
                             doc='position of recording within a compartment. 0 is close to soma, 1 is other end')
    Compartments.add_dataset(name='position_index', neurodata_type_inc='VectorIndex',
                             doc='indexes position', quantity='?')
    Compartments.add_dataset(name='label', neurodata_type_inc='VectorData', doc='labels for compartments',
                             dtype='text', quantity='?')
    Compartments.add_dataset(name='label_index', neurodata_type_inc='VectorIndex', doc='indexes label', quantity='?')

    CompartmentsSeries = NWBGroupSpec(neurodata_type_def='CompartmentSeries', neurodata_type_inc='TimeSeries',
                                      doc='Stores continuous data from cell compartments')
    CompartmentsSeries.add_link(name='compartments', target_type='Compartments', quantity='?',
                                doc='meta-data about compartments in this CompartmentSeries')

    SimulationMetaData = NWBGroupSpec(default_name='simulation', neurodata_type_def='SimulationMetaData',
                                      neurodata_type_inc='LabMetaData', doc='group that holds metadata for simulation')
    SimulationMetaData.add_group(name='compartments', neurodata_type_inc='Compartments',
                                 doc='table that holds information about what places are being recorded')
    SimulationMetaData.add_attribute(name='help', dtype='text', doc='help',
                                     value='container for simulation meta-data that goes in /general')

    new_data_types = [Compartments, CompartmentsSeries, SimulationMetaData]

    types_to_include = ['TimeSeries', 'VectorData', 'VectorIndex', 'DynamicTable', 'LabMetaData']
    for ndtype in types_to_include:
        ns_builder.include_type(ndtype, namespace='core')

    export_spec(ns_builder, new_data_types)


if __name__ == "__main__":
    main()
