import os
import copy
import logging
import shutil
import tarfile
import gzip
from hashlib import sha256

logger  = logging.getLogger('nrc_ngs_dl.sequence_run')
class SequenceRun:
    def __init__(self, a_lane, file_info, dest_folder):
        """Initialize the object 
        Args:
            a_lane: information of a lane
            file_info: information of all the files in this lane
            dest_folder: the folder to keep all the fastq files of this lane
        """
        self.data_url = a_lane['pack_data_url']
        self.file_info = file_info
        self.path_source_file = os.path.join(dest_folder,a_lane['package_name'])
        self.path_destination_folder = os.path.join(dest_folder,a_lane['package_name'].split('.')[0])
        if os.path.exists(self.path_destination_folder):
            logger.info('Delete folder for broken/reprocessed data')
            shutil.rmtree(self.path_destination_folder)
        os.mkdir(self.path_destination_folder)
       
    def unzip_package(self):
        """Unzip a .tar or .tar.gz file"""
        try:
            logger.info('Unzip file')
            tar = tarfile.open(self.path_source_file)
            tar.extractall(self.path_destination_folder)
            tar.close()
        except:
            logger.info("An empty .tar/.tar.gz file")
            return False
        return True

    def name_mapping(self,oldname):
        """Find the correspondent new name for a file"""
        oldname_parts = oldname.split("_")
        index = 0
        for a_row in self.file_info:
            if a_row['sample_name']==oldname_parts[0]:
                newname = a_row['biomaterial']+"_"+oldname_parts[0]+"_"+oldname_parts[-1]
                fileIndex = index
            index+=1
        if newname is None:
            #logger.info('cannot find matching name %s' % oldname)
            newname = oldname+'_old_name'    
        return oldname, newname, fileIndex


    def rename_files(self):
        """Rename files in a lane with new names"""
        logger.info('Rename files')
        #path_to_old_file = self.path_destination_folder
        path_to_old_file = []
        for dirpath, dirname,filename in os.walk(self.path_destination_folder):
            for a_dirname in dirname:
                path_to_old_file.append(os.path.join(dirpath,a_dirname))
        
        for a_path in path_to_old_file:    
            for dirpath, dirname,filename in os.walk(a_path):
                for a_file in filename:
                    oldname_short, newname_short,fileIndex = self.name_mapping(a_file)
                    oldname = os.path.join(a_path, oldname_short)
                    newname = os.path.join(self.path_destination_folder, newname_short)
                
                    f = open(oldname, 'rb')
                    a_code = sha256(f.read()).hexdigest();
                    os.rename(oldname, newname)
                    #zip file and sha256
                
                    newnamezip = newname+".gz";
                    with open(newname) as f_in, gzip.open(newnamezip, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                    #if self.file_info[fileIndex] has old name, new name. sha256
                    if 'new_name' in self.file_info[fileIndex]:
                        new_row = copy.deepcopy(self.file_info[fileIndex])
                        fileIndex = len(self.file_info)
                        self.file_info.append(new_row)
                    
                    self.file_info[fileIndex]['original_name'] = oldname_short
                    self.file_info[fileIndex]['new_name'] = newname_short
                    self.file_info[fileIndex]['folder_name'] = self.path_destination_folder
                    self.file_info[fileIndex]['SHA256'] = a_code
                    self.file_info[fileIndex]['file_size'] = os.stat(newname).st_size
                    os.unlink(newname)
                
            if os.path.isdir(a_path):
                os.rmdir(a_path)

        
      
