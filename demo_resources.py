#!/usr/bin/env python3
"""Demo script showing resource-aware model selection."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core import get_system_resources, format_resources
from src.models import get_model_registry
from src.config import get_config

def main():
    print("🔧 Airganizer - Resource-Aware Model Selection Demo")
    print("=" * 70)
    print()
    
    # Show system resources
    resources = get_system_resources()
    formatted = format_resources(resources)
    
    print("💻 System Resources:")
    print(f"  Total RAM:      {formatted['total_ram']}")
    print(f"  Available RAM:  {formatted['available_ram']}")
    print(f"  CPU Cores:      {formatted['cpu_cores']}")
    print(f"  Platform:       {formatted['platform']}")
    print(f"  GPU Available:  {formatted['gpu']}")
    if resources.has_gpu:
        print(f"  GPU Memory:     {formatted['gpu_memory']}")
    print()
    
    # Get model registry
    registry = get_model_registry()
    all_models = registry.get_all_models()
    
    print(f"📚 All Available Models ({len(all_models)} total):")
    print("-" * 70)
    
    for model in all_models:
        ram_str = f"{model.ram_required_gb:.1f}GB" if model.ram_required_gb else "N/A"
        print(f"  {model.name:<25} | {model.provider:<10} | RAM: {ram_str:>7} | {model.type}")
    print()
    
    # Filter by current system resources
    # Leave 20% RAM headroom
    usable_ram = resources.total_ram_gb * 0.8
    suitable_models = registry.filter_by_resources(usable_ram)
    
    print(f"✅ Models That Can Run on This System ({len(suitable_models)}):")
    print(f"   (with {usable_ram:.1f}GB available RAM)")
    print("-" * 70)
    
    for model in suitable_models:
        ram_str = f"{model.ram_required_gb:.1f}GB" if model.ram_required_gb else "N/A"
        print(f"  {model.name:<25} | {model.provider:<10} | RAM: {ram_str:>7}")
    print()
    
    # Show models that won't fit
    unsuitable = [m for m in all_models if m not in suitable_models]
    if unsuitable:
        print(f"❌ Models That Won't Fit ({len(unsuitable)}):")
        print("-" * 70)
        for model in unsuitable:
            ram_str = f"{model.ram_required_gb:.1f}GB" if model.ram_required_gb else "N/A"
            print(f"  {model.name:<25} | Needs: {ram_str:>7} | Available: {usable_ram:.1f}GB")
        print()
    
    # Configuration examples
    print("⚙️  Configuration Examples:")
    print("-" * 70)
    print()
    
    print("1. Limit system RAM usage to 8GB:")
    print("   ~/.config/airganizer/config.json:")
    print('   { "system": { "max_ram_usage_gb": 8.0 } }')
    print()
    
    print("2. Only allow specific models:")
    print('   { "models": {')
    print('       "available_models": {')
    print('         "gpt-4o": {"enabled": true, "allow_online": true},')
    print('         "llama3.2:1b": {"enabled": true, "max_ram_gb": 4.0}')
    print('       }')
    print('     }')
    print('   }')
    print()
    
    print("3. Disable online models (local only):")
    print('   { "models": {')
    print('       "available_models": {')
    print('         "gpt-4o": {"enabled": false},')
    print('         "llama3.2:1b": {"enabled": true}')
    print('       }')
    print('     }')
    print('   }')
    print()
    
    # Smart recommendations based on system
    print("💡 Smart Recommendations for Your System:")
    print("-" * 70)
    
    if resources.total_ram_gb < 8:
        print("⚠️  Limited RAM detected (< 8GB)")
        print("   Recommendation: Use online models (OpenAI/Anthropic)")
        print("   Or use tiny local models like llama3.2:1b")
    elif resources.total_ram_gb < 16:
        print("📊 Moderate RAM detected (8-16GB)")
        print("   Recommendation: Mix of online and small local models")
        print("   Can run: llama3.2:1b, llama3.2, codellama")
    else:
        print("🚀 Sufficient RAM detected (16GB+)")
        print("   Recommendation: Can run most local models")
        print("   Can run: All models including llama3.2-vision")
    print()
    
    if not resources.has_gpu:
        print("ℹ️  No GPU detected - CPU inference will be slower")
        print("   For better performance, consider using online models")
    print()
    
    print("✨ Ready to analyze with resource-aware model selection!")

if __name__ == '__main__':
    main()
