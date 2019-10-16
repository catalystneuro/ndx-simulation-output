# -*- coding: utf-8 -*-

import os.path

from pynwb.spec import NWBNamespaceBuilder, export_spec, NWBGroupSpec


def main():
    # these arguments were auto-generated from your cookiecutter inputs
    ns_builder = NWBNamespaceBuilder(doc='Data types for recording data from multiple compartments of multiple '
                                         'neurons in a single TimeSeries.',
                                     name='ndx-simulation-output',
                                     version='0.2.6',
                                     author='Ben Dichter',
                                     contact='ben.dichter@gmail.com')

    types_to_include = ['TimeSeries', 'VectorData', 'VectorIndex', 'DynamicTable', 'LabMetaData']
    for ndtype in types_to_include:
        ns_builder.include_type(ndtype, namespace='core')

    Compartments = NWBGroupSpec(default_name='compartments',
                                neurodata_type_def='Compartments',
                                neurodata_type_inc='DynamicTable',
                                doc='Table that holds information about what places are being recorded.')
    Compartments.add_dataset(name='number',
                             neurodata_type_inc='VectorData',
                             dtype='int',
                             doc='Cell compartment ids corresponding to a each column in the data.')
    Compartments.add_dataset(name='number_index',
                             neurodata_type_inc='VectorIndex',
                             doc='Index that maps cell to compartments.',
                             quantity='?')
    Compartments.add_dataset(name='position',
                             neurodata_type_inc='VectorData',
                             dtype='float',
                             quantity='?',
                             doc='Position of recording within a compartment. 0 is close to soma, 1 is other end.')
    Compartments.add_dataset(name='position_index',
                             neurodata_type_inc='VectorIndex',
                             doc='Index for position.',
                             quantity='?')
    Compartments.add_dataset(name='label',
                             neurodata_type_inc='VectorData',
                             doc='Labels for compartments.',
                             dtype='text',
                             quantity='?')
    Compartments.add_dataset(name='label_index',
                             neurodata_type_inc='VectorIndex',
                             doc='indexes label',
                             quantity='?')

    CompartmentsSeries = NWBGroupSpec(neurodata_type_def='CompartmentSeries',
                                      neurodata_type_inc='TimeSeries',
                                      doc='Stores continuous data from cell compartments')
    CompartmentsSeries.add_link(name='compartments',
                                target_type='Compartments',
                                quantity='?',
                                doc='Metadata about compartments in this CompartmentSeries.')

    SimulationMetaData = NWBGroupSpec(name='simulation',
                                      neurodata_type_def='SimulationMetaData',
                                      neurodata_type_inc='LabMetaData',
                                      doc='Group that holds metadata for simulations.')
    SimulationMetaData.add_group(name='compartments',
                                 neurodata_type_inc='Compartments',
                                 doc='Table that holds information about what places are being recorded.')

    new_data_types = [Compartments, CompartmentsSeries, SimulationMetaData]

    # export the spec to yaml files in the spec folder
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'spec'))
    export_spec(ns_builder, new_data_types, output_dir)


if __name__ == "__main__":
    main()
