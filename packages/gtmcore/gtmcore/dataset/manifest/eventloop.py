import asyncio


def get_event_loop():
    # Temporary helper method to configure an event loop inside Flask. Can be removed once using an asyncio compatible
    # framework
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop
