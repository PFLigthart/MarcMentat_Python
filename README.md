# MarcMentat_Python
Code to run finite element analysis in MarcMentat using python scripts. This allows for an optimisation loop to be setup with a finite element analysis within the loop.

## Contents
1. Instructions for how to setup a conda virtual environment in windows and to add the required libraries is provided.
2. Instructions for how to setup a python script that can interface with MarcMentat is provided.
3. Instructions for how to run the python script from the conda prompt *(terminal)* is is also provided.

My personal files used for my masters thesis are included and can be used as an example. A short discription of what my code is designed for is also provided.

## How to setup the conda virtual environment and add the required libraries.
The libraries required cannot be installed using either Pip or Conda. These libraries are part of the propriatary software and hence need to be copied into the virtual environment.
I use [miniconda](https://docs.conda.io/en/latest/miniconda.html) to setup my virtual environements.It is "a small, bootstrap version of [Anaconda](https://www.anaconda.com/)".

Here is a step by step procedure.

1. Open the anaconda terminal.
    * This can be found by seaching 'Anaconda Prompt' in the windows menu.
2. Create a virtual environemnt using conda
    * conda create --name Apex_Mentat_Pip python=3.8
	    * It is not recommended to mix conda and pip package intalls. Therefor the 'Pip' was appended to name to deonte that all packages within the environemnet should be installed using pip
3. Activate the environment.
	* conda activate Apex_Mentat_Pip
4. Install the required packages using pip (numpy and scipy) however, the installation of scipy will also install numpy.
	* pip install scipy
5. Move py_mentat and py_post files into virtual environmnet.
	* Files are located at: C:\Program Files\MSC.Software\Marc\2021.4.0\mentat2021.4\shlib\win64
		py_mentat.py
		py_post.py
    * Move files into the conda virtual environment.
	    * (Thanks to SB Chung for the following steps.)
	    * Depending on what environment you are using, the following steps may vary. However, if a conda environment is being used the following can be done
            1. Open the anaconda terminal.
            2. Activate the environment.
                * conda activate Apex_Mentat_Pip
            3. type: import sys
            4. type: sys.path
                * Different paths will be displayed. Look for the path that shows were the DLLs are stored.
                    * e.g.
                C:\\Users\\jubil\\miniconda3\\envs\\Apex_mentat_pip\\DLLs
            5. If present, remove the double '\\' to be only a single '\\', as shown below:
                * C:\Users\<your username>\miniconda3\envs\Apex_mentat_pip\DLLs
        * Place the py_mentat and py_post files into this directory. 
* The virtual environment should now be able to use these libraries.
