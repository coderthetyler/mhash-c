#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

"""
Takes dataset and minhashing results as input and generates a plot comparing
pair similarity with the probability of a call from mhash. A number of buckets
must be specified as well as the distribution is discreet.
"""

from sys import argv
import os
import random
from pymhlib import Dataset, Observation
import argparse
from math import floor


""" Parse program arguments """
desc = "Generates a plot of similarity versus calling probability for pairs."
parser = argparse.ArgumentParser(description=desc)
parser.add_argument("-d", 
                    action="store",
                    type=str,
                    dest="dsetpath",
                    help="path to original dataset",
                    required=True)
parser.add_argument("-p", 
                    action="store", 
                    type=str, 
                    dest="mhashpath",
                    help="path to minhashing results",
                    required=True)
parser.add_argument("-b",
                    action="store",
                    type=int,
                    dest="nbuckets",
                    help="number of buckets to group pairs into",
                    required=True)
parser.add_argument("-E", 
                    action="count", 
                    dest="isexcl",
                    help="minhashing was run exclusively, i.e. on a dataset with itself",
                    required=False)
parser.add_argument("-o", 
                    action="store", 
                    type=str, 
                    dest="outpath",
                    default=None,
                    help="path to output PNG file",
                    required=False)
parser.add_argument("-m",
                    action="store",
                    type=float,
                    dest="minb",
                    default=0.0,
                    help="minimum similarity bound",
                    required=False)
parser.add_argument("-M",
                    action="store",
                    type=float,
                    dest="maxb",
                    help="maximum similarity bound",
                    default=1.0,
                    required=False)
args = parser.parse_args()
dsetpath = args.dsetpath
mhashpath = args.mhashpath
nbuckets = args.nbuckets
isexcl = args.isexcl
outpath = args.outpath
minb = args.minb
maxb = args.maxb


""" Load plotting library, if necessary """
if not outpath is None:
	import matplotlib as mpl
	# Don't require a display device
	# Stolen from: https://stackoverflow.com/a/4935945
	mpl.use('Agg')
	import matplotlib.pyplot as plt


""" Load datasets from file """
with open(dsetpath, "r") as f:
	dsets = Dataset.from_file(f)
d1 = dsets[0]
if isexcl == 1:
	d2 = dsets[0]
else:
	d2 = dsets[1]


""" Partition pairs into buckets based on similarity """
buckets = [0.0] * nbuckets
for i in range(d1.N):
	for j in range(d2.N):
		if isexcl and i == j:
			continue
		sim = d1.obvs[i].jaccard(d2.obvs[j])
		if sim < minb or sim > maxb:
			continue
		b = int(floor(nbuckets * (sim-minb)/(maxb-minb)))
		if b == nbuckets:
			b -= 1
		buckets[b] += 1


""" Count number of pairs in each bucket called by mhash """
ncalled = [0.0] * nbuckets
with open(mhashpath, "r") as f:
	cnt = 0
	ln = f.readline()
	while ln:
		dat = [int(x) for x in ln.rstrip().split(",")]
		i = dat[0]
		for j in dat[1:]:
			sim = d1.obvs[i].jaccard(d2.obvs[j])
			if sim < minb or sim > maxb:
				continue
			b = int(floor(nbuckets * (sim-minb)/(maxb-minb)))
			if b == nbuckets:
				b -= 1
			ncalled[b] += 1
		ln = f.readline()


""" Output graph and print data table """
x = [b for b in range(nbuckets)]
s = ["{}:{}".format(minb+b*(maxb-minb)/nbuckets, minb+(b+1)*(maxb-minb)/nbuckets) for b in range(nbuckets)]
ps = [0.0] * nbuckets
for b in range(nbuckets):
	if buckets[b] == 0:
		ps[b] = 0.0
	else:
		ps[b] = ncalled[b] / buckets[b]
print("similarity,proportion,called,total")
for i in range(len(ps)):
	print("{},{}".format(s[i], ps[i]))
if not outpath is None:
	plt.plot(x,ps)
	plt.ylim(0.0,1.0)
	plt.xticks(x,s,rotation="vertical")
	plt.subplots_adjust(bottom=0.05)
	plt.savefig(outpath, bbox_inches="tight")

print("done.")
