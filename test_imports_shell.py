#!/usr/bin/env python
"""Quick import diagnostics via Django shell."""
import importlib
import traceback

print("=" * 80)
print("1. Testing: apps.main.views")
print("=" * 80)
try:
    m = importlib.import_module("apps.main.views")
    print("✓ Successfully imported apps.main.views")
    has_subscribe = hasattr(m, "subscribe_push_notifications")
    print(f"  Has 'subscribe_push_notifications': {has_subscribe}")
    if has_subscribe:
        print(f"  Type: {type(getattr(m, 'subscribe_push_notifications'))}")
    # List all attributes containing 'subscribe'
    subscribe_attrs = [a for a in dir(m) if "subscribe" in a.lower()]
    print(f"  Attributes containing 'subscribe': {subscribe_attrs}")
except Exception as e:
    print(f"✗ Import failed:")
    traceback.print_exc()

print("\n" + "=" * 80)
print("2. Testing: apps.portfolio.views.performance_api")
print("=" * 80)
try:
    m = importlib.import_module("apps.portfolio.views.performance_api")
    print("✓ Successfully imported apps.portfolio.views.performance_api")
    has_subscribe = hasattr(m, "subscribe_push_notifications")
    print(f"  Has 'subscribe_push_notifications': {has_subscribe}")
    if has_subscribe:
        print(f"  Type: {type(getattr(m, 'subscribe_push_notifications'))}")
    subscribe_attrs = [a for a in dir(m) if "subscribe" in a.lower()]
    print(f"  Attributes containing 'subscribe': {subscribe_attrs}")
except Exception as e:
    print(f"✗ Import failed:")
    traceback.print_exc()

print("\n" + "=" * 80)
print("3. Testing: apps.portfolio.views (direct)")
print("=" * 80)
try:
    m = importlib.import_module("apps.portfolio.views")
    print("✓ Successfully imported apps.portfolio.views")
    has_subscribe = hasattr(m, "subscribe_push_notifications")
    print(f"  Has 'subscribe_push_notifications': {has_subscribe}")
    if has_subscribe:
        print(f"  Type: {type(getattr(m, 'subscribe_push_notifications'))}")
    subscribe_attrs = [a for a in dir(m) if "subscribe" in a.lower()]
    print(f"  Attributes containing 'subscribe': {subscribe_attrs}")
except Exception as e:
    print(f"✗ Import failed:")
    traceback.print_exc()

print("\n" + "=" * 80)
