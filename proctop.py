#!/usr/bin/env python3
"""proctop - Quick process stats. Top CPU/memory consumers at a glance.

Usage:
    proctop.py                  Top 10 by CPU
    proctop.py --mem            Top 10 by memory
    proctop.py --find node      Find processes matching name
    proctop.py --summary        System summary (load, uptime, process count)
"""

import subprocess, sys, argparse, re

def run(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

def top_by(sort="cpu", n=10):
    key = "-o %cpu" if sort == "cpu" else "-o %mem"
    out = run(f"ps aux {key} | head -{n+1}")
    lines = out.strip().split("\n")
    if not lines:
        return
    # Print header
    print(f"{'USER':<12} {'PID':>6} {'%CPU':>5} {'%MEM':>5} {'RSS':>8} {'COMMAND'}")
    print("-" * 70)
    for line in lines[1:]:
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        user, pid, cpu, mem, vsz, rss = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        cmd = parts[10][:50]
        rss_mb = f"{int(rss)/1024:.0f}M"
        print(f"{user:<12} {pid:>6} {cpu:>5} {mem:>5} {rss_mb:>8} {cmd}")

def find_proc(name: str):
    out = run(f"ps aux | grep -i '{name}' | grep -v grep")
    lines = out.strip().split("\n")
    if not lines or not lines[0]:
        print(f"No processes matching '{name}'")
        return
    print(f"{'PID':>6} {'%CPU':>5} {'%MEM':>5} {'COMMAND'}")
    print("-" * 60)
    for line in lines:
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        print(f"{parts[1]:>6} {parts[2]:>5} {parts[3]:>5} {parts[10][:50]}")
    print(f"\n{len(lines)} matches")

def summary():
    uptime = run("uptime").strip()
    procs = run("ps aux | wc -l").strip()
    disk = run("df -h / | tail -1").strip().split()
    mem = run("vm_stat | head -5")
    
    print(f"Uptime: {uptime}")
    print(f"Processes: {int(procs)-1}")
    if len(disk) >= 5:
        print(f"Disk: {disk[3]} free of {disk[1]} ({disk[4]} used)")
    
    # Parse vm_stat for memory
    pages = {}
    for line in mem.split("\n"):
        m = re.match(r'(.+?):\s+(\d+)', line)
        if m:
            pages[m.group(1).strip()] = int(m.group(2))
    page_size = 16384  # Apple Silicon
    if "Pages free" in pages:
        free_gb = pages["Pages free"] * page_size / (1024**3)
        active_gb = pages.get("Pages active", 0) * page_size / (1024**3)
        print(f"Memory: {active_gb:.1f}G active, {free_gb:.1f}G free")

def main():
    parser = argparse.ArgumentParser(description="Quick process stats")
    parser.add_argument("--mem", action="store_true", help="Sort by memory")
    parser.add_argument("--find", type=str, help="Find process by name")
    parser.add_argument("--summary", action="store_true", help="System summary")
    parser.add_argument("-n", type=int, default=10, help="Number of results")
    args = parser.parse_args()

    if args.summary:
        summary()
    elif args.find:
        find_proc(args.find)
    elif args.mem:
        top_by("mem", args.n)
    else:
        top_by("cpu", args.n)

if __name__ == "__main__":
    main()
