#!/usr/bin/env python3
"""
SOC2 Run Manager Utility

Utility functions for managing timestamped analysis runs.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

class RunManager:
    """Manages timestamped analysis runs"""
    
    def __init__(self, base_path: str = "../data/processed"):
        self.base_path = base_path
        self.runs_path = os.path.join(base_path, "runs")
        self.latest_link = os.path.join(base_path, "latest")
    
    def list_runs(self) -> List[str]:
        """List all available runs"""
        if not os.path.exists(self.runs_path):
            return []
        
        runs = []
        for item in os.listdir(self.runs_path):
            run_path = os.path.join(self.runs_path, item)
            if os.path.isdir(run_path):
                runs.append(item)
        
        return sorted(runs, reverse=True)  # Most recent first
    
    def get_latest_run(self) -> str:
        """Get the current latest run timestamp"""
        if os.path.islink(self.latest_link):
            target = os.readlink(self.latest_link)
            return os.path.basename(target)
        return None
    
    def get_run_info(self, run_timestamp: str) -> Dict[str, Any]:
        """Get information about a specific run"""
        run_path = os.path.join(self.runs_path, run_timestamp)
        if not os.path.exists(run_path):
            return None
        
        # Get file list and sizes
        files = []
        total_size = 0
        for file in os.listdir(run_path):
            file_path = os.path.join(run_path, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                files.append({"name": file, "size": size})
                total_size += size
        
        # Try to get generation timestamp from variance report
        generation_time = None
        variance_file = os.path.join(run_path, "control_variance_report.json")
        if os.path.exists(variance_file):
            try:
                with open(variance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    generation_time = data.get('generation_timestamp')
            except:
                pass
        
        return {
            "timestamp": run_timestamp,
            "path": run_path,
            "files": files,
            "total_size": total_size,
            "generation_time": generation_time,
            "is_latest": self.get_latest_run() == run_timestamp
        }
    
    def create_new_run_timestamp(self) -> str:
        """Generate a new timestamp for a run"""
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def update_latest_link(self, run_timestamp: str):
        """Update the latest symlink to point to specified run"""
        target = f"runs/{run_timestamp}"
        
        # Remove existing link if it exists
        if os.path.exists(self.latest_link) or os.path.islink(self.latest_link):
            os.unlink(self.latest_link)
        
        # Create new symlink
        os.symlink(target, self.latest_link)
        print(f"✅ Updated latest link to: {run_timestamp}")
    
    def clean_old_runs(self, keep_count: int = 5):
        """Keep only the most recent N runs"""
        runs = self.list_runs()
        latest = self.get_latest_run()
        
        if len(runs) <= keep_count:
            print(f"📁 Only {len(runs)} runs exist, keeping all")
            return
        
        to_delete = runs[keep_count:]
        deleted_count = 0
        
        for run in to_delete:
            if run == latest:
                print(f"⚠️  Skipping latest run: {run}")
                continue
            
            run_path = os.path.join(self.runs_path, run)
            try:
                import shutil
                shutil.rmtree(run_path)
                deleted_count += 1
                print(f"🗑️  Deleted run: {run}")
            except Exception as e:
                print(f"❌ Failed to delete run {run}: {e}")
        
        print(f"✅ Cleanup complete: {deleted_count} runs deleted, {len(runs) - deleted_count} retained")
    
    def print_run_summary(self):
        """Print a summary of all runs"""
        runs = self.list_runs()
        latest = self.get_latest_run()
        
        print("📊 SOC2 Analysis Runs Summary")
        print("=" * 50)
        print(f"Total runs: {len(runs)}")
        print(f"Latest run: {latest}")
        print()
        
        for run in runs[:10]:  # Show top 10 most recent
            info = self.get_run_info(run)
            if info:
                indicator = "👉" if info["is_latest"] else "  "
                size_mb = info["total_size"] / (1024 * 1024)
                file_count = len(info["files"])
                
                print(f"{indicator} {run} - {file_count} files, {size_mb:.1f}MB")
        
        if len(runs) > 10:
            print(f"   ... and {len(runs) - 10} older runs")

def main():
    """Command line interface for run management"""
    import sys
    
    manager = RunManager()
    
    if len(sys.argv) < 2:
        print("SOC2 Run Manager")
        print("Usage: python run_manager.py <command>")
        print()
        print("Commands:")
        print("  list        - List all runs")
        print("  latest      - Show latest run")
        print("  info <run>  - Show info about specific run")
        print("  clean [N]   - Keep only N most recent runs (default: 5)")
        print("  summary     - Show summary of all runs")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        runs = manager.list_runs()
        for run in runs:
            indicator = "👉" if manager.get_latest_run() == run else "  "
            print(f"{indicator} {run}")
    
    elif command == "latest":
        latest = manager.get_latest_run()
        if latest:
            print(f"Latest run: {latest}")
            info = manager.get_run_info(latest)
            if info:
                size_mb = info["total_size"] / (1024 * 1024)
                print(f"Files: {len(info['files'])}")
                print(f"Size: {size_mb:.1f}MB")
                if info["generation_time"]:
                    print(f"Generated: {info['generation_time']}")
        else:
            print("No runs found")
    
    elif command == "info":
        if len(sys.argv) < 3:
            print("Usage: python run_manager.py info <run_timestamp>")
            return
        
        run = sys.argv[2]
        info = manager.get_run_info(run)
        if info:
            print(f"Run: {info['timestamp']}")
            print(f"Path: {info['path']}")
            print(f"Is Latest: {info['is_latest']}")
            print(f"Total Size: {info['total_size'] / (1024 * 1024):.1f}MB")
            if info["generation_time"]:
                print(f"Generated: {info['generation_time']}")
            print("Files:")
            for file in info["files"]:
                size_kb = file["size"] / 1024
                print(f"  {file['name']} - {size_kb:.1f}KB")
        else:
            print(f"Run not found: {run}")
    
    elif command == "clean":
        keep_count = 5
        if len(sys.argv) >= 3:
            try:
                keep_count = int(sys.argv[2])
            except ValueError:
                print("Invalid number for keep count")
                return
        
        manager.clean_old_runs(keep_count)
    
    elif command == "summary":
        manager.print_run_summary()
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()