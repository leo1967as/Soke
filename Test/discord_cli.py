import argparse
import sys
import json
from discord_utils import DiscordManager

def main():
    parser = argparse.ArgumentParser(description="AI-Friendly Discord CLI Utility")
    parser.add_argument("--guild", default="1475450344334037063", help="Guild ID")
    parser.add_argument("--token-path", default=r"d:\GoogleDriveSync\Work\2026\Sokeber\GoogleSheet\Finance\Resource\Bot_Token", help="Path to bot token")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List Channels
    subparsers.add_parser("list", help="List channels in a compact JSON format")

    # Move Channel
    move_parser = subparsers.add_parser("move", help="Move channel to a category")
    move_parser.add_argument("--channel", required=True)
    move_parser.add_argument("--category", required=True)
    move_parser.add_argument("--pos", type=int, default=None)

    # Rename Channel
    rename_parser = subparsers.add_parser("rename", help="Rename a channel")
    rename_parser.add_argument("--channel", required=True)
    rename_parser.add_argument("--name", required=True)

    # Simple Check
    subparsers.add_parser("check", help="Verify connection and token")

    args = parser.parse_args()

    # Initialize Manager
    manager = DiscordManager(args.token_path)

    if args.command == "list":
        channels = manager.get_channels(args.guild)
        # Format for AI: List only ID, Name, Type, Parent
        compact_list = [
            {"id": c["id"], "name": c["name"], "type": c["type"], "pid": c.get("parent_id")}
            for c in channels
        ]
        print(json.dumps(compact_list))

    elif args.command == "move":
        success, msg = manager.move_channel(args.channel, args.category, args.pos)
        print(json.dumps({"success": success, "response": msg}))

    elif args.command == "rename":
        success, msg = manager.rename_channel(args.channel, args.name)
        print(json.dumps({"success": success, "response": msg}))

    elif args.command == "check":
        channels = manager.get_channels(args.guild)
        if isinstance(channels, list):
            print(json.dumps({"status": "OK", "channel_count": len(channels)}))
        else:
            print(json.dumps({"status": "ERROR", "msg": channels}))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
