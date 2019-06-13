
from pynwb.spec import (
    NWBNamespaceBuilder,
    NWBGroupSpec,
    NWBAttributeSpec,
    NWBDatasetSpec,
    NWBLinkSpec
)
from export_spec import export_spec


def main():
    ns_builder = NWBNamespaceBuilder(doc='Holds structures for recording data from multiple compartments of multiple neurons in a single TimeSeries',
                                     name='ndx-simulation-output',
                                     version='0.1.0',
                                     author='Ben Dichter',
                                     contact='ben.dichter@gmail.com')

    Compartments = NWBGroupSpec(
        default_name='compartments',
        neurodata_type_def='Compartments',
        neurodata_type_inc='DynamicTable',
        doc='table that holds information about what places are being recorded',
        datasets=[
            NWBDatasetSpec(name='number',
                           neurodata_type_inc='VectorData',
                           doc='cell compartment ids corresponding to a each column in the data',
                           dtype='int'),
            NWBDatasetSpec(name='number_index',
                           neurodata_type_inc='VectorIndex',
                           doc='maps cell to compartments',
                           quantity='?'),
            NWBDatasetSpec(name='position',
                           neurodata_type_inc='VectorData',
                           doc='position of recording within a compartment. 0 is close to soma, 1 is other end',
                           dtype='float',
                           quantity='?'),
            NWBDatasetSpec(name='position_index',
                           neurodata_type_inc='VectorIndex',
                           doc='indexes position',
                           quantity='?'),
            NWBDatasetSpec(name='label',
                           neurodata_type_inc='VectorData',
                           doc='labels for compartments',
                           dtype='text',
                           quantity='?'),
            NWBDatasetSpec(name='label_index',
                           neurodata_type_inc='VectorIndex',
                           doc='indexes label',
                           quantity='?')
        ]
    )
    CompartmentsSeries = NWBGroupSpec(
        neurodata_type_def='CompartmentSeries',
        neurodata_type_inc='TimeSeries',
        doc='Stores continuous data from cell compartments',
        links=[
            NWBLinkSpec(name='compartments',
                        target_type='Compartments',
                        doc='meta-data about compartments in this CompartmentSeries',
                        quantity='?')
        ]
    )

    # TODO: add the new data types to this list
    new_data_types = [Compartments, CompartmentsSeries]

    # TODO: include the types that are used and their namespaces (where to find them)
    types_to_include = ['TimeSeries', 'VectorData', 'VectorIndex', 'DynamicTable']
    for ndtype in types_to_include:
        ns_builder.include_type(ndtype, namespace='core')

    export_spec(ns_builder, new_data_types)


if __name__ == "__main__":
    main()
