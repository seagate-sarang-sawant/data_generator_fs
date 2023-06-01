### Motivation:
    Problem: Python script to load a filesystem with 1 billion files
    Details:
    The directory and sub-directory structure should be like the tree
    structure shown below. Depth of directory should be 5 levels and
    each directory (including root mount point) should have
    10 sub-directories.
    e.g.
    
    /root_mount_point
    ├── dir1
    │   ├── dir1_1
    │   │   ├── dir1_1_1
    │   │   │   ├── dir1_1_1_1
    │   │   │   │   ├── dir1_1_1_1_1
    │   │   │   │   ├── dir1_1_1_1_2
    │   │   │   │   ├── dir1_1_1_1_3
    │   │   │   │   ├── ...
    │   │   │   │   └── dir1_1_1_1_10
    │   │   │   ├── dir1_1_1_2
    │   │   │   ├── dir1_1_1_3
    │   │   │   ├── ...
    │   │   │   └── dir1_1_1_10
    │   │   ├── dir1_1_2
    │   │   ├── dir1_1_3
    │   │   ├── ....
    │   │   └── dir1_1_10
    │   ├── dir1_2
    │   ├── dir1_3
    │   ├── ...
    │   └── dir1_10
    ├── dir2
    │   ├── dir2_1
    │   ├── dir2_2
    │   ├── dir2_3
    │   ├── ...
    │   └── dir2_10
    ├── ...
    └── dir10
    ├── dir10_1
    ├── dir10_2
    ├── dir10_3
    ├── ...
    └── dir10_10
    
    Distribution of 1 billion files can be done uniformly. i.e., Each directory/sub-directory can contain equal number of files. As each level has 10 directories, 5 levels will have 105 (100k) directories/sub-directories. Therefore, upon uniform distribution, each directory will have 109/105 = 104 (10k) files.
    File size can vary randomly between 4kb to 1mb.
    Content of file can be random text.
    The number and size range of files can be altered as per future requirement.


### Solution and Usage:
Utility `generate_data_in_fs.py` can be used to create folder hierarchy and data files
of random sizes specified with size command line argument. The script calculates the
number of directories generated and creates files in each directory including the 
top (rootdir) directory. In case the total files specified (--files) can not
be uniformly distributed among folders, script creates files with approximation.     

Script can be benchmarked with timeit and increasing numbers
adhering to storage capacity of the file system.
Script does not check the capacity before generating the data which
 can be added in the script. 
Example command:
```
generate_data_in_fs.py --files=200 --depth=3 --dirs=5 
--rootdir="/Users/sarangsawant" -l=10

usage: generate_data_in_fs.py [-h] [-d DEPTH] [-n DIRS] [-r ROOTDIR] [-s SIZE] [-t FILES] [-c CONTENT] [-l LOG_LEVEL] [-p]

options:
  -h, --help            show this help message and exit
  -d DEPTH, --depth DEPTH
                        Depth of directory structure. e.g. 5 level depth under var dir /var/a/b/c/d/e
  -n DIRS, --dirs DIRS  Number of directories to be created within a dir at any level.
  -r ROOTDIR, --rootdir ROOTDIR
                        Root dir in which the data is to be created
  -s SIZE, --size SIZE  Size range of the file to be created e.g. 4KB-8KB, 4KB-1MB
  -t FILES, --files FILES
                        Number of files to be created in the directory structure.
  -c CONTENT, --content CONTENT
                        Content type Random or else.
  -l LOG_LEVEL, --log_level LOG_LEVEL
                        log level value as defined belowCRITICAL = 50FATAL = CRITICALERROR = 40WARNING = 30 WARN = WARNINGINFO = 20 DEBUG = 10
  -p                    Time the run.

```

