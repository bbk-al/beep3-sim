#!/usr/bin/env python3
# Author: Adam Light <la002@mail.cryst.bbk.ac.uk>
"""MRes Bioinformatics with Systems Biology Project

This module implements the management of a pipeline of processes.
The pipeline is specified in a configuration file.

Example use:
	pipeline.py -p <pipeline-spec> <pdb>
with <pdb> being a PDB Id.

This module contains the following functions:
	- runCommand -- runs the specified command, managing logs and errors
	- runPipeline -- runs processes in the pipeline if their input files
	                 need to be updated
	- readPipeline -- reads the pipeline configuration
"""
__version__ = '1.0'
__all__ = [
	'runCommand',
	'runPipeline',
	'readPipeline',
]

# imports
from os import environ as env, chdir, getcwd, remove, path, sep as pathsep
from typing import Iterable, Tuple
import argparse
from io import TextIOWrapper
import logging as log
import subprocess
import time

# User-defined types
# Process pipeline type:  a "structured" tuple that ought to be a class...
# First element of each tuple is index of command in that tuple.
# String elements before the command are input types, after are output types.
#Pipeline = Iterable[Tuple[int, str, ...]]
Pipeline = Iterable[Tuple]

# Global variables

# Functions

# Generic runCommand knows nothing of pipelines
def runCommand(cmd: str, dummy = False) -> int:
	"""Runs the command provided, logging and reporting errors consistently.

	- cmd	  -- the command to be run
	- dummy	  -- if true does not run processes, just echoes commands.

	Note: the cmd is run from the directory determined by the python script
	invocation (this is necessary because some commands are relative to this
	location).  Filenames on the command line must therefore be absolute.
	"""
	echo = "echo " if (dummy) else "" 
	cwd = getcwd()
	here = path.dirname(path.realpath(__file__))
	chdir(here)
	binpath = env['PATH']
	if binpath[0:2] != ".:":
		env['PATH'] = ".:" + binpath
	retcode = -1
	log.info("---")  # Separator line in logfile
	log.info(cmd)
	try:
		p = subprocess.Popen(echo + cmd, shell=True, env = env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		for line in p.stdout:
			log.info(line)
		retcode = p.wait()  # No timeout, consider adding timeouts to pipeline
	except OSError as e:
		log.error(f"Execution failed: {e}")
		return -1
	finally:
		chdir(cwd)
		env['PATH'] = binpath

	if retcode < 0:
		log.warning("Process terminated by signal %d" % (-retcode))
	elif retcode > 0:
		log.warning(f"Process returned {retcode}")
	else:
		log.info("Process completed successfully")
	return retcode

# Pipeline management
def runPipeline(pipe: Pipeline, pdbid: str, refresh=False, dummy=False) -> int:
	"""Runs the process pipeline for the pdb id supplied.

	- pipe	  -- list of tuples;  the last element in each tuple is the process 
				 specification, a string with {s} to be replaced by the pdbid;
				 the rest of the tuple elements are file types.
	- pdbid	  -- a string for the PDB Id
	- refresh -- if true forces the pipeline to run for each process.
	- dummy	  -- if true does not run processes, just echoes commands.
	Returns the number of the process in the pipeline that was reached.
	"""
	# Start processing from the first out-of-date or non-existent file type
	ll=log.getLevelName(log.getLogger().getEffectiveLevel())
	#lf=log.getLogger().handlers[0].baseFilename  - no multiple process logging
	required = 0 if refresh else len(pipe)  # type: int
	for n in range(len(pipe)):
		if required > n:
			# Find oldest output file
			pt = None  # previous file modification time
			for t in pipe[n][pipe[n][0]+1:]:
				file = f"{pdbid}{t}"  # type: str
				if path.exists(file):
					mt = path.getmtime(file)
					if pt == None or mt < pt:
						pt = mt
				else:
					log.debug(f"Output {file} not found")
					required = n
					break
			log.debug(f"Oldest output for process {n} is {file}")
	
			# Test each input file age against oldest output file
			for t in pipe[n][1:pipe[n][0]]:
				if required <= n:	# Already found requirement
					break
				try:
					file = f"{pdbid}{t}"  # type: str
					log.debug(f"Test {file} existence")
					assert path.exists(file)
					mt = path.getmtime(file)
					log.debug(f"Test {file} time")
					assert mt <= pt
				except:
					log.debug("Required from here {n}")
					required = -1
				if required >= 0:  # Input exists and is younger than output
					continue
				if n == 0:  # First input not found
					break
				# Find process with this input as output
				try:
					required = \
						[r for r in range(n) if t in pipe[r][pipe[r][0]+1:]][0]
					log.debug(f"Set required to {required}")
				except:
					log.error(f"File type {t} used before produced")
					raise
				break
		if required < 0:
			log.error(f"Error:  {pdbid}.pdb not found")
			break
		elif required < n:
			cmd = pipe[required][pipe[required][0]].format(s=pdbid,ll=ll)
			if runCommand(cmd, dummy) != 0:
				# Delete the output from the failed command
				for t in pipe[required][pipe[required][0]+1:]:
					try:
						os.remove(f"{pdbid}{t}")
					except:
						pass
				break
			required += 1
	return required

# Reading the pipeline configuration
# This is possibly a little quick and dirty...
def readPipeline(pcfg: TextIOWrapper) -> Pipeline:
	"""Reads the pipeline configuration from the supplied stream.

	- pcfg	  -- configuration data stream.
	"""
	cfg = [ "[" + s.strip() + "], " for s in pcfg if s.strip()[0] != '#']
	pipe = eval("[" + str().join(cfg) + "]")
	# Set the first element to be the index to the command
	for p in range(len(pipe)):
		for c in range(len(pipe[p])):
			if "{s}" in pipe[p][c]:
				pipe[p] = tuple([c+1] + pipe[p])
				break
		if c >= len(pipe[p])-1:
			log.error("No command specification found in process {p}")
			raise ValueError
	# Add the terminal entry - final outputs become inputs, blank command
	try:
		pipe += [(-1, pipe[-1][pipe[-1][0]+1:], '')]
	except:
		log.error("No output specification on final process")
		raise
	return pipe

# Main program
if __name__== "__main__":

	# Set up command line parsing
	parser = argparse.ArgumentParser(description=\
					'Calculate the energy of a complete scenario of '
					'subject and crowder proteins.')
	# -p pipeline config file
	parser.add_argument('-p', metavar='pipeline', type=argparse.FileType('r'),
						dest='pipeline', default='pipeline.cfg',
						help='name of pipeline specification file')
	# -w working directory
	parser.add_argument('-w', metavar='work-dir',
						dest='workdir', default=".",
						help='working directory (and location of PDB files)')
	# -loglevel
	parser.add_argument('--loglevel', metavar='(INFO|WARNING|ERROR)',
					dest='loglevel', required=False, default="INFO",
					help='minimum log level to capture: INFO, WARNING, ERROR')
	# -f force refresh of pipeline
	parser.add_argument('-f', action='store_true', dest='refresh',
						help='force refresh of whole pipeline')
	# -d dummy run - only log the commands that would be run
	parser.add_argument('-d', action='store_true', dest='dummy',
						help='dummy run, log commands to be run only')
	# PDB Ids
	parser.add_argument('pdbidlist', metavar='PDB-Id',
						nargs='+',
						help='list of PDB Ids to be processed')

	# Interpret arguments
	args = vars(parser.parse_args())
	refresh = args['refresh']
	loglevel = args['loglevel']
	pcfg = args['pipeline']
	workdir=args['workdir']
	dummy = args['dummy']
	pdbidlist = args['pdbidlist']

	# Set up logging
	log.basicConfig(filename="pipeline.log", filemode='w',
	                format="%(asctime)s %(levelname)s:%(message)s",
	                level=getattr(log, loglevel.upper()))

	# Interpret workdir as an absolute path
	if workdir[0] != pathsep:
		workdir = path.join(env['PWD'], workdir)

	# Read the pipeline
	pipeline = readPipeline(pcfg)
	log.info("Pipeline read with %d processes" % (len(pipeline)))

	# Run the pipeline using absolute path of PDB files
	for pdbid in pdbidlist:
		pdbpath = path.join(workdir, pdbid) if pdbid[0] != pathsep else pdbid
		rv = runPipeline(pipeline, path.join(workdir, pdbid), refresh, dummy)
		if rv < len(pipeline) - 1:
			print(rv, len(pipeline))
			log.error("Failed to generate mesh files, exiting")
			exit(1)

	# Exit cleanly
	exit(0)

