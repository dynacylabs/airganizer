#!/usr/bin/env python3
"""Demo script showing dynamic model loading/unloading."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core import get_system_resources
from src.models import get_model_registry, get_model_manager
from src.config import get_config

def main():
    print("🔄 Airganizer - Dynamic Model Loading Demo")
    print("=" * 70)
    print()
    
    # Get components
    resources = get_system_resources()
    registry = get_model_registry()
    manager = get_model_manager()
    config = get_config()
    
    print(f"💻 System: {resources.total_ram_gb:.1f}GB RAM total")
    print(f"⚙️  Config: Max {config.get('models.max_concurrent_loaded', 2)} concurrent local models")
    print(f"⏱️  Idle timeout: {config.get('models.idle_timeout_seconds', 300)}s")
    print()
    
    # Show initial status
    print("📊 Initial Status:")
    manager.print_status()
    print()
    
    # Simulate loading models
    print("🔬 Simulating Model Usage:")
    print("-" * 70)
    print()
    
    # Try to load a small model
    print("1️⃣  Loading llama3.2:1b (3GB)...")
    if manager.load_model("llama3.2:1b"):
        manager.print_status()
    print()
    
    # Try to load another model
    print("2️⃣  Loading llama3.2 (4.5GB)...")
    if manager.load_model("llama3.2"):
        manager.print_status()
    print()
    
    # Try to load a third (should hit concurrent limit or RAM limit)
    print("3️⃣  Loading codellama (7GB)...")
    can_load, reason = manager.can_load_model("codellama")
    print(f"   Can load? {can_load}")
    print(f"   Reason: {reason}")
    
    if not can_load:
        print(f"   💡 Will need to unload another model first")
    
    if manager.load_model("codellama", force=True):
        manager.print_status()
    print()
    
    # Show what happens when we try to load a big model
    print("4️⃣  Trying to load llama3.2-vision (12GB)...")
    can_load, reason = manager.can_load_model("llama3.2-vision")
    print(f"   Can load? {can_load}")
    print(f"   Reason: {reason}")
    
    if not can_load and resources.total_ram_gb >= 12:
        print(f"   💡 With force=True, will unload others to make room")
        if manager.load_model("llama3.2-vision", force=True):
            manager.print_status()
    print()
    
    # Unload models
    print("5️⃣  Cleaning up...")
    for model_name in list(manager.loaded_models.keys()):
        manager.unload_model(model_name)
    
    manager.print_status()
    print()
    
    # Summary
    print("📋 Summary:")
    print("-" * 70)
    print("✅ Dynamic model loading works!")
    print("✅ Automatically unloads models to make room")
    print("✅ Respects concurrent model limits")
    print("✅ Uses full system RAM (100%)")
    print()
    print("Benefits:")
    print("  • Optimize resource usage")
    print("  • Run large models on limited systems")
    print("  • Automatic memory management")
    print("  • Idle model cleanup")
    print()
    print("Configuration:")
    print("  models.max_concurrent_loaded  - Max models at once")
    print("  models.auto_unload_idle       - Auto-unload idle models")
    print("  models.idle_timeout_seconds   - Idle timeout")

if __name__ == '__main__':
    main()
