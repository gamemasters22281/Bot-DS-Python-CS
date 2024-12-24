import sys
import os
import discord
from discord.ext import commands
import a2s
import urllib.parse
import json
import requests

from config import *

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

def get_config_path(filename):
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), filename)
    else:
        return os.path.join(os.path.dirname(__file__), filename)

def load_servers():
    servers_path = get_config_path('servers.json')
    try:
        with open(servers_path, 'r') as f:
            servers = json.load(f)
            print("Серверы загружены:", servers)
            for key, value in servers.items():
                if not isinstance(value, list) or len(value) != 2 or not all(isinstance(x, str) for x in value):
                    print(f"Некорректный формат адреса сервера: {key} - {value}")
                    return {}
            return {key: [value[0], int(value[1])] for key, value in servers.items()}
    except FileNotFoundError:
        print(f"Файл {servers_path} не найден!")
        return {}

def format_duration(seconds):
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    duration_parts = []

    if days > 0:
        duration_parts.append(f'{days} дн' if days > 1 else '1 дн')
    if hours > 0:
        duration_parts.append(f'{hours} ч' if hours > 1 else '1 ч')
    if minutes > 0:
        duration_parts.append(f'{minutes} мин' if minutes > 1 else '1 мин')
    if seconds > 0:
        duration_parts.append(f'{seconds} сек' if seconds > 1 else '1 сек')

    return ', '.join(duration_parts) if duration_parts else '0 сек'

def get_map_image_url(map_name):
    map_image_url = f"{BASE_IMG_URL}{urllib.parse.quote(map_name)}.jpg"
    try:
        response = requests.head(map_image_url)
        if response.status_code == 200:
            return map_image_url
        else:
            return f"{BASE_IMG_URL}none.jpg"
    except requests.RequestException:
        return f"{BASE_IMG_URL}none.jpg"

@bot.event
async def on_ready():
    print("Bot is ready")

@bot.command(name="server_info", help="Показывает информацию о сервере CS 1.6")
async def server_info(ctx, server_number: int = None):
    if server_number is None:
        await ctx.send("Пожалуйста, укажите номер сервера. Например: !server_info 1")
        return

    if server_number < 1 or server_number > 30:
        await ctx.send("Номер сервера должен быть от 1 до 30.")
        return

    server_key = f"server_{server_number}"
    servers = load_servers()
    if server_key not in servers:
        await ctx.send(f"Сервер с номером {server_number} не найден.")
        return

    address = tuple(servers[server_key])
    print("Адрес сервера:", address)
    try:
        info = a2s.info(address)
        players = a2s.players(address)

        embed = discord.Embed(title=f"Информация о сервере CS 1.6 #{server_number}", color=0x00ff00)
        embed.add_field(name="Название сервера", value=info.server_name, inline=False)
        embed.add_field(name="Карта", value=info.map_name, inline=False)
        embed.add_field(name="Количество игроков", value=f"{info.player_count}/{info.max_players}", inline=False)
        embed.add_field(name="IP адрес", value=f"{address[0]}:{address[1]}", inline=False)

        map_image_url = get_map_image_url(info.map_name)
        embed.set_image(url=map_image_url)

        player_info = ""
        for player in players:
            player_info += f"Ник: {player.name}\n"
            player_info += f"Время на сервере: {format_duration(int(player.duration))}\n"
            player_info += f"Фраги: {player.score}\n\n"

            # Ограничиваем длину поля player_info
            if len(player_info) > 1000:
                break

        if player_info:
            embed.add_field(name="Информация об игроках", value=player_info[:1024], inline=False)
        else:
            embed.add_field(name="Информация об игроках", value="Нет активных игроков", inline=False)

        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="Ошибка", description=f"Не удалось получить информацию о сервере #{server_number}. Ошибка: {str(e)}", color=0xff0000)
        embed.set_image(url=f"{BASE_IMG_URL}none.jpg")
        await ctx.send(embed=embed)

@bot.command(name="list_servers", help="Показывает список доступных серверов")
async def list_servers(ctx):
    servers = load_servers()
    server_list = "\n".join([f"{key.split('_')[1]}: {value[0]}:{value[1]}" for key, value in servers.items()])
    embed = discord.Embed(title="Список доступных серверов", description=server_list, color=0x00ff00)
    await ctx.send(embed=embed)

bot.run(TOKEN)
