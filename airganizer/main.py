"""Main entry point for the Airganizer CLI."""

import argparse
import json
import sys
from pathlib import Path

from airganizer.scanner import FileScanner
from airganizer.config import Config
from airganizer.organizer import StructureOrganizer
from airganizer.ai_providers import OpenAIProvider, AnthropicProvider, OllamaProvider


def main():
    """Main function to run the file organizer."""
    parser = argparse.ArgumentParser(
        description='Airganizer - An AI-powered file organizing system'
    )
    
    parser.add_argument(
        'directory',
        type=str,
        help='Directory to scan and organize'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--tree',
        action='store_true',
        help='Output directory structure as JSON'
    )
    
    parser.add_argument(
        '--organize',
        action='store_true',
        help='Generate organized directory structure using AI'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        metavar='FILE',
        help='Save output to file (structure or tree)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        metavar='FILE',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--init-config',
        action='store_true',
        help='Create default configuration file'
    )
    
    parser.add_argument(
        '--provider',
        type=str,
        choices=['openai', 'anthropic', 'ollama'],
        help='AI provider to use (overrides config)'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=4000,
        help='Maximum chunk size in characters (default: 4000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    args = parser.parse_args()
    
    # Handle init-config
    if args.init_config:
        config = Config(args.config)
        config.create_default_config()
        return
    
    try:
        # Initialize the scanner
        scanner = FileScanner(args.directory)
        
        # Handle tree output mode
        if args.tree:
            tree = scanner.build_tree()
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(tree, f, indent=2)
                print(f"Tree structure saved to: {args.output}")
            else:
                print(json.dumps(tree, indent=2))
            return
        
        # Handle organize mode
        if args.organize:
            # Load configuration
            config = Config(args.config)
            
            # Override provider if specified
            if args.provider:
                config.set('ai_provider', args.provider)
            
            # Get AI provider config
            provider_config = config.get_ai_provider_config()
            
            # Create AI provider
            print(f"Using AI provider: {provider_config['provider']}")
            
            if provider_config['provider'] == 'openai':
                if not provider_config['api_key']:
                    print("Error: OpenAI API key not configured.", file=sys.stderr)
                    print("Set OPENAI_API_KEY environment variable or configure in .airganizer.yaml")
                    sys.exit(1)
                ai_provider = OpenAIProvider(
                    api_key=provider_config['api_key'],
                    model=provider_config['model']
                )
            elif provider_config['provider'] == 'anthropic':
                if not provider_config['api_key']:
                    print("Error: Anthropic API key not configured.", file=sys.stderr)
                    print("Set ANTHROPIC_API_KEY environment variable or configure in .airganizer.yaml")
                    sys.exit(1)
                ai_provider = AnthropicProvider(
                    api_key=provider_config['api_key'],
                    model=provider_config['model']
                )
            else:  # ollama
                ai_provider = OllamaProvider(
                    model=provider_config['model'],
                    base_url=provider_config['base_url']
                )
            
            # Test connection
            print("Testing AI connection...")
            if not ai_provider.test_connection():
                print("Error: Could not connect to AI provider.", file=sys.stderr)
                sys.exit(1)
            print("✓ Connection successful\n")
            
            # Build file tree
            if args.debug:
                print("[DEBUG] Building file tree...")
                print(f"[DEBUG] Root path: {scanner.root_path}")
            else:
                print("Building file tree...")
            
            tree = scanner.build_tree()
            
            if args.debug:
                tree_json = json.dumps(tree)
                print(f"[DEBUG] Tree size: {len(tree_json)} characters")
                print(f"[DEBUG] Root files: {len(tree.get('files', []))}")
                print(f"[DEBUG] Root directories: {len(tree.get('dirs', {}))}")
            
            # Create organizer
            chunk_size = args.chunk_size if args.chunk_size else config.get('chunk_size', 4000)
            
            if args.debug:
                print(f"[DEBUG] Chunk size: {chunk_size} characters")
            
            organizer = StructureOrganizer(
                ai_provider=ai_provider,
                chunk_size=chunk_size,
                debug=args.debug
            )
            
            # Generate structure
            structure = organizer.organize(tree)
            
            # Print structure
            organizer.print_structure()
            
            # Save if output specified
            if args.output:
                organizer.save_structure(args.output)
            
            return
        
        # Default: scan and list files
        print(f"Scanning directory: {scanner.root_path}")
        print("-" * 60)
        
        # Scan for files
        files = scanner.scan()
        
        print(f"\nFound {len(files)} files:\n")
        
        # Display files
        for file_path in sorted(files):
            if args.verbose:
                info = scanner.get_file_info(file_path)
                print(f"  {info['relative_path']}")
                print(f"    Size: {info['size']} bytes")
                print(f"    Extension: {info['extension'] or '(none)'}")
                print()
            else:
                relative = file_path.relative_to(scanner.root_path)
                print(f"  {relative}")
        
        print("-" * 60)
        print(f"Total: {len(files)} files")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
