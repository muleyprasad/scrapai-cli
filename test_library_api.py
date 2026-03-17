#!/usr/bin/env python3
"""Test script for ScrapAI Python Library API."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set free LLM model for testing (using OpenRouter free tier)
os.environ["SCRAPAI_LLM_API"] = "https://openrouter.ai/api/v1"
os.environ["SCRAPAI_LLM_KEY"] = os.getenv("OPENROUTER_API_KEY", "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")
# Try this specific free model that's known to work
os.environ["SCRAPAI_LLM_MODEL"] = "openrouter/hunter-alpha"

#"anthropic/claude-sonnet-4.6" # "anthropic/claude-3-haiku"
from scrapai import (
    setup,
    verify,
    list_projects,
    list_spiders,
    generate_spider,
    crawl,
    show_items,
    db_stats,
    SpiderNotFoundError,
)


def test_basic_api():
    """Test basic API functions."""
    print("=" * 60)
    print("Testing ScrapAI Library API")
    print("=" * 60)

    # 1. Verify environment
    print("\n1. Testing verify()...")
    result = verify()
    print(f"   ✓ Environment verified: {result.success}")
    print(f"   ✓ Checks: {result.checks}")

    # 2. Get database stats
    print("\n2. Testing db_stats()...")
    stats = db_stats()
    print(f"   ✓ Spiders: {stats.total_spiders}")
    print(f"   ✓ Items: {stats.total_items}")
    print(f"   ✓ Projects: {len(stats.projects)}")

    # 3. List projects
    print("\n3. Testing list_projects()...")
    projects = list_projects()
    print(f"   ✓ Found {len(projects)} projects")
    for p in projects:
        print(f"      - {p.name}: {p.spider_count} spiders")

    # 4. List spiders
    print("\n4. Testing list_spiders()...")
    for project in projects:
        spiders = list_spiders(project=project.name)
        print(f"   Project '{project.name}': {len(spiders)} spiders")
        for s in spiders:
            print(f"      - {s.name}: {s.last_crawl_item_count} items")

    return True


def test_generate_spider_simple():
    """Test simple spider generation with free model.

    Note: Free models on OpenRouter may have limited availability.
    This test demonstrates the API flow - actual generation may require
    a paid model or different API key with free model access.
    """
    print("\n" + "=" * 60)
    print("Testing Spider Generation (Free Model)")
    print("=" * 60)

    # Check for API key - also check environment
    api_key = os.environ.get("SCRAPAI_LLM_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("\n   ⚠️  OPENROUTER_API_KEY not set, skipping generation test")
        print("   Set it with: export OPENROUTER_API_KEY=your_key")
        return None

    from scrapai import generate_spider, delete_spider, list_spiders, crawl, show_items
    from urllib.parse import urlparse

    # Target URL for spider generation
    url = "https://www.remitrate.com/"
    project = "remitrate"

    # Spider name = domain with dots→underscores (no project suffix per CLAUDE.md)
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace("www.", "")
    spider_name = domain.replace(".", "_")

    print(f"\n1. Generating spider for: {url}")
    print(f"   Expected spider name: {spider_name}")
    print(f"   Project: {project}")

    # Check if spider already exists and delete it
    try:
        existing_spiders = list_spiders(project=project)
        spider_exists = any(s.name == spider_name for s in existing_spiders)

        if spider_exists:
            print(f"\n   🗑️  Spider '{spider_name}' already exists. Deleting...")
            delete_spider(name=spider_name, project=project)
            print(f"   ✓ Deleted existing spider '{spider_name}'")
    except Exception as e:
        print(f"   ⚠️  Could not check/delete existing spider: {e}")

    # Generate new spider
    print(f"\n2. Generating spider via LLM...")
    spider_result = None
    try:
        result = generate_spider(
            url=url,
            project=project,
            description="Single page only. Extract the page title from the homepage. Do not follow any links.",
        )
        print(f"   ✓ Spider generated successfully!")
        print(f"   Name: {result.name}")
        print(f"   Project: {result.project}")
        print(f"   Imported: {result.imported}")
        if result.test_crawl_item_count is not None:
            print(f"   Test crawl items: {result.test_crawl_item_count}")
        spider_result = result
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
        return None

    # Get the page title by crawling and showing items
    if spider_result:
        print(f"\n3. Crawling to get page title...")
        try:
            crawl_result = crawl(
                spider=spider_result.name,
                project=project,
                limit=1,
            )
            print(f"   ✓ Crawl completed! Items: {crawl_result.item_count}")

            # Show items to get the title
            items_result = show_items(
                spider=spider_result.name,
                project=project,
                limit=1,
            )
            if items_result.items:
                item = items_result.items[0]
                if item is not None:
                    title = item.get('title', 'N/A')
                    print(f"\n   📄 Page Title: {title}")
                else:
                    print(f"\n   ⚠️  First item is None")
            else:
                print(f"   ⚠️  No items found")
        except Exception as e:
            print(f"   ❌ Crawl/show failed: {e}")

    return spider_result


def test_crawl_and_show(spider_name, project):
    """Test crawling and showing items."""
    if not spider_name:
        print("\n   ⚠️  No spider to test, skipping crawl test")
        return

    print("\n" + "=" * 60)
    print(f"Testing Crawl: {spider_name}")
    print("=" * 60)

    # Run crawl with limit
    print(f"\n1. Running crawl (limit=5)...")
    try:
        result = crawl(
            spider=spider_name,
            project=project,
            limit=5,
        )
        print(f"   ✓ Crawl completed!")
        print(f"   Items: {result.item_count}")
        print(f"   Duration: {result.duration_ms}ms")
        print(f"   Success: {result.success}")

    except SpiderNotFoundError as e:
        print(f"   ❌ Spider not found: {e}")
        return
    except Exception as e:
        print(f"   ❌ Crawl failed: {e}")
        return

    # Show items
    print("\n2. Showing items...")
    items_result = show_items(
        spider=spider_name,
        project=project,
        limit=3,
    )

    print(f"   ✓ Found {len(items_result.items)} items")
    print(f"   Total in DB: {items_result.total_count}")

    for i, item in enumerate(items_result.items, 1):
        print(f"\n   Item {i}:")
        if item is None:
            print(f"      ⚠️  Item is None")
            continue
        print(f"      URL: {item.get('url', 'N/A')}")
        title = item.get('title')
        if title:
            print(f"      Title: {title[:80]}...")
        else:
            print(f"      Title: N/A")
        content = item.get("content", "")
        if content:
            print(f"      Content: {content[:100]}...")


def main():
    """Run all tests."""
    print("\n🔬 ScrapAI Library API Test Suite\n")

    # Test basic API (no API key needed)
    test_basic_api()

    # Test with free LLM (needs OPENROUTER_API_KEY)
    result = test_generate_spider_simple()

    if result:
        # Get the spider name from the result (could be SpiderInfo object or dict)
        if hasattr(result, "name"):
            spider_name = result.name
            project = result.project
        else:
            spider_name = result.get("name") if isinstance(result, dict) else result
            project = result.get("project") if isinstance(result, dict) else "default"
        test_crawl_and_show(spider_name, project)

    print("\n" + "=" * 60)
    print("✅ Test Suite Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
