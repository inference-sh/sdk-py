"""Real API test for sync and async clients."""
import asyncio
from inferencesh import inference, async_inference, TaskStatus

API_KEY = "1nfsh-40d0xtgj90nd2tbtxjg2s96e1p"

TASK_PARAMS = {
    "app": "infsh/text-templating",
    "input": {
        "template": "hello {1}",
        "strings": ["world"]
    },
    "version": "53bk0yzkth5vevthqdvv81zpzy",
    "infra": "cloud",
    "variant": "default"
}


def test_sync():
    """Test synchronous client."""
    print("=" * 50)
    print("SYNC CLIENT TEST")
    print("=" * 50)

    client = inference(api_key=API_KEY, base_url="https://api-dev.inference.sh")

    # Test 1: Run and wait (default)
    print("\n1. tasks.run() - wait for completion (default)")
    task = client.tasks.run(TASK_PARAMS)
    print(f"   Task ID: {task['id']}")
    print(f"   Status: {TaskStatus(task['status']).name}")
    if task["status"] == TaskStatus.COMPLETED:
        print(f"   Output: {task['output']}")

    # Test 2: Run with wait=False
    print("\n2. tasks.run(wait=False) - return immediately")
    task = client.tasks.run(TASK_PARAMS, wait=False)
    print(f"   Task ID: {task['id']}")
    print(f"   Status: {TaskStatus(task['status']).name}")

    # Test 3: get
    print(f"\n3. tasks.get('{task['id']}')")
    task_info = client.tasks.get(task["id"])
    print(f"   Status: {TaskStatus(task_info['status']).name}")

    # Test 4: Stream updates
    print("\n4. tasks.run(stream=True) - stream updates")
    for update in client.tasks.run(TASK_PARAMS, stream=True):
        status = update.get('status')
        if status is not None:
            status_name = TaskStatus(status).name
            print(f"   Status: {status_name}")
            if status == TaskStatus.COMPLETED:
                print(f"   Output: {update.get('output')}")
                break

    # Test 5: stream
    print("\n5. tasks.stream() - stream existing task")
    task = client.tasks.run(TASK_PARAMS, wait=False)
    with client.tasks.stream(task["id"]) as stream:
        for update in stream:
            status = update.get('status')
            if status is not None:
                status_name = TaskStatus(status).name
                print(f"   Status: {status_name}")
                if status == TaskStatus.COMPLETED:
                    print(f"   Output: {update.get('output')}")
                    break

    print("\n✓ Sync client tests passed!")


async def test_async():
    """Test asynchronous client."""
    print("\n" + "=" * 50)
    print("ASYNC CLIENT TEST")
    print("=" * 50)

    client = async_inference(api_key=API_KEY, base_url="https://api-dev.inference.sh")

    # Test 1: Run and wait (default)
    print("\n1. await tasks.run() - wait for completion (default)")
    task = await client.tasks.run(TASK_PARAMS)
    print(f"   Task ID: {task['id']}")
    print(f"   Status: {TaskStatus(task['status']).name}")
    if task["status"] == TaskStatus.COMPLETED:
        print(f"   Output: {task['output']}")

    # Test 2: Run with wait=False
    print("\n2. await tasks.run(wait=False) - return immediately")
    task = await client.tasks.run(TASK_PARAMS, wait=False)
    print(f"   Task ID: {task['id']}")
    print(f"   Status: {TaskStatus(task['status']).name}")

    # Test 3: get
    print(f"\n3. await tasks.get('{task['id']}')")
    task_info = await client.tasks.get(task["id"])
    print(f"   Status: {TaskStatus(task_info['status']).name}")

    # Test 4: Stream updates
    print("\n4. async for in await tasks.run(stream=True)")
    async for update in await client.tasks.run(TASK_PARAMS, stream=True):
        status = update.get('status')
        if status is not None:
            status_name = TaskStatus(status).name
            print(f"   Status: {status_name}")
            if status == TaskStatus.COMPLETED:
                print(f"   Output: {update.get('output')}")
                break

    # Test 5: stream
    print("\n5. async with tasks.stream()")
    task = await client.tasks.run(TASK_PARAMS, wait=False)
    async with client.tasks.stream(task["id"]) as stream:
        async for update in stream:
            status = update.get('status')
            if status is not None:
                status_name = TaskStatus(status).name
                print(f"   Status: {status_name}")
                if status == TaskStatus.COMPLETED:
                    print(f"   Output: {update.get('output')}")
                    break

    print("\n✓ Async client tests passed!")


if __name__ == "__main__":
    # Run sync tests
    test_sync()

    # Run async tests
    asyncio.run(test_async())

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)
