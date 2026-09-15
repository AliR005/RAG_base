"""Общие фикстуры и хелперы тестов."""

import asyncio


def run(coro):
    return asyncio.run(coro)
