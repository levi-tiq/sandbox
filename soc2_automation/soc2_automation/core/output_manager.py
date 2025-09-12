#!/usr/bin/env python3
"""
SOC2 Output Manager

Centralized output path management for consistent file organization.
Creates timestamped output directories with organized subdirectories.

New structure:
data/outputs/
├── YYYY-MM-DD_HHMMSS/
│   ├── reports/          # Generated reports, summaries
│   ├── visuals/          # PNG, HTML visualizations  
│   ├── json/             # JSON data files, analysis results
│   ├── summaries/        # Text summaries, logs
│   └── metadata.json     # Run metadata
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

class OutputManager:
    """Manages output directory structure and path generation"""
    
    def __init__(self, base_dir: str = "data/outputs"):
        self.base_dir = base_dir
        self.current_run_id = None
        self.current_run_path = None
        self.subdirs = {
            'reports': 'Generated reports and summaries',
            'visuals': 'PNG, HTML, and other visualizations', 
            'json': 'JSON data files and analysis results',
            'summaries': 'Text summaries, logs, and documentation'
        }
        
    def create_new_run(self, run_description: str = "SOC2 Analysis Run") -> str:
        """Create a new timestamped run directory"""
        # Generate timestamp-based run ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_run_id = timestamp
        
        # Create run directory path
        self.current_run_path = os.path.join(self.base_dir, timestamp)
        
        # Create directory structure
        os.makedirs(self.current_run_path, exist_ok=True)
        
        # Create subdirectories
        for subdir in self.subdirs:
            subdir_path = os.path.join(self.current_run_path, subdir)
            os.makedirs(subdir_path, exist_ok=True)
        
        # Create run metadata
        metadata = {
            'run_id': self.current_run_id,
            'created_at': datetime.now().isoformat(),
            'description': run_description,
            'subdirectories': self.subdirs,
            'status': 'in_progress'
        }
        
        metadata_path = os.path.join(self.current_run_path, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Created new run: {self.current_run_id}")
        print(f"📁 Output directory: {self.current_run_path}")
        
        return self.current_run_path
    
    def get_latest_run(self) -> Optional[str]:
        """Get the most recent run directory"""
        if not os.path.exists(self.base_dir):
            return None
        
        # Get all run directories
        run_dirs = [d for d in os.listdir(self.base_dir) 
                   if os.path.isdir(os.path.join(self.base_dir, d)) 
                   and d.replace('_', '').replace('-', '').isdigit()]
        
        if not run_dirs:
            return None
        
        # Sort by timestamp (newest first)
        run_dirs.sort(reverse=True)
        latest_run = run_dirs[0]
        
        self.current_run_id = latest_run
        self.current_run_path = os.path.join(self.base_dir, latest_run)
        
        return self.current_run_path
    
    def set_current_run(self, run_id: str) -> bool:
        """Set a specific run as current"""
        run_path = os.path.join(self.base_dir, run_id)
        
        if os.path.exists(run_path):
            self.current_run_id = run_id
            self.current_run_path = run_path
            return True
        else:
            return False
    
    def get_output_path(self, category: str, filename: str, create_run_if_needed: bool = True) -> str:
        """Get full output path for a file"""
        # Validate category
        if category not in self.subdirs:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {list(self.subdirs.keys())}")
        
        # Create run if needed
        if not self.current_run_path:
            if create_run_if_needed:
                self.create_new_run()
            else:
                raise ValueError("No current run set. Call create_new_run() first.")
        
        # Ensure subdirectory exists
        subdir_path = os.path.join(self.current_run_path, category)
        os.makedirs(subdir_path, exist_ok=True)
        
        # Return full file path
        return os.path.join(subdir_path, filename)
    
    def get_category_path(self, category: str) -> str:
        """Get path to a specific category directory"""
        if category not in self.subdirs:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {list(self.subdirs.keys())}")
        
        if not self.current_run_path:
            raise ValueError("No current run set. Call create_new_run() first.")
        
        return os.path.join(self.current_run_path, category)
    
    def complete_run(self, summary: str = "") -> None:
        """Mark the current run as complete"""
        if not self.current_run_path:
            return
        
        metadata_path = os.path.join(self.current_run_path, 'metadata.json')
        
        # Update metadata
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata['status'] = 'completed'
            metadata['completed_at'] = datetime.now().isoformat()
            metadata['summary'] = summary
            
            # Count generated files
            file_counts = {}
            for category in self.subdirs:
                category_path = os.path.join(self.current_run_path, category)
                if os.path.exists(category_path):
                    file_counts[category] = len([f for f in os.listdir(category_path) 
                                               if os.path.isfile(os.path.join(category_path, f))])
                else:
                    file_counts[category] = 0
            
            metadata['file_counts'] = file_counts
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Run {self.current_run_id} completed")
            print(f"📊 Generated files: {sum(file_counts.values())} total")
            for category, count in file_counts.items():
                if count > 0:
                    print(f"   {category}: {count} files")
    
    def list_runs(self) -> list:
        """List all available runs"""
        if not os.path.exists(self.base_dir):
            return []
        
        runs = []
        run_dirs = [d for d in os.listdir(self.base_dir) 
                   if os.path.isdir(os.path.join(self.base_dir, d))]
        
        for run_dir in sorted(run_dirs, reverse=True):
            metadata_path = os.path.join(self.base_dir, run_dir, 'metadata.json')
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                runs.append(metadata)
            else:
                # Create basic metadata for runs without it
                runs.append({
                    'run_id': run_dir,
                    'created_at': 'unknown',
                    'description': 'Legacy run',
                    'status': 'unknown'
                })
        
        return runs
    
    def cleanup_old_runs(self, keep_count: int = 10) -> None:
        """Keep only the most recent N runs"""
        runs = self.list_runs()
        
        if len(runs) <= keep_count:
            return
        
        # Remove older runs
        runs_to_remove = runs[keep_count:]
        
        for run in runs_to_remove:
            run_path = os.path.join(self.base_dir, run['run_id'])
            if os.path.exists(run_path):
                import shutil
                shutil.rmtree(run_path)
                print(f"🗑️  Removed old run: {run['run_id']}")
        
        print(f"✅ Cleanup complete, kept {keep_count} most recent runs")


# Convenience functions for common usage patterns
def get_output_manager() -> OutputManager:
    """Get a singleton output manager instance"""
    if not hasattr(get_output_manager, '_instance'):
        get_output_manager._instance = OutputManager()
    return get_output_manager._instance

def create_new_analysis_run(description: str = "SOC2 Analysis Run") -> str:
    """Create a new analysis run and return the path"""
    manager = get_output_manager()
    return manager.create_new_run(description)

def get_analysis_output_path(category: str, filename: str) -> str:
    """Get output path for analysis files"""
    manager = get_output_manager()
    return manager.get_output_path(category, filename)

def complete_analysis_run(summary: str = "") -> None:
    """Complete the current analysis run"""
    manager = get_output_manager()
    manager.complete_run(summary)


def main():
    """Test the output manager"""
    print("🧪 Testing Output Manager")
    print("=" * 40)
    
    # Create output manager
    manager = OutputManager()
    
    # Create new run
    run_path = manager.create_new_run("Test SOC2 Analysis Run")
    
    # Test file path generation
    json_path = manager.get_output_path('json', 'test_results.json')
    visual_path = manager.get_output_path('visuals', 'test_chart.png')
    report_path = manager.get_output_path('reports', 'analysis_summary.txt')
    
    print(f"\n📁 Test paths generated:")
    print(f"   JSON: {json_path}")
    print(f"   Visual: {visual_path}")
    print(f"   Report: {report_path}")
    
    # Create test files
    with open(json_path, 'w') as f:
        json.dump({'test': 'data'}, f)
    
    with open(report_path, 'w') as f:
        f.write("Test analysis summary")
    
    # Complete run
    manager.complete_run("Test run completed successfully")
    
    # List runs
    runs = manager.list_runs()
    print(f"\n📊 Available runs: {len(runs)}")
    for run in runs:
        print(f"   {run['run_id']}: {run.get('description', 'No description')} ({run.get('status', 'unknown')})")


if __name__ == "__main__":
    main()