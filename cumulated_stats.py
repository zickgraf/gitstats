#!/usr/bin/env python3

import datetime
import os
import re
import subprocess

start_date = datetime.datetime(2017, 1, 1)
start_unix = datetime.datetime.timestamp(start_date)

def shell_run(command):
	print("(" + command + ")")
	return subprocess.check_output(command, text=True, shell=True)
	
# adapted from gitstats
def getstatsummarycounts(line):
	numbers = re.findall("\d+", line)
	numbers = list(map(int, numbers))
	if len(numbers) == 1:
		# neither insertions nor deletions: may probably only happen for "0 files changed"
		numbers.append(0)
		numbers.append(0)
	elif len(numbers) == 2 and "(+)" in line:
		# only insertions were printed on line
		numbers.append(0)
	elif len(numbers) == 2 and "(-)" in line:
		# only deletions were printed on line
		numbers.insert(1, 0)
	return numbers


repos = os.listdir("repos")

diffs = {}
for repo in repos:
	output = shell_run('cd repos/' + repo + ' && git log --shortstat --first-parent -m --pretty=format:"%H|%at"')

	lines = output.split("\n")
	
	total_lines = 0
	
	while len(lines) > 0:
		line = lines.pop(0)
		
		if len(line) == 0:
			continue

		parts = line.split("|")
		assert(len(parts) == 2)

		commit_hash = parts[0]
		timestamp = int(parts[1])
		
		if len(lines) > 0 and "changed" in lines[0]:
			nextline = lines.pop(0)
			(files, inserted, deleted) = getstatsummarycounts(nextline)
			diff = inserted - deleted
			if diff != 0:
				if abs(diff) >= 10000:
					print("commit " + commit_hash + " in repo " + repo + " has large diff: " + str(diff))
				diffs[timestamp] = diff
				total_lines += diff
	
	print("package " + repo + " has " + str(total_lines) + " lines")

# adapted from gitstats
f = open("lines_of_code.dat", "w")
lines_of_code = 0
for timestamp in sorted(diffs.keys()):
	lines_of_code += diffs[timestamp]
	if timestamp >= start_unix:
		f.write("%d %d\n" % (timestamp, lines_of_code))
f.close()

f = open("lines_of_code.plot", "w")
f.write(
"""
set terminal png size 1280,1024
set size 1.0,1.0
set output 'lines_of_code.png'
unset key
set yrange [0:]
set xdata time
set timefmt "%s"
set format x "%Y-%m-%d"
set grid y
set ylabel "Lines"
set xtics rotate
set bmargin 6
plot 'lines_of_code.dat' using 1:2 w lines
""")
f.close()

shell_run("gnuplot lines_of_code.plot")
