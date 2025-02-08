import asyncio

from emby_webhook import run_emby_webhook_server

async def main():
    """主函数：同时运行 bot 和 webhook server"""
    # 创建任务
    webhook_task = asyncio.create_task(run_emby_webhook_server())

    # 等待两个任务完成
    await asyncio.gather(webhook_task)


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())