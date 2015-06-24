import dicom
import os
import sys
import pandas as pd
import numpy as np

# Define scraper function.
def get_dcm_info(scan_dir, temp_path):
    # Set parameters to scrape from common header fields (and how they should be labeled).
    params_dict = {'scan_date': 'AcquisitionDate','scanner_institution':'InstitutionName',
                   'scanner_manufacturer':'Manufacturer','scanner_model':'ManufacturerModelName',
                   'field_strength':'MagneticFieldStrength','sequence_name':'SequenceName',
                   'repetition_time':'RepetitionTime','echo_time':'EchoTime','flip_angle':'FlipAngle',
                   'pixel_spacing':'PixelSpacing','slice_thickness':'SliceThickness',
                   'slice_spacing':'SpacingBetweenSlices','matrix_size':'AcquisitionMatrix'}
    # Set parameters to scrape from Siemens CSA header fields.
    csa_dict = {'n_slices':[0x19, 0x100a],'field_of_view':[0x51, 0x100c]}
    # Get a list of image files in the scan directory.
    img_list = os.listdir(scan_dir)
    # If there are image files in the scan directory...
    if len(img_list) > 0:
        # Initialize a dictionary with n_volumes as the first value.
        info_dict = {'n_volumes':len(img_list)}
        # Get the path to the first file in the image list.
        file_path= '/'.join([scan_dir, img_list[0]])
        # Unzip the compressed DICOM to the temporary image path.
        os.system('gunzip -c {} > {}'.format(file_path, temp_path))
        try:
            dcm_data = dicom.read_file(temp_path)
        except:
            print('......unable to load DICOM, continuing to next scan.')
            for k in params_dict.keys():
                info_dict[k] = 'Not Found'
            for k in csa_dict.keys():
                info_dict[k] = 'Not Found'
            os.system('rm {}'.format(temp_path))
            return info_dict
        else:
            # Try to get information from standard DICOM headers.
            for k, v in params_dict.iteritems():
                try:
                    info_dict[k] = dcm_data.get(v)
                except:
                    info_dict[k] = 'Not Found'    
            # Try to get information from Siemens CSA headers.
            for k, v in csa_dict.iteritems():
                try:
                    info_dict[k] = dcm_data[hex(csa_dict[k][0]), hex(csa_dict[k][1])].value
                except:
                    info_dict[k] = 'Not Found'
            os.system('rm {}'.format(temp_path))
            return info_dict

list_path, data_dir, tmp_path, out_path = sys.argv[1:]

subject_list = np.loadtxt(list_path, dtype='S')

dict_store = []
for subject in subject_list:
    print('Processing subject {}...'.format(subject))
    subject_dir = '/'.join([data_dir, subject])
    dir_items = os.listdir(subject_dir)
    for item in dir_items:
        item_path = '/'.join([subject_dir, item])
        # If the item is a directory, we assume it is a scan directory.
        if os.path.isdir(item_path):
            print('...attempting to extract header information from {}'.format(item))
            scan_dict = get_dcm_info(item_path, tmp_path)
            scan_dict['subject_id'] = subject
            scan_dict['scan_name'] = item
            dict_store.append(scan_dict)
        else:
            pass

info_df = pd.DataFrame.from_dict(dict_store)
info_df.to_csv(out_path)
