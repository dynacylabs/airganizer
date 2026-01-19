#!/usr/bin/env python3
"""Quick test to verify debug flag works."""

import logging
import sys

# Simulate the setup_logging function
def setup_logging(log_level: str) -> None:
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Test different log levels
print("=" * 60)
print("Testing DEBUG logging")
print("=" * 60)
setup_logging('DEBUG')
logger = logging.getLogger(__name__)

logger.debug("This is a DEBUG message - you should see this with --debug")
logger.info("This is an INFO message - you should see this with --verbose or --debug")
logger.warning("This is a WARNING message - you should always see this")

print("\n" + "=" * 60)
print("Testing INFO logging")
print("=" * 60)
# Reset logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

setup_logging('INFO')
logger = logging.getLogger(__name__)

logger.debug("This is a DEBUG message - you should NOT see this with --verbose only")
logger.info("This is an INFO message - you should see this with --verbose")
logger.warning("This is a WARNING message - you should always see this")

print("\n" + "=" * 60)
print("Testing WARNING logging")
print("=" * 60)
# Reset logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

setup_logging('WARNING')
logger = logging.getLogger(__name__)

logger.debug("This is a DEBUG message - you should NOT see this")
logger.info("This is an INFO message - you should NOT see this")
logger.warning("This is a WARNING message - you should see this")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
