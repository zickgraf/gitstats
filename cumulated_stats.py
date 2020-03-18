#!/usr/bin/env python3

import datetime
import os
import re
import subprocess

start_date = datetime.datetime(2000, 1, 1)
start_unix = datetime.datetime.timestamp(start_date)

def shell_run(command):
	print("(" + command + ")")
	return subprocess.check_output(command, text=True, shell=True)

def shell_run_success(command):
	#print("(" + command + ")")
	return subprocess.call(command, shell=True) == 0
	
	
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


os.chdir("repos")
repos = os.listdir(".")

diffs = {}
for repo in repos:
	os.chdir(repo)
	
	print("Getting stats for " + repo)
	
	# get a linear history
	lines = shell_run('git log --shortstat --reverse --first-parent -m --pretty=format:"%H|%at"').split("\n")

	# get initial commit of the linear history and all additional root commits
	initial_commit_hash = lines[0].split("|")[0]
	root_commit_hashes = shell_run("git rev-list --max-parents=0 HEAD").split("\n")
	if initial_commit_hash not in root_commit_hashes:
		printf("Error: the initial commit is not a root commit")
		exit(1)
	root_commit_hashes.remove(initial_commit_hash)

	# for any root commit find merge with the initial commit of the linear history
	# ignore the merge commits and instead consider the log of the subtrees
	blacklist = []
	for root_commit_hash in root_commit_hashes:
		if len(root_commit_hash) == 0:
			continue
		# find first merge commit which is a descendant of initial commit and root commit
		merge_commit_hashes = shell_run("git rev-list --reverse --topo-order --merges --ancestry-path ^%s ^%s HEAD" % (initial_commit_hash, root_commit_hash)).split("\n")
		found_merge_commit_hash = False
		for merge_commit_hash in merge_commit_hashes:
			if shell_run_success("git merge-base --is-ancestor %s %s" % (initial_commit_hash, merge_commit_hash)) and shell_run_success("git merge-base --is-ancestor %s %s" % (root_commit_hash, merge_commit_hash)):
				found_merge_commit_hash = True
				break
		if not found_merge_commit_hash:
			print("Could not find merge commit")
			exit(1)
		blacklist.append(merge_commit_hash)
		# get second parent of merge commit
		parent_commit_hashes = shell_run("git log --pretty=%P -n 1 " + merge_commit_hash).split(" ")
		if len(parent_commit_hashes) != 2:
			print("Merge commit must have exactly two parents")
			exit(1)
		new_lines = shell_run('git log --shortstat --reverse --first-parent -m --pretty=format:"%H|%at" ' + parent_commit_hashes[1]).split("\n")
		lines.extend(new_lines)
		
	cumulated_lines = 0
	
	while len(lines) > 0:
		line = lines.pop(0)
		
		if len(line) == 0:
			continue

		parts = line.split("|")
		assert(len(parts) == 2)

		commit_hash = parts[0]
		timestamp = int(parts[1])
		if timestamp in diffs:
			print("Warning: duplicate timestamp: " + commit_hash)
		else:
			diffs[timestamp] = 0
		
		if len(lines) > 0 and "changed" in lines[0]:
			nextline = lines.pop(0)
			(files, inserted, deleted) = getstatsummarycounts(nextline)
			diff = inserted - deleted
			if diff != 0 and commit_hash not in blacklist:
				if abs(diff) >= 10000:
					print("commit " + commit_hash + " in repo " + repo + " has large diff: " + str(diff))
				diffs[timestamp] += diff
				cumulated_lines += diff
	
	print("Package " + repo + " has " + str(cumulated_lines) + " lines")
	
	# sanity check: let git compute the total number of lines
	output = shell_run("git diff --shortstat `git hash-object -t tree /dev/null`")
	result = re.search("(\d+) insertions", output)
	if result is None:
		print("Could not get number of lines")
		exit(1)
	total_lines = int(result.group(1))
	if cumulated_lines != total_lines:
		print("Error: found %d cumulated lines but %d total lines" % (cumulated_lines, total_lines));
	
	os.chdir("..")

os.chdir("..")

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
